"""Title/description/tags text file — the human-facing counterpart to
metadata.json, meant for pasting into YouTube Studio."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from beyin101 import publish_info  # noqa: E402
from beyin101.topics import TOPICS  # noqa: E402


class TestWriteYoutubeInfo:
    def test_contains_title_description_and_all_tags(self, tmp_path):
        topic = TOPICS[0]
        out = publish_info.write_youtube_info(topic, tmp_path / "info.txt")
        text = out.read_text(encoding="utf-8")

        assert topic.title in text
        assert topic.description in text
        for tag in topic.tags:
            assert tag in text

    def test_tags_are_comma_separated_on_one_line(self, tmp_path):
        """YouTube's tag field takes a single comma-separated paste — tags
        broken across lines would need reassembling by hand."""
        topic = TOPICS[0]
        out = publish_info.write_youtube_info(topic, tmp_path / "info.txt")
        text = out.read_text(encoding="utf-8")
        joined = ", ".join(topic.tags)
        assert joined in text

    def test_creates_missing_parent_directories(self, tmp_path):
        dest = tmp_path / "nested" / "folder" / "info.txt"
        publish_info.write_youtube_info(TOPICS[0], dest)
        assert dest.exists()

    def test_overwrites_an_existing_file(self, tmp_path):
        dest = tmp_path / "info.txt"
        dest.write_text("eski içerik", encoding="utf-8")
        publish_info.write_youtube_info(TOPICS[1], dest)
        assert "eski içerik" not in dest.read_text(encoding="utf-8")
        assert TOPICS[1].title in dest.read_text(encoding="utf-8")


class TestBackfill:
    def test_only_writes_for_topics_with_a_produced_video(self, tmp_path):
        produced, unproduced = TOPICS[0], TOPICS[1]
        folder = tmp_path / produced.slug
        folder.mkdir()
        (folder / "video_long_1080p.mp4").write_bytes(b"x")

        written = publish_info.backfill([produced, unproduced], tmp_path)

        assert written == [produced]
        assert (folder / publish_info.FILENAME).exists()
        assert not (tmp_path / unproduced.slug).exists()

    def test_covers_videos_made_before_this_feature_existed(self, tmp_path):
        """The exact scenario this was built for: an old output folder with
        a video and no info file, from a run that predates this feature."""
        old = TOPICS[2]
        folder = tmp_path / old.slug
        folder.mkdir()
        (folder / "video_long_1080p.mp4").write_bytes(b"x")
        (folder / "shorts_1.mp4").write_bytes(b"x")
        # deliberately no youtube_bilgileri.txt — simulates a pre-feature run

        written = publish_info.backfill([old], tmp_path)

        assert written == [old]
        content = (folder / publish_info.FILENAME).read_text(encoding="utf-8")
        assert old.title in content

    def test_empty_output_directory_writes_nothing(self, tmp_path):
        assert publish_info.backfill(TOPICS[:5], tmp_path) == []

    def test_running_twice_is_safe(self, tmp_path):
        topic = TOPICS[0]
        folder = tmp_path / topic.slug
        folder.mkdir()
        (folder / "video_long_1080p.mp4").write_bytes(b"x")

        first = publish_info.backfill([topic], tmp_path)
        second = publish_info.backfill([topic], tmp_path)
        assert first == second == [topic]
