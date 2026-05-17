#!/usr/bin/env python3
"""
Sistema de generación automática de videos para YouTube
Genera guión, voz, imágenes y monta el video final
"""

import os
import json
import re
import subprocess
from pathlib import Path
from datetime import datetime
import sys
from dotenv import load_dotenv
import ssl
import certifi
import httpx
import requests

# Bypass SSL global para redes corporativas (debe ir antes de importar google libs)
ssl._create_default_https_context = ssl._create_unverified_context
os.environ['PYTHONHTTPSVERIFY'] = '0'

# Parchear httplib2 globalmente para que googleapiclient no verifique SSL
try:
    import httplib2
    _orig_httplib2_init = httplib2.Http.__init__
    def _patched_httplib2_init(self, *args, **kwargs):
        kwargs['disable_ssl_certificate_validation'] = True
        _orig_httplib2_init(self, *args, **kwargs)
    httplib2.Http.__init__ = _patched_httplib2_init
except ImportError:
    pass

from google import genai
from google.genai import types as genai_types
from groq import Groq

# Cargar variables de entorno
load_dotenv()

# Configuración
YOUTUBE_API_KEY = os.getenv("YOUTUBE_API_KEY")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
PEXELS_API_KEY = os.getenv("PEXELS_API_KEY")
OUTPUT_DIR = Path(os.getenv("OUTPUT_DIR", "./videos_output"))
TEMP_DIR = Path(os.getenv("TEMP_DIR", "./temp"))
VIDEO_DURATION = int(os.getenv("VIDEO_DURATION_SECONDS", 58))
VIDEO_RESOLUTION = os.getenv("VIDEO_RESOLUTION", "1080x1920")

# Crear directorios
OUTPUT_DIR.mkdir(exist_ok=True)
TEMP_DIR.mkdir(exist_ok=True)

def _get_gemini_client():
    key = os.getenv("GEMINI_API_KEY")
    try:
        _httpx_client = httpx.Client(verify=False)
        return genai.Client(api_key=key, http_options={"httpxClient": _httpx_client})
    except Exception:
        return genai.Client(api_key=key)


def _get_groq_client():
    """Obtiene cliente de Groq como fallback"""
    return Groq(api_key=GROQ_API_KEY)


NICHES = [
    "ganar dinero con inteligencia artificial 2026",
    "crypto bitcoin ethereum 2026",
    "finanzas personales inversion 2026",
    "habitos millonarios mindset exito 2026",
    "psicologia manipulacion lenguaje corporal",
    "productividad trabajo remoto side hustle 2026",
]

FALLBACK_TOPICS = [
    # IA
    {"title": "Como ganar dinero con IA en 2026", "niche": "IA"},
    {"title": "La IA que genera dinero mientras duermes", "niche": "IA"},
    {"title": "Herramientas de IA para ganar dinero online", "niche": "IA"},
    # Crypto
    {"title": "Bitcoin va a subir o bajar en 2026", "niche": "Crypto"},
    {"title": "Ethereum superara a Bitcoin este ano", "niche": "Crypto"},
    {"title": "Altcoins que van a explotar en 2026", "niche": "Crypto"},
    # Finanzas
    {"title": "3 inversiones que te haran rico en 2026", "niche": "Finanzas"},
    {"title": "Como invertir 100 euros y multiplicarlos", "niche": "Finanzas"},
    {"title": "Error financiero que comete el 90% de la gente", "niche": "Finanzas"},
    # Mindset millonario
    {"title": "5 habitos que tienen todos los millonarios", "niche": "Mindset"},
    {"title": "Como piensan los ricos vs los pobres", "niche": "Mindset"},
    {"title": "La mentalidad que te hara rico en 2026", "niche": "Mindset"},
    {"title": "Por que el 99% nunca sera rico", "niche": "Mindset"},
    # Psicologia
    {"title": "3 senales de que alguien te esta mintiendo", "niche": "Psicologia"},
    {"title": "Como detectar manipuladores en 30 segundos", "niche": "Psicologia"},
    {"title": "Trucos psicologicos para caerle bien a todos", "niche": "Psicologia"},
    {"title": "Lenguaje corporal que revela atraccion", "niche": "Psicologia"},
    # Productividad
    {"title": "La rutina mañanera de los CEOs millonarios", "niche": "Productividad"},
    {"title": "3 side hustles que pagan mas que tu trabajo", "niche": "Productividad"},
    {"title": "Trabajos remotos que pagan 5000 euros al mes", "niche": "Productividad"},
    {"title": "Como ser productivo trabajando solo 4 horas", "niche": "Productividad"},
]


def get_trending_topics_from_youtube():
    """
    Busca videos trending en YouTube sobre IA, crypto y finanzas
    Rota entre los 3 nichos en cada ejecucion
    """
    import random

    print("[*] Buscando temas trending en YouTube...")

    # Rotar nicho aleatoriamente entre los 3
    niche_query = random.choice(NICHES)
    print(f"[*] Nicho seleccionado: {niche_query}")

    try:
        url = "https://www.googleapis.com/youtube/v3/search"
        params = {
            "part": "snippet",
            "type": "video",
            "maxResults": 10,
            "order": "viewCount",
            "q": niche_query,
            "regionCode": "ES",
            "relevanceLanguage": "es",
            "videoDuration": "short",
            "publishedAfter": "2026-01-01T00:00:00Z",
            "key": YOUTUBE_API_KEY,
        }

        response = requests.get(url, params=params, timeout=10, verify=False)
        response.raise_for_status()

        results = response.json()
        topics = []

        for item in results.get("items", []):
            title = item["snippet"]["title"]
            description = item["snippet"]["description"]
            topics.append({
                "title": title,
                "description": description[:200],
                "channel": item["snippet"]["channelTitle"]
            })

        if topics:
            return topics[:3]
        else:
            raise Exception("Sin resultados")

    except Exception as e:
        print(f"[WARN] Error con YouTube API: {e}")
        print("[*] Usando temas predefinidos del nicho...")
        import random
        return [random.choice(FALLBACK_TOPICS)]


def generate_script_with_claude(topic: str):
    """
    Genera un guión usando Gemini (primero) o Groq (fallback si Gemini sin cuota)
    Alterna entre Tipo A (viralidad pura) y Tipo B (conversion con CTA inteligente)
    """
    import random
    print(f"Generando guion para: {topic}")

    # 50% viralidad pura, 50% conversion con CTA estrategica
    video_type = random.choice(["VIRALIDAD", "CONVERSION"])
    print(f"[*] Tipo de video: {video_type}")

    if video_type == "VIRALIDAD":
        cta_instructions = """
    TIPO DE VIDEO: VIRALIDAD PURA (sin CTA de suscripcion)
    - OBJETIVO: maxima retencion + bajo swipe rate
    - NO incluir CTA de "suscribete"
    - Solo incluir CTA suave de like/comentario al final si encaja
    - Toda la energia en hacer el video impactante y completo
    - El espectador debe quedarse hasta el final por la curiosidad
    """
    else:
        cta_instructions = """
    TIPO DE VIDEO: CONVERSION (CTA estrategica ANTES del climax)
    - OBJETIVO: conseguir suscriptores con CTA bien colocada
    - REGLA CRITICA: la CTA NO va al final, va EN MEDIO antes de revelar la informacion clave
    - Estructura obligatoria:
      1. HOOK (2 segundos)
      2. Generar curiosidad / problema
      3. CTA EN MEDIO: "Suscribete si quieres saber [lo que viene a continuacion]"
      4. Revelar la informacion (climax)
      5. Final
    - Ejemplos de CTA estrategica:
      * "Suscribete si quieres saber la respuesta..." (antes de dar la respuesta)
      * "Sigueme si crees que esto te hara rico..." (antes del consejo clave)
      * "Suscribete para no perderte el truco que viene..." (antes del truco)
    - La CTA debe sentirse natural, conectada con lo que va a venir
    - NO repetir CTA al final, solo una vez en el medio
    """

    prompt = f"""
    Eres el mejor creador de YouTube Shorts virales del mundo. Has creado videos con +10M de vistas.
    Tu objetivo: que este Short consiga MAXIMA retencion y suscriptores.

    Tema: {topic}

    {cta_instructions}

    REGLAS CRITICAS PARA VIRALIZAR:

    TITULO (lo mas importante - decide si hacen click):
    - Maximo 60 caracteres
    - USA UNA de estas FORMULAS VIRALES PROBADAS (con millones de vistas):

      FORMULA 1 - Storytelling personal (1M+ vistas):
        * "ChatGPT me hizo rico: Mi historia con IA"
        * "Como gane 5000€ con esta IA en 30 dias"

      FORMULA 2 - Negacion + Alternativa (600K+ vistas):
        * "NO inviertas en Bitcoin en 2026 (HAZ ESTO)"
        * "NO uses esta IA (usa esta otra)"

      FORMULA 3 - Estadistica shock + pregunta (3M+ vistas):
        * "Por que el 95% pierde dinero con IA"
        * "Por que el 99% no consigue ser rico"

      FORMULA 4 - GRATIS/FREE (1.8M+ vistas):
        * "5 herramientas IA gratis que cambian todo"
        * "Como ganar dinero GRATIS con IA"

      FORMULA 5 - Autoridad + Drama (550K+ vistas):
        * "YouTube acaba de DESTRUIR a los canales IA"
        * "Google acaba de cambiar TODO con esta IA"

      FORMULA 6 - Warning/Peligro (alta retencion):
        * "Cuidado con este SCAM de IA"
        * "NO compres esta cripto: es estafa"

    - USA palabras gancho: SECRETO, NADIE, ERROR, TRUCO, NUNCA, SIEMPRE, RAPIDO, GRATIS, ESTAFA, CUIDADO, MUERE, DESTRUYE, KILLED

    GANCHO (primeros 2 segundos - aqui se pierde la gente):
    - "PARA todo y mira esto..."
    - "Si no haces esto vas a perder dinero..."
    - "Esto va a cambiar tu vida en 60 segundos"
    - "El 99% de la gente no sabe esto..."
    - "Lo que nadie te cuenta sobre [tema]..."

    GUION:
    - Maximo 100 palabras en total
    - Frases CORTAS y con IMPACTO (3-7 palabras por frase)
    - Tono: urgente, energetico, directo, autoridad
    - Construye TENSION: problema → solucion
    - Sin emojis en el texto

    RETENCION (lo mas importante de un Short):
    - El espectador debe quedarse hasta el final (no deslizar)
    - Cada frase genera curiosidad para la siguiente
    - Frases cortas y con impacto (3-7 palabras)
    - Si es tipo VIRALIDAD: sin CTA de suscripcion
    - Si es tipo CONVERSION: CTA UNICA en medio (antes del climax)

    HASHTAGS (5-7 estrategicos para alcance):
    - SIEMPRE incluir: #shorts
    - Mezcla generales (#dinero #ia) + nicho especifico

    SEO YOUTUBE (CRITICO para aparecer en busquedas):

    HASHTAGS (5-7 maximo en el video):
    - SIEMPRE incluir: #shorts
    - 2-3 hashtags BROAD (alto volumen): #dinero #ia #finanzas
    - 2-3 hashtags ESPECIFICOS (low competition): #bitcoin2026 #ganarconai #emprendimiento

    TAGS YOUTUBE (15-20 tags para SEO - NO confundir con hashtags):
    Son palabras clave que ayudan a YouTube a entender de que va el video.
    Mezcla:
    - 5 tags de keyword principal (variaciones): "ganar dinero con ia", "ia para ganar dinero", "como ganar dinero con ai", "ia inteligencia artificial dinero"
    - 5 tags de keyword secundaria: "ia 2026", "herramientas ia", "ia gratis", "ai tools"
    - 5 tags long-tail: "como ganar 1000 euros con ia", "mejor ia para hacer dinero 2026"
    - 5 tags broad: "shorts", "youtube shorts", "viral", "tutorial", "espanol"

    DESCRIPCION SEO (CRITICO):
    - Primera linea: TITULO + keyword principal (lo que YouTube indexa mas)
    - 2-3 lineas: Resumen con keywords naturales
    - Linea 4: CTA para suscribirse
    - Linea 5: Hashtags al final

    Ejemplo descripcion SEO:
    "Aprende a ganar dinero con IA en 2026 con estas herramientas gratis.
    En este video te muestro las mejores IAs para hacer dinero online,
    perfectas para emprendedores y principiantes que quieren empezar hoy.

    Suscribete para mas trucos como este!

    #shorts #dinero #ia #ganardinero #emprendimiento"

    Responde SOLO en JSON sin texto extra:
    {{
        "titulo": "Titulo VIRAL con gancho probado (max 60 caracteres con KEYWORD principal)",
        "guion": "GANCHO IMPACTANTE de 2 segundos. Desarrollo con tension. CTA final fuerte.",
        "hashtags": "#shorts #hashtag2 #hashtag3 #hashtag4 #hashtag5 #hashtag6",
        "tags_seo": "tag1, tag2, tag3, tag4, tag5, tag6, tag7, tag8, tag9, tag10, tag11, tag12, tag13, tag14, tag15",
        "descripcion": "Linea 1 con keyword principal. Linea 2-3 resumen con keywords naturales. CTA suscripcion. Hashtags al final."
    }}
    """

    response_text = None

    # Intentar primero con Gemini
    try:
        print("[*] Intentando con Gemini...")
        gemini_client = _get_gemini_client()
        response = gemini_client.models.generate_content(
            model="gemini-2.0-flash",
            contents=prompt
        )
        response_text = response.text
        print("[OK] Guion generado con Gemini")
    except Exception as e:
        error_msg = str(e)
        if "429" in error_msg or "RESOURCE_EXHAUSTED" in error_msg or "quota" in error_msg.lower():
            print(f"[WARN] Gemini sin cuota, usando Groq como fallback...")
            try:
                groq_client = _get_groq_client()
                response = groq_client.chat.completions.create(
                    model="llama-3.1-8b-instant",
                    messages=[{"role": "user", "content": prompt}],
                    temperature=0.7,
                    max_tokens=1024
                )
                response_text = response.choices[0].message.content
                print("[OK] Guion generado con Groq")
            except Exception as groq_error:
                print(f"[ERROR] Groq tambien fallo: {groq_error}")
                raise
        else:
            print(f"[ERROR] Error en Gemini: {e}")
            raise

    # Parsear JSON
    try:
        json_match = re.search(r'\{.*\}', response_text, re.DOTALL)
        if json_match:
            content = json.loads(json_match.group())
        else:
            content = {
                "titulo": topic,
                "guion": response_text,
                "hashtags": "#IA #YouTube #Shorts",
                "descripcion": topic
            }
    except json.JSONDecodeError:
        content = {
            "titulo": topic,
            "guion": response_text,
            "hashtags": "#IA #YouTube #Shorts",
            "descripcion": topic
        }

    return content


def _format_srt_time(seconds: float) -> str:
    h = int(seconds // 3600)
    m = int((seconds % 3600) // 60)
    s = int(seconds % 60)
    ms = int((seconds % 1) * 1000)
    return f"{h:02d}:{m:02d}:{s:02d},{ms:03d}"


def generate_speech_with_gtts(text: str, output_path: str):
    """
    Genera voz usando gTTS (Google TTS) — funciona en cloud/CI sin restricciones
    """
    print("[*] Generando voz en off con gTTS...")

    try:
        from gtts import gTTS

        tts = gTTS(text=text, lang='es', slow=False)
        tts.save(output_path)
        print(f"[OK] Voz generada: {output_path}")

        # Generar SRT aproximado basado en palabras
        srt_path = output_path.replace(".mp3", ".srt")
        words = text.split()
        words_per_sec = 2.8
        chunk_size = 7
        srt_lines = []
        idx = 1
        for i in range(0, len(words), chunk_size):
            chunk = words[i:i + chunk_size]
            t_start = i / words_per_sec
            t_end = (i + len(chunk)) / words_per_sec
            srt_lines.append(
                f"{idx}\n{_format_srt_time(t_start)} --> {_format_srt_time(t_end)}\n{' '.join(chunk)}\n"
            )
            idx += 1
        with open(srt_path, "w", encoding="utf-8") as f:
            f.write("\n".join(srt_lines))
        print(f"[OK] Subtitulos generados: {srt_path}")
        return True

    except Exception as e:
        print(f"[ERROR] Error al generar voz: {e}")
        return False


def generate_speech_with_edge_tts(text: str, output_path: str):
    """
    Genera voz usando Edge TTS — voz natural de Microsoft (gratis)
    Funciona tanto en local como en GitHub Actions
    """
    print("[*] Generando voz en off con Edge TTS (voz natural)...")
    try:
        import edge_tts
        import asyncio

        srt_path = output_path.replace(".mp3", ".srt")

        async def generate():
            communicate = edge_tts.Communicate(text, voice="es-ES-AlvaroNeural")
            submaker = edge_tts.SubMaker()
            with open(output_path, "wb") as audio_file:
                async for chunk in communicate.stream():
                    if chunk["type"] == "audio":
                        audio_file.write(chunk["data"])
                    elif chunk["type"] == "SentenceBoundary":
                        submaker.feed(chunk)
            with open(srt_path, "w", encoding="utf-8") as srt_file:
                srt_file.write(submaker.get_srt())

        asyncio.run(generate())
        print(f"[OK] Voz generada: {output_path}")
        print(f"[OK] Subtitulos generados: {srt_path}")
        return True
    except Exception as e:
        print(f"[WARN] Edge TTS fallo ({e}), usando gTTS...")
        return generate_speech_with_gtts(text, output_path)


def download_images_from_pexels(topic: str, count: int = 3):
    """
    Descarga imágenes libres de Pexels relacionadas al tema
    """
    print(f"[*] Descargando {count} imagenes de Pexels...")

    urls = []
    try:
        pexels_url = "https://api.pexels.com/v1/search"
        headers = {"Authorization": PEXELS_API_KEY}
        params = {
            "query": topic,
            "per_page": count,
            "orientation": "portrait"
        }

        response = requests.get(pexels_url, headers=headers, params=params, timeout=10, verify=False)
        response.raise_for_status()

        data = response.json()

        for i, photo in enumerate(data.get("photos", [])[:count]):
            img_url = photo["src"]["portrait"]
            img_path = TEMP_DIR / f"image_{i}.jpg"

            img_response = requests.get(img_url, timeout=10, verify=False)
            with open(img_path, "wb") as f:
                f.write(img_response.content)

            urls.append(str(img_path))
            print(f"  [OK] Descargada imagen {i+1}")

    except Exception as e:
        print(f"[WARN] Error descargando imagenes: {e}")
        print("   Usando imagenes placeholder...")

    return urls


def create_video_with_ffmpeg(images: list, audio_path: str, output_path: str, srt_path: str = None):
    """
    Crea video a partir de imágenes y audio usando FFmpeg
    """
    print(f"[*] Creando video con FFmpeg...")

    try:
        # Si no hay imágenes, crear una imagen placeholder
        if not images:
            placeholder = TEMP_DIR / "placeholder.png"
            from PIL import Image, ImageDraw

            img = Image.new('RGB', (1080, 1920), color='#1a1a1a')
            d = ImageDraw.Draw(img)
            d.text((540, 960), "Loading...", fill="white", anchor="mm")
            img.save(placeholder)
            images = [str(placeholder)]

        # Calcular duración por imagen
        duration_per_image = VIDEO_DURATION / len(images)

        # Crear filtro FFmpeg
        filter_parts = []
        concat_parts = []

        for i, img in enumerate(images):
            # Escalar a 1080x1920 LLENANDO toda la pantalla (crop en vez de pad)
            filter_parts.append(f"[{i}:v]scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920,setsar=1[img{i}]")
            concat_parts.append(f"[img{i}]")

        concat_filter = "".join(concat_parts) + f"concat=n={len(images)}:v=1:a=0[v]"

        full_filter = ";".join(filter_parts) + ";" + concat_filter

        # Buscar ffmpeg (PATH o ruta directa en Windows)
        ffmpeg_bin = "ffmpeg"
        ffmpeg_paths = [
            r"C:\ffmpeg\ffmpeg-8.1.1-essentials_build\bin\ffmpeg.exe",
            r"C:\ffmpeg\bin\ffmpeg.exe",
        ]
        for p in ffmpeg_paths:
            if os.path.exists(p):
                ffmpeg_bin = p
                break

        cmd = [ffmpeg_bin, "-y"]

        # Agregar imágenes como inputs
        for img in images:
            cmd.extend(["-loop", "1", "-t", str(duration_per_image), "-i", img])

        # Audio
        cmd.extend(["-i", audio_path])

        # Filtros y output
        cmd.extend([
            "-filter_complex", full_filter,
            "-map", "[v]",
            "-map", f"{len(images)}:a",
            "-c:v", "libx264",
            "-preset", "medium",
            "-c:a", "aac",
            "-shortest",
            output_path
        ])

        # Paso 1: crear video sin subtitulos
        tmp_output = output_path.replace(".mp4", "_nosubs.mp4")
        subprocess.run(cmd[:-1] + [tmp_output], check=True, capture_output=True)

        # Paso 2: quemar subtitulos si existe el SRT
        if srt_path and os.path.exists(srt_path):
            print("[*] Quemando subtitulos en el video...")
            import shutil
            # Copiar SRT al directorio actual (ruta relativa, sin letra de unidad)
            local_srt = "subs_temp.srt"
            shutil.copy(srt_path, local_srt)
            # Convertir SRT a ASS con FFmpeg (evita problemas de libass con rutas Windows)
            local_ass = "subs_temp.ass"
            conv_result = subprocess.run(
                [ffmpeg_bin, "-y", "-i", local_srt, local_ass],
                capture_output=True
            )
            if conv_result.returncode == 0:
                sub_filter = "ass=subs_temp.ass"
            else:
                # Fallback: escapar ruta absoluta para libass en Windows
                abs_srt = os.path.abspath(local_srt).replace("\\", "/")
                # Escapar el colon de la letra de unidad: C:/ -> C\:/
                abs_srt = abs_srt[0] + "\\:" + abs_srt[2:]
                sub_filter = f"subtitles='{abs_srt}':force_style='FontSize=18,FontName=Arial,Bold=1,PrimaryColour=&H00FFFFFF,OutlineColour=&H00000000,Outline=3,Shadow=1,Alignment=2,MarginV=80'"
            # Aplicar estilo si usamos ASS
            if sub_filter.startswith("ass="):
                # El estilo va incrustado en el ASS; usamos override para forzar fuente/tamaño
                sub_filter = "ass=subs_temp.ass"
            cmd2 = [
                ffmpeg_bin, "-y", "-i", tmp_output,
                "-vf", sub_filter,
                "-c:v", "libx264", "-preset", "medium",
                "-c:a", "copy",
                output_path
            ]
            result = subprocess.run(cmd2, capture_output=True)
            for f in [local_srt, local_ass]:
                try:
                    os.remove(f)
                except:
                    pass
            if result.returncode != 0:
                print("[WARN] Subtitulos fallaron, usando video sin subtitulos")
                if os.path.exists(tmp_output):
                    os.rename(tmp_output, output_path)
            else:
                if os.path.exists(tmp_output):
                    os.remove(tmp_output)
        else:
            os.rename(tmp_output, output_path)

        print(f"[OK] Video creado: {output_path}")
        return True

    except Exception as e:
        print(f"[ERROR] Error creando video: {e}")
        return False


def upload_to_youtube(video_path: str, title: str, description: str, tags: str, seo_tags: str = ""):
    """
    Sube el video a YouTube usando el token OAuth (desde archivo o env var)
    seo_tags: lista de tags SEO separados por coma para mejorar busqueda
    """
    print(f"[*] Subiendo a YouTube...")
    print(f"   Titulo: {title}")

    try:
        from google.oauth2.credentials import Credentials
        from google.auth.transport.requests import Request
        from googleapiclient.discovery import build
        from googleapiclient.http import MediaFileUpload

        SCOPES = ['https://www.googleapis.com/auth/youtube.upload']
        TOKEN_FILE = 'youtube_token.json'

        # Intentar cargar desde env var primero (CI), luego desde archivo (local)
        token_json_str = os.getenv("YOUTUBE_TOKEN")
        if token_json_str:
            try:
                print(f"[DEBUG] Token desde env var, longitud: {len(token_json_str)}")
                token_json_str = token_json_str.strip().strip("'\"")
                print(f"[DEBUG] Después de strip, longitud: {len(token_json_str)}")
                print(f"[DEBUG] Primeros 100 chars: {token_json_str[:100]}")
                creds = Credentials.from_authorized_user_info(json.loads(token_json_str), SCOPES)
            except Exception as e:
                print(f"[WARN] Env token inválido: {e}, intentando archivo...")
                if not os.path.exists(TOKEN_FILE):
                    print("[ERROR] No hay token de YouTube en env ni archivo")
                    return False
                with open(TOKEN_FILE, 'r', encoding='utf-8') as f:
                    raw = f.read()
                print(f"[DEBUG] Token desde archivo, longitud: {len(raw)}")
                print(f"[DEBUG] Primeros 100 chars (raw): {repr(raw[:100])}")
                raw = raw.strip().strip("'\"")
                print(f"[DEBUG] Después de strip, longitud: {len(raw)}")
                print(f"[DEBUG] Primeros 100 chars (stripped): {repr(raw[:100])}")
                creds = Credentials.from_authorized_user_info(json.loads(raw), SCOPES)
        else:
            print("[DEBUG] YOUTUBE_TOKEN no está en env, leyendo desde archivo...")
            if not os.path.exists(TOKEN_FILE):
                print("[ERROR] No hay token de YouTube. Ejecuta primero: python setup_youtube_auth.py")
                return False
            with open(TOKEN_FILE, 'r', encoding='utf-8') as f:
                raw = f.read()
            print(f"[DEBUG] Token desde archivo, longitud: {len(raw)}")
            print(f"[DEBUG] Primeros 100 chars (raw): {repr(raw[:100])}")
            raw = raw.strip().strip("'\"")
            print(f"[DEBUG] Después de strip, longitud: {len(raw)}")
            print(f"[DEBUG] Primeros 100 chars (stripped): {repr(raw[:100])}")
            creds = Credentials.from_authorized_user_info(json.loads(raw), SCOPES)

        # Renovar token si ha expirado
        if creds.expired:
            print(f"[*] Token expirado, renovando...")
            if not creds.refresh_token:
                print("[ERROR] No hay refresh_token disponible")
                return False
            try:
                refresh_session = requests.Session()
                refresh_session.verify = False
                creds.refresh(Request(session=refresh_session))
                print(f"[OK] Token renovado exitosamente")
                # Guardar token renovado en archivo
                with open(TOKEN_FILE, 'w') as f:
                    f.write(creds.to_json())
                print(f"[OK] Token guardado en {TOKEN_FILE}")
            except Exception as refresh_error:
                print(f"[ERROR] Fallo al renovar token: {refresh_error}")
                print(f"[WARN] Continuando con token expirado (puede fallar la subida)...")
        else:
            print(f"[OK] Token válido")

        youtube = build('youtube', 'v3', credentials=creds)

        # Añadir #Shorts para que YouTube lo clasifique como Short/Reel
        shorts_title = (title + ' #Shorts')[:100]
        shorts_description = description[:4900] + '\n\n' + tags + ' #Shorts'

        # Combinar hashtags + tags SEO para maximo alcance en busquedas
        tag_list = [t.lstrip('#') for t in tags.split()] + ['Shorts']
        if seo_tags:
            # Agregar tags SEO (separados por coma)
            seo_tag_list = [t.strip() for t in seo_tags.split(",") if t.strip()]
            tag_list.extend(seo_tag_list)
        # YouTube permite max 500 caracteres total en tags, deduplicar
        tag_list = list(dict.fromkeys(tag_list))[:30]
        print(f"[DEBUG] Tags SEO aplicados: {len(tag_list)} tags")

        body = {
            'snippet': {
                'title': shorts_title,
                'description': shorts_description,
                'tags': tag_list,
                'categoryId': '28',
            },
            'status': {
                'privacyStatus': 'public',
                'selfDeclaredMadeForKids': False,
                'madeForKids': False,
            }
        }

        media = MediaFileUpload(video_path, mimetype='video/mp4', resumable=True, chunksize=1024*1024)
        request = youtube.videos().insert(part='snippet,status', body=body, media_body=media)

        response = None
        while response is None:
            status, response = request.next_chunk()
            if status:
                print(f"  Subiendo... {int(status.progress() * 100)}%")

        video_id = response['id']
        print(f"[OK] Video subido!")
        print(f"   URL: https://www.youtube.com/watch?v={video_id}")
        return True

    except Exception as e:
        print(f"[WARN] No se pudo subir a YouTube: {e}")
        print(f"   Video guardado localmente: {video_path}")
        return False


def main():
    """
    Flujo principal: genera contenido, voz, video y sube a YouTube
    """
    print("\n" + "="*60)
    print("SISTEMA DE GENERACION DE VIDEOS PARA YOUTUBE")
    print("="*60 + "\n")

    # 1. Obtener temas trending
    topics = get_trending_topics_from_youtube()
    topic = topics[0]["title"] if topics else "IA generativa"

    print(f"\n[*] Tema seleccionado: {topic}\n")

    # 2. Generar guion
    content = generate_script_with_claude(topic)
    print(f"\n[*] Guion generado:\n{content['guion']}\n")

    # 3. Generar voz
    audio_path = TEMP_DIR / "voice.mp3"
    if not generate_speech_with_edge_tts(content['guion'], str(audio_path)):
        print("[ERROR] No se pudo generar la voz")
        return False

    # 4. Descargar imagenes
    images = download_images_from_pexels(topic, count=10)

    # 5. Crear video
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    video_path = OUTPUT_DIR / f"video_{timestamp}.mp4"

    srt_path = str(audio_path).replace(".mp3", ".srt")
    if not create_video_with_ffmpeg(images, str(audio_path), str(video_path), srt_path):
        print("[ERROR] Error al crear el video")
        return False

    # 6. Subir a YouTube (con tags SEO)
    upload_to_youtube(
        str(video_path),
        content['titulo'],
        content['descripcion'],
        content['hashtags'],
        content.get('tags_seo', '')
    )

    print("\n" + "="*60)
    print("[OK] PROCESO COMPLETADO")
    print("="*60)
    print(f"\n  Video guardado: {video_path}")
    print(f"  Titulo: {content['titulo']}")
    print(f"  Hashtags: {content['hashtags']}\n")

    return True


if __name__ == "__main__":
    main()
