"""Pure-logic tests for the YouTube uploader.

The actual API calls need a real OAuth token and a live upload, neither of
which exist in a test environment — those parts can only be exercised for
real. What's tested here is everything that doesn't need the network: quota
error classification and the per-file upload state that lets a batch resume
without re-uploading what already made it to YouTube.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from beyin101 import youtube_upload as yu  # noqa: E402


class FakeHttpError(Exception):
    def __init__(self, content: bytes):
        self.content = content
        super().__init__(content.decode())


class TestQuotaDetection:
    def test_recognises_the_documented_quota_error(self):
        body = (
            b'{"error": {"errors": [{"reason": "quotaExceeded", '
            b'"message": "The request cannot be completed because you have '
            b'exceeded your quota."}]}}'
        )
        assert yu.is_quota_error(FakeHttpError(body))

    def test_does_not_flag_an_unrelated_403(self):
        body = b'{"error": {"errors": [{"reason": "forbidden", "message": "Access denied"}]}}'
        assert not yu.is_quota_error(FakeHttpError(body))

    def test_does_not_flag_a_plain_upload_failure(self):
        body = b'{"error": {"errors": [{"reason": "backendError"}]}}'
        assert not yu.is_quota_error(FakeHttpError(body))


class TestUploadState:
    def test_no_state_file_means_empty_state(self, tmp_path):
        assert yu.load_upload_state(tmp_path) == {}

    def test_records_round_trip(self, tmp_path):
        record = yu.UploadRecord("abc123", "https://youtu.be/abc123", "2026-09-06 10:00:00")
        yu.save_upload_record(tmp_path, "video_long_1080p.mp4", record)

        loaded = yu.load_upload_state(tmp_path)
        assert loaded["video_long_1080p.mp4"].video_id == "abc123"
        assert loaded["video_long_1080p.mp4"].url == "https://youtu.be/abc123"

    def test_partial_upload_resumes_correctly(self, tmp_path):
        """The exact scenario this exists for: the long video uploaded, a
        Short then hit the daily quota. Re-running must not re-upload the
        long video, and must still attempt the missing Shorts."""
        long_record = yu.UploadRecord("long1", "https://youtu.be/long1", "t1")
        yu.save_upload_record(tmp_path, "video_long_1080p.mp4", long_record)

        state = yu.load_upload_state(tmp_path)
        assert "video_long_1080p.mp4" in state
        assert "shorts_1.mp4" not in state

    def test_saving_one_file_does_not_erase_another(self, tmp_path):
        yu.save_upload_record(
            tmp_path, "video_long_1080p.mp4",
            yu.UploadRecord("a", "https://youtu.be/a", "t"),
        )
        yu.save_upload_record(
            tmp_path, "shorts_1.mp4",
            yu.UploadRecord("b", "https://youtu.be/b", "t"),
        )
        state = yu.load_upload_state(tmp_path)
        assert set(state.keys()) == {"video_long_1080p.mp4", "shorts_1.mp4"}

    def test_re_uploading_the_same_file_overwrites_its_own_record(self, tmp_path):
        yu.save_upload_record(
            tmp_path, "video_long_1080p.mp4",
            yu.UploadRecord("old", "https://youtu.be/old", "t1"),
        )
        yu.save_upload_record(
            tmp_path, "video_long_1080p.mp4",
            yu.UploadRecord("new", "https://youtu.be/new", "t2"),
        )
        state = yu.load_upload_state(tmp_path)
        assert len(state) == 1
        assert state["video_long_1080p.mp4"].video_id == "new"
