"""Real YouTube uploads via the official Data API v3 — not a browser extension.

Nothing here can act on its own: the first run needs a human to sign into the
channel's Google account in a browser and click Allow, exactly once. That step
cannot be automated from a remote session with no browser and no login of its
own. After that one-time consent, a refresh token is cached and every future
call runs unattended.

Two hard limits worth knowing before relying on this:
  - Google's default project quota is 10,000 units/day, and one upload costs
    1,600. That is six uploads a day, not more, unless a quota increase is
    requested (a review process, not a checkbox).
  - Uploads default to "private". This pipeline runs unattended and nothing
    here watches the output before it airs; auto-publishing to a public
    channel with no human review is a mistake waiting to happen. Raise
    YOUTUBE_PRIVACY in .env once you're checking uploads before making them
    public — this default is deliberate, not an oversight.
"""
from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

SCOPES = ["https://www.googleapis.com/auth/youtube.upload"]
# Google's own taxonomy; 27 = Education, the natural fit for this channel.
CATEGORY_EDUCATION = "27"


class UploadQuotaExceeded(RuntimeError):
    """The day's 10,000-unit project quota is spent. Distinct from other
    failures because retrying now will not help — only waiting for the
    daily reset (Pacific time) or requesting a quota increase will."""


class AuthenticationRequired(RuntimeError):
    """No usable token yet, and no interactive terminal to complete the
    one-time consent flow — e.g. running unattended over SSH. Fix: run once
    with a browser available so the flow can complete and cache a token."""


def is_quota_error(exc: Exception) -> bool:
    """Whether an HttpError from the API is the daily quota, not something
    else wearing a 403 (e.g. an unverified-app scope restriction)."""
    body = getattr(exc, "content", b"")
    text = body.decode("utf-8", "ignore") if isinstance(body, bytes) else str(body)
    text = (text + str(exc)).lower()
    return "quotaexceeded" in text or "quota" in text and "exceed" in text


def get_credentials(client_secret_path: Path, token_path: Path):
    """Load a cached token, refreshing if expired; otherwise run the
    one-time interactive consent flow and cache the result.

    Imports the Google libraries lazily so the rest of the package works
    without them installed for anyone who never touches upload."""
    from google.auth.transport.requests import Request
    from google.oauth2.credentials import Credentials
    from google_auth_oauthlib.flow import InstalledAppFlow

    creds = None
    if token_path.exists():
        creds = Credentials.from_authorized_user_file(str(token_path), SCOPES)

    if creds and creds.expired and creds.refresh_token:
        creds.refresh(Request())

    if not creds or not creds.valid:
        if not client_secret_path.exists():
            raise AuthenticationRequired(
                f"{client_secret_path} bulunamadı. Google Cloud Console'dan "
                "indirdiğin OAuth istemci dosyasını bu isimle projeye koy. "
                "README'deki 'YouTube otomatik yükleme' bölümü adım adım anlatıyor."
            )
        try:
            flow = InstalledAppFlow.from_client_secrets_file(
                str(client_secret_path), SCOPES
            )
            creds = flow.run_local_server(port=0)
        except Exception as exc:  # no browser/display reachable
            raise AuthenticationRequired(
                "Tarayıcı açılamadı, ilk izin verme adımı tamamlanamadı. "
                f"Bu adım interaktif bir oturumda çalıştırılmalı. ({exc})"
            ) from exc
        token_path.write_text(creds.to_json(), encoding="utf-8")

    return creds


def build_client(client_secret_path: Path, token_path: Path):
    from googleapiclient.discovery import build

    creds = get_credentials(client_secret_path, token_path)
    return build("youtube", "v3", credentials=creds)


def upload_video(
    youtube,
    video_path: Path,
    *,
    title: str,
    description: str,
    tags: list[str],
    privacy_status: str = "private",
    category_id: str = CATEGORY_EDUCATION,
) -> str:
    """Upload one file, return the resulting video id.

    Raises UploadQuotaExceeded on a quota-exhausted 403 so callers can stop
    a batch cleanly instead of retrying into more failures.
    """
    from googleapiclient.errors import HttpError
    from googleapiclient.http import MediaFileUpload

    body = {
        "snippet": {
            "title": title[:100],  # YouTube's own title length ceiling
            "description": description[:5000],
            "tags": tags,
            "categoryId": category_id,
        },
        "status": {"privacyStatus": privacy_status},
    }
    media = MediaFileUpload(str(video_path), chunksize=-1, resumable=True)

    request = youtube.videos().insert(
        part="snippet,status", body=body, media_body=media
    )
    try:
        response = None
        while response is None:
            _, response = request.next_chunk()
    except HttpError as exc:
        if is_quota_error(exc):
            raise UploadQuotaExceeded(
                "Günlük YouTube yükleme kotası doldu (varsayılan 10.000 birim, "
                "bir yükleme 1.600 birim — günde altı video). Yarın (Pasifik "
                "saatiyle gece yarısı) sıfırlanır."
            ) from exc
        raise

    return response["id"]


@dataclass
class UploadRecord:
    video_id: str
    url: str
    uploaded_at: str


def state_path(folder: Path) -> Path:
    return folder / "yuklendi.json"


def load_upload_state(folder: Path) -> dict[str, UploadRecord]:
    path = state_path(folder)
    if not path.exists():
        return {}
    raw = json.loads(path.read_text(encoding="utf-8"))
    return {
        key: UploadRecord(value["video_id"], value["url"], value["uploaded_at"])
        for key, value in raw.items()
    }


def save_upload_record(folder: Path, key: str, record: UploadRecord) -> None:
    """Merge one more uploaded file into the folder's record, keyed by
    filename (e.g. "video_long_1080p.mp4", "shorts_1.mp4") so a partially
    uploaded topic — long video done, Shorts not yet — resumes correctly
    instead of re-uploading what already made it to YouTube."""
    state = load_upload_state(folder)
    state[key] = record
    path = state_path(folder)
    path.write_text(
        json.dumps(
            {
                k: {"video_id": v.video_id, "url": v.url, "uploaded_at": v.uploaded_at}
                for k, v in state.items()
            },
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )
