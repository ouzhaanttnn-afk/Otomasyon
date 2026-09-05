"""Control-flow tests for the unattended run.

Nobody is watching a batch, so the parts that matter are the ones that decide
whether to keep going: skipping finished work, surviving a bad topic, and
stopping when the account is out of characters instead of failing repeatedly.
Production itself is stubbed — the montage is covered elsewhere.
"""
import sys
from pathlib import Path
from types import SimpleNamespace

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from beyin101 import batch  # noqa: E402
from beyin101.tts import QuotaExhausted  # noqa: E402


@pytest.fixture
def config(tmp_path):
    return SimpleNamespace(
        output_dir=tmp_path / "output",
        elevenlabs_key="sk_test_key_value",
        pixabay_key="0000-test",
    )


def _stub_generate(calls, *, fail_on=(), quota_on=None):
    def generate(topic, config):
        calls.append(topic.slug)
        if quota_on and topic.slug == quota_on:
            raise QuotaExhausted("kota bitti")
        if topic.slug in fail_on:
            raise RuntimeError("Pixabay hiç sonuç döndürmedi")
        out = config.output_dir / topic.slug
        out.mkdir(parents=True, exist_ok=True)
        (out / "video_long_1080p.mp4").write_bytes(b"x")
        return SimpleNamespace(seconds=61.0)
    return generate


def test_produces_every_topic_when_quota_allows(monkeypatch, config):
    calls = []
    monkeypatch.setattr(batch, "generate", _stub_generate(calls))
    monkeypatch.setattr(batch, "remaining_characters", lambda c: 10_000_000)

    report = batch.run_batch(config)

    assert len(calls) == len(batch.TOPICS)
    assert len(report.produced) == len(batch.TOPICS)
    assert not report.failed


def test_limit_caps_the_run(monkeypatch, config):
    calls = []
    monkeypatch.setattr(batch, "generate", _stub_generate(calls))
    monkeypatch.setattr(batch, "remaining_characters", lambda c: 10_000_000)

    report = batch.run_batch(config, limit=3)

    assert len(calls) == 3
    assert len(report.produced) == 3
    assert "3" in report.stopped_reason


def test_already_produced_topics_are_skipped(monkeypatch, config):
    first = batch.TOPICS[0]
    done = config.output_dir / first.slug
    done.mkdir(parents=True)
    # Finished means the long video *and* its Shorts; see the retry test below.
    (done / "video_long_1080p.mp4").write_bytes(b"x")
    (done / "shorts_1.mp4").write_bytes(b"x")

    calls = []
    monkeypatch.setattr(batch, "generate", _stub_generate(calls))
    monkeypatch.setattr(batch, "remaining_characters", lambda c: 10_000_000)

    report = batch.run_batch(config)

    assert first.slug not in calls, "biten iş tekrar üretilmemeli"
    assert any(o.state == "skipped" for o in report.outcomes)


def test_one_failure_does_not_end_the_run(monkeypatch, config):
    broken = batch.TOPICS[1].slug
    calls = []
    monkeypatch.setattr(batch, "generate", _stub_generate(calls, fail_on={broken}))
    monkeypatch.setattr(batch, "remaining_characters", lambda c: 10_000_000)

    report = batch.run_batch(config)

    assert len(calls) == len(batch.TOPICS), "hatadan sonra devam etmeli"
    assert len(report.failed) == 1
    assert len(report.produced) == len(batch.TOPICS) - 1


def test_stops_before_starting_a_topic_it_cannot_afford(monkeypatch, config):
    calls = []
    monkeypatch.setattr(batch, "generate", _stub_generate(calls))
    # Enough for the first topic only.
    first_cost = len(batch.TOPICS[0].load_script())
    monkeypatch.setattr(
        batch, "remaining_characters", lambda c: first_cost + batch.QUOTA_MARGIN + 10
    )

    report = batch.run_batch(config)

    assert len(calls) == 1, "kota yetmeyince ikinciye başlamamalı"
    assert "kota" in report.stopped_reason.lower()


def test_stops_when_the_api_reports_quota_exhausted(monkeypatch, config):
    third = batch.TOPICS[2].slug
    calls = []
    monkeypatch.setattr(batch, "generate", _stub_generate(calls, quota_on=third))
    # Quota unreadable, so exhaustion can only be learned from the failure.
    monkeypatch.setattr(batch, "remaining_characters", lambda c: None)

    report = batch.run_batch(config)

    assert len(calls) == 3, "kota hatasından sonra devam etmemeli"
    assert len(report.produced) == 2
    assert report.stopped_reason


def test_report_file_is_written_for_the_user_to_read_later(monkeypatch, config):
    calls = []
    monkeypatch.setattr(batch, "generate", _stub_generate(calls, fail_on={batch.TOPICS[0].slug}))
    monkeypatch.setattr(batch, "remaining_characters", lambda c: 10_000_000)

    batch.run_batch(config, limit=2)

    report_file = config.output_dir / "toplu_uretim_raporu.txt"
    assert report_file.exists()
    text = report_file.read_text(encoding="utf-8")
    assert "Üretilen" in text and "HATA" in text


def test_failure_messages_do_not_leak_the_api_key(monkeypatch, config):
    def leaky(topic, config):
        raise RuntimeError(f"istek başarısız: key={config.elevenlabs_key}")

    monkeypatch.setattr(batch, "generate", leaky)
    monkeypatch.setattr(batch, "remaining_characters", lambda c: 10_000_000)

    report = batch.run_batch(config, limit=1)

    joined = " ".join(o.detail for o in report.outcomes)
    assert config.elevenlabs_key not in joined


def test_a_topic_whose_shorts_all_failed_is_retried(monkeypatch, config):
    """A long video with no Shorts is unfinished work. Skipping on the long
    video alone would strand it forever, which is exactly what happened when
    a filter fault wiped out every Short in a run."""
    stranded = batch.TOPICS[0]
    folder = config.output_dir / stranded.slug
    folder.mkdir(parents=True)
    (folder / "video_long_1080p.mp4").write_bytes(b"x")   # no shorts_*.mp4

    calls = []
    monkeypatch.setattr(batch, "generate", _stub_generate(calls))
    monkeypatch.setattr(batch, "remaining_characters", lambda c: 10_000_000)

    batch.run_batch(config, limit=1)

    assert calls == [stranded.slug], "Shorts'u eksik konu yeniden denenmeli"


def test_a_fully_finished_topic_is_left_alone(monkeypatch, config):
    done = batch.TOPICS[0]
    folder = config.output_dir / done.slug
    folder.mkdir(parents=True)
    (folder / "video_long_1080p.mp4").write_bytes(b"x")
    (folder / "shorts_1.mp4").write_bytes(b"x")

    calls = []
    monkeypatch.setattr(batch, "generate", _stub_generate(calls))
    monkeypatch.setattr(batch, "remaining_characters", lambda c: 10_000_000)

    batch.run_batch(config, limit=1)

    assert done.slug not in calls
