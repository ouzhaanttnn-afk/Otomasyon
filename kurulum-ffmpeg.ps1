# FFmpeg kurulumu (Windows)
#
#   Kullanım — indirdiğin zip'i göstererek:
#     powershell -ExecutionPolicy Bypass -File kurulum-ffmpeg.ps1 -Zip "$HOME\Downloads\ffmpeg-release-essentials.zip"
#
#   Ya da zip'i de kendisi indirsin:
#     powershell -ExecutionPolicy Bypass -File kurulum-ffmpeg.ps1
#
# Yaptığı iş: arşivi açar, C:\ffmpeg altına yerleştirir, bin klasörünü PATH'e
# ekler. Yönetici yetkisi istemez — PATH'i sadece senin kullanıcın için yazar.

param(
    [string]$Zip = "",
    [string]$Hedef = "C:\ffmpeg"
)

$ErrorActionPreference = "Stop"

function Adim($m) { Write-Host "`n==> $m" -ForegroundColor Cyan }
function Tamam($m) { Write-Host "    OK  $m" -ForegroundColor Green }
function Hata($m) { Write-Host "    HATA  $m" -ForegroundColor Red }

# Zaten kurulu mu?
if (Get-Command ffmpeg -ErrorAction SilentlyContinue) {
    Tamam "FFmpeg zaten PATH'te: $((Get-Command ffmpeg).Source)"
    ffmpeg -version | Select-Object -First 1
    exit 0
}

# 1) Arşivi bul ya da indir
if (-not $Zip) {
    Adim "FFmpeg indiriliyor (~80 MB, biraz sürebilir)"
    $Zip = Join-Path $env:TEMP "ffmpeg.zip"
    $url = "https://www.gyan.dev/ffmpeg/builds/ffmpeg-release-essentials.zip"
    # Varsayılan ilerleme çubuğu indirmeyi çok yavaşlatıyor
    $eski = $ProgressPreference; $ProgressPreference = "SilentlyContinue"
    Invoke-WebRequest -Uri $url -OutFile $Zip -UseBasicParsing
    $ProgressPreference = $eski
    Tamam "indirildi"
}

if (-not (Test-Path $Zip)) {
    Hata "Arşiv bulunamadı: $Zip"
    Write-Host "    -Zip parametresiyle indirdiğin dosyanın tam yolunu ver."
    exit 1
}

# 2) Aç
Adim "Arşiv açılıyor"
$gecici = Join-Path $env:TEMP ("ffmpeg_" + [guid]::NewGuid().ToString("N").Substring(0,8))
Expand-Archive -Path $Zip -DestinationPath $gecici -Force

# Arşivin içinde ffmpeg-7.x-essentials_build gibi tek bir klasör var; asıl
# aradığımız onun içindeki bin klasörü.
$bin = Get-ChildItem -Path $gecici -Recurse -Filter "ffmpeg.exe" |
       Select-Object -First 1
if (-not $bin) {
    Hata "Arşivin içinde ffmpeg.exe yok. Yanlış dosya olabilir."
    Remove-Item $gecici -Recurse -Force
    exit 1
}
$kaynak = Split-Path (Split-Path $bin.FullName -Parent) -Parent
Tamam "bulundu: $($bin.FullName)"

# 3) Yerleştir
Adim "$Hedef klasörüne taşınıyor"
if (Test-Path $Hedef) {
    Write-Host "    $Hedef zaten var, içeriği yenileniyor"
    Remove-Item (Join-Path $Hedef "*") -Recurse -Force -ErrorAction SilentlyContinue
} else {
    New-Item -ItemType Directory -Path $Hedef -Force | Out-Null
}
Copy-Item -Path (Join-Path $kaynak "*") -Destination $Hedef -Recurse -Force
Remove-Item $gecici -Recurse -Force
Tamam "yerleştirildi"

# 4) PATH
$binYolu = Join-Path $Hedef "bin"
if (-not (Test-Path (Join-Path $binYolu "ffmpeg.exe"))) {
    Hata "$binYolu içinde ffmpeg.exe yok"
    exit 1
}

Adim "PATH'e ekleniyor"
$mevcut = [Environment]::GetEnvironmentVariable("Path", "User")
$parcalar = @()
if ($mevcut) { $parcalar = $mevcut -split ";" | Where-Object { $_ -ne "" } }

if ($parcalar -contains $binYolu) {
    Tamam "zaten ekliymiş"
} else {
    # Aynı yolu iki kez eklememek için mevcut listeyi koruyarak sona ekle
    $yeni = (($parcalar + $binYolu) -join ";")
    [Environment]::SetEnvironmentVariable("Path", $yeni, "User")
    Tamam "eklendi"
}
# Bu oturumda da hemen kullanılabilsin
$env:Path = "$env:Path;$binYolu"

# 5) Doğrula
Adim "Doğrulanıyor"
& (Join-Path $binYolu "ffmpeg.exe") -version | Select-Object -First 1
& (Join-Path $binYolu "ffprobe.exe") -version | Select-Object -First 1

Write-Host "`nKurulum tamam." -ForegroundColor Green
Write-Host "ONEMLI: Acik olan butun terminalleri kapatip yeniden ac," -ForegroundColor Yellow
Write-Host "yoksa PATH degisikligi o pencerelerde gorunmez.`n" -ForegroundColor Yellow
Write-Host "Sonra sunu calistir:  python main.py --check`n"
