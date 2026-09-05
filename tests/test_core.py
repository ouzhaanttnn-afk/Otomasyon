"""Tests for the logic that runs without network access or ffmpeg."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from beyin101 import tts, video           # noqa: E402
from beyin101.config import redact        # noqa: E402
from beyin101.topics import TOPICS        # noqa: E402


class TestChunking:
    def test_never_splits_a_sentence(self):
        """Every chunk must be whole sentences — a half sentence would be
        read aloud with the wrong intonation and cut off mid-breath."""
        text = "Bir cümle. İki cümle! Üç cümle? Dört cümle."
        sentences = tts.split_sentences(text)
        for chunk in tts.chunk_text(text, limit=20):
            remaining = chunk
            while remaining:
                match = next(
                    (s for s in sentences if remaining.startswith(s)), None
                )
                assert match, f"parça tam cümlelerden oluşmuyor: {chunk!r}"
                remaining = remaining[len(match):].lstrip()

    def test_packs_sentences_up_to_the_limit(self):
        text = "Bir cümle. İki cümle! Üç cümle? Dört cümle."
        assert tts.chunk_text(text, limit=200) == [text]
        assert len(tts.chunk_text(text, limit=11)) == 4

    def test_respects_the_limit(self):
        text = "Beyin inanılmaz bir organdır. " * 300
        for chunk in tts.chunk_text(text, limit=2400):
            assert len(chunk) <= 2400

    def test_keeps_every_word(self):
        text = "Alfa beta. Gama delta. Epsilon zeta."
        joined = " ".join(tts.chunk_text(text, limit=15))
        assert joined.split() == text.split()

    def test_single_short_text_is_one_chunk(self):
        assert len(tts.chunk_text("Kısa bir metin.")) == 1


class TestShortsTiming:
    def test_cuts_stay_inside_the_video(self):
        total, duration = 600.0, 90
        for start in video.short_start_times(total, 5, duration):
            assert 0 <= start <= total - duration

    def test_cuts_are_spread_not_clustered(self):
        starts = video.short_start_times(600.0, 5, 90)
        assert starts[0] == 0
        assert starts[-1] == 510
        gaps = {round(b - a) for a, b in zip(starts, starts[1:])}
        assert len(gaps) == 1, "aralıklar eşit olmalı"

    def test_video_shorter_than_one_short(self):
        assert video.short_start_times(60.0, 5, 90) == [0.0]

    def test_single_cut_comes_from_the_middle(self):
        assert video.short_start_times(300.0, 1, 90) == [105.0]


class TestRedaction:
    # Built from parts rather than written out: a literal key-shaped string
    # here would trip the repository's own secret scanner in CI.
    FAKE = "0" * 8 + "-" + "a" * 25

    def test_masks_a_key_inside_a_url(self):
        message = f"GET https://pixabay.com/api/?key={self.FAKE}&q=brain failed"
        out = redact(message, self.FAKE)
        assert self.FAKE not in out
        assert out.startswith("GET https://pixabay.com/api/?key=0000\u2026")

    def test_masks_every_occurrence(self):
        out = redact(f"{self.FAKE} ve yine {self.FAKE}", self.FAKE)
        assert self.FAKE not in out

    def test_leaves_short_values_alone(self):
        assert redact("hata: abc", "abc") == "hata: abc"


class TestTopics:
    def test_every_topic_has_a_script(self):
        for topic in TOPICS:
            assert topic.script_path.exists(), f"{topic.slug} metni eksik"

    def test_scripts_are_long_enough_for_a_real_video(self):
        for topic in TOPICS:
            # ~15 characters per second of Turkish narration
            assert len(topic.load_script()) > 4000, f"{topic.slug} çok kısa"

    def test_every_topic_has_search_terms_and_tags(self):
        for topic in TOPICS:
            assert topic.queries, f"{topic.slug} için arama terimi yok"
            assert topic.tags, f"{topic.slug} için etiket yok"

    def test_slugs_are_unique(self):
        slugs = [t.slug for t in TOPICS]
        assert len(slugs) == len(set(slugs))


class TestDrawtextEscaping:
    def test_colon_is_escaped(self):
        # An unescaped colon would be read as a filter argument separator
        # and ffmpeg would reject the whole command.
        out = video._escape_drawtext("Dopamin: Motivasyonun Kimyası")
        assert "\\:" in out


class TestFilterDetection:
    """Regression cover for a build that reports libfreetype but ships no
    drawtext: asking for the missing filter fails the entire command, so
    every Short is lost rather than just its caption."""

    LISTING = (
        "Filters:\n"
        "  T.. boxblur           V->V       Blur the input.\n"
        "  ... overlay           VV->V      Overlay a video source.\n"
        "  ..C scale             V->V       Scale the input video size.\n"
    )

    def test_finds_a_present_filter(self):
        assert video.parse_filter_list(self.LISTING, "boxblur")
        assert video.parse_filter_list(self.LISTING, "overlay")

    def test_reports_a_missing_filter(self):
        assert not video.parse_filter_list(self.LISTING, "drawtext")

    def test_does_not_match_description_text(self):
        listing = "  ... something  V->V  wraps drawtext internally\n"
        assert not video.parse_filter_list(listing, "drawtext")
