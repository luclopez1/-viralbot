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

# Cargar variables de entorno
load_dotenv()

# Configuración
YOUTUBE_API_KEY = os.getenv("YOUTUBE_API_KEY")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
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


NICHES = [
    "ganar dinero con inteligencia artificial 2026",
    "crypto bitcoin ethereum 2026",
    "finanzas personales inversion 2026",
]

FALLBACK_TOPICS = [
    {"title": "Como ganar dinero con IA en 2026", "niche": "IA"},
    {"title": "Bitcoin va a subir o bajar en 2026", "niche": "Crypto"},
    {"title": "3 inversiones que te haran rico en 2026", "niche": "Finanzas"},
    {"title": "La IA que genera dinero mientras duermes", "niche": "IA"},
    {"title": "Ethereum superara a Bitcoin este ano", "niche": "Crypto"},
    {"title": "Como invertir 100 euros y multiplicarlos", "niche": "Finanzas"},
    {"title": "Herramientas de IA para ganar dinero online", "niche": "IA"},
    {"title": "Altcoins que van a explotar en 2026", "niche": "Crypto"},
    {"title": "Error financiero que comete el 90% de la gente", "niche": "Finanzas"},
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
    Genera un guión de 30-60 segundos usando Gemini (gratis)
    """
    print(f"Generando guion para: {topic}")

    prompt = f"""
    Eres un experto creador de contenido viral para YouTube Shorts.
    Genera un guion CORTO y VIRAL para un YouTube Short de 60 segundos.

    Tema: {topic}

    REGLAS CRITICAS:
    1. GANCHO en los primeros 3 segundos: pregunta impactante, dato sorprendente o afirmacion provocadora que haga IMPOSIBLE saltar el video. Ejemplos de ganchos: "El 99% de la gente no sabe esto...", "Esto va a cambiar tu vida en 60 segundos", "Lo que nadie te cuenta sobre..."
    2. Maximo 90 palabras en total
    3. Tono: urgente, energetico, directo
    4. CTA claro al final (suscribete, comenta, dale like)
    5. Sin emojis en el texto
    6. Cada frase corta y con impacto

    Responde SOLO en JSON sin texto extra:
    {{
        "titulo": "Titulo con gancho (max 60 caracteres, usa numeros o preguntas)",
        "guion": "GANCHO IMPACTANTE aqui. Resto del guion...",
        "hashtags": "#hashtag1 #hashtag2 #hashtag3 #hashtag4 #hashtag5",
        "descripcion": "Descripcion de 2-3 lineas para YouTube con palabras clave"
    }}
    """

    gemini_client = _get_gemini_client()
    response = gemini_client.models.generate_content(
        model="gemini-2.0-flash",
        contents=prompt
    )
    response_text = response.text

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


def generate_speech_with_edge_tts(text: str, output_path: str):
    """
    Genera voz usando Edge TTS (gratis, sin limites)
    """
    print("[*] Generando voz en off...")

    try:
        # Instalar edge-tts si no está disponible
        try:
            import edge_tts
        except ImportError:
            print("[*] Instalando edge-tts...")
            subprocess.run([sys.executable, "-m", "pip", "install", "edge-tts", "-q"])
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
        print(f"[ERROR] Error al generar voz: {e}")
        return False


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
            # Escalar a 1080x1920 con padding
            filter_parts.append(f"[{i}:v]scale=1080:1920:force_original_aspect_ratio=decrease,pad=1080:1920:(ow-iw)/2:(oh-ih)/2[img{i}]")
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


def upload_to_youtube(video_path: str, title: str, description: str, tags: str):
    """
    Sube el video a YouTube usando el token OAuth guardado
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

        if not os.path.exists(TOKEN_FILE):
            print("[ERROR] No hay token de YouTube. Ejecuta primero: python setup_youtube_auth.py")
            return False

        with open(TOKEN_FILE, 'r') as f:
            raw = f.read().strip()
            # Limpiar posibles comillas envolventes del secret de CI
            if raw.startswith(("'", '"')) and raw.endswith(("'", '"')):
                raw = raw[1:-1]
        creds = Credentials.from_authorized_user_info(json.loads(raw), SCOPES)

        # Renovar token si ha expirado
        if creds.expired and creds.refresh_token:
            refresh_session = requests.Session()
            refresh_session.verify = False
            creds.refresh(Request(session=refresh_session))
            with open(TOKEN_FILE, 'w') as f:
                f.write(creds.to_json())

        youtube = build('youtube', 'v3', credentials=creds)

        # Añadir #Shorts para que YouTube lo clasifique como Short/Reel
        shorts_title = (title + ' #Shorts')[:100]
        shorts_description = description[:4900] + '\n\n' + tags + ' #Shorts'
        tag_list = [t.lstrip('#') for t in tags.split()] + ['Shorts']

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

    # 6. Subir a YouTube
    upload_to_youtube(
        str(video_path),
        content['titulo'],
        content['descripcion'],
        content['hashtags']
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
