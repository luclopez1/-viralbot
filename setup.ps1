# Script de setup para Windows PowerShell

Write-Host "================================" -ForegroundColor Cyan
Write-Host "SETUP - YouTube IA Automation" -ForegroundColor Cyan
Write-Host "================================" -ForegroundColor Cyan

# 1. Crear directorios
Write-Host "`n[1/5] Creando directorios..." -ForegroundColor Yellow
New-Item -ItemType Directory -Force -Path "videos_output" > $null
New-Item -ItemType Directory -Force -Path "temp" > $null
Write-Host "✅ Directorios creados" -ForegroundColor Green

# 2. Verificar Python
Write-Host "`n[2/5] Verificando Python..." -ForegroundColor Yellow
try {
    $pythonVersion = python --version 2>&1
    Write-Host "✅ Python encontrado: $pythonVersion" -ForegroundColor Green
} catch {
    Write-Host "❌ Python no instalado. Descárgalo de https://www.python.org" -ForegroundColor Red
    exit
}

# 3. Verificar FFmpeg
Write-Host "`n[3/5] Verificando FFmpeg..." -ForegroundColor Yellow
try {
    $ffmpegVersion = ffmpeg -version 2>&1 | Select-Object -First 1
    Write-Host "✅ FFmpeg encontrado" -ForegroundColor Green
} catch {
    Write-Host "⚠️  FFmpeg no encontrado. Descárgalo de https://ffmpeg.org/download.html" -ForegroundColor Yellow
    Write-Host "   O instala via Chocolatey: choco install ffmpeg" -ForegroundColor Yellow
}

# 4. Instalar dependencias Python
Write-Host "`n[4/5] Instalando dependencias Python..." -ForegroundColor Yellow
python -m pip install anthropic requests python-dotenv edge-tts pillow google-auth-oauthlib google-api-python-client --trusted-host pypi.org --trusted-host files.pythonhosted.org -q
Write-Host "✅ Dependencias instaladas" -ForegroundColor Green

# 5. Crear .env si no existe
Write-Host "`n[5/5] Configurando .env..." -ForegroundColor Yellow
if (-Not (Test-Path ".env")) {
    Copy-Item "config.env" ".env"
    Write-Host "✅ Archivo .env creado. EDÍTALO con tus API keys!" -ForegroundColor Green
} else {
    Write-Host "✅ .env ya existe" -ForegroundColor Green
}

Write-Host "`n================================" -ForegroundColor Cyan
Write-Host "✅ SETUP COMPLETADO" -ForegroundColor Cyan
Write-Host "================================" -ForegroundColor Cyan

Write-Host "`n📋 PRÓXIMOS PASOS:" -ForegroundColor Yellow
Write-Host "1. Edita .env con tus API keys (ANTHROPIC_API_KEY, YOUTUBE_API_KEY, PEXELS_API_KEY)"
Write-Host "2. Ejecuta: python generate_content.py"
Write-Host "3. Para automatizar, instala n8n: npm install -g n8n"
Write-Host "4. Ejecuta n8n: n8n start"
Write-Host ""
