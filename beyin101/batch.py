"""Unattended batch production.

Runs every topic in turn so nobody has to sit at the keyboard. Three things
matter for a run nobody is watching: it must not repeat work already done, one
bad topic must not take the rest down with it, and it has to stop by itself
when the account runs out of characters rather than failing twenty times over.
"""
from __future__ import annotations

import time
from dataclasses import dataclass, field
from pathlib import Path

import requests

from .config import Config, redact
from .pipeline import generate
from .topics import TOPICS, Topic
from .tts import QuotaExhausted

# Leave a little headroom so a run does not die mid-narration and waste the
# characters it already spent on the first chunks.
QUOTA_MARGIN = 1500


@dataclass
class Outcome:
    slug: str
    title: str
    state: str          # done | skipped | failed | stopped
    detail: str = ""
    seconds: float = 0.0


@dataclass
class BatchReport:
    outcomes: list[Outcome] = field(default_factory=list)
    stopped_reason: str = ""

    @property
    def produced(self) -> list[Outcome]:
        return [o for o in self.outcomes if o.state == "done"]

    @property
    def failed(self) -> list[Outcome]:
        return [o for o in self.outcomes if o.state == "failed"]


def already_produced(topic: Topic, config: Config) -> bool:
    """Whether this topic is finished, not merely started.

    Checking the long video alone would strand a topic whose Shorts all
    failed: the file exists, so every later run skips it and the Shorts never
    appear. Requiring at least one Short means such a topic is retried, and
    the retry is cheap — the narration and clips are cached, so it costs
    montage time and no API characters.
    """
    folder = config.output_dir / topic.slug
    if not (folder / "video_long_1080p.mp4").exists():
        return False
    return any(folder.glob("shorts_*.mp4"))


def remaining_characters(config: Config) -> int | None:
    """Characters left this period, or None when the key cannot read quota."""
    try:
        response = requests.get(
            "https://api.elevenlabs.io/v1/user/subscription",
            headers={"xi-api-key": config.elevenlabs_key},
            timeout=30,
        )
        if not response.ok:
            return None
        data = response.json()
        return int(data["character_limit"]) - int(data["character_count"])
    except (requests.RequestException, KeyError, ValueError, TypeError):
        return None


def _write_log(report: BatchReport, path: Path) -> None:
    lines = [
        "Beyin 101 - toplu üretim raporu",
        time.strftime("%Y-%m-%d %H:%M:%S"),
        "",
    ]
    for outcome in report.outcomes:
        mark = {"done": "OK  ", "skipped": "ATLA", "failed": "HATA", "stopped": "DUR "}[
            outcome.state
        ]
        line = f"{mark} {outcome.title}"
        if outcome.state == "done":
            line += f"  ({outcome.seconds / 60:.1f} dk)"
        elif outcome.detail:
            line += f"  — {outcome.detail}"
        lines.append(line)
    lines += [
        "",
        f"Üretilen : {len(report.produced)}",
        f"Başarısız: {len(report.failed)}",
    ]
    if report.stopped_reason:
        lines.append(f"Durma sebebi: {report.stopped_reason}")
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def run_batch(config: Config, *, limit: int | None = None) -> BatchReport:
    report = BatchReport()
    config.output_dir.mkdir(parents=True, exist_ok=True)
    log_path = config.output_dir / "toplu_uretim_raporu.txt"

    remaining = remaining_characters(config)
    if remaining is None:
        print("ℹ Kalan kota okunamadı; kota bitince üretim kendiliğinden duracak.\n")
    else:
        print(f"ℹ Kalan kota: {remaining} karakter\n")

    produced = 0
    for topic in TOPICS:
        if limit is not None and produced >= limit:
            report.stopped_reason = f"istenen {limit} video üretildi"
            break

        if already_produced(topic, config):
            print(f"⏭  {topic.title} — zaten üretilmiş, atlanıyor")
            report.outcomes.append(
                Outcome(topic.slug, topic.title, "skipped", "zaten üretilmiş")
            )
            continue

        try:
            needed = len(topic.load_script())
        except FileNotFoundError as exc:
            report.outcomes.append(Outcome(topic.slug, topic.title, "failed", str(exc)))
            continue

        if remaining is not None and remaining < needed + QUOTA_MARGIN:
            reason = (
                f"kalan kota {remaining} karakter, "
                f"sıradaki metin {needed} karakter gerektiriyor"
            )
            print(f"\n⏹  Duruluyor: {reason}")
            report.stopped_reason = reason
            report.outcomes.append(Outcome(topic.slug, topic.title, "stopped", reason))
            break

        try:
            result = generate(topic, config)
        except QuotaExhausted as exc:
            print(f"\n⏹  Duruluyor: {exc}")
            report.stopped_reason = str(exc)
            report.outcomes.append(Outcome(topic.slug, topic.title, "stopped", str(exc)))
            break
        except Exception as exc:  # one bad topic must not end the run
            message = redact(exc, config.elevenlabs_key, config.pixabay_key)
            print(f"   ❌ {topic.title} üretilemedi: {message}")
            report.outcomes.append(
                Outcome(topic.slug, topic.title, "failed", message[:200])
            )
            _write_log(report, log_path)
            continue

        produced += 1
        report.outcomes.append(
            Outcome(topic.slug, topic.title, "done", seconds=result.seconds)
        )
        if remaining is not None:
            remaining -= needed
        print(f"   ✅ {topic.title} hazır ({result.seconds / 60:.1f} dk)"
              + (f", kalan kota ~{remaining}" if remaining is not None else ""))
        _write_log(report, log_path)

    _write_log(report, log_path)
    return report
