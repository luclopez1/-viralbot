# 🔑 Guía completa para obtener API Keys

Sigue estos pasos para obtener cada API key necesaria.

## 1. 🤖 Claude API (Anthropic)

**Paso 1:** Ve a https://console.anthropic.com

**Paso 2:** Haz click en "Sign In" (o "Sign Up" si no tienes cuenta)

**Paso 3:** Una vez dentro, ve a "API Keys" en el menú lateral

**Paso 4:** Haz click en "Create Key"

**Paso 5:** Copia la key (se mostrará solo una vez)

**Paso 6:** Pega en tu `.env`:
```env
ANTHROPIC_API_KEY=sk-ant-...
```

**Límites Free:**
- 5 solicitudes por minuto
- ~100K tokens de entrada/mes (usarás ~50 tokens por guión)

---

## 2. 🎥 YouTube Data API

### Parte A: Crear proyecto en Google Cloud

**Paso 1:** Ve a https://console.cloud.google.com

**Paso 2:** Haz click en "Create Project" (arriba a la izquierda)

**Paso 3:** Dale un nombre (ej: "YouTube IA Bot")

**Paso 4:** Espera a que se cree (1-2 minutos)

### Parte B: Habilitar YouTube Data API v3

**Paso 1:** En la barra de búsqueda, escribe "YouTube Data API v3"

**Paso 2:** Haz click en el resultado

**Paso 3:** Haz click en "ENABLE"

**Paso 4:** Espera a que se active

### Parte C: Crear credenciales OAuth 2.0

**Paso 1:** Vuelve al dashboard del proyecto

**Paso 2:** Ve a "Credentials" (en el menú izquierdo)

**Paso 3:** Haz click en "+ Create Credentials" → "OAuth 2.0 Client IDs"

**Paso 4:** Si aparece un popup, haz click en "Configure Consent Screen"

**Paso 5:** Selecciona "External" → "Create"

**Paso 6:** Completa el formulario:
- Nombre de la aplicación: "YouTube Video Bot"
- Email: tu email
- Los otros campos son opcionales

**Paso 7:** Haz click en "Save and Continue"

**Paso 8:** En "Scopes", haz click en "Add or Remove Scopes"

**Paso 9:** Busca "youtube" y selecciona:
- `https://www.googleapis.com/auth/youtube.upload`
- `https://www.googleapis.com/auth/youtube`

**Paso 10:** Haz click en "Update"

**Paso 11:** Vuelve a "Credentials"

**Paso 12:** Haz click en "+ Create Credentials" → "OAuth 2.0 Client IDs"

**Paso 13:** Selecciona "Desktop application"

**Paso 14:** Haz click en "Create"

**Paso 15:** Haz click en "Download JSON"

**Paso 16:** Guarda el archivo como `youtube_credentials.json` en tu carpeta del proyecto

### Parte D: Obtener API Key simple (para búsquedas)

**Paso 1:** Ve a "Credentials" nuevamente

**Paso 2:** Haz click en "+ Create Credentials" → "API Key"

**Paso 3:** Copia la key

**Paso 4:** Pega en `.env`:
```env
YOUTUBE_API_KEY=AIza...
```

**Límites Free:**
- 10,000 unidades/día
- 1 upload/día gratis (depende de verificación)
- Búsquedas ilimitadas (1 unidad = 100 búsquedas)

---

## 3. 📷 Pexels API (Imágenes gratis)

**Paso 1:** Ve a https://www.pexels.com/api/

**Paso 2:** Haz click en "Request API Key"

**Paso 3:** Completa el formulario corto

**Paso 4:** Acepta términos

**Paso 5:** Tu API key aparecerá instantáneamente

**Paso 6:** Copia y pega en `.env`:
```env
PEXELS_API_KEY=563492ad6...
```

**Límites Free:**
- 200 solicitudes/hora
- Ilimitado en total
- **Completamente gratis**

---

## 4. 🎵 ElevenLabs (Voz - OPCIONAL)

> ⚠️ **Nota**: Edge-TTS es gratis e ilimitado. Solo usa ElevenLabs si quieres mejor calidad.

**Paso 1:** Ve a https://elevenlabs.io/app/api-keys

**Paso 2:** Haz Sign Up (gratis)

**Paso 3:** Una vez dentro, copia tu API key

**Paso 4:** Pega en `.env`:
```env
ELEVENLABS_API_KEY=sk_...
ELEVENLABS_VOICE_ID=21m00Tcm4TlvDq8ikWAM
```

**Límites Free:**
- 10,000 caracteres/mes
- ~5-10 videos medianos/mes
- Buena calidad de voz

---

## ✅ Verificar que todo está bien

Una vez tengas todas las keys, ejecuta esto:

```bash
python -c "
import os
from dotenv import load_dotenv
load_dotenv()

keys = {
    'ANTHROPIC_API_KEY': os.getenv('ANTHROPIC_API_KEY'),
    'YOUTUBE_API_KEY': os.getenv('YOUTUBE_API_KEY'),
    'PEXELS_API_KEY': os.getenv('PEXELS_API_KEY'),
}

for key, value in keys.items():
    status = '✅' if value else '❌'
    print(f'{status} {key}: {'Configurada' if value else 'FALTA'}')
"
```

Deberías ver todos en ✅

---

## 🚨 Resolving de problemas comunes

### "API Key invalid"
- Verifica que sea la key completa (copy-paste)
- Asegúrate de no tener espacios al inicio/final
- Espera 2-3 minutos después de crear la key

### "YouTube upload disabled"
- Google requiere verificación de canales nuevos
- Envíales un video de prueba manualmente primero
- O espera 24 horas

### "Pexels rate limited"
- Espera 1 hora
- O usa una VPN
- O descarga imágenes manualmente

### "FFmpeg not found"
```bash
# Windows (Chocolatey)
choco install ffmpeg

# Mac
brew install ffmpeg

# Linux
sudo apt install ffmpeg
```

---

## 📝 Template de .env final

```env
# APIs
ANTHROPIC_API_KEY=sk-ant-xxxxx
YOUTUBE_API_KEY=AIzaxxxxx
PEXELS_API_KEY=563492adxxxxxx
ELEVENLABS_API_KEY=sk_xxxxx (opcional)
ELEVENLABS_VOICE_ID=21m00Tcm4TlvDq8ikWAM

# Directorios
OUTPUT_DIR=./videos_output
TEMP_DIR=./temp
ASSETS_DIR=./assets

# YouTube
YOUTUBE_CHANNEL_ID=tu_channel_id_aqui

# Video config
VIDEO_DURATION_SECONDS=60
VIDEO_FPS=24
VIDEO_RESOLUTION=1080x1920
```

---

## 🎯 Costo total

| Servicio | Costo | Uso |
|----------|-------|-----|
| Claude | Gratis (créditos iniciales) | ~1 guión/video |
| YouTube API | Gratis | 6 uploads/día |
| Pexels | Gratis | Ilimitado |
| ElevenLabs | Gratis (10k chars/mes) | 1-2 videos/mes |
| Edge-TTS | **Gratis ilimitado** | Recomendado |
| FFmpeg | Gratis | Local |
| **TOTAL** | **$0** | ✅ |

---

¡Listo! Ya puedes ejecutar: `python generate_content.py`
