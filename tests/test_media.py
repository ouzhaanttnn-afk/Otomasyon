"""Query interleaving tests — the fix for the "just a spinning clock" bug.

download_clips takes the first N entries of whatever list_clips returns, so
the ordering that list produces is what actually ends up on screen. These
tests operate on the pure interleaving function; no network involved.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from beyin101 import media  # noqa: E402


def _hits(query: str, ids: list[int]) -> list[dict]:
    return [{"id": i, "q": query} for i in ids]


class TestInterleaveByQuery:
    def test_round_robins_evenly_across_queries(self):
        per_query = {
            "clock": _hits("clock", list(range(1, 31))),      # 30 hits
            "hourglass": _hits("hourglass", [101, 102, 103]),  # 3 hits
            "calendar": _hits("calendar", [201, 202, 203]),    # 3 hits
        }
        result = media.interleave_by_query(per_query)

        # This is the actual bug: taking the first 6 under the old
        # insertion-order behaviour would be six clocks and nothing else.
        first_six = result[:6]
        sources = {h["q"] for h in first_six}
        assert sources == {"clock", "hourglass", "calendar"}, (
            "ilk birkaç klip tek sorgudan geliyor — döngü kırıldı"
        )

    def test_a_query_with_many_more_hits_does_not_starve_the_others(self):
        per_query = {
            "clock": _hits("clock", list(range(1, 31))),
            "sunset": _hits("sunset", [901, 902]),
        }
        result = media.interleave_by_query(per_query)
        top_24 = result[:24]
        assert any(h["q"] == "sunset" for h in top_24), (
            "az sonuçlu sorgu, ilk 24'e hiç girmiyor"
        )

    def test_no_duplicate_ids_even_if_queries_overlap(self):
        per_query = {
            "clock": _hits("clock", [1, 2, 3]),
            "time lapse": [{"id": 2, "q": "time lapse"}, {"id": 4, "q": "time lapse"}],
        }
        result = media.interleave_by_query(per_query)
        ids = [h["id"] for h in result]
        assert len(ids) == len(set(ids)) == 4

    def test_empty_query_result_is_skipped_without_crashing(self):
        per_query = {"clock": _hits("clock", [1, 2]), "obscure term": []}
        result = media.interleave_by_query(per_query)
        assert [h["id"] for h in result] == [1, 2]

    def test_preserves_all_hits_just_reorders_them(self):
        per_query = {
            "a": _hits("a", [1, 2, 3]),
            "b": _hits("b", [4, 5]),
            "c": _hits("c", [6]),
        }
        result = media.interleave_by_query(per_query)
        assert {h["id"] for h in result} == {1, 2, 3, 4, 5, 6}
        assert len(result) == 6
