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

from beyin101 import tts, video  # noqa: E402

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


def test_shorts_survive_a_caption_that_cannot_be_drawn(tmp_path, monkeypatch):
    """Claim drawtext is available when it is not, so the captioned command
    fails. The Shorts must still be produced, untitled — losing the title is
    acceptable, losing all five clips is not."""
    clips_dir = tmp_path / "clips"
    clips_dir.mkdir()
    clips = [_make(clips_dir / "a.mp4", "1280x720", 25, 6)]

    narration = tmp_path / "n.mp3"
    subprocess.run(
        [FFMPEG, "-y", "-loglevel", "error", "-f", "lavfi",
         "-i", "sine=frequency=200:duration=20", "-c:a", "libmp3lame", str(narration)],
        check=True,
    )

    work = tmp_path / "w"
    work.mkdir()
    normalised = video.normalise_clips(
        clips, work / "norm", ffmpeg=FFMPEG, width=1920, height=1080
    )
    long_video = video.build_long_video(
        normalised, narration, tmp_path / "long.mp4", work,
        ffmpeg=FFMPEG, ffprobe=FFPROBE,
    )

    monkeypatch.setattr(video, "has_filter", lambda ffmpeg, name: True)
    monkeypatch.setattr(video, "find_font", lambda: "/nonexistent/font.ttf")

    shorts = video.build_shorts(
        long_video, tmp_path / "out", "Dopamin: Motivasyonun Kimyasi",
        ffmpeg=FFMPEG, ffprobe=FFPROBE, count=2, duration=8,
    )
    assert len(shorts) == 2, "altyazı başarısız olunca Shorts kaybolmamalı"
    for short in shorts:
        assert _dimensions(short) == (1080, 1920)


def test_shorts_start_on_the_boundaries_they_are_given(assembled):
    """Cuts must land on the paragraph offsets measured from the narration,
    not on a stopwatch — that is the difference between a Short that opens on
    a thought and one that opens mid-sentence."""
    long_video, _ = assembled
    total = video.probe_duration(FFPROBE, long_video)
    boundaries = [0.0, 8.0, 16.0, 24.0, 32.0]

    out = long_video.parent / "boundary_shorts"
    shorts = video.build_shorts(
        long_video, out, "Sinir Bilim",
        ffmpeg=FFMPEG, ffprobe=FFPROBE, count=2, duration=6,
        boundaries=boundaries,
    )

    assert len(shorts) == 2
    for short in shorts:
        assert video.probe_duration(FFPROBE, short) == pytest.approx(6, abs=0.3)

    chosen = video.choose_short_starts(boundaries, total, 2, 6)
    assert all(c in boundaries for c in chosen), "kesimler sınırlardan seçilmeli"


def test_outro_boundary_is_never_chosen():
    boundaries = [0.0, 60.0, 120.0, 180.0, 240.0]
    chosen = video.choose_short_starts(boundaries, total=300.0, count=3, duration=30)
    assert 240.0 not in chosen, "son paragraf outro, Short oradan başlamamalı"


def test_falls_back_to_even_spacing_without_boundaries():
    # A single boundary leaves nothing usable once the outro is dropped.
    chosen = video.choose_short_starts([0.0], total=300.0, count=3, duration=30)
    assert chosen == video.short_start_times(300.0, 3, 30)


def test_narration_offsets_are_measured_not_estimated(tmp_path):
    """narrate() reuses cached parts without touching the API, so this
    exercises the real offset maths: each boundary must be the summed duration
    of the parts before it, not a guess from character counts."""
    # Each paragraph must exceed half the chunk limit or two will be merged
    # into one chunk and there will be fewer boundaries than parts.
    text = "\n\n".join(f"Paragraf {i} burada devam ediyor. " * 20 for i in range(3))
    chunks = tts.chunk_by_paragraph(text)

    parts_dir = tmp_path / "_tts_parts"
    parts_dir.mkdir()
    lengths = [4, 7, 5]
    assert len(chunks) == len(lengths), f"beklenen parça sayısı değişti: {len(chunks)}"
    for index, seconds in enumerate(lengths):
        subprocess.run(
            [FFMPEG, "-y", "-loglevel", "error", "-f", "lavfi",
             "-i", f"sine=frequency=300:duration={seconds}",
             "-c:a", "libmp3lame", str(parts_dir / f"part_{index:03d}.mp3")],
            check=True,
        )

    destination, offsets = tts.narrate(
        text, tmp_path / "narration.mp3",
        api_key="unused-because-parts-are-cached",
        voice_id="v", model_id="m", ffmpeg=FFMPEG, ffprobe=FFPROBE,
    )

    assert destination.exists()
    assert offsets[0] == 0.0
    assert offsets[1] == pytest.approx(4, abs=0.3)
    assert offsets[2] == pytest.approx(11, abs=0.4)
    assert video.probe_duration(FFPROBE, destination) == pytest.approx(16, abs=0.5)
