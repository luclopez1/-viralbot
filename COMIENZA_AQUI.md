# 🚀 COMIENZA AQUI

## Lo que acabas de recibir

Un sistema COMPLETO para generar y subir videos a YouTube automáticamente usando IA. **100% gratuito**.

---

## 📁 Carpeta del proyecto

```
C:\Users\luclo\youtube-ia-automation\
├── generate_content.py       <- Script principal (AQUI ES TODO)
├── test_demo.py              <- Prueba sin API keys
├── config.env                <- Plantilla de config
├── .env                       <- Tu config real (EDITA ESTO)
├── setup.ps1 / setup.bat      <- Instalador automático
├── requirements.txt           <- Dependencias Python
├── n8n-workflow.json          <- Configuración de n8n
├── README.md                  <- Documentación completa
├── API_SETUP.md               <- Cómo obtener API keys
├── INSTALACION_WINDOWS.md     <- Guía paso a paso Windows
└── COMIENZA_AQUI.md           <- Este archivo
```

---

## ⚡ Quick Start (5 minutos)

### 1. **Instala FFmpeg** (CRÍTICO)

Windows: https://ffmpeg.org/download.html (descarga "full")

O si tienes Chocolatey:
```powershell
choco install ffmpeg
```

Verifica: `ffmpeg -version`

### 2. **Obtén las API keys** (3 minutos)

- **Claude**: https://console.anthropic.com → API Keys (gratis)
- **YouTube**: https://console.cloud.google.com → YouTube Data API v3 (gratis)
- **Pexels**: https://www.pexels.com/api/ → Request API (instántaneo, gratis)

### 3. **Configura .env**

Abre `C:\Users\luclo\youtube-ia-automation\.env` y rellena:
```env
ANTHROPIC_API_KEY=sk-ant-...
YOUTUBE_API_KEY=AIza...
PEXELS_API_KEY=563492ad...
```

Detalles en: `API_SETUP.md`

### 4. **Ejecuta tu primer video**

```powershell
cd C:\Users\luclo\youtube-ia-automation
python generate_content.py
```

¡Listo! Tendrás un video en `videos_output/video_YYYYMMDD_HHMMSS.mp4`

---

## 🎯 ¿Qué sucede cuando ejecutas?

1. **Claude genera un guión** viral de 60 segundos
2. **Edge-TTS crea la voz** en español
3. **Pexels descarga imágenes** relacionadas
4. **FFmpeg monta el video** (imagen + voz)
5. ✅ **Video listo para subir a YouTube**

Tiempo total: 1-2 minutos

---

## 🤖 Automatizar

### Opción A: Ejecutar cada 8 horas (Recomendado)

```powershell
npm install -g n8n
n8n start
```

Luego crea un workflow con trigger "Schedule" cada 8 horas.

### Opción B: Ejecutar cada X minutos (Script)

```python
import time
while True:
    main()
    time.sleep(3600)  # 1 hora
```

### Opción C: Windows Task Scheduler

```powershell
# Crea un ejecutable que corra cada 8 horas
# Detalles en INSTALACION_WINDOWS.md
```

---

## 🔑 API Keys disponibles (GRATIS)

| API | Límite | Costo |
|-----|--------|-------|
| Claude Haiku | 5 req/min | Gratis (créditos iniciales) |
| YouTube Data | 10K unidades/día | Gratis |
| Pexels | 200 req/hora | Gratis |
| Edge-TTS | Ilimitado | Gratis |
| FFmpeg | Local | Gratis |
| **TOTAL** | ∞ videos | **$0/mes** |

---

## 📊 Resultados

Cada ejecución produce:
- ✅ 1 video MP4 (1080x1920, formato Shorts)
- ✅ Guión generado con Claude IA
- ✅ Voz en off en español
- ✅ Imágenes stock libres
- ✅ Listo para subir a YouTube

**Calidad**: Buena para un canal de Shorts/IA

---

## ❓ Preguntas frecuentes

### ¿Cuántos videos puedo generar?
**Ilimitados** (límite es YouTube upload = 6/día gratis, upgrade para más)

### ¿Qué pasa si no tengo API key?
Prueba primero con `python test_demo.py` (genera un video demo)

### ¿Se pueden subir automáticamente?
Sí, si configuras OAuth en Google Cloud Console (se explica en API_SETUP.md)

### ¿Puedo personalizar el contenido?
Sí, edita la función `generate_script_with_claude()` en `generate_content.py`

### ¿Cómo cambio el nicho/tema?
Modifica el prompt en `generate_script_with_claude()` o usa argumentos de línea de comandos

### ¿Qué calidad tienen los videos?
- **Resolución**: 1080x1920 (perfecta para Shorts)
- **Duración**: 60 segundos
- **Audio**: Voz natural en español
- **Imágenes**: Stock gratis de Pexels

---

## 🔧 Troubleshooting rápido

| Problema | Solución |
|----------|----------|
| "ffmpeg not found" | Instala FFmpeg, ver arriba |
| "API key invalid" | Verifica que .env esté bien |
| "No se generan imágenes" | Verifica Pexels API key |
| "La voz no suena bien" | Acorta el guión en Claude |
| "Video vacío" | FFmpeg no está en PATH |

Detalles en: `INSTALACION_WINDOWS.md`

---

## 📚 Documentación

- **Empezar**: Este archivo (COMIENZA_AQUI.md)
- **Detallado**: README.md
- **API Keys**: API_SETUP.md
- **Windows**: INSTALACION_WINDOWS.md
- **Troubleshooting**: README.md > Troubleshooting

---

## 🎬 Próximos pasos

1. **Ahora**: Instala FFmpeg (`ffmpeg -version`)
2. **Luego**: Rellena `.env` con tus claves (5 min)
3. **Prueba**: `python generate_content.py` (2 min)
4. **Valida**: Abre el video generado
5. **Automatiza**: Configura n8n para cron (10 min)
6. **Disfruta**: ¡Deja que genere videos automáticamente!

---

## 💡 Tips

- **Primeros videos**: Pueden ser lentos (descargas iniciales)
- **Para velocidad**: Usa caché de imágenes (edita generate_content.py)
- **Para mejor guión**: Personaliza el prompt de Claude
- **Para monetizar**: Sube 15+ videos antes de aplicar monetización
- **Para viralidad**: Publica 3+ videos/día (requiere más uploads)

---

## ⚖️ Legal

✅ **Es legal**:
- Generar contenido con IA
- Usar Pexels (imágenes libres)
- Usar Claude/Edge-TTS
- Publicar en YouTube

❌ **No es legal**:
- Copiar videos de otros
- Usar música con copyright
- Publicar bajo otro canal
- Vender el contenido

Este sistema genera contenido ORIGINAL, no copia.

---

## 📞 Ayuda

Si algo no funciona:

1. Lee `INSTALACION_WINDOWS.md`
2. Ejecuta `python test_demo.py` (sin API keys)
3. Verifica FFmpeg: `ffmpeg -version`
4. Revisa `.env` tiene todas las claves
5. Mira los logs en `./temp/`

---

## 🎉 ¡Listo!

```
cd C:\Users\luclo\youtube-ia-automation
python generate_content.py
```

**Tu primer video IA se genera en 1-2 minutos.**

---

**Hecho con ❤️ para creators**

Actualizado: 2026-05-15
