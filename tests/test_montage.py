"""Montage tests that need a real ffmpeg.

Skipped automatically when ffmpeg is absent, so CI stays fast, but they run on
a machine that has it — worth doing once before spending API credit, because
they exercise the whole assembly path with synthetic inputs.

    pytest tests/test_montage.py -q
"""
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from beyin101 import video  # noqa: E402

FFMPEG = shutil.which("ffmpeg")
FFPROBE = shutil.which("ffprobe")

pytestmark = pytest.mark.skipif(
    not (FFMPEG and FFPROBE), reason="ffmpeg/ffprobe kurulu değil"
)


def _make(path: Path, size: str, rate: int, seconds: int) -> Path:
    subprocess.run(
        [FFMPEG, "-y", "-loglevel", "error", "-f", "lavfi",
         "-i", f"testsrc=size={size}:duration={seconds}:rate={rate}",
         "-pix_fmt", "yuv420p", "-c:v", "libx264", "-preset", "ultrafast", str(path)],
        check=True,
    )
    return path


def _dimensions(path: Path) -> tuple[int, int]:
    out = subprocess.run(
        [FFPROBE, "-v", "error", "-select_streams", "v:0",
         "-show_entries", "stream=width,height", "-of", "csv=p=0", str(path)],
        capture_output=True, text=True, check=True,
    ).stdout.strip()
    width, height = out.split(",")[:2]
    return int(width), int(height)


@pytest.fixture(scope="module")
def assembled(tmp_path_factory):
    root = tmp_path_factory.mktemp("montage")
    clips_dir = root / "clips"
    clips_dir.mkdir()

    # Deliberately mismatched sources: the concat demuxer rejects these unless
    # normalisation really happens.
    clips = [
        _make(clips_dir / "a.mp4", "1280x720", 25, 6),
        _make(clips_dir / "b.mp4", "640x480", 30, 5),
        _make(clips_dir / "c.mp4", "480x854", 24, 5),
    ]

    narration = root / "narration.mp3"
    subprocess.run(
        [FFMPEG, "-y", "-loglevel", "error", "-f", "lavfi",
         "-i", "sine=frequency=200:duration=40", "-c:a", "libmp3lame", str(narration)],
        check=True,
    )

    work = root / "work"
    work.mkdir()
    normalised = video.normalise_clips(
        clips, work / "norm", ffmpeg=FFMPEG, width=1920, height=1080
    )
    long_video = video.build_long_video(
        normalised, narration, root / "long.mp4", work,
        ffmpeg=FFMPEG, ffprobe=FFPROBE,
    )
    shorts = video.build_shorts(
        long_video, root / "out", "Dopamin: Motivasyonun Kimyası",
        ffmpeg=FFMPEG, ffprobe=FFPROBE, count=3, duration=10,
    )
    return long_video, shorts


def test_mismatched_clips_are_normalised_and_joined(assembled):
    long_video, _ = assembled
    assert _dimensions(long_video) == (1920, 1080)


def test_long_video_matches_the_narration_length(assembled):
    long_video, _ = assembled
    assert video.probe_duration(FFPROBE, long_video) == pytest.approx(40, abs=1.0)


def test_every_short_is_produced(assembled):
    _, shorts = assembled
    assert len(shorts) == 3


def test_shorts_are_vertical(assembled):
    _, shorts = assembled
    for short in shorts:
        assert _dimensions(short) == (1080, 1920)


def test_shorts_are_exactly_the_requested_length(assembled):
    """Input-side seeking snaps to a keyframe and overshoots by seconds on a
    concatenated source; the cut must land where it was asked to."""
    _, shorts = assembled
    for short in shorts:
        assert video.probe_duration(FFPROBE, short) == pytest.approx(10, abs=0.3)
