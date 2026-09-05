# 🧠 Beyin 101 — YouTube Video Otomasyonu

Bir konu seç, sistem senin yerine seslendirmeyi yapsın, görselleri bulsun,
videoyu kursun ve Shorts'ları kessin.

**Çıktı:** 1 adet uzun video (1080p, yatay) + 5 adet Shorts (1080×1920, dikey).

### Shorts nasıl kesiliyor?

Kronometreyle değil. Seslendirme paragraf paragraf üretiliyor ve her parçanın
gerçek süresi ölçülüyor, böylece metindeki paragraf başlarının seste tam nereye
denk geldiği biliniyor. Shorts'lar bu noktalardan başlıyor.

Sebebi şu: 90 saniyede bir kör kesmek, klibi cümlenin ortasında açıyor. Shorts'ta
ilk iki saniyede tutamazsan izleyici kaydırıp geçiyor — bir düşüncenin başında
açılmak ile bir cümlenin ortasında açılmak arasındaki fark burada.

Videonun son paragrafı hiç seçilmiyor; orası kapanış konuşması ve "izlediğiniz
için teşekkürler" ile açılan bir Short boşa gider. Klibin sonu hâlâ cümle
ortasına gelebiliyor, o yüzden son saniyede ses kısılarak bitiş kasıtlı
gösteriliyor.

---

## Ne yapıyor?

| Adım | Nasıl |
|---|---|
| Seslendirme | ElevenLabs, Türkçe, `eleven_multilingual_v2` |
| Görseller | Pixabay'den telifsiz video klipleri |
| Montaj | FFmpeg — klipler normalize edilip sese göre diziliyor |
| Shorts | Paragraf başlarından kesilmiş 5 dikey klip (1080×1920) |
| Metadata | Başlık, açıklama ve etiketler `metadata.json` içinde |

---

## Kurulum

Üç şey gerekiyor: **Python**, **FFmpeg** ve **iki API anahtarı**.

### 1. Python

Python 3.10 veya üstü. Kurulu mu diye bakmak için:

```bash
python --version
```

Yoksa: <https://www.python.org/downloads/> — Windows'ta kurulum sırasında
**"Add Python to PATH"** kutusunu işaretlemeyi unutma.

### 2. FFmpeg

Videoyu birleştiren program. Bu olmadan sistem çalışmaz.

**Windows — script ile (kolay yol)**

Proje klasöründe PowerShell aç ve şunu çalıştır:

```powershell
# zip'i zaten indirdiysen yolunu ver
powershell -ExecutionPolicy Bypass -File kurulum-ffmpeg.ps1 -Zip "$HOME\Downloads\ffmpeg-release-essentials.zip"

# ya da indirmesini de ona bırak
powershell -ExecutionPolicy Bypass -File kurulum-ffmpeg.ps1
```

Arşivi açar, `C:\ffmpeg` altına yerleştirir ve PATH'e ekler. Yönetici yetkisi
gerekmez. Bittikten sonra **açık olan tüm terminalleri kapatıp yeniden aç.**

**Windows — elle**
1. <https://www.gyan.dev/ffmpeg/builds/> adresinden `ffmpeg-release-essentials.zip` indir
2. ZIP'i aç. İçinde `ffmpeg-7.x-essentials_build` gibi tek bir klasör var;
   onun içindekileri `C:\ffmpeg` klasörüne kopyala. Sonuçta
   `C:\ffmpeg\bin\ffmpeg.exe` yolu oluşmalı.
3. PowerShell aç ve şunu yapıştır:
   ```powershell
   [Environment]::SetEnvironmentVariable("Path",
     [Environment]::GetEnvironmentVariable("Path","User") + ";C:\ffmpeg\bin", "User")
   ```
4. PowerShell'i kapat, yeniden aç, test et: `ffmpeg -version`

**macOS**
```bash
brew install ffmpeg
```

**Linux**
```bash
sudo apt install ffmpeg
```

### 3. Projeyi indir ve bağımlılıkları kur

```bash
git clone https://github.com/ouzhaanttnn-afk/otomasyon.git
cd otomasyon
pip install -r requirements.txt
```

---

## 🔑 API anahtarları nereye yazılıyor?

**Anahtarlar hiçbir zaman kodun içine yazılmaz.** Bu depo herkese açık; koda
gömülen bir anahtar birkaç saat içinde otomatik taranıp kötüye kullanılır.
Bunun yerine `.env` adında bir dosya kullanıyoruz ve o dosya `.gitignore`
sayesinde GitHub'a **hiç gönderilmiyor**.

### En kolay yol

```bash
python kurulum.py
```

Anahtarları tek tek sorar ve `.env` dosyasını doğru biçimde kendisi yazar.
Elle dosya düzenlemen gerekmez — hangi dosyaya yazacağını karıştırma riski de
ortadan kalkar. Anahtarını yenilediğinde de aynı komutu çalıştır: boş
bıraktığın alanlar olduğu gibi kalır.

### Elle yapmak istersen

**1.** Proje klasöründe `.env.example` dosyasının bir kopyasını çıkar ve adını
`.env` yap.

```bash
# macOS / Linux
cp .env.example .env

# Windows (PowerShell)
Copy-Item .env.example .env
```

**2.** `.env` dosyasını herhangi bir metin düzenleyiciyle (Not Defteri de olur)
aç. İçi şöyle görünecek:

```
ELEVENLABS_API_KEY=
ELEVENLABS_VOICE_ID=21m00Tcm4TlvDq8ikWAM
ELEVENLABS_MODEL_ID=eleven_multilingual_v2
PIXABAY_API_KEY=
```

**3.** İki anahtarı eşittir işaretinin **hemen sağına**, tırnak veya boşluk
koymadan yapıştır:

```
ELEVENLABS_API_KEY=sk_buraya_kendi_anahtarin
PIXABAY_API_KEY=12345678-buraya_kendi_anahtarin
```

**4.** Kaydet ve kapat. Bitti.

### Anahtarları nereden alıyorsun?

| Servis | Adres | Not |
|---|---|---|
| ElevenLabs | <https://elevenlabs.io/app/settings/api-keys> | Profil → API Keys → Create |
| Pixabay | <https://pixabay.com/api/docs/> | Giriş yaptıktan sonra sayfanın üstünde görünür |

### Türkçe ses seçimi

`ELEVENLABS_VOICE_ID` alanındaki varsayılan değer İngilizce tonlu bir ses.
Daha doğal bir Türkçe okuma için ElevenLabs panelinde **Voices** bölümüne gir,
beğendiğin sesin sayfasını aç, **ID**'sini kopyala ve `.env` dosyasındaki
`ELEVENLABS_VOICE_ID` satırına yapıştır.

### GitHub Actions kullanacaksan

Depoda otomatik test çalışıyor ve bunun için anahtara ihtiyaç yok. Eğer ileride
üretimi de GitHub üzerinde çalıştırmak istersen anahtarları şuraya koyarsın:

> Depo sayfası → **Settings** → **Secrets and variables** → **Actions** →
> **New repository secret**

İsimleri `.env` dosyasındakiyle birebir aynı olmalı: `ELEVENLABS_API_KEY`,
`PIXABAY_API_KEY`.

---

## Kullanım

### Önce kurulumu doğrula

```bash
python main.py --check
```

Bu komut hiçbir kota harcamadan şunları kontrol eder: FFmpeg kurulu mu,
anahtarlar okunabiliyor mu, anahtarlar geçerli mi, kalan kotan yetiyor mu,
metinler yerinde mi. Bir sorun varsa ne yapman gerektiğini de yazar.

### Video üret

```bash
# menüden seç
python main.py

# doğrudan bir konu
python main.py --topic hafiza

# konuları listele
python main.py --list
```

### Gözetimsiz toplu üretim

```bash
python main.py --batch
```

Sırayla bütün konuları üretir. Başında beklemene gerek yok:

- **Biteni tekrar üretmez.** Klasöründe uzun videosu olan konu atlanır, yani
  yarıda kesilen bir çalışmayı tekrar başlatmak baştan başlamak anlamına gelmez.
- **Kota bitince temiz durur.** Her konudan önce kalan karakter hakkını kontrol
  eder; sıradaki metin sığmıyorsa başlamaz. Anahtarın kotayı okuyamıyorsa, API
  kotanın bittiğini bildirdiği anda durur.
- **Bir konu patlarsa diğerleri devam eder.** Hatalar rapora yazılır, üretim
  durmaz.
- **Rapor bırakır.** `output/toplu_uretim_raporu.txt` dosyasında hangi videonun
  üretildiği, hangisinin neden atlandığı yazılıdır. Her videodan sonra
  güncellenir, yani iş yarıda kalsa bile rapor elinde olur.

En fazla kaç video üretileceğini sınırlamak istersen:

```bash
python main.py --batch --limit 10
```

### Tarayıcı arayüzü

```bash
python app.py
```

Sonra <http://127.0.0.1:5000> adresini aç. Konunun yanındaki **Üret** düğmesine
bas; ilerleme sayfada görünür.

---

## Çıktılar

```
output/
└── hafiza/
    ├── video_long_1080p.mp4    ← YouTube'a yüklenecek uzun video
    ├── shorts_1.mp4            ← Shorts / Reels / TikTok
    ├── shorts_2.mp4
    ├── shorts_3.mp4
    ├── shorts_4.mp4
    ├── shorts_5.mp4
    ├── narration.mp3           ← ham seslendirme
    └── metadata.json           ← başlık, açıklama, etiketler
```

`metadata.json` içindeki başlık ve açıklamayı YouTube'a yüklerken doğrudan
kopyalayabilirsin.

---

## Maliyet

| Servis | Ücret |
|---|---|
| ElevenLabs Creator | ~$22/ay, 100.000 karakter |
| Pixabay | Ücretsiz |
| FFmpeg | Ücretsiz |

Depoda **30 konu** var, toplamı yaklaşık **134.000 karakter**. Aylık kota
100.000 olduğu için hepsi bir ayda çıkmaz — toplu üretim yettiği yere kadar
gider, kalanı sıradaki ay tamamlar. Yeni konular ay değişince eklenmiş olsa da
sıra numarası değil dosya varlığı belirleyici: `--batch` hangi konunun
üretildiğine klasöre bakarak karar veriyor, sırayı değil.

Kaba ölçü: bir video ortalama **4.500 karakter**, yani 100.000 karakterlik
kotayla ayda yaklaşık **20-22 video**.

Süreç yarıda kalırsa endişelenme: üretilen ses parçaları diske yazılıyor,
tekrar çalıştırdığında kaldığı yerden devam eder ve aynı metin için ikinci kez
ücret ödemezsin.

---

## Yeni konu eklemek

Kod değiştirmene gerek yok. İki adım:

**1.** Metni `scripts/` klasörüne yeni bir `.txt` dosyası olarak koy.
Örneğin `scripts/beyin-plastisitesi.txt`.

**2.** `beyin101/topics.py` dosyasındaki listeye bir kayıt ekle:

```python
Topic(
    slug="beyin-plastisitesi",          # dosya adıyla aynı olmalı
    title="Beyin Plastisitesi",
    description="YouTube açıklaması buraya.",
    queries=["brain", "neuron", "learning"],   # Pixabay arama terimleri
    tags=["beyin", "plastisite", "nörobilim"],
),
```

Metin uzunluğu için kaba ölçü: **1 dakika ≈ 800 karakter**. Mevcut metinler
4.000–7.000 karakter arasında, yani 5–8 dakikalık videolar üretiyor.

---

## Bilinen sınırlar

**Vercel'de çalışmaz.** Depoda daha önce bir `vercel.json` vardı, kaldırıldı.
Sebebi: Vercel gibi sunucusuz platformlarda FFmpeg kurulu değil, dosya sistemi
salt okunur ve istek süresi saniyelerle sınırlı. Video üretimi ise dakikalar
sürüyor ve diske yazması gerekiyor. Bu iş kendi bilgisayarında ya da normal bir
sunucuda çalışır.

**YouTube'a yükleme otomatik değil.** Videolar klasöre düşüyor, yüklemeyi sen
yapıyorsun. Otomatik yükleme için YouTube Data API ve OAuth kurulumu gerekiyor;
henüz eklenmedi.

**Video süresi metne bağlı.** Mevcut metinler 7–8 dakikalık videolar üretiyor.
Daha uzunu için metinleri uzatman yeterli.

---

## Sorun giderme

| Belirti | Sebep / çözüm |
|---|---|
| `FFmpeg bulunamadı` | FFmpeg kurulu değil ya da PATH'e eklenmemiş. Terminali yeniden başlatmayı dene. |
| `Eksik ortam değişkeni` | `.env` dosyası yok ya da anahtar satırı boş. |
| `ElevenLabs anahtarı reddedildi` | Anahtar yanlış kopyalanmış veya iptal edilmiş. Panelden yenisini al. |
| `kalan kota yetmiyor` | Aylık karakter hakkın bitmiş. Tek tek üret ya da planı yükselt. |
| Pixabay hiç sonuç döndürmedi | Anahtar geçersiz ya da internet yok. `--check` çalıştır. |
| Shorts'ta yazı görünmüyor | Font yok ya da FFmpeg derlemende `drawtext` filtresi yok. Video ve Shorts yine üretilir, sadece başlık yazısı olmaz. |

---

## Testler

```bash
pip install pytest
pytest tests/ -q
```

İki grup test var:

- **`tests/test_core.py`** — ağ ve FFmpeg gerektirmez. Metin bölme, Shorts
  zamanlaması, anahtar maskeleme, filtre yoklaması ve konu tanımları.
- **`tests/test_montage.py`** — FFmpeg kuruluysa çalışır, değilse otomatik
  atlanır. Sentetik kliplerle gerçek montajı yapar ve çıktının 1920×1080,
  Shorts'ların 1080×1920 ve tam istenen sürede olduğunu doğrular.

İkincisi FFmpeg kurulumunu doğrulamanın en sağlam yolu: hiç API kotası
harcamadan, montaj zincirinin baştan sona çalıştığını gösterir. İlk videonu
üretmeden önce bir kez çalıştırman iyi olur.

---

## Güvenlik notu

- `.env` dosyası `.gitignore` içinde — kazayla gönderilmesi engellenmiş durumda.
- Her `push`'ta CI, depoda anahtar deseni arar ve bulursa derlemeyi kırar.
- Hata mesajlarında anahtarlar maskelenir (`2962…cc49` gibi), böylece bir hata
  çıktısını paylaşırken anahtarın açığa çıkmaz.
- Anahtarını yanlışlıkla bir yere yapıştırdıysan: ilgili panelden iptal edip
  yenisini oluştur. İki dakikalık iş, riski sıfırlar.
