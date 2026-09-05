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


def search_clips(
    queries: list[str],
    *,
    api_key: str,
    per_query: int = 30,
) -> list[dict]:
    """Pool video results across several search terms, de-duplicated by id."""
    seen: dict[int, dict] = {}
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

        for hit in response.json().get("hits", []):
            seen.setdefault(hit["id"], hit)

    return list(seen.values())


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
