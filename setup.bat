@echo off
chcp 65001 >nul
setlocal enabledelayedexpansion

echo.
echo ================================
echo SETUP - YouTube IA Automation
echo ================================
echo.

REM 1. Crear directorios
echo [1/5] Creando directorios...
if not exist "videos_output" mkdir "videos_output"
if not exist "temp" mkdir "temp"
echo. ✓ Directorios creados

REM 2. Verificar Python
echo.
echo [2/5] Verificando Python...
python --version >nul 2>&1
if errorlevel 1 (
    echo. ✗ Python no instalado. Descargalo de https://www.python.org
    pause
    exit /b 1
) else (
    for /f "tokens=*" %%i in ('python --version 2^>^&1') do set pythonVersion=%%i
    echo. ✓ !pythonVersion!
)

REM 3. Verificar FFmpeg
echo.
echo [3/5] Verificando FFmpeg...
ffmpeg -version >nul 2>&1
if errorlevel 1 (
    echo. ⚠ FFmpeg no encontrado. Descargalo de https://ffmpeg.org/download.html
    echo.    O instala via Chocolatey: choco install ffmpeg
) else (
    echo. ✓ FFmpeg encontrado
)

REM 4. Instalar dependencias
echo.
echo [4/5] Instalando dependencias Python...
python -m pip install anthropic requests python-dotenv edge-tts pillow google-auth-oauthlib google-api-python-client --trusted-host pypi.org --trusted-host files.pythonhosted.org -q
echo. ✓ Dependencias instaladas

REM 5. Crear .env
echo.
echo [5/5] Configurando .env...
if not exist ".env" (
    copy "config.env" ".env"
    echo. ✓ Archivo .env creado. EDÍTALO con tus API keys!
) else (
    echo. ✓ .env ya existe
)

echo.
echo ================================
echo ✓ SETUP COMPLETADO
echo ================================
echo.
echo PRÓXIMOS PASOS:
echo 1. Edita .env con tus API keys
echo 2. Ejecuta: python generate_content.py
echo 3. Para automatizar: npm install -g n8n
echo 4. Luego: n8n start
echo.
pause
