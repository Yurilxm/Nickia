# Nickia - script de instalacao (rodar uma vez no PC da sua mae)
# Uso: clique com botao direito -> "Executar com PowerShell"

$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $PSScriptRoot
Set-Location $Root

function Info($m)  { Write-Host "[Nickia] $m" -ForegroundColor Cyan }
function Ok($m)    { Write-Host "[OK] $m"     -ForegroundColor Green }
function Erro($m)  { Write-Host "[ERRO] $m"   -ForegroundColor Red }

Info "Diretorio: $Root"

# ---- 1. Python 3.10 ----
Info "Verificando Python 3.10..."
$pyOk = $false
try {
    $v = & py -3.10 --version 2>&1
    if ($LASTEXITCODE -eq 0) {
        Ok "Python 3.10 encontrado: $v"
        $pyOk = $true
    }
} catch { }

if (-not $pyOk) {
    Info "Python 3.10 nao encontrado. Tentando instalar via winget..."
    $wg = Get-Command winget -ErrorAction SilentlyContinue
    if (-not $wg) {
        Erro "winget nao disponivel. Instale manualmente:"
        Erro "https://www.python.org/downloads/release/python-31011/"
        Erro "Marque 'Add python.exe to PATH' durante a instalacao."
        pause
        exit 1
    }
    winget install --id Python.Python.3.10 -e --source winget --accept-package-agreements --accept-source-agreements
    Info "Python instalado. Feche e reabra este script para continuar."
    pause
    exit 0
}

# ---- 2. FFmpeg ----
Info "Verificando FFmpeg..."
if (-not (Get-Command ffmpeg -ErrorAction SilentlyContinue)) {
    Info "FFmpeg nao encontrado. Tentando instalar via winget..."
    $wg = Get-Command winget -ErrorAction SilentlyContinue
    if (-not $wg) {
        Erro "winget nao disponivel. Instale FFmpeg manualmente:"
        Erro "https://www.gyan.dev/ffmpeg/builds/"
        pause
        exit 1
    }
    winget install --id Gyan.FFmpeg -e --source winget --accept-package-agreements --accept-source-agreements
    Info "FFmpeg instalado. Feche e reabra este script para continuar."
    pause
    exit 0
}
Ok "FFmpeg encontrado"

# ---- 3. Venv ----
$VenvPath = Join-Path $Root "venv"
if (-not (Test-Path $VenvPath)) {
    Info "Criando ambiente virtual..."
    & py -3.10 -m venv $VenvPath
    Ok "Venv criado em $VenvPath"
} else {
    Ok "Venv ja existe"
}

$PyExe = Join-Path $VenvPath "Scripts\python.exe"
if (-not (Test-Path $PyExe)) {
    Erro "Venv corrompido. Apague a pasta 'venv' e rode de novo."
    pause
    exit 1
}

# ---- 4. Dependencias ----
Info "Atualizando pip..."
& $PyExe -m pip install --upgrade pip --quiet

Info "Instalando PyTorch CPU (pode demorar ~5 min)..."
& $PyExe -m pip install torch==2.6.0 torchaudio==2.6.0 `
    --index-url https://download.pytorch.org/whl/cpu `
    --extra-index-url https://pypi.org/simple

Info "Instalando demais dependencias (pode demorar ~5 min)..."
& $PyExe -m pip install -r requirements.txt

Ok "Dependencias instaladas"

# ---- 5. Baixar modelo ----
$CacheDir = Join-Path $env:USERPROFILE ".cache\huggingface\hub\models--ResembleAI--chatterbox"
if (Test-Path $CacheDir) {
    Ok "Modelo ja esta em cache"
} else {
    Info "Baixando modelo Chatterbox (~2 GB, uma vez so)..."
    $env:HF_HUB_DISABLE_SYMLINKS_WARNING = "1"
    & $PyExe -c "from chatterbox.mtl_tts import ChatterboxMultilingualTTS; import torch; ChatterboxMultilingualTTS.from_pretrained(device=torch.device('cpu')); print('OK')"
    Ok "Modelo baixado"
}

# ---- 6. Atalho no Desktop ----
Info "Criando atalho no Desktop..."
$Desktop = [Environment]::GetFolderPath("Desktop")
$Launcher = Join-Path $Root "iniciar.bat"
$Link = Join-Path $Desktop "Nickia.lnk"

$WshShell = New-Object -ComObject WScript.Shell
$Shortcut = $WshShell.CreateShortcut($Link)
$Shortcut.TargetPath = $Launcher
$Shortcut.WorkingDirectory = $Root
$Shortcut.IconLocation = "$env:SystemRoot\System32\shell32.dll,138"
$Shortcut.Description = "Nickia - Voz da Loja"
$Shortcut.Save()

Ok "Atalho criado: $Link"
Write-Host ""
Write-Host "==================================================" -ForegroundColor Green
Write-Host " Instalacao concluida!" -ForegroundColor Green
Write-Host " A partir de agora, use o atalho 'Nickia' no Desktop." -ForegroundColor Green
Write-Host "==================================================" -ForegroundColor Green
Write-Host ""
pause
