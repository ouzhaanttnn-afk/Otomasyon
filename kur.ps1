# Beyin 101 - kurulum
#
# Bu dosya dogrudan indirilip calistirilmak icin yazildi:
#
#   $env:B_ELEVEN="anahtar"; $env:B_PIXABAY="anahtar"
#   irm https://raw.githubusercontent.com/ouzhaanttnn-afk/otomasyon/main/kur.ps1 | iex
#
# Satir devami icin backtick KULLANILMAZ: dosya LF satir sonlariyla
# kaydedildiginde backtick+LF bazi PowerShell surumlerinde ayristirma
# hatasi verir ve script hic calismaz. Uzun satirlar oldugu gibi birakildi.

$Proje   = Join-Path $HOME "beyin101"
$Ffmpeg  = "C:\ffmpeg"
$LogPath = Join-Path $HOME "beyin101_kurulum_log.txt"

function Adim($n, $m) { Write-Host "`n[$n/5] $m" -ForegroundColor Cyan }
function Ok($m)       { Write-Host "      OK   $m" -ForegroundColor Green }

$hataOldu = $false
try { Start-Transcript -Path $LogPath -Force | Out-Null } catch { }

try {
    $ProgressPreference = "SilentlyContinue"
    $ErrorActionPreference = "Stop"
    try { [Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12 } catch { }

    $eleven  = $env:B_ELEVEN
    $pixabay = $env:B_PIXABAY
    if (-not $eleven)  { $eleven  = Read-Host "ElevenLabs API anahtarin" }
    if (-not $pixabay) { $pixabay = Read-Host "Pixabay API anahtarin" }
    if (-not $eleven -or -not $pixabay) { throw "Anahtarlar bos birakilamaz." }

    Write-Host "`n===================================" -ForegroundColor White
    Write-Host "  Beyin 101 - Kurulum" -ForegroundColor White
    Write-Host "===================================" -ForegroundColor White

    Adim 1 "Python kontrol ediliyor"
    $py = $null
    foreach ($c in @("python", "py")) {
        $cmd = Get-Command $c -ErrorAction SilentlyContinue
        if ($cmd) {
            $v = & $c --version 2>&1
            if ("$v" -match "Python 3\.(\d+)" -and [int]$Matches[1] -ge 10) { $py = $c; break }
        }
    }
    if (-not $py) { throw "Python 3.10+ bulunamadi. https://www.python.org/downloads/ adresinden kur ve kurulumda 'Add Python to PATH' kutusunu isaretle." }
    Ok "$py - $(& $py --version 2>&1)"

    Adim 2 "Proje dosyalari indiriliyor"
    $zip = Join-Path $env:TEMP "beyin101.zip"
    $tmp = Join-Path $env:TEMP "beyin101_x"
    Invoke-WebRequest -Uri "https://github.com/ouzhaanttnn-afk/otomasyon/archive/refs/heads/main.zip" -OutFile $zip -UseBasicParsing
    if (Test-Path $tmp) { Remove-Item $tmp -Recurse -Force }
    Expand-Archive -Path $zip -DestinationPath $tmp -Force
    $kaynak = Get-ChildItem $tmp -Directory | Select-Object -First 1
    if (-not $kaynak) { throw "Arsiv beklendigi gibi degil." }
    if (-not (Test-Path $Proje)) { New-Item -ItemType Directory -Path $Proje -Force | Out-Null }
    Copy-Item (Join-Path $kaynak.FullName "*") -Destination $Proje -Recurse -Force
    Remove-Item $tmp -Recurse -Force
    Remove-Item $zip -Force
    Ok $Proje

    Adim 3 "FFmpeg kuruluyor"
    $binYolu = Join-Path $Ffmpeg "bin"
    if (Test-Path (Join-Path $binYolu "ffmpeg.exe")) {
        Ok "zaten kurulu"
    } else {
        Write-Host "      indiriliyor (~80 MB, birkac dakika surebilir)..."
        $fzip = Join-Path $env:TEMP "ffmpeg.zip"
        $ftmp = Join-Path $env:TEMP "ffmpeg_x"
        Invoke-WebRequest -Uri "https://www.gyan.dev/ffmpeg/builds/ffmpeg-release-essentials.zip" -OutFile $fzip -UseBasicParsing
        if (Test-Path $ftmp) { Remove-Item $ftmp -Recurse -Force }
        Expand-Archive -Path $fzip -DestinationPath $ftmp -Force
        $exe = Get-ChildItem $ftmp -Recurse -Filter "ffmpeg.exe" | Select-Object -First 1
        if (-not $exe) { throw "Arsivin icinde ffmpeg.exe yok." }
        $kok = Split-Path (Split-Path $exe.FullName -Parent) -Parent
        if (-not (Test-Path $Ffmpeg)) { New-Item -ItemType Directory -Path $Ffmpeg -Force | Out-Null }
        Copy-Item (Join-Path $kok "*") -Destination $Ffmpeg -Recurse -Force
        Remove-Item $ftmp -Recurse -Force
        Remove-Item $fzip -Force
        Ok $Ffmpeg
    }

    $kayitli = [Environment]::GetEnvironmentVariable("Path", "User")
    $parcalar = @()
    if ($kayitli) { $parcalar = $kayitli -split ";" | Where-Object { $_ -ne "" } }
    if ($parcalar -contains $binYolu) {
        Ok "PATH zaten ekli"
    } else {
        [Environment]::SetEnvironmentVariable("Path", (($parcalar + $binYolu) -join ";"), "User")
        Ok "PATH'e eklendi"
    }
    $env:Path = "$env:Path;$binYolu"

    Adim 4 "API anahtarlari yaziliyor"
    $envDosya = Join-Path $Proje ".env"
    $satirlar = @(
        "# Bu dosya .gitignore icinde - GitHub'a gitmez.",
        "# Anahtarlari asla .env.example dosyasina yazma.",
        "",
        "ELEVENLABS_API_KEY=$eleven",
        "ELEVENLABS_VOICE_ID=21m00Tcm4TlvDq8ikWAM",
        "ELEVENLABS_MODEL_ID=eleven_multilingual_v2",
        "PIXABAY_API_KEY=$pixabay",
        "OUTPUT_DIR=output"
    )
    $satirlar | Set-Content -Path $envDosya -Encoding UTF8
    Ok $envDosya

    Adim 5 "Python paketleri kuruluyor"
    Push-Location $Proje
    try {
        & $py -m pip install --quiet --upgrade pip 2>&1 | Out-Null
        & $py -m pip install --quiet -r requirements.txt
        if ($LASTEXITCODE -ne 0) { throw "pip paketleri kuramadi." }
        Ok "tamam"
        Write-Host "`n===================================" -ForegroundColor White
        Write-Host "  Dogrulama" -ForegroundColor White
        Write-Host "===================================" -ForegroundColor White
        & $py main.py --check
    } finally { Pop-Location }

    Write-Host "`n===================================" -ForegroundColor Green
    Write-Host "  KURULUM BITTI" -ForegroundColor Green
    Write-Host "===================================" -ForegroundColor Green

    if ($env:B_BATCH -eq "1") {
        # Unattended production: the whole point is that nobody is here, so it
        # runs in this same window and the report survives in output/.
        Write-Host ""
        Write-Host "  Toplu uretim basliyor. Bilgisayari acik birak." -ForegroundColor Yellow
        Write-Host "  Bu saatler surebilir; pencereyi kapatma." -ForegroundColor Yellow
        Write-Host ""
        Push-Location $Proje
        try {
            if ($env:B_LIMIT) { & $py main.py --batch --limit $env:B_LIMIT }
            else              { & $py main.py --batch }
        } finally { Pop-Location }
    } else {
        Write-Host ""
        Write-Host "  YENI bir PowerShell ac ve:" -ForegroundColor Yellow
        Write-Host "      cd `"$Proje`""
        Write-Host "      python main.py"
        Write-Host ""
        Write-Host "  (Yeni pencere sart: PATH degisikligi eskisinde gorunmez.)" -ForegroundColor Yellow
    }
}
catch {
    $hataOldu = $true
    Write-Host "`n=== KURULUM DURDU ===" -ForegroundColor Red
    Write-Host "  $($_.Exception.Message)" -ForegroundColor Red
    Write-Host "  Satir: $($_.InvocationInfo.ScriptLineNumber)" -ForegroundColor DarkGray
    Write-Host "  Log: $LogPath" -ForegroundColor Yellow
}
finally {
    try { Stop-Transcript | Out-Null } catch { }
    if ($hataOldu) { Write-Host "`nSonuc: HATA (yukari bak)`n" -ForegroundColor Red }
    else { Write-Host "`nSonuc: BASARILI`n" -ForegroundColor Green }
}
