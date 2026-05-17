#!/usr/bin/env python3
"""
Sistema de generación de videos LARGOS (8-10 minutos) para YouTube
Genera guión, voz, imágenes y monta el video final en formato horizontal 1920x1080
Rota entre 4 tipos: Listicle, Tutorial, Análisis, Storytelling
"""

import os
import json
import re
import random
import subprocess
from pathlib import Path
from datetime import datetime
import sys

# Importar funciones del script principal
sys.path.insert(0, str(Path(__file__).parent))

# Configurar entorno antes de importar
from dotenv import load_dotenv
load_dotenv()

import ssl
import certifi
import httpx
import requests

ssl._create_default_https_context = ssl._create_unverified_context
os.environ['PYTHONHTTPSVERIFY'] = '0'

try:
    import httplib2
    _orig_httplib2_init = httplib2.Http.__init__
    def _patched_httplib2_init(self, *args, **kwargs):
        kwargs['disable_ssl_certificate_validation'] = True
        _orig_httplib2_init(self, *args, **kwargs)
    httplib2.Http.__init__ = _patched_httplib2_init
except ImportError:
    pass

# Importar funciones desde el script principal
from generate_content import (
    _get_gemini_client,
    _get_groq_client,
    download_images_from_pexels,
    generate_speech_with_edge_tts,
    NICHES,
    FALLBACK_TOPICS,
)

# Configuración para video largo
YOUTUBE_API_KEY = os.getenv("YOUTUBE_API_KEY")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
PEXELS_API_KEY = os.getenv("PEXELS_API_KEY")
OUTPUT_DIR = Path(os.getenv("OUTPUT_DIR", "./videos_output"))
TEMP_DIR = Path(os.getenv("TEMP_DIR", "./temp"))
LONG_VIDEO_DURATION = 540  # 9 minutos (entre 8-10)
LONG_VIDEO_RESOLUTION = "1920x1080"  # Horizontal para video normal

OUTPUT_DIR.mkdir(exist_ok=True)
TEMP_DIR.mkdir(exist_ok=True)


# 4 tipos de contenido que rotan aleatoriamente
CONTENT_TYPES = ["listicle", "tutorial", "analisis", "storytelling"]


def get_random_topic():
    """Obtiene un tema aleatorio para el video largo"""
    print("[*] Seleccionando tema para video largo...")

    niche = random.choice(NICHES)
    print(f"[*] Nicho seleccionado: {niche}")

    try:
        url = "https://www.googleapis.com/youtube/v3/search"
        params = {
            "part": "snippet",
            "type": "video",
            "maxResults": 5,
            "order": "viewCount",
            "q": niche,
            "regionCode": "ES",
            "relevanceLanguage": "es",
            "videoDuration": "medium",  # 4-20 minutos
            "publishedAfter": "2026-01-01T00:00:00Z",
            "key": YOUTUBE_API_KEY,
        }

        response = requests.get(url, params=params, timeout=10, verify=False)
        response.raise_for_status()

        results = response.json()
        if results.get("items"):
            topic = results["items"][0]["snippet"]["title"]
            return topic
    except Exception as e:
        print(f"[WARN] Error con YouTube API: {e}")

    # Fallback
    fallback = random.choice(FALLBACK_TOPICS)
    return fallback["title"]


def generate_long_script(topic: str, content_type: str):
    """
    Genera un guión LARGO (8-10 minutos = ~1200-1500 palabras)
    Tipo: listicle, tutorial, analisis, storytelling
    """
    print(f"[*] Generando guion tipo: {content_type.upper()}")
    print(f"[*] Tema: {topic}")

    # Prompt base según tipo de contenido
    type_prompts = {
        "listicle": """
        Crea un LISTICLE en formato "Top 7" o "10 mejores" o "5 razones por las que".
        Estructura:
        - Introducción con gancho fuerte (30 seg)
        - 5-7 puntos numerados con explicación detallada
        - Cada punto: ejemplo concreto + por qué importa
        - Conclusión con CTA fuerte
        """,
        "tutorial": """
        Crea un TUTORIAL paso a paso para conseguir un objetivo concreto.
        Estructura:
        - Introducción: qué van a aprender y por qué (1 min)
        - 5-7 pasos detallados, ordenados
        - Cada paso: qué hacer + cómo hacerlo + error común
        - Conclusión + recapitulación + CTA
        """,
        "analisis": """
        Crea un ANALISIS PROFUNDO de una tendencia, mercado o concepto.
        Estructura:
        - Hook con pregunta provocadora o dato shock
        - Contexto: qué está pasando
        - Análisis: por qué está pasando, datos, ejemplos
        - Proyección: qué viene después
        - Conclusión + opinion personal + CTA
        """,
        "storytelling": """
        Crea una HISTORIA real o ficticia inspiradora sobre el tema.
        Estructura:
        - Hook: empieza por el clímax o resultado increíble
        - Contexto: quién es el protagonista, situación inicial
        - Conflicto: qué problema enfrentaba
        - Resolución: cómo lo solucionó paso a paso
        - Lección + CTA al espectador
        """
    }

    prompt = f"""
    Eres el mejor creador de YouTube long-form (8-10 minutos) en español.
    Has creado canales con millones de suscriptores.

    Tema: {topic}
    Tipo de contenido: {content_type.upper()}

    {type_prompts[content_type]}

    ESTRUCTURA OBLIGATORIA (formato capitulos profesionales):
    El video DEBE tener 5 SECCIONES/CAPITULOS claramente definidos.
    Cada seccion debe tener:
    - Titulo descriptivo y atractivo
    - 3 puntos clave que se desarrollan en el guion
    - Transicion narrativa hacia la siguiente seccion (conecta ideas)

    Ejemplo de estructura:
    SECCION 1: "El Problema Que Nadie Te Dice" (1.5 min)
      - Punto 1: Estado actual del mercado/situacion
      - Punto 2: Por que es un problema
      - Punto 3: Transicion: "Pero hay una solucion..."

    SECCION 2: "La Primera Herramienta/Concepto Clave" (1.5 min)
      - Punto 1: Introducir el primer elemento
      - Punto 2: Como funciona / ejemplo real
      - Punto 3: Transicion al siguiente

    SECCION 3: "El Truco/Estrategia Avanzada" (1.5 min)
      - Punto 1: Profundizar con dato/estrategia avanzada
      - Punto 2: Caso practico o ejemplo
      - Punto 3: Conectar con la accion practica

    SECCION 4: "Como Aplicarlo HOY Mismo" (2 min)
      - Punto 1: Pasos concretos accionables
      - Punto 2: Errores comunes a evitar
      - Punto 3: Resultados esperados

    SECCION 5: "El Proximo Paso (Conclusion)" (1.5 min)
      - Punto 1: Recap de los puntos clave
      - Punto 2: Vision a futuro / urgencia
      - Punto 3: CTA fuerte de suscripcion

    REGLAS CRITICAS:
    1. DURACION: El guion debe ser de 1200-1500 palabras (8-10 minutos hablados)
    2. GANCHO INICIAL (primeros 15 segundos antes de Seccion 1): pregunta impactante o dato shock
    3. NO PERDER RETENCION: cada seccion termina anticipando la siguiente
    4. PROMESA al principio: "Al final de este video vas a saber..."
    5. CTA cada 2-3 minutos: "Sigueme para mas videos asi"
    6. Tono: directo, autoridad, energetico
    7. Sin emojis en el texto
    8. Frases claras y bien estructuradas (no como Shorts)
    9. INCLUIR EN LA DESCRIPCION los timestamps de cada seccion (0:00 Intro, 0:30 Seccion 1, etc.)

    CTA FINAL OBLIGATORIO (ULTIMA PARTE DEL GUION - critico para suscriptores):
    El guion DEBE TERMINAR SIEMPRE con un CTA FUERTE de suscripcion de 2-3 frases.
    Ejemplos (usa una variacion):
    - "Si te ha gustado este video, suscribete al canal para saber mas sobre este tema.
       Activa la campana para no perderte ningun video. Nos vemos en el proximo."
    - "Suscribete para mas contenido como este. Dale like si te ha aportado valor
       y comparte el video con alguien que lo necesite. Hasta la proxima."
    - "Si quieres mas informacion sobre [tema], suscribete y activa la campana.
       En el proximo video voy a hablar de [tema relacionado]. No te lo pierdas."
    - "Suscribete para descubrir mas secretos como este cada dia. Dale like, comenta
       que te ha parecido y compartelo con quien lo necesite. Nos vemos pronto."
    IMPORTANTE: El video DEBE cerrar SIEMPRE con esta llamada a la accion clara.

    TITULO VIRAL (max 70 caracteres) - USA FORMULAS PROBADAS CON MILLONES DE VISTAS:

    FORMULA 1 - Storytelling personal (1M+ vistas):
      "ChatGPT me hizo rico: Mi historia REAL con IA"
      "Como gane mi primer millon con IA en 2026"

    FORMULA 2 - Negacion + Alternativa (600K+ vistas):
      "NO inviertas en Bitcoin en 2026 (HAZ ESTO)"
      "NO empieces dropshipping (mira esto en su lugar)"

    FORMULA 3 - Estadistica shock + pregunta (3M+ vistas):
      "Por que el 95% pierde dinero con IA"
      "Por que el 99% nunca consigue ser rico"

    FORMULA 4 - GRATIS/FREE (1.8M+ vistas):
      "Top 10 herramientas IA GRATIS para 2026"
      "Los mejores cursos de IA totalmente GRATIS"

    FORMULA 5 - Autoridad + Drama (550K+ vistas):
      "Google acaba de DESTRUIR este negocio con IA"
      "OpenAI acaba de matar 5 industrias"

    FORMULA 6 - Warning + Lista (alta retencion):
      "12 SCAMS de IA que debes evitar en 2026"
      "Cuidado con estas 5 estafas crypto"

    Palabras gancho probadas: KILLED, DESTROYED, NUNCA, SIEMPRE, GRATIS, SECRETO, NADIE, REAL, ESTAFA, CUIDADO, 99%, 95%

    Responde SOLO en JSON sin texto extra:
    {{
        "titulo": "Titulo viral largo (max 70 caracteres)",
        "esquema": [
            {{
                "seccion": 1,
                "titulo": "Titulo de la primera seccion",
                "puntos": ["punto 1", "punto 2", "punto 3"]
            }},
            {{
                "seccion": 2,
                "titulo": "Titulo de la segunda seccion",
                "puntos": ["punto 1", "punto 2", "punto 3"]
            }},
            {{
                "seccion": 3,
                "titulo": "Titulo de la tercera seccion",
                "puntos": ["punto 1", "punto 2", "punto 3"]
            }},
            {{
                "seccion": 4,
                "titulo": "Titulo de la cuarta seccion",
                "puntos": ["punto 1", "punto 2", "punto 3"]
            }},
            {{
                "seccion": 5,
                "titulo": "Titulo de la quinta seccion (conclusion + CTA)",
                "puntos": ["punto 1", "punto 2", "CTA fuerte"]
            }}
        ],
        "guion": "Guion completo de 1200-1500 palabras siguiendo la estructura de las 5 secciones del esquema",
        "hashtags": "#dinero #ia #finanzas #emprendimiento #educacion #youtube #2026",
        "descripcion": "Descripcion atractiva con CTA + TIMESTAMPS de cada seccion (formato: 0:00 Intro, 0:30 Seccion 1: titulo, 2:00 Seccion 2: titulo, etc.) + palabras clave."
    }}
    """

    response_text = None

    # Intentar primero con Gemini
    try:
        print("[*] Intentando con Gemini...")
        gemini_client = _get_gemini_client()
        from google.genai import types as genai_types
        response = gemini_client.models.generate_content(
            model="gemini-2.0-flash",
            contents=prompt
        )
        response_text = response.text
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
                    max_tokens=4000,
                )
                response_text = response.choices[0].message.content
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
                "hashtags": "#dinero #ia #finanzas #educacion #youtube",
                "descripcion": topic,
            }
    except json.JSONDecodeError:
        content = {
            "titulo": topic,
            "guion": response_text,
            "hashtags": "#dinero #ia #finanzas #educacion #youtube",
            "descripcion": topic,
        }

    return content


def create_long_video_with_ffmpeg(images: list, audio_path: str, output_path: str, srt_path: str = None):
    """
    Crea video LARGO en formato 1920x1080 (horizontal) a partir de imágenes y audio
    """
    print(f"[*] Creando video LARGO con FFmpeg (1920x1080)...")

    try:
        if not images:
            placeholder = TEMP_DIR / "placeholder_long.png"
            from PIL import Image, ImageDraw
            img = Image.new('RGB', (1920, 1080), color='#1a1a1a')
            d = ImageDraw.Draw(img)
            d.text((960, 540), "Loading...", fill="white", anchor="mm")
            img.save(placeholder)
            images = [str(placeholder)]

        # Obtener duración real del audio
        ffprobe_bin = "ffprobe"
        ffprobe_paths = [
            r"C:\ffmpeg\ffmpeg-8.1.1-essentials_build\bin\ffprobe.exe",
            r"C:\ffmpeg\bin\ffprobe.exe",
        ]
        for p in ffprobe_paths:
            if os.path.exists(p):
                ffprobe_bin = p
                break

        try:
            probe = subprocess.run(
                [ffprobe_bin, "-v", "quiet", "-of", "csv=p=0",
                 "-show_entries", "format=duration", audio_path],
                capture_output=True, text=True
            )
            audio_duration = float(probe.stdout.strip())
        except:
            audio_duration = LONG_VIDEO_DURATION

        duration_per_image = audio_duration / len(images)

        # Filtro FFmpeg horizontal 1920x1080 (LLENA TODA LA PANTALLA con crop)
        filter_parts = []
        concat_parts = []

        for i, img in enumerate(images):
            # scale=increase + crop: llena toda la pantalla recortando si es necesario
            # Sin bandas negras - imagen completa
            filter_parts.append(
                f"[{i}:v]scale=1920:1080:force_original_aspect_ratio=increase,"
                f"crop=1920:1080,setsar=1[img{i}]"
            )
            concat_parts.append(f"[img{i}]")

        concat_filter = "".join(concat_parts) + f"concat=n={len(images)}:v=1:a=0[v]"
        full_filter = ";".join(filter_parts) + ";" + concat_filter

        # Buscar ffmpeg
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
        for img in images:
            cmd.extend(["-loop", "1", "-t", str(duration_per_image), "-i", img])
        cmd.extend(["-i", audio_path])
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

        subprocess.run(cmd, check=True, capture_output=True)
        print(f"[OK] Video LARGO creado: {output_path}")
        return True

    except Exception as e:
        print(f"[ERROR] Error creando video largo: {e}")
        return False


def upload_long_video_to_youtube(video_path: str, title: str, description: str, tags: str):
    """
    Sube un video LARGO (no Short) a YouTube
    """
    from google.oauth2.credentials import Credentials
    from google.auth.transport.requests import Request
    from googleapiclient.discovery import build
    from googleapiclient.http import MediaFileUpload

    print(f"[*] Subiendo video LARGO a YouTube...")
    print(f"    Titulo: {title}")

    TOKEN_FILE = 'youtube_token.json'
    SCOPES = ['https://www.googleapis.com/auth/youtube.upload']

    try:
        # Leer token (mismo proceso que el upload normal)
        token_env = os.getenv("YOUTUBE_TOKEN")
        if token_env:
            raw = token_env.strip().strip("'\"")
            creds = Credentials.from_authorized_user_info(json.loads(raw), SCOPES)
        else:
            if not os.path.exists(TOKEN_FILE):
                print("[ERROR] No hay token de YouTube")
                return False
            with open(TOKEN_FILE, 'r', encoding='utf-8') as f:
                raw = f.read().strip().strip("'\"")
            creds = Credentials.from_authorized_user_info(json.loads(raw), SCOPES)

        # Renovar token si ha expirado
        if creds.expired and creds.refresh_token:
            print(f"[*] Renovando token...")
            refresh_session = requests.Session()
            refresh_session.verify = False
            creds.refresh(Request(session=refresh_session))
            with open(TOKEN_FILE, 'w') as f:
                f.write(creds.to_json())
            print(f"[OK] Token renovado")

        youtube = build('youtube', 'v3', credentials=creds)

        # NO añadir #Shorts (es video largo)
        long_title = title[:100]
        long_description = description[:4900] + '\n\n' + tags
        tag_list = [t.lstrip('#') for t in tags.split()]

        body = {
            'snippet': {
                'title': long_title,
                'description': long_description,
                'tags': tag_list,
                'categoryId': '28',  # Ciencia y tecnología
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
        print(f"[OK] Video LARGO subido!")
        print(f"   URL: https://www.youtube.com/watch?v={video_id}")
        return True

    except Exception as e:
        print(f"[WARN] No se pudo subir: {e}")
        return False


def main():
    """
    Flujo principal para video largo
    """
    print("\n" + "="*60)
    print("SISTEMA DE GENERACION DE VIDEOS LARGOS PARA YOUTUBE")
    print("="*60 + "\n")

    # 1. Seleccionar tipo de contenido aleatorio
    content_type = random.choice(CONTENT_TYPES)
    print(f"[*] Tipo de contenido: {content_type.upper()}\n")

    # 2. Obtener tema
    topic = get_random_topic()
    print(f"[*] Tema seleccionado: {topic}\n")

    # 3. Generar guion largo
    content = generate_long_script(topic, content_type)
    word_count = len(content['guion'].split())
    print(f"\n[*] Guion generado: {word_count} palabras (~{word_count // 150} min)")

    # Mostrar esquema si existe
    if "esquema" in content and content["esquema"]:
        print("\n[*] ESQUEMA DEL VIDEO:")
        print("="*60)
        for seccion in content["esquema"]:
            print(f"\n  SECCION {seccion.get('seccion', '?')}: {seccion.get('titulo', 'Sin titulo')}")
            for punto in seccion.get('puntos', []):
                print(f"    - {punto}")
        print("="*60 + "\n")

    # 4. Generar voz
    audio_path = TEMP_DIR / "voice_long.mp3"
    if not generate_speech_with_edge_tts(content['guion'], str(audio_path)):
        print("[ERROR] No se pudo generar la voz")
        return False

    # 5. Descargar muchas imágenes (videos largos necesitan más)
    images = download_images_from_pexels(topic, count=25)

    # 6. Crear video largo (horizontal)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    video_path = OUTPUT_DIR / f"video_long_{timestamp}.mp4"

    srt_path = str(audio_path).replace(".mp3", ".srt")
    if not create_long_video_with_ffmpeg(images, str(audio_path), str(video_path), srt_path):
        print("[ERROR] Error al crear el video")
        return False

    # 7. Subir como video normal (no Short)
    upload_long_video_to_youtube(
        str(video_path),
        content['titulo'],
        content['descripcion'],
        content['hashtags']
    )

    print("\n" + "="*60)
    print("[OK] VIDEO LARGO COMPLETADO")
    print("="*60)
    print(f"\n  Tipo: {content_type.upper()}")
    print(f"  Video: {video_path}")
    print(f"  Titulo: {content['titulo']}")
    print(f"  Duracion: ~{word_count // 150} minutos\n")

    return True


if __name__ == "__main__":
    main()
