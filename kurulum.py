#!/usr/bin/env python3
"""Interactive setup: writes .env so nobody has to edit it by hand.

Hand-editing is where this goes wrong — the template and the real file differ
by five characters in the name, and putting keys in the tracked template
publishes them. This asks for the values and writes the right file.

    python kurulum.py
"""
from __future__ import annotations

import sys
from pathlib import Path

ENV = Path(".env")
TEMPLATE = Path(".env.example")

FIELDS = [
    ("ELEVENLABS_API_KEY", "ElevenLabs API anahtarı",
     "https://elevenlabs.io/app/settings/api-keys", True),
    ("PIXABAY_API_KEY", "Pixabay API anahtarı",
     "https://pixabay.com/api/docs/", True),
    ("ELEVENLABS_VOICE_ID", "Seslendirme sesi ID (boş bırak = varsayılan)",
     "ElevenLabs → Voices → sesin sayfası → ID", False),
]

DEFAULTS = {
    "ELEVENLABS_VOICE_ID": "21m00Tcm4TlvDq8ikWAM",
    "ELEVENLABS_MODEL_ID": "eleven_multilingual_v2",
    "OUTPUT_DIR": "output",
}


def read_existing() -> dict[str, str]:
    if not ENV.exists():
        return {}
    values = {}
    for line in ENV.read_text(encoding="utf-8").splitlines():
        if "=" in line and not line.strip().startswith("#"):
            key, _, value = line.partition("=")
            values[key.strip()] = value.strip()
    return values


def mask(value: str) -> str:
    return f"{value[:4]}…{value[-4:]}" if len(value) > 8 else "(kısa)"


def main() -> int:
    print("\n🔑 Beyin 101 — anahtar kurulumu\n")

    if not TEMPLATE.exists():
        print("❌ .env.example bulunamadı. Doğru klasörde misin?")
        print(f"   Şu an buradasın: {Path.cwd()}")
        return 1

    existing = read_existing()
    if existing:
        print("Mevcut .env bulundu. Değiştirmek istemediğin alanı boş geç.\n")

    values = dict(DEFAULTS)
    values.update(existing)

    for name, label, where, required in FIELDS:
        current = existing.get(name, "")
        suffix = f"  [şu an: {mask(current)}]" if current else ""
        print(f"{label}{suffix}")
        print(f"  nereden: {where}")
        try:
            entered = input("  > ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nİptal edildi.")
            return 1

        # People paste with surrounding quotes and stray spaces; strip both
        # rather than writing a value that will not parse later.
        entered = entered.strip().strip('"').strip("'").strip()

        if entered:
            values[name] = entered
        elif current:
            values[name] = current
        elif required:
            print("  ❌ Bu alan zorunlu.\n")
            return 1
        else:
            values[name] = DEFAULTS.get(name, "")
        print()

    lines = [
        "# Bu dosya .gitignore içinde — GitHub'a gitmez.",
        "# Anahtarları asla .env.example dosyasına yazma, o dosya herkese açık.",
        "",
    ]
    for key in ("ELEVENLABS_API_KEY", "ELEVENLABS_VOICE_ID", "ELEVENLABS_MODEL_ID",
                "PIXABAY_API_KEY", "OUTPUT_DIR"):
        lines.append(f"{key}={values.get(key, DEFAULTS.get(key, ''))}")
    ENV.write_text("\n".join(lines) + "\n", encoding="utf-8")

    print(f"✅ {ENV.resolve()} yazıldı.\n")
    print("Şimdi kurulumu doğrula:\n")
    print("    python main.py --check\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
