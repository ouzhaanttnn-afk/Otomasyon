#!/usr/bin/env python3
"""Beyin 101 — komut satırı arayüzü.

  python main.py --check            kurulumu doğrula
  python main.py --list             konuları listele
  python main.py --topic hafiza     tek konu üret
  python main.py --all              hepsini üret
  python main.py                    menüden seç
"""
from __future__ import annotations

import argparse
import sys

from beyin101.config import Config, ConfigError, redact, require_ffmpeg
from beyin101.pipeline import generate
from beyin101.topics import BY_SLUG, TOPICS

OK, BAD, WARN = "  ✅", "  ❌", "  ⚠️ "


def cmd_check() -> int:
    """Validate everything before a run burns any API credit."""
    print("\n🔎 Kurulum kontrolü\n")
    problems = 0

    try:
        ffmpeg, ffprobe = require_ffmpeg()
        print(f"{OK} FFmpeg bulundu: {ffmpeg}")
    except ConfigError as exc:
        print(f"{BAD} {exc}")
        problems += 1

    try:
        config = Config.load()
        print(f"{OK} API anahtarları .env dosyasından okundu")
    except ConfigError as exc:
        print(f"{BAD} {exc}")
        return problems + 1

    total_chars = 0
    for topic in TOPICS:
        if topic.script_path.exists():
            size = len(topic.load_script())
            total_chars += size
            print(f"{OK} metin: {topic.slug} ({size} karakter)")
        else:
            print(f"{BAD} metin eksik: {topic.script_path}")
            problems += 1

    # Live key checks — these are the failures that would otherwise only show
    # up halfway through a paid run.
    import requests

    try:
        response = requests.get(
            "https://api.elevenlabs.io/v1/user/subscription",
            headers={"xi-api-key": config.elevenlabs_key},
            timeout=30,
        )
        if response.ok:
            data = response.json()
            used = data.get("character_count", 0)
            limit = data.get("character_limit", 0)
            left = limit - used
            print(f"{OK} ElevenLabs bağlantısı: plan={data.get('tier')} "
                  f"kalan kota={left}/{limit} karakter")
            if left < total_chars:
                print(f"{WARN} Tüm konular {total_chars} karakter tutuyor, "
                      f"kalan kota yetmiyor. Tek tek üretmeyi dene.")
        else:
            print(f"{BAD} ElevenLabs anahtarı reddedildi ({response.status_code})")
            problems += 1
    except Exception as exc:
        print(f"{BAD} ElevenLabs'e ulaşılamadı: {redact(exc, config.elevenlabs_key)}")
        problems += 1

    try:
        response = requests.get(
            "https://pixabay.com/api/videos/",
            params={"key": config.pixabay_key, "q": "brain", "per_page": 3},
            timeout=30,
        )
        if response.ok:
            print(f"{OK} Pixabay bağlantısı: {response.json().get('totalHits')} sonuç")
        else:
            print(f"{BAD} Pixabay anahtarı reddedildi ({response.status_code})")
            problems += 1
    except Exception as exc:
        print(f"{BAD} Pixabay'e ulaşılamadı: {redact(exc, config.pixabay_key)}")
        problems += 1

    print()
    if problems:
        print(f"❌ {problems} sorun var. Yukarıdakileri düzeltip tekrar çalıştır.\n")
    else:
        print("✅ Her şey hazır. `python main.py` ile başlayabilirsin.\n")
    return problems


def cmd_list() -> int:
    print("\n🧠 Konular\n")
    for index, topic in enumerate(TOPICS, start=1):
        mark = "✅" if topic.script_path.exists() else "❌"
        print(f"  {index}. {mark} {topic.title}   [{topic.slug}]")
    print()
    return 0


def run_topic(slug: str) -> int:
    topic = BY_SLUG.get(slug)
    if not topic:
        print(f"Bilinmeyen konu: {slug}. `--list` ile bak.")
        return 1
    try:
        config = Config.load()
        result = generate(topic, config)
    except (ConfigError, RuntimeError, FileNotFoundError) as exc:
        print(f"\n❌ {exc}\n")
        return 1

    print(f"\n✅ Tamamlandı ({result.seconds / 60:.1f} dakika)")
    print(f"   klasör : {result.long_video.parent}")
    print(f"   uzun   : {result.long_video.name}")
    for short in result.shorts:
        print(f"   shorts : {short.name}")
    print(f"   meta   : {result.metadata.name}\n")
    return 0


def interactive() -> int:
    cmd_list()
    try:
        choice = input("Seç (1-%d): " % len(TOPICS)).strip()
    except (EOFError, KeyboardInterrupt):
        print()
        return 1
    if not choice.isdigit() or not 1 <= int(choice) <= len(TOPICS):
        print("Geçersiz seçim.")
        return 1
    return run_topic(TOPICS[int(choice) - 1].slug)


def main() -> int:
    parser = argparse.ArgumentParser(description="Beyin 101 video otomasyonu")
    parser.add_argument("--check", action="store_true", help="kurulumu doğrula")
    parser.add_argument("--list", action="store_true", help="konuları listele")
    parser.add_argument("--topic", help="üretilecek konunun slug'ı")
    parser.add_argument("--all", action="store_true", help="tüm konuları üret")
    args = parser.parse_args()

    if args.check:
        return cmd_check()
    if args.list:
        return cmd_list()
    if args.all:
        return max(run_topic(t.slug) for t in TOPICS)
    if args.topic:
        return run_topic(args.topic)
    return interactive()


if __name__ == "__main__":
    sys.exit(main())
