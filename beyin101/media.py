"""Royalty-free B-roll from Pixabay.

Ten minutes of video needs far more footage than one search returns, so each
topic carries several search terms and the results are pooled. Downloads are
cached by clip id: the second run of a topic costs no bandwidth.
"""
from __future__ import annotations

from pathlib import Path

import requests

from .config import redact

VIDEO_API = "https://pixabay.com/api/videos/"


def interleave_by_query(per_query: dict[str, list[dict]]) -> list[dict]:
    """Round-robin across queries instead of exhausting one before the next.

    A plain dict keyed by clip id, filled query by query, keeps hits in
    insertion order — so if the first query alone returns more hits than the
    download limit, every downloaded clip comes from that one query and the
    rest of the topic's queries are never reached. A topic like "zaman", whose
    first term is "clock", ends up as nothing but spinning clocks for the
    entire video. Round-robin picks one hit per query per round, so the final
    list draws from every query roughly evenly regardless of how many results
    any single one returned.
    """
    order = list(per_query.keys())
    cursors = {q: 0 for q in order}
    interleaved: list[dict] = []
    seen_ids: set[int] = set()

    progressed = True
    while progressed:
        progressed = False
        for query in order:
            hits = per_query[query]
            cursor = cursors[query]
            while cursor < len(hits) and hits[cursor]["id"] in seen_ids:
                cursor += 1
            if cursor < len(hits):
                hit = hits[cursor]
                interleaved.append(hit)
                seen_ids.add(hit["id"])
                cursors[query] = cursor + 1
                progressed = True
            else:
                cursors[query] = cursor

    return interleaved


def search_clips(
    queries: list[str],
    *,
    api_key: str,
    per_query: int = 30,
) -> list[dict]:
    """Pool video results across several search terms, interleaved so a
    single popular query cannot crowd out the rest before download selects
    from the front of the list."""
    per_query_hits: dict[str, list[dict]] = {}
    for query in queries:
        try:
            response = requests.get(
                VIDEO_API,
                params={
                    "key": api_key,
                    "q": query,
                    "per_page": per_query,
                    "video_type": "all",
                    "safesearch": "true",
                    "order": "popular",
                },
                timeout=60,
            )
            response.raise_for_status()
        except requests.RequestException as exc:
            print(f"   ! '{query}' araması başarısız: {redact(exc, api_key)}")
            continue

        per_query_hits[query] = response.json().get("hits", [])

    return interleave_by_query(per_query_hits)


def _best_stream(hit: dict) -> str | None:
    """Prefer the largest rendition that is still sane to download."""
    videos = hit.get("videos", {})
    for size in ("large", "medium", "small", "tiny"):
        entry = videos.get(size)
        if entry and entry.get("url"):
            return entry["url"]
    return None


def download_clips(
    hits: list[dict],
    cache_dir: Path,
    *,
    limit: int,
) -> list[Path]:
    """Download up to `limit` clips, skipping any already cached."""
    cache_dir.mkdir(parents=True, exist_ok=True)
    paths: list[Path] = []

    for hit in hits:
        if len(paths) >= limit:
            break
        url = _best_stream(hit)
        if not url:
            continue

        target = cache_dir / f"pixabay_{hit['id']}.mp4"
        if target.exists() and target.stat().st_size > 0:
            paths.append(target)
            continue

        try:
            with requests.get(url, stream=True, timeout=180) as stream:
                stream.raise_for_status()
                with open(target, "wb") as handle:
                    for block in stream.iter_content(chunk_size=1 << 16):
                        handle.write(block)
        except requests.RequestException as exc:
            print(f"   ! klip {hit['id']} indirilemedi: {exc}")
            target.unlink(missing_ok=True)
            continue

        paths.append(target)
        print(f"   klip {len(paths)}/{limit} indirildi")

    return paths
