"""Optional background music, mixed under the narration.

There is no automated source for this: Pixabay's public API covers images and
videos only, not music (confirmed against its documented endpoints — there is
no /api/music/ or equivalent). Getting real royalty-free tracks means either
registering for a separate service and its own key, or downloading a few by
hand once (e.g. from the YouTube Audio Library, which needs no account and
many tracks there require no attribution). This module does the second: pick
whatever the user has dropped in music/, mix it in quietly, and do nothing at
all if the folder is empty — the feature is opt-in by the folder's contents.
"""
from __future__ import annotations

import random
import subprocess
from pathlib import Path

AUDIO_EXTENSIONS = {".mp3", ".wav", ".m4a", ".ogg", ".flac"}


def pick_random_track(music_dir: Path) -> Path | None:
    """A random audio file from `music_dir`, or None if there is nothing usable."""
    if not music_dir.is_dir():
        return None
    tracks = [
        p for p in music_dir.iterdir()
        if p.is_file() and p.suffix.lower() in AUDIO_EXTENSIONS
    ]
    return random.choice(tracks) if tracks else None


def mix_with_narration(
    narration: Path,
    music: Path,
    destination: Path,
    *,
    ffmpeg: str,
    volume: float,
) -> Path:
    """Lay `music` under `narration` at a low volume, matched to its length.

    The music track loops indefinitely on the input side; `amix`'s
    `duration=first` stops the output exactly when the narration (the first
    input) ends, so a three-minute track under an eight-minute narration loops
    rather than leaving five minutes silent — the case worth testing, since
    forgetting the loop flag would silently truncate to the shorter input.
    A limiter guards against clipping from the additive mix.
    """
    destination.parent.mkdir(parents=True, exist_ok=True)
    filter_complex = (
        "[0:a]aformat=channel_layouts=stereo[a0];"
        f"[1:a]volume={volume},aformat=channel_layouts=stereo[a1];"
        "[a0][a1]amix=inputs=2:duration=first:dropout_transition=2,"
        "alimiter=limit=0.95[aout]"
    )
    subprocess.run(
        [ffmpeg, "-y", "-hide_banner", "-loglevel", "error",
         "-i", str(narration),
         "-stream_loop", "-1", "-i", str(music),
         "-filter_complex", filter_complex,
         "-map", "[aout]",
         "-c:a", "libmp3lame", "-b:a", "192k",
         str(destination)],
        check=True,
    )
    return destination
