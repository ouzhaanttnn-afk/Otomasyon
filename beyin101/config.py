"""Runtime configuration, read from the environment.

Keys live in .env locally and in GitHub Secrets for CI. Nothing secret is
ever written to this file — the repository is public.
"""
from __future__ import annotations

import os
import shutil
from dataclasses import dataclass
from pathlib import Path


def _load_dotenv(path: Path = Path(".env")) -> None:
    """Minimal .env reader so the package has no hard dependency on python-dotenv."""
    if not path.exists():
        return
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, value = line.partition("=")
        os.environ.setdefault(key.strip(), value.strip().strip('"').strip("'"))


def redact(message: object, *secrets: str) -> str:
    """Strip API keys out of anything we are about to print.

    Errors from requests embed the full query string, so an unredacted
    traceback pasted into a forum or an issue leaks the key.
    """
    text = str(message)
    for secret in secrets:
        if secret and len(secret) > 8:
            text = text.replace(secret, f"{secret[:4]}…{secret[-4:]}")
    return text


class ConfigError(RuntimeError):
    """Raised when the environment cannot support a run."""


@dataclass(frozen=True)
class Config:
    elevenlabs_key: str
    elevenlabs_voice: str
    elevenlabs_model: str
    pixabay_key: str
    output_dir: Path
    width: int
    height: int
    shorts_count: int
    short_duration: int

    @classmethod
    def load(cls) -> "Config":
        _load_dotenv()
        missing = [
            name
            for name in ("ELEVENLABS_API_KEY", "PIXABAY_API_KEY")
            if not os.environ.get(name)
        ]
        if missing:
            raise ConfigError(
                "Eksik ortam değişkeni: "
                + ", ".join(missing)
                + "\n.env.example dosyasını .env olarak kopyalayıp anahtarlarını gir."
            )
        return cls(
            elevenlabs_key=os.environ["ELEVENLABS_API_KEY"],
            elevenlabs_voice=os.environ.get(
                "ELEVENLABS_VOICE_ID", "21m00Tcm4TlvDq8ikWAM"
            ),
            elevenlabs_model=os.environ.get(
                "ELEVENLABS_MODEL_ID", "eleven_multilingual_v2"
            ),
            pixabay_key=os.environ["PIXABAY_API_KEY"],
            output_dir=Path(os.environ.get("OUTPUT_DIR", "output")),
            width=int(os.environ.get("VIDEO_WIDTH", 1920)),
            height=int(os.environ.get("VIDEO_HEIGHT", 1080)),
            shorts_count=int(os.environ.get("SHORTS_COUNT", 5)),
            short_duration=int(os.environ.get("SHORT_DURATION", 90)),
        )


def require_ffmpeg() -> tuple[str, str]:
    """Return (ffmpeg, ffprobe) paths, or explain how to install them."""
    ffmpeg = shutil.which("ffmpeg")
    ffprobe = shutil.which("ffprobe")
    if not ffmpeg or not ffprobe:
        raise ConfigError(
            "FFmpeg bulunamadı. Kurulum:\n"
            "  Windows : https://ffmpeg.org/download.html → static build → C:\\ffmpeg\\bin PATH'e ekle\n"
            "  macOS   : brew install ffmpeg\n"
            "  Linux   : sudo apt install ffmpeg"
        )
    return ffmpeg, ffprobe
