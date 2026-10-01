@echo off
title Nickia - Voz da Loja
cd /d "%~dp0"

if not exist "venv\Scripts\activate.bat" (
    echo.
    echo [ERRO] Ambiente nao instalado.
    echo Rode primeiro: scripts\install.ps1
    echo.
    pause
    exit /b 1
)

call "venv\Scripts\activate.bat"

echo.
echo Iniciando Nickia... aguarde alguns segundos.
echo O navegador vai abrir automaticamente.
echo Para PARAR o Nickia, feche esta janela.
echo.

start "" /min cmd /c "timeout /t 5 /nobreak >nul && start http://localhost:8000"
python scripts\run_server.py

pause
