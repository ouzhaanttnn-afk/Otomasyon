"""Background music tests. Real ffmpeg only — skipped otherwise."""
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from beyin101 import music, video  # noqa: E402

FFMPEG = shutil.which("ffmpeg")
FFPROBE = shutil.which("ffprobe")
pytestmark = pytest.mark.skipif(not (FFMPEG and FFPROBE), reason="ffmpeg kurulu değil")


class TestPickRandomTrack:
    def test_none_when_directory_missing(self, tmp_path):
        assert music.pick_random_track(tmp_path / "yok") is None

    def test_none_when_directory_empty(self, tmp_path):
        d = tmp_path / "music"; d.mkdir()
        assert music.pick_random_track(d) is None

    def test_ignores_non_audio_files(self, tmp_path):
        d = tmp_path / "music"; d.mkdir()
        (d / "readme.txt").write_text("not audio")
        assert music.pick_random_track(d) is None

    def test_finds_an_audio_file(self, tmp_path):
        d = tmp_path / "music"; d.mkdir()
        (d / "track.mp3").write_bytes(b"x")
        assert music.pick_random_track(d) == d / "track.mp3"


def _tone(path: Path, seconds: int, freq: int) -> Path:
    subprocess.run(
        [FFMPEG, "-y", "-loglevel", "error", "-f", "lavfi",
         "-i", f"sine=frequency={freq}:duration={seconds}",
         "-c:a", "libmp3lame", str(path)],
        check=True,
    )
    return path


class TestMixWithNarration:
    def test_short_track_loops_to_cover_a_long_narration(self, tmp_path):
        """The real risk here: forgetting -stream_loop would leave the mix
        truncated to the music file's own length instead of the narration's."""
        narration = _tone(tmp_path / "narration.mp3", seconds=8, freq=220)
        short_music = _tone(tmp_path / "music.mp3", seconds=3, freq=880)

        out = music.mix_with_narration(
            narration, short_music, tmp_path / "mixed.mp3", ffmpeg=FFMPEG, volume=0.15
        )

        assert out.exists()
        assert video.probe_duration(FFPROBE, out) == pytest.approx(8, abs=0.3)

    def test_output_has_an_audio_stream(self, tmp_path):
        narration = _tone(tmp_path / "narration.mp3", seconds=4, freq=220)
        track = _tone(tmp_path / "music.mp3", seconds=4, freq=880)
        out = music.mix_with_narration(
            narration, track, tmp_path / "mixed.mp3", ffmpeg=FFMPEG, volume=0.15
        )
        info = subprocess.run([FFMPEG, "-i", str(out)], capture_output=True, text=True).stderr
        assert "Audio:" in info

    def test_longer_track_is_trimmed_not_left_running(self, tmp_path):
        narration = _tone(tmp_path / "narration.mp3", seconds=4, freq=220)
        long_music = _tone(tmp_path / "music.mp3", seconds=20, freq=880)
        out = music.mix_with_narration(
            narration, long_music, tmp_path / "mixed.mp3", ffmpeg=FFMPEG, volume=0.15
        )
        assert video.probe_duration(FFPROBE, out) == pytest.approx(4, abs=0.3)
