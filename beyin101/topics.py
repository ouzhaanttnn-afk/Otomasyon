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
    Topic(
        slug="bilinc",
        title="Bilinç Nedir?",
        description=(
            "Beyindeki işlemler neden bir şey gibi hissettiriyor? Ayrılmış "
            "beyin hastalarından tepkisiz hastalarda bilinç ölçmeye kadar, "
            "bilimin bu soruda nereye geldiğini anlatıyoruz."
        ),
        queries=["consciousness", "brain scan", "mind", "abstract neurons", "thinking", "science lab"],
        tags=["bilinç", "beyin", "felsefe", "nörobilim", "zihin"],
    ),
    Topic(
        slug="sezgi",
        title="Sezgi Ne Zaman Güvenilir?",
        description=(
            "İçinden gelen ses bazen çok isabetli, bazen felaket. Sezginin "
            "hangi koşullarda çalıştığını, hangilerinde sadece özgüven "
            "ürettiğini anlatıyoruz."
        ),
        queries=["intuition", "chess player", "firefighter", "decision", "expert", "thinking"],
        tags=["sezgi", "karar verme", "uzmanlık", "psikoloji", "beyin"],
    ),
    Topic(
        slug="yalnizlik",
        title="Yalnızlık Beyinde Ne Yapar?",
        description=(
            "Yalnızlık kaç kişiyle çevrili olduğunla ilgili değil. Beynin bunu "
            "neden tehdit olarak işlediğini ve döngüyü neyin kırdığını "
            "anlatıyoruz."
        ),
        queries=["loneliness", "alone city", "empty room", "solitude", "window rain", "crowd"],
        tags=["yalnızlık", "sosyal", "beyin", "psikoloji", "sağlık"],
    ),
    Topic(
        slug="korku",
        title="Korku ve Fobiler",
        description=(
            "Örümceğin zararsız olduğunu bilmek neden hiçbir şeyi değiştirmiyor? "
            "Korkunun nasıl öğrenildiğini, neden silinmediğini ve maruz "
            "bırakmanın nasıl işlediğini anlatıyoruz."
        ),
        queries=["fear", "spider", "heights", "dark forest", "anxiety", "brain"],
        tags=["korku", "fobi", "amigdala", "psikoloji", "beyin"],
    ),
    Topic(
        slug="mizah",
        title="Neden Gülüyoruz?",
        description=(
            "Gülmelerin çoğu şakaya verilen tepki değil. Mizahın beyindeki "
            "mekanizmasını ve gülmenin gerçekte ne işe yaradığını anlatıyoruz."
        ),
        queries=["laughing", "friends laughing", "comedy", "happy people", "smile", "social"],
        tags=["mizah", "gülme", "sosyal", "beyin", "psikoloji"],
    ),
    Topic(
        slug="yaslanma",
        title="Beyin Yaşlanınca Ne Oluyor?",
        description=(
            "Bazı şeyler geriliyor, bazıları gelişiyor. Normal yaşlanma ile "
            "demansı ayıran çizgiyi ve gerçekten işe yarayan korumaları "
            "anlatıyoruz."
        ),
        queries=["elderly", "senior couple", "aging", "old hands", "memory", "brain"],
        tags=["yaşlanma", "hafıza", "demans", "beyin", "sağlık"],
    ),
    Topic(
        slug="ergenlik",
        title="Ergen Beyni",
        description=(
            "Ergenler riski biliyor, yine de alıyor. Ödül sistemi ile kontrol "
            "sisteminin neden farklı hızda geliştiğini ve akranların bunu nasıl "
            "değiştirdiğini anlatıyoruz."
        ),
        queries=["teenager", "high school", "youth friends", "skateboard", "students", "brain"],
        tags=["ergenlik", "gelişim", "beyin", "ebeveynlik", "psikoloji"],
    ),
    Topic(
        slug="plasebo",
        title="Plasebo Etkisi",
        description=(
            "Etken maddesi olmayan bir hap nasıl işe yarıyor? Beklentinin "
            "tetiklediği gerçek biyolojiyi ve bu etkinin nerede bittiğini "
            "anlatıyoruz."
        ),
        queries=["pills", "medicine", "doctor patient", "pharmacy", "laboratory", "health"],
        tags=["plasebo", "beklenti", "tıp", "beyin", "nörobilim"],
    ),
    Topic(
        slug="koku",
        title="Koku ve Hafıza",
        description=(
            "Bir koku neden seni aniden yıllar öncesine götürüyor? Kokunun "
            "diğer duyulardan farklı yolunu ve lezzetin aslında ne olduğunu "
            "anlatıyoruz."
        ),
        queries=["flowers smell", "coffee aroma", "kitchen cooking", "perfume", "nature scent", "memory"],
        tags=["koku", "hafıza", "duyu", "beyin", "nörobilim"],
    ),
    Topic(
        slug="beyin-mitleri",
        title="Beyin Hakkında 7 Yaygın Yanlış",
        description=(
            "Yüzde on efsanesinden öğrenme stillerine, beyin oyunlarından "
            "klasik müzik iddiasına: en yaygın yedi yanlışı tek tek ele "
            "alıyoruz."
        ),
        queries=["brain", "myth", "question mark", "science", "education", "books"],
        tags=["beyin", "mit", "bilim", "nörobilim", "yanlış bilgi"],
    ),
    Topic(
        slug="yanilsamalar",
        title="Görme Yanılsamaları Ne Anlatıyor?",
        description=(
            "Gözlerin bir kamera değil. Beynin eksik veriyi nasıl tahminle "
            "tamamladığını ve yanılsamaların bu sistemi nasıl açığa "
            "çıkardığını anlatıyoruz."
        ),
        queries=["optical illusion", "checkerboard", "abstract pattern", "eye vision", "geometric shapes", "brain"],
        tags=["yanılsama", "görme", "algı", "beyin", "nörobilim"],
    ),
    Topic(
        slug="ikna",
        title="İkna Psikolojisi",
        description=(
            "Bir hediye neden seni satın almaya itiyor? Karşılıklılık, sosyal "
            "kanıt, kıtlık ve diğer etki ilkelerini ve bunlara karşı nasıl "
            "korunacağını anlatıyoruz."
        ),
        queries=["persuasion", "sales", "negotiation", "marketing", "handshake business", "advertising"],
        tags=["ikna", "psikoloji", "etki", "pazarlama", "davranış"],
    ),
    Topic(
        slug="karar-yorgunlugu",
        title="Karar Yorgunluğu",
        description=(
            "Gün ilerledikçe kararların neden kötüleşiyor? Hakim kararlarından "
            "günlük seçimlere, karar yorgunluğunun ne olduğunu ve neyin işe "
            "yaradığını anlatıyoruz."
        ),
        queries=["decision", "tired office", "choices", "judge courtroom", "overwhelmed work", "brain"],
        tags=["karar verme", "yorgunluk", "verimlilik", "psikoloji", "beyin"],
    ),
    Topic(
        slug="sikilma",
        title="Sıkılmanın Faydası Var mı?",
        description=(
            "İnsanlar yalnız kalıp sıkılmaktansa kendine elektrik şoku vermeyi "
            "tercih etti. Sıkılmanın neden bir alarm olduğunu ve yaratıcılıkla "
            "bağını anlatıyoruz."
        ),
        queries=["boredom", "waiting room", "empty room", "staring window", "bored person", "daydreaming"],
        tags=["sıkılma", "yaratıcılık", "dikkat", "psikoloji", "beyin"],
    ),
    Topic(
        slug="nostalji",
        title="Nostalji Neden İyi Hissettiriyor?",
        description=(
            "Bir zamanlar hastalık sayılan nostalji, bugün faydalı bir "
            "duygusal araç olarak inceleniyor. Sosyal bağ, anlam ve ruh hali "
            "üzerindeki etkisini anlatıyoruz."
        ),
        queries=["old photos", "vintage memory", "nostalgia", "family album", "retro", "sunset memory"],
        tags=["nostalji", "hafıza", "duygu", "psikoloji", "beyin"],
    ),
    Topic(
        slug="icedisadonuk",
        title="İçe Dönük mü Dışa Dönük mü?",
        description=(
            "Aynı parti bir kişiyi bitkin, diğerini enerjik bırakıyor. "
            "Uyarılma teorisini ve bunun kişilik tercihi değil biyoloji "
            "olduğunu anlatıyoruz."
        ),
        queries=["party crowd", "quiet reading", "social gathering", "alone time", "personality", "friends group"],
        tags=["içe dönük", "dışa dönük", "kişilik", "psikoloji", "beyin"],
    ),
    Topic(
        slug="el-tercihi",
        title="Neden Çoğu İnsan Sağlak?",
        description=(
            "İnsanların onda dokuzu sağ elini kullanıyor ve bu oran binlerce "
            "yıldır değişmiyor. El tercihinin beyin lateralizasyonuyla "
            "ilişkisini anlatıyoruz."
        ),
        queries=["handwriting hand", "writing pen", "tools hand", "scissors", "brain hemisphere", "hands"],
        tags=["el tercihi", "solaklık", "beyin", "lateralizasyon", "nörobilim"],
    ),
    Topic(
        slug="ikizler",
        title="Doğa mı Terbiye mi? İkiz Çalışmaları",
        description=(
            "Ayrı büyütülen ikizlerin şaşırtıcı benzerlikleri bize ne "
            "anlatıyor? Kalıtım payının yaşla nasıl değiştiğini ve genlerin "
            "çevreyi nasıl şekillendirdiğini anlatıyoruz."
        ),
        queries=["twins", "identical twins", "family genetics", "children playing", "siblings", "dna"],
        tags=["ikiz çalışması", "genetik", "kişilik", "gelişim", "nörobilim"],
    ),
    Topic(
        slug="yalan",
        title="Yalan Söylemek ve Yalanı Anlamak",
        description=(
            "İlk yalan aslında bir zihinsel gelişim işareti. Neden yüz "
            "ifadesine bakarak yalan tespit edemediğimizi ve gerçekte neyin "
            "işe yaradığını anlatıyoruz."
        ),
        queries=["lying face", "interrogation", "child playing", "poker face", "detective", "conversation"],
        tags=["yalan", "aldatma", "psikoloji", "iletişim", "beyin"],
    ),
    Topic(
        slug="secenek-felci",
        title="Çok Seçenek Neden Kötü?",
        description=(
            "Yirmi dört çeşit reçel, altı çeşitten daha az sattı. Seçenek "
            "fazlalığının karar kalitesini ve memnuniyeti nasıl düşürdüğünü "
            "anlatıyoruz."
        ),
        queries=["supermarket shelf", "choices variety", "shopping decision", "grocery store", "options", "jam jars"],
        tags=["seçenek felci", "karar verme", "tüketici psikolojisi", "davranış", "beyin"],
    ),
]

BY_SLUG = {topic.slug: topic for topic in TOPICS}
