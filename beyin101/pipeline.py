"""End-to-end: topic in, finished long video plus Shorts out."""
from __future__ import annotations

import json
import time
from dataclasses import dataclass
from pathlib import Path

from . import media, tts, video
from .config import Config, require_ffmpeg
from .topics import Topic

# One clip is rarely longer than ~20s, so this is roughly 8 minutes of footage
# before anything repeats.
CLIP_TARGET = 24


@dataclass
class Result:
    topic: Topic
    long_video: Path
    shorts: list[Path]
    metadata: Path
    seconds: float


def generate(topic: Topic, config: Config) -> Result:
    ffmpeg, ffprobe = require_ffmpeg()
    started = time.time()

    work = config.output_dir / topic.slug
    work.mkdir(parents=True, exist_ok=True)
    cache = config.output_dir / "_cache"
    temp = work / "_temp"
    temp.mkdir(exist_ok=True)

    print(f"\n▶ {topic.title}")

    script = topic.load_script()
    print(f"  metin: {len(script)} karakter")

    print("  seslendirme…")
    narration = tts.narrate(
        script,
        work / "narration.mp3",
        api_key=config.elevenlabs_key,
        voice_id=config.elevenlabs_voice,
        model_id=config.elevenlabs_model,
        ffmpeg=ffmpeg,
    )
    duration = video.probe_duration(ffprobe, narration)
    print(f"  ses hazır: {duration / 60:.1f} dakika")

    print("  görseller aranıyor…")
    hits = media.search_clips(topic.queries, api_key=config.pixabay_key)
    if not hits:
        raise RuntimeError(
            "Pixabay hiç sonuç döndürmedi. Anahtarı ve internet bağlantısını kontrol et."
        )
    print(f"  {len(hits)} aday klip bulundu, {CLIP_TARGET} tanesi indiriliyor…")
    clips = media.download_clips(hits, cache, limit=CLIP_TARGET)
    if not clips:
        raise RuntimeError("Hiçbir klip indirilemedi.")

    print("  klipler normalize ediliyor…")
    normalised = video.normalise_clips(
        clips, temp, ffmpeg=ffmpeg, width=config.width, height=config.height
    )

    print("  uzun video birleştiriliyor…")
    long_video = video.build_long_video(
        normalised, narration, work / "video_long_1080p.mp4", temp,
        ffmpeg=ffmpeg, ffprobe=ffprobe,
    )

    print("  Shorts kesiliyor…")
    shorts = video.build_shorts(
        long_video, work, topic.title,
        ffmpeg=ffmpeg, ffprobe=ffprobe,
        count=config.shorts_count, duration=config.short_duration,
    )

    metadata_path = work / "metadata.json"
    metadata_path.write_text(
        json.dumps(
            {
                "slug": topic.slug,
                "baslik": topic.title,
                "aciklama": topic.description,
                "etiketler": topic.tags,
                "sure_saniye": round(duration, 1),
                "uzun_video": long_video.name,
                "shorts": [s.name for s in shorts],
                "olusturulma": time.strftime("%Y-%m-%d %H:%M:%S"),
            },
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )

    return Result(
        topic=topic,
        long_video=long_video,
        shorts=shorts,
        metadata=metadata_path,
        seconds=time.time() - started,
    )
