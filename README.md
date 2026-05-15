# 🤖 Sistema Automático de Generación de Videos para YouTube

Sistema completo en Python que genera videos virales para YouTube automáticamente usando Claude IA, voz sintetizada y Pexels.

## 🎯 ¿Qué hace?

1. **Detecta temas trending** en YouTube
2. **Genera guiones** cortos y virales con Claude IA
3. **Crea voz en off** con Edge-TTS (gratis, ilimitado)
4. **Descarga imágenes** libres de derechos desde Pexels
5. **Monta el video** con FFmpeg
6. **Sube a YouTube** automáticamente (opcional)

## ⚙️ Instalación

### 1. Requisitos previos
```bash
# Verificar Node.js
node --version

# Verificar FFmpeg
ffmpeg -version
```

Si no tienes FFmpeg:
- **Windows**: Descarga de https://ffmpeg.org/download.html
- O usa Chocolatey: `choco install ffmpeg`

### 2. Clonar/Crear carpeta
```bash
mkdir youtube-ia-automation
cd youtube-ia-automation
```

### 3. Instalar dependencias Python
```bash
pip install -r requirements.txt
```

### 4. Configurar API Keys

Copia `config.env` y rellena con tus claves:

```bash
cp config.env .env
# Edita .env con tus API keys
```

#### 🔑 Dónde obtener las claves:

**Claude (Anthropic)**
- Ve a: https://console.anthropic.com
- Crea una API key
- Pega en `ANTHROPIC_API_KEY`

**YouTube Data API**
- Ve a: https://console.cloud.google.com
- Crea proyecto nuevo
- Habilita "YouTube Data API v3"
- Crea credenciales (OAuth 2.0)
- Descarga JSON → guárdalo como `youtube_credentials.json`
- Pega la API key en `YOUTUBE_API_KEY`

**Pexels (gratis)**
- Ve a: https://www.pexels.com/api/
- Solicita API key (instántaneo)
- Pega en `PEXELS_API_KEY`

**ElevenLabs (opcional)**
- Si usas en vez de Edge-TTS
- Ve a: https://elevenlabs.io/app/api-keys
- Obtén la key
- Pega en `ELEVENLABS_API_KEY`

## 🚀 Uso

### Generar UN video manualmente
```bash
python generate_content.py
```

### Automatizar con n8n (recomendado)

```bash
# Instalar n8n
npm install -g n8n

# Ejecutar n8n
n8n start
```

Luego:
1. Ve a http://localhost:5678
2. Crea un workflow nuevo
3. Usa el trigger "Schedule" (cada 8 horas)
4. Agrega nodo "Execute Command" con:
   ```bash
   python /ruta/a/generate_content.py
   ```
5. Activa el workflow

### Automatizar con cron (Linux/Mac)
```bash
# Editar crontab
crontab -e

# Agregar línea (cada 8 horas)
0 */8 * * * cd /ruta/a/proyecto && python generate_content.py
```

## 📁 Estructura

```
youtube-ia-automation/
├── generate_content.py    # Script principal
├── config.env            # Variables de entorno
├── requirements.txt      # Dependencias Python
├── README.md            # Este archivo
├── videos_output/       # Videos generados (se crea automáticamente)
└── temp/               # Archivos temporales (se crea automáticamente)
```

## 🔧 Configuración

En `.env` puedes ajustar:

```env
VIDEO_DURATION_SECONDS=60      # Duración del video
VIDEO_RESOLUTION=1080x1920     # Resolución (Shorts format)
VIDEO_FPS=24                   # Fotogramas por segundo
```

## ⚠️ Notas importantes

1. **Límites de API**
   - YouTube Data API: ~6 uploads/día gratis
   - Claude: Usa plan gratuito (limitado)
   - Pexels: Ilimitado
   - Edge-TTS: Ilimitado

2. **Para subir a YouTube**
   - Necesitas autenticarte con Google OAuth la primera vez
   - Se guarda token en `youtube_token.json`
   - No compartas este archivo

3. **Calidad del contenido**
   - Los videos son aleatorios (usa Pexels + Claude)
   - Mejor resultado con temas consistentes
   - Personaliza `generate_script_with_claude()` para tu nicho

4. **Optimización para Shorts**
   - Resolución automática: 1080x1920
   - Duración: 60 segundos máximo
   - Subtítulos: Agrega manualmente en YouTube Studio

## 🐛 Troubleshooting

**"FFmpeg not found"**
```bash
# Windows: Agregar FFmpeg al PATH
# O instalar via Chocolatey
choco install ffmpeg
```

**"API key invalid"**
- Verifica que esté en `.env`
- Prueba la key en la consola de cada servicio

**"No se pueden descargar imágenes"**
- Verifica tu IP no esté bloqueada de Pexels
- Prueba con VPN

**"El audio no se sincroniza"**
- Aumenta `VIDEO_DURATION_SECONDS`
- O acorta el guión en Claude

## 📊 Resultados esperados

Cada ejecución produce:
- ✅ 1 video MP4 (en `videos_output/`)
- ✅ Guión generado con IA
- ✅ Voz natural en español
- ✅ Imágenes stock libres
- ✅ Ready para subir a YouTube

## 🎓 Próximos pasos

1. Ejecuta manualmente: `python generate_content.py`
2. Prueba el video generado
3. Activa n8n para automatizar
4. Personaliza los guiones para tu nicho
5. Monitorea analytics en YouTube

## 📝 Licencia

MIT - Úsalo libremente

## 💬 Soporte

Si tienes problemas:
1. Revisa los logs
2. Verifica las API keys
3. Prueba componentes por separado
4. Consulta la documentación de cada API

---

**Hecho con ❤️ para creators**
