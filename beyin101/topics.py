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
    Topic(
        slug="aliskanlik",
        title="Alışkanlıklar Nasıl Oluşur?",
        description=(
            "Günlük davranışlarının yarısı karar değil, alışkanlık. Beynin bir "
            "davranışı nasıl otomatiğe aldığını, işaret-rutin-ödül döngüsünü ve "
            "alışkanlık kurmanın işe yarayan yollarını anlatıyoruz."
        ),
        queries=["habit", "morning routine", "brain", "daily life", "discipline", "repetition"],
        tags=["alışkanlık", "davranış", "beyin", "nörobilim", "psikoloji", "kişisel gelişim"],
    ),
    Topic(
        slug="erteleme",
        title="Erteleme: Neden Yapamıyoruz?",
        description=(
            "Erteleme tembellik değil, duygudan kaçış. Beyinde ne olduğunu ve "
            "iradeyi zorlamadan döngüyü kırmanın yollarını anlatıyoruz."
        ),
        queries=["procrastination", "deadline", "office stress", "clock", "student study", "desk"],
        tags=["erteleme", "prokrastinasyon", "motivasyon", "beyin", "psikoloji", "verimlilik"],
    ),
    Topic(
        slug="noroplastisite",
        title="Beyin Kendini Değiştirebilir mi?",
        description=(
            "Yetişkin beyni sabit değil. Londra taksi şoförlerinden müzisyenlere, "
            "beynin deneyimle nasıl yeniden şekillendiğini anlatıyoruz."
        ),
        queries=["neuron", "brain scan", "learning", "taxi london", "musician", "science"],
        tags=["nöroplastisite", "beyin", "öğrenme", "nörobilim", "gelişim"],
    ),
    Topic(
        slug="muzik",
        title="Müzik Beyni Nasıl Değiştirir?",
        description=(
            "Müzik beynin en geniş alanını aynı anda çalıştıran şeylerden biri. "
            "Tüylerin neden diken diken olduğunu ve müziğin hafızayla kurduğu "
            "olağanüstü bağı anlatıyoruz."
        ),
        queries=["music", "concert", "headphones", "piano", "orchestra", "sound waves"],
        tags=["müzik", "beyin", "nörobilim", "hafıza", "duygu"],
    ),
    Topic(
        slug="egzersiz",
        title="Egzersiz ve Beyin",
        description=(
            "Hareketin beyne ne yaptığı çoğu insanın tahmininden büyük. "
            "Hipokampüs, büyüme faktörleri ve ruh hali üzerindeki ölçülmüş "
            "etkileri anlatıyoruz."
        ),
        queries=["running", "exercise", "gym", "jogging park", "fitness", "brain"],
        tags=["egzersiz", "spor", "beyin", "sağlık", "nörobilim", "hafıza"],
    ),
    Topic(
        slug="beslenme",
        title="Beslenme Beyni Nasıl Etkiler?",
        description=(
            "Beyin enerjinin beşte birini tüketiyor. Ne yediğinin gerçekte ne "
            "kadar fark yarattığını ve internetteki iddiaların hangisinin doğru "
            "olduğunu anlatıyoruz."
        ),
        queries=["healthy food", "vegetables", "fish omega", "cooking", "nuts", "brain"],
        tags=["beslenme", "beyin", "sağlık", "omega 3", "nörobilim"],
    ),
    Topic(
        slug="onyargilar",
        title="Bilişsel Önyargılar",
        description=(
            "Kararlarını gerekçelerle verdiğini sanıyorsun. Beynin kullandığı "
            "kısayolları ve bunların ürettiği sistematik yanılgıları anlatıyoruz."
        ),
        queries=["decision", "chess thinking", "business meeting", "choice", "brain", "puzzle"],
        tags=["önyargı", "karar verme", "psikoloji", "beyin", "davranışsal ekonomi"],
    ),
    Topic(
        slug="duygular",
        title="Duygular Nereden Geliyor?",
        description=(
            "Önce mi korkarsın, önce mi kalbin hızlanır? Duyguların bedensel "
            "sinyal ile bağlamın yorumundan nasıl doğduğunu anlatıyoruz."
        ),
        queries=["emotion", "face expression", "heart", "people talking", "brain", "mood"],
        tags=["duygu", "amigdala", "beyin", "psikoloji", "nörobilim"],
    ),
    Topic(
        slug="dil",
        title="Dil ve Beyin",
        description=(
            "Ses dalgaları saniyeler içinde anlama dönüşüyor. Bebeklerin neden "
            "her dili öğrenebildiğini, okumanın beyinde nasıl yer açtığını "
            "anlatıyoruz."
        ),
        queries=["language", "books reading", "child learning", "alphabet", "speaking", "brain"],
        tags=["dil", "beyin", "okuma", "nörobilim", "çocuk gelişimi"],
    ),
    Topic(
        slug="agri",
        title="Ağrı Gerçekten Nerede?",
        description=(
            "Ağrı doku hasarının ölçüsü değil, beynin ürettiği bir alarm. "
            "Kronik ağrının neden iyileşmiş dokuda bile sürdüğünü anlatıyoruz."
        ),
        queries=["pain", "hospital", "physical therapy", "doctor patient", "nerve", "healing"],
        tags=["ağrı", "kronik ağrı", "beyin", "sağlık", "nörobilim"],
    ),
    Topic(
        slug="empati",
        title="Empati ve Ayna Nöronlar",
        description=(
            "Birinin acısını gördüğünde beyninde ne oluyor? Ayna nöronların "
            "gerçekte ne yaptığını ve empatinin üç ayrı bileşenini anlatıyoruz."
        ),
        queries=["empathy", "helping hands", "friends talking", "community", "kindness", "brain"],
        tags=["empati", "ayna nöron", "beyin", "psikoloji", "sosyal"],
    ),
    Topic(
        slug="bagimlilik",
        title="Bağımlılık Beyinde Ne Yapar?",
        description=(
            "Bağımlılık irade sorunu değil. Ödül sisteminin nasıl ele "
            "geçirildiğini, istemek ile beğenmenin neden ayrıldığını anlatıyoruz."
        ),
        queries=["addiction", "recovery", "support group", "brain", "therapy", "hope"],
        tags=["bağımlılık", "dopamin", "beyin", "nörobilim", "sağlık"],
    ),
    Topic(
        slug="yaraticilik",
        title="Yaratıcılık Nasıl Çalışır?",
        description=(
            "İyi fikirler neden duşta geliyor? Sağ beyin efsanesini yıkıp "
            "yaratıcılığın gerçek mekanizmasını anlatıyoruz."
        ),
        queries=["creativity", "art studio", "idea lightbulb", "painting", "design", "brainstorm"],
        tags=["yaratıcılık", "beyin", "fikir", "nörobilim", "sanat"],
    ),
    Topic(
        slug="meditasyon",
        title="Meditasyon Beyni Değiştirir mi?",
        description=(
            "Abartı ile inkâr arasında gerçek ne? Araştırmaların hangi etkileri "
            "desteklediğini, hangilerinin kanıtın ötesinde olduğunu anlatıyoruz."
        ),
        queries=["meditation", "calm nature", "breathing", "yoga", "peaceful", "mindfulness"],
        tags=["meditasyon", "farkındalık", "beyin", "stres", "nörobilim"],
    ),
    Topic(
        slug="zaman",
        title="Zaman Algısı",
        description=(
            "Çocukken bir yaz sonsuzdu, şimdi yıllar uçuyor. Beynin zamanı nasıl "
            "inşa ettiğini ve neden yaşla birlikte hızlandığını anlatıyoruz."
        ),
        queries=["clock", "time lapse", "hourglass", "calendar", "sunset", "city timelapse"],
        tags=["zaman", "algı", "beyin", "hafıza", "nörobilim"],
    ),
]

BY_SLUG = {topic.slug: topic for topic in TOPICS}
