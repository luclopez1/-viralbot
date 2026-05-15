# 🪟 Guía COMPLETA de Instalación para Windows

## Paso 0: Verificar FFmpeg (IMPORTANTE!)

FFmpeg no está en tu PATH. Necesitas instalarlo.

### Opción A: Chocolatey (Recomendado)

Si tienes Chocolatey:
```powershell
choco install ffmpeg
```

### Opción B: Instalación manual

1. Ve a https://ffmpeg.org/download.html
2. Click en "Windows builds by BtbN"
3. Descarga la versión `full` (la más grande)
4. Extrae a `C:\ffmpeg`
5. Abre PowerShell como admin y ejecuta:
```powershell
[Environment]::SetEnvironmentVariable("Path", "$env:Path;C:\ffmpeg\bin", [EnvironmentVariableTarget]::Machine)
```
6. Reinicia PowerShell
7. Verifica: `ffmpeg -version`

### Opción C: Scoop (si lo tienes)
```powershell
scoop install ffmpeg
```

---

## Paso 1: Instalar dependencias

Una vez FFmpeg esté listo:

```powershell
cd C:\Users\luclo\youtube-ia-automation
python setup.ps1
```

O en CMD:
```cmd
cd C:\Users\luclo\youtube-ia-automation
setup.bat
```

---

## Paso 2: Configurar API Keys

1. **Edita `.env`**:
```powershell
notepad .env
```

2. Sigue la guía: `API_SETUP.md` (en la misma carpeta)

3. Rellena con tus claves:
```env
ANTHROPIC_API_KEY=sk-ant-xxxxx
YOUTUBE_API_KEY=AIzaxxxxx
PEXELS_API_KEY=563492adxxxxx
```

---

## Paso 3: Prueba el sistema

### Demo (sin API keys):
```powershell
python test_demo.py
```

Debería generar un video en `videos_output/demo_video.mp4`

### Generación real (con API keys):
```powershell
python generate_content.py
```

---

## Paso 4: Automatizar con n8n

### Instalar n8n:
```powershell
npm install -g n8n
```

### Ejecutar n8n:
```powershell
n8n start
```

Luego:
1. Ve a http://localhost:5678
2. Crea un workflow nuevo
3. Agrega trigger "Schedule" (cada 8 horas)
4. Agrega acción "Execute Command" con:
```bash
cd C:\Users\luclo\youtube-ia-automation && python generate_content.py
```
5. Activa el workflow

---

## Troubleshooting

### "ffmpeg: command not found"

**Solución 1** - Agregar al PATH manualmente:

1. Extrae FFmpeg a `C:\ffmpeg`
2. En tu script Python, al inicio agrega:
```python
import os
os.environ['PATH'] = r'C:\ffmpeg\bin;' + os.environ['PATH']
```

**Solución 2** - Usa ruta completa:

En `generate_content.py`, cambia:
```python
subprocess.run(['ffmpeg', ...])
```

Por:
```python
subprocess.run([r'C:\ffmpeg\bin\ffmpeg', ...])
```

### "SSL Certificate error"

Ya lo tenemos resuelto con:
```powershell
pip install --trusted-host pypi.org --trusted-host files.pythonhosted.org
```

### "PIL/edge-tts not installed"

```powershell
pip install pillow edge-tts --trusted-host pypi.org --trusted-host files.pythonhosted.org
```

### "Video se genera vacío"

Probablemente FFmpeg no está corriendo. Verifica:
```powershell
ffmpeg -version
```

Si dice "no encontrado", mira arriba cómo instalarlo.

---

## ✅ Checklist Final

- [ ] FFmpeg instalado (`ffmpeg -version` funciona)
- [ ] Python 3.8+ (`python --version`)
- [ ] Node.js (`node --version`)
- [ ] Carpeta creada: `C:\Users\luclo\youtube-ia-automation`
- [ ] Archivos descargados (generate_content.py, etc.)
- [ ] `.env` configurado con API keys
- [ ] `python test_demo.py` genera un video
- [ ] `python generate_content.py` genera un video de verdad
- [ ] n8n instalado (opcional)

---

## 🚀 Casos de uso

### Generar 1 video manualmente:
```powershell
python generate_content.py
```

### Generar 3 videos cada 8 horas:
```powershell
n8n start
# Configurar workflow + cron
```

### Generar infinitos videos (script loop):
```python
# Agrega al final de generate_content.py:
import time
while True:
    main()
    time.sleep(28800)  # 8 horas
```

---

## 📧 Si nada funciona

1. Verifica FFmpeg: `ffmpeg -version`
2. Verifica Python: `python --version`
3. Prueba con: `python test_demo.py`
4. Revisa los logs en `./temp/`
5. Lee `README.md`

¡Éxito!
