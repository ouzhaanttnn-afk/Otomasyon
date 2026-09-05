"""The human-readable title/description/tags file for uploading to YouTube.

metadata.json already carries this data, but it's machine-shaped — nested
JSON with Turkish field names, meant for the pipeline to read back, not for a
person to copy out of while filling in YouTube Studio's upload form. This
writes a second, plain-text file with the same three fields laid out so each
one can be selected and pasted on its own.
"""
from __future__ import annotations

from pathlib import Path

from .topics import Topic

FILENAME = "youtube_bilgileri.txt"


def write_youtube_info(topic: Topic, destination: Path) -> Path:
    """Write title/description/tags as plain text, sectioned for copy-paste."""
    destination.parent.mkdir(parents=True, exist_ok=True)
    text = (
        f"BAŞLIK\n"
        f"======\n"
        f"{topic.title}\n"
        f"\n"
        f"AÇIKLAMA\n"
        f"========\n"
        f"{topic.description}\n"
        f"\n"
        f"ETİKETLER (virgülle ayrılmış — YouTube'un etiket kutusuna doğrudan yapıştır)\n"
        f"=========\n"
        f"{', '.join(topic.tags)}\n"
    )
    destination.write_text(text, encoding="utf-8")
    return destination


def backfill(topics: list[Topic], output_dir: Path) -> list[Topic]:
    """Write the info file for every topic whose video already exists.

    Covers videos produced before this feature existed — and any produced
    since, if a run somehow skipped it — since it only checks the filesystem
    and costs nothing to re-run. Topics with no long video yet are left
    alone; there is nothing to publish information for.
    """
    written: list[Topic] = []
    for topic in topics:
        folder = output_dir / topic.slug
        if not (folder / "video_long_1080p.mp4").exists():
            continue
        write_youtube_info(topic, folder / FILENAME)
        written.append(topic)
    return written
