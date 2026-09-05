"""The five launch topics.

Each topic carries the Pixabay search terms that produce usable B-roll for it,
plus the YouTube metadata, so adding a sixth topic is a data edit here and one
new file under scripts/ — no code change.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

SCRIPTS_DIR = Path(__file__).resolve().parent.parent / "scripts"


@dataclass(frozen=True)
class Topic:
    slug: str
    title: str
    description: str
    queries: list[str]
    tags: list[str] = field(default_factory=list)

    @property
    def script_path(self) -> Path:
        return SCRIPTS_DIR / f"{self.slug}.txt"

    def load_script(self) -> str:
        if not self.script_path.exists():
            raise FileNotFoundError(
                f"Metin bulunamadı: {self.script_path}\n"
                "scripts/ altına bu isimle bir .txt dosyası ekle."
            )
        return self.script_path.read_text(encoding="utf-8").strip()


TOPICS: list[Topic] = [
    Topic(
        slug="hafiza",
        title="Hafıza Nasıl Çalışır?",
        description=(
            "Beynin bir anıyı nasıl kaydettiğini, nasıl sakladığını ve neden "
            "unuttuğunu adım adım anlatıyoruz. Hipokampüsten uzun süreli "
            "belleğe, tekrar aralıklarından uyku sırasındaki pekiştirmeye kadar."
        ),
        queries=["brain", "neuron", "memory", "science laboratory", "synapse", "thinking"],
        tags=["hafıza", "beyin", "nörobilim", "bellek", "öğrenme", "psikoloji"],
    ),
    Topic(
        slug="dopamin",
        title="Dopamin: Motivasyonun Kimyası",
        description=(
            "Dopamin bir ödül değil, bir beklenti sinyalidir. Motivasyonun "
            "arkasındaki kimyayı, telefon bildirimlerinin neden bu kadar güçlü "
            "olduğunu ve sistemi nasıl geri kazanacağını anlatıyoruz."
        ),
        queries=["brain chemistry", "molecule", "motivation", "smartphone addiction",
                 "neuron", "laboratory"],
        tags=["dopamin", "motivasyon", "beyin", "nörobilim", "alışkanlık", "psikoloji"],
    ),
    Topic(
        slug="rem-uykusu",
        title="REM Uykusu ve Rüyalar",
        description=(
            "Uyurken beyin kapanmaz, vardiya değiştirir. REM uykusunda ne olduğunu, "
            "rüyaların neye yaradığını ve uykusuzluğun hafızaya ne yaptığını anlatıyoruz."
        ),
        queries=["sleep", "night sky", "dream", "bedroom night", "brain", "stars"],
        tags=["uyku", "rüya", "REM", "beyin", "nörobilim", "sağlık"],
    ),
    Topic(
        slug="kaygi",
        title="Kaygı Beyni Nasıl Etkiler?",
        description=(
            "Kaygı bir karakter zayıflığı değil, aşırı hassaslaşmış bir alarm "
            "sistemidir. Amigdalanın rolünü, kronik stresin beyinde ne değiştirdiğini "
            "ve sistemi yeniden ayarlamanın yollarını anlatıyoruz."
        ),
        queries=["anxiety", "stress", "meditation", "calm nature", "brain", "breathing"],
        tags=["kaygı", "anksiyete", "stres", "beyin", "nörobilim", "psikoloji"],
    ),
    Topic(
        slug="dikkat",
        title="Dikkat ve Konsantrasyon",
        description=(
            "Dikkat bir kas değil, bir filtre. Çoklu görevin neden bir yanılsama "
            "olduğunu, odaklanmanın beyindeki mekanizmasını ve derin çalışmayı "
            "geri kazanmanın yollarını anlatıyoruz."
        ),
        queries=["focus", "concentration", "study", "office work", "brain", "reading"],
        tags=["dikkat", "odaklanma", "konsantrasyon", "verimlilik", "beyin", "nörobilim"],
    ),
]

BY_SLUG = {topic.slug: topic for topic in TOPICS}
