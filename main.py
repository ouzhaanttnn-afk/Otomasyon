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
import time

from beyin101.config import Config, ConfigError, redact, require_ffmpeg
from beyin101.batch import run_batch
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

    def api_detail(response) -> str:
        """ElevenLabs explains the refusal in the body; surface it verbatim."""
        try:
            data = response.json()
        except ValueError:
            return response.text[:200]
        detail = data.get("detail", data)
        if isinstance(detail, dict):
            return detail.get("message") or detail.get("status") or str(detail)[:200]
        return str(detail)[:200]

    # A key from the wrong place is indistinguishable from a revoked one in
    # the API's reply, so say so before the request rather than after.
    if not config.elevenlabs_key.startswith("sk_"):
        print(f"{WARN} ElevenLabs anahtarı 'sk_' ile başlamıyor. "
              "Panelden alınan anahtarlar bu önekle gelir; "
              "başka bir değer kopyalanmış olabilir.")

    headers = {"xi-api-key": config.elevenlabs_key}

    # Quota lives behind a permission a narrowly scoped key may not carry, so a
    # refusal here says nothing about whether narration will work.
    try:
        response = requests.get(
            "https://api.elevenlabs.io/v1/user/subscription", headers=headers, timeout=30
        )
        if response.ok:
            data = response.json()
            used = data.get("character_count", 0)
            limit = data.get("character_limit", 0)
            left = limit - used
            print(f"{OK} ElevenLabs kotasi: plan={data.get('tier')} "
                  f"kalan={left}/{limit} karakter")
            if left < total_chars:
                print(f"{WARN} Tüm konular {total_chars} karakter tutuyor, "
                      f"kalan kota yetmiyor. Tek tek üretmeyi dene.")
        else:
            print(f"{WARN} Kota okunamadı ({response.status_code}: "
                  f"{api_detail(response)})")
            print("       Anahtarın 'User' okuma yetkisi yoksa bu normaldir; "
                  "asıl test aşağıda.")
    except Exception as exc:
        print(f"{WARN} Kota sorgulanamadı: {redact(exc, config.elevenlabs_key)}")

    # The real test: synthesise a few characters through the same endpoint the
    # pipeline uses. Costs about seven characters and proves the whole path.
    try:
        response = requests.post(
            f"https://api.elevenlabs.io/v1/text-to-speech/{config.elevenlabs_voice}",
            headers={**headers, "Content-Type": "application/json"},
            json={"text": "Merhaba.", "model_id": config.elevenlabs_model},
            timeout=60,
        )
        if response.ok and response.content[:3] in (b"ID3", b"\xff\xfb", b"\xff\xf3"):
            print(f"{OK} ElevenLabs seslendirme çalışıyor "
                  f"({len(response.content)} bayt ses üretildi)")
        elif response.ok:
            print(f"{OK} ElevenLabs yanıt verdi ({len(response.content)} bayt)")
        else:
            detail = api_detail(response)
            print(f"{BAD} ElevenLabs seslendirme reddedildi "
                  f"({response.status_code}): {detail}")
            if response.status_code == 401:
                print("       Anahtar geçersiz ya da iptal edilmiş. Panelden yeni oluştur:")
                print("       https://elevenlabs.io/app/settings/api-keys")
            elif response.status_code == 400 and "voice" in detail.lower():
                print(f"       ELEVENLABS_VOICE_ID geçersiz olabilir: {config.elevenlabs_voice}")
                print("       ElevenLabs → Voices → sesin sayfası → ID kopyala, .env içine yaz.")
            elif response.status_code in (401, 403):
                print("       Anahtarın 'Text to Speech' yetkisi yok. "
                      "Panelden yetkiyi ekle ya da tam yetkili yeni anahtar oluştur.")
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


def cmd_batch(limit: int | None) -> int:
    """Produce every topic in one unattended run."""
    try:
        config = Config.load()
    except ConfigError as exc:
        print(f"\n❌ {exc}\n")
        return 1

    print("\n🎬 Toplu üretim başlıyor. Bilgisayarı açık bırakman yeterli.\n")
    started = time.time()
    report = run_batch(config, limit=limit)

    print("\n" + "=" * 42)
    print("  TOPLU ÜRETİM RAPORU")
    print("=" * 42)
    for outcome in report.outcomes:
        mark = {"done": "✅", "skipped": "⏭ ", "failed": "❌", "stopped": "⏹ "}[outcome.state]
        print(f"  {mark} {outcome.title}")
        if outcome.state == "failed" and outcome.detail:
            print(f"        {outcome.detail[:110]}")
    print("-" * 42)
    print(f"  Üretilen : {len(report.produced)} video")
    if report.failed:
        print(f"  Başarısız: {len(report.failed)}")
    if report.stopped_reason:
        print(f"  Durdu    : {report.stopped_reason}")
    print(f"  Süre     : {(time.time() - started) / 60:.0f} dakika")
    print(f"  Klasör   : {config.output_dir.resolve()}")
    print(f"  Rapor    : {(config.output_dir / 'toplu_uretim_raporu.txt').resolve()}")
    print()
    return 0 if report.produced else 1


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
    parser.add_argument("--batch", action="store_true",
                        help="gözetimsiz toplu üretim: kota bitene kadar devam eder")
    parser.add_argument("--limit", type=int, default=None,
                        help="--batch ile: en fazla kaç video üretilsin")
    args = parser.parse_args()

    if args.check:
        return cmd_check()
    if args.list:
        return cmd_list()
    if args.batch:
        return cmd_batch(args.limit)
    if args.all:
        return max(run_topic(t.slug) for t in TOPICS)
    if args.topic:
        return run_topic(args.topic)
    return interactive()


if __name__ == "__main__":
    sys.exit(main())
