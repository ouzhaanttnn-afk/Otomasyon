"""Turkish narration via ElevenLabs.

A ten minute script is far longer than one request accepts, so the text is
split on sentence boundaries and rendered in chunks. Each request is given the
neighbouring text as context, which keeps intonation continuous across the
joins instead of resetting at every chunk.
"""
from __future__ import annotations

import re
import subprocess
import time
from pathlib import Path

import requests

from .video import probe_duration

API = "https://api.elevenlabs.io/v1/text-to-speech"
# Well under every tier's per-request ceiling, and short enough that a failed
# chunk is cheap to retry.
CHUNK_CHARS = 2400
# Narration is chunked smaller than the API requires so that paragraph
# boundaries land often enough to give a Short somewhere sensible to start.
# Small enough for cut points, large enough that intonation does not reset
# every few sentences.
PARAGRAPH_CHUNK_CHARS = 1100


class QuotaExhausted(RuntimeError):
    """The account is out of characters.

    Distinct from other failures because it is not worth retrying and, in a
    batch, it means every remaining topic will fail the same way — so the run
    should stop rather than grind through nineteen identical errors.
    """


def split_sentences(text: str) -> list[str]:
    parts = re.split(r"(?<=[.!?…])\s+", text.strip())
    return [p.strip() for p in parts if p.strip()]


def chunk_text(text: str, limit: int = CHUNK_CHARS) -> list[str]:
    """Group sentences into chunks without ever splitting mid-sentence."""
    chunks: list[str] = []
    current = ""
    for sentence in split_sentences(text):
        if current and len(current) + len(sentence) + 1 > limit:
            chunks.append(current)
            current = sentence
        else:
            current = f"{current} {sentence}".strip()
    if current:
        chunks.append(current)
    return chunks


def chunk_by_paragraph(text: str, limit: int = PARAGRAPH_CHUNK_CHARS) -> list[str]:
    """Chunk on paragraph breaks, falling back to sentences when one is long.

    Every chunk boundary becomes a known point on the audio timeline once the
    parts are rendered, and a paragraph start is where a Short can begin
    without opening mid-thought. Sentence-level chunking would give more cut
    points but many of them land mid-argument.
    """
    chunks: list[str] = []
    current = ""
    for para in (p.strip() for p in text.split("\n\n")):
        if not para:
            continue
        if len(para) > limit:
            if current:
                chunks.append(current)
                current = ""
            chunks.extend(chunk_text(para, limit))
            continue
        if current and len(current) + len(para) + 1 > limit:
            chunks.append(current)
            current = para
        else:
            current = f"{current} {para}".strip()
    if current:
        chunks.append(current)
    return chunks


def _is_quota_error(response) -> bool:
    """Whether a refusal is about exhausted characters rather than a bad key."""
    try:
        detail = response.json().get("detail", {})
    except ValueError:
        return "quota" in response.text.lower()
    text = str(detail).lower()
    return "quota" in text or "exceeded" in text or "insufficient" in text


def _render_chunk(
    text: str,
    *,
    api_key: str,
    voice_id: str,
    model_id: str,
    previous_text: str | None,
    next_text: str | None,
    retries: int = 3,
) -> bytes:
    payload = {
        "text": text,
        "model_id": model_id,
        "voice_settings": {
            "stability": 0.45,
            "similarity_boost": 0.75,
            "style": 0.30,
            "use_speaker_boost": True,
        },
    }
    if previous_text:
        payload["previous_text"] = previous_text[-500:]
    if next_text:
        payload["next_text"] = next_text[:500]

    last_error: Exception | None = None
    for attempt in range(retries):
        try:
            response = requests.post(
                f"{API}/{voice_id}",
                headers={"xi-api-key": api_key, "Content-Type": "application/json"},
                json=payload,
                timeout=180,
            )
            if response.status_code == 429:
                wait = 2 ** attempt * 5
                print(f"   hız sınırı, {wait}s bekleniyor…")
                time.sleep(wait)
                continue
            if response.status_code in (401, 402) and _is_quota_error(response):
                raise QuotaExhausted(
                    "ElevenLabs karakter kotası bitti. "
                    "Aylık kota yenilenene kadar yeni seslendirme üretilemez."
                )
            response.raise_for_status()
            return response.content
        except QuotaExhausted:
            raise
        except requests.RequestException as exc:  # network or HTTP error
            last_error = exc
            if attempt == retries - 1:
                break
            time.sleep(2 ** attempt * 3)
    raise RuntimeError(f"ElevenLabs isteği başarısız: {last_error}")


def narrate(
    text: str,
    destination: Path,
    *,
    api_key: str,
    voice_id: str,
    model_id: str,
    ffmpeg: str,
    ffprobe: str | None = None,
) -> tuple[Path, list[float]]:
    """Render `text` to one mp3 and report where each chunk begins.

    The offsets are measured from the rendered parts rather than estimated
    from character counts, so they are exact. They are what lets a Short start
    on a paragraph instead of wherever a stopwatch happens to land.
    """
    chunks = chunk_by_paragraph(text)
    destination.parent.mkdir(parents=True, exist_ok=True)
    parts_dir = destination.parent / "_tts_parts"
    parts_dir.mkdir(exist_ok=True)

    part_paths: list[Path] = []
    for index, chunk in enumerate(chunks):
        part = parts_dir / f"part_{index:03d}.mp3"
        if not part.exists():  # resume a half-finished run instead of re-paying
            print(f"   ses {index + 1}/{len(chunks)} ({len(chunk)} karakter)…")
            audio = _render_chunk(
                chunk,
                api_key=api_key,
                voice_id=voice_id,
                model_id=model_id,
                previous_text=chunks[index - 1] if index else None,
                next_text=chunks[index + 1] if index + 1 < len(chunks) else None,
            )
            part.write_bytes(audio)
        part_paths.append(part)

    offsets: list[float] = []
    if ffprobe:
        running = 0.0
        for part in part_paths:
            offsets.append(running)
            running += probe_duration(ffprobe, part)

    if len(part_paths) == 1:
        part_paths[0].replace(destination)
    else:
        listing = parts_dir / "concat.txt"
        listing.write_text(
            "\n".join(f"file '{p.resolve().as_posix()}'" for p in part_paths),
            encoding="utf-8",
        )
        subprocess.run(
            [ffmpeg, "-y", "-hide_banner", "-loglevel", "error",
             "-f", "concat", "-safe", "0", "-i", str(listing),
             "-c:a", "libmp3lame", "-b:a", "192k", str(destination)],
            check=True,
        )
    return destination, offsets
