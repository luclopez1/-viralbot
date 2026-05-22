#!/usr/bin/env python3
"""
Sistema de generacion de videos tipo RANKING animado
Crea Top 5 (Shorts) o Top 10 (videos largos) con barras animadas
inspirado en canales que generan $200K+ con este tipo de contenido
"""

import os
import json
import re
import random
import subprocess
import sys
from pathlib import Path
from datetime import datetime
from dotenv import load_dotenv
import ssl
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

load_dotenv()

sys.path.insert(0, str(Path(__file__).parent))
from generate_content import (
    _get_gemini_client,
    _get_groq_client,
    generate_speech_with_edge_tts,
    upload_to_youtube,
)

YOUTUBE_API_KEY = os.getenv("YOUTUBE_API_KEY")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
OUTPUT_DIR = Path(os.getenv("OUTPUT_DIR", "./videos_output"))
TEMP_DIR = Path(os.getenv("TEMP_DIR", "./temp"))

OUTPUT_DIR.mkdir(exist_ok=True)
TEMP_DIR.mkdir(exist_ok=True)

# Temas virales para rankings
RANKING_TOPICS = [
    {"tema": "Top {n} IAs que te haran rico en 2026", "unidad": "$/mes", "tipo": "ia"},
    {"tema": "Top {n} criptomonedas que van a explotar en 2026", "unidad": "% prevision", "tipo": "crypto"},
    {"tema": "Top {n} hombres mas ricos del mundo", "unidad": "$ billones", "tipo": "ricos"},
    {"tema": "Top {n} formas de ganar dinero con IA en 2026", "unidad": "$/mes potencial", "tipo": "ia"},
    {"tema": "Top {n} habitos de millonarios", "unidad": "% adopcion", "tipo": "habitos"},
    {"tema": "Top {n} side hustles mas rentables 2026", "unidad": "$/mes", "tipo": "negocio"},
    {"tema": "Top {n} acciones mas rentables de 2026", "unidad": "% rentabilidad", "tipo": "inversion"},
    {"tema": "Top {n} mejores inversiones de 2026", "unidad": "% ROI anual", "tipo": "inversion"},
    {"tema": "Top {n} errores financieros que arruinan tu vida", "unidad": "% afectados", "tipo": "finanzas"},
    {"tema": "Top {n} libros que cambiaran tu vida en 2026", "unidad": "millones vendidos", "tipo": "educacion"},
    {"tema": "Top {n} apps que te haran ganar dinero en 2026", "unidad": "$ promedio/mes", "tipo": "apps"},
    {"tema": "Top {n} negocios online sin inversion", "unidad": "$/mes potencial", "tipo": "negocio"},
]


def generate_ranking_data(num_items: int = 5):
    """Genera datos del ranking con IA"""
    template = random.choice(RANKING_TOPICS)
    topic = template["tema"].format(n=num_items)
    unidad = template["unidad"]
    tipo = template["tipo"]

    print(f"[*] Generando ranking: {topic}")

    prompt = f"""
    Eres experto en crear rankings virales para YouTube.

    Tema: {topic}
    Tipo: {tipo}
    Unidad de medicion: {unidad}

    Crea un TOP {num_items} con datos REALISTAS (no inventes locuras).
    Cada item debe tener:
    - "posicion": numero (1 = mejor, {num_items} = ultimo)
    - "nombre": nombre del item (corto, 2-4 palabras maximo)
    - "valor": numero (sin simbolos, solo numero)
    - "descripcion": frase de 5-10 palabras describiendolo

    REGLAS:
    1. Los valores deben tener PROGRESION coherente (mayor en el #1)
    2. Los nombres deben ser RECONOCIBLES (marcas reales, conceptos conocidos)
    3. Las descripciones deben generar CURIOSIDAD

    Tambien genera:
    - "titulo_viral": titulo del video (max 60 caracteres, gancho fuerte)
    - "intro": frase de gancho de 10-15 palabras para empezar el video
    - "outro": frase final con CTA de suscripcion (10-15 palabras)

    Responde SOLO en JSON sin texto extra:
    {{
        "titulo_viral": "...",
        "intro": "Hook impactante para empezar",
        "items": [
            {{"posicion": {num_items}, "nombre": "Item ultimo", "valor": 1000, "descripcion": "..."}},
            {{"posicion": {num_items-1}, "nombre": "...", "valor": 2000, "descripcion": "..."}},
            ...
            {{"posicion": 1, "nombre": "El mejor", "valor": 10000, "descripcion": "..."}}
        ],
        "outro": "CTA final con suscripcion",
        "hashtags": "#shorts #top #ranking #ia #dinero #viral",
        "tags_seo": "top 10, ranking, viral, dinero, ia, 2026, mejores, comparacion, lista",
        "descripcion": "Descripcion SEO con keywords y CTA"
    }}
    """

    response_text = None
    try:
        print("[*] Intentando con Gemini...")
        gemini_client = _get_gemini_client()
        response = gemini_client.models.generate_content(
            model="gemini-2.0-flash",
            contents=prompt
        )
        response_text = response.text
        print("[OK] Gemini respondio")
    except Exception as e:
        if "429" in str(e) or "RESOURCE_EXHAUSTED" in str(e) or "quota" in str(e).lower():
            print(f"[WARN] Gemini sin cuota, usando Groq...")
            # Prompt simplificado para Groq
            prompt_groq = f"""Crea un TOP {num_items} ranking sobre: {topic}
Unidad: {unidad}

Responde SOLO en JSON con exactamente {num_items} items:
{{
    "titulo_viral": "titulo gancho max 60 chars",
    "intro": "frase gancho 10-15 palabras",
    "items": [
        {{"posicion": {num_items}, "nombre": "Nombre", "valor": 100, "descripcion": "frase corta"}},
        {{"posicion": {num_items-1}, "nombre": "Nombre", "valor": 200, "descripcion": "frase corta"}},
        {{"posicion": {num_items-2}, "nombre": "Nombre", "valor": 500, "descripcion": "frase corta"}},
        {{"posicion": 2, "nombre": "Nombre", "valor": 800, "descripcion": "frase corta"}},
        {{"posicion": 1, "nombre": "Nombre", "valor": 1000, "descripcion": "frase corta"}}
    ],
    "outro": "CTA suscripcion 10-15 palabras",
    "hashtags": "#shorts #top #ranking #viral",
    "tags_seo": "top ranking, viral, 2026",
    "descripcion": "Descripcion SEO con CTA"
}}"""
            for groq_model in ["llama-3.3-70b-versatile", "llama-3.1-8b-instant"]:
                try:
                    print(f"[*] Probando Groq: {groq_model}...")
                    groq_client = _get_groq_client()
                    response = groq_client.chat.completions.create(
                        model=groq_model,
                        messages=[{"role": "user", "content": prompt_groq}],
                        temperature=0.7,
                        max_tokens=3000,
                    )
                    response_text = response.choices[0].message.content
                    print(f"[OK] Groq {groq_model} respondio")
                    break
                except Exception as groq_err:
                    print(f"[WARN] Groq {groq_model} fallo: {groq_err}")
                    continue
        else:
            raise

    if not response_text:
        raise Exception("Ningun modelo respondio")

    try:
        json_match = re.search(r'\{.*\}', response_text, re.DOTALL)
        content = json.loads(json_match.group())
    except Exception as parse_err:
        print(f"[ERROR] JSON parse fallo: {parse_err}")
        print(f"[DEBUG] Respuesta preview: {response_text[:300]}")
        content = None

    if not content or "items" not in content:
        raise Exception("No se pudo generar el ranking")

    content["unidad"] = unidad
    content["tipo"] = tipo
    return content


def create_ranking_frames(content: dict, vertical: bool = True):
    """
    Genera frames animados del ranking usando PIL
    vertical=True para Shorts (1080x1920), False para video largo (1920x1080)
    """
    from PIL import Image, ImageDraw, ImageFont

    print("[*] Creando frames del ranking...")

    if vertical:
        W, H = 1080, 1920
    else:
        W, H = 1920, 1080

    # Colores del tema (estilo moderno)
    BG = "#0a0a14"
    ACCENT = "#00ff88"  # Verde neón
    TEXT = "#ffffff"
    GRAY = "#888899"
    GOLD = "#ffd700"
    SILVER = "#c0c0c0"
    BRONZE = "#cd7f32"

    # Buscar fuente disponible (Ubuntu, Windows, Mac)
    FONT_CANDIDATES = [
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
        "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf",
        "C:\\Windows\\Fonts\\arialbd.ttf",
        "C:\\Windows\\Fonts\\arial.ttf",
        "/System/Library/Fonts/Helvetica.ttc",
        "arial.ttf",
    ]
    font_path = None
    for fp in FONT_CANDIDATES:
        if os.path.exists(fp):
            font_path = fp
            break

    def _load_font(size):
        if font_path:
            try:
                return ImageFont.truetype(font_path, size)
            except Exception:
                pass
        try:
            return ImageFont.truetype("DejaVuSans-Bold.ttf", size)
        except Exception:
            return ImageFont.load_default()

    if vertical:
        font_title = _load_font(80)
        font_position = _load_font(180)
        font_name = _load_font(75)
        font_value = _load_font(95)
        font_desc = _load_font(45)
    else:
        font_title = _load_font(90)
        font_position = _load_font(200)
        font_name = _load_font(85)
        font_value = _load_font(115)
        font_desc = _load_font(50)

    print(f"[*] Usando fuente: {font_path or 'default'}")

    frames_dir = TEMP_DIR / "ranking_frames"
    frames_dir.mkdir(exist_ok=True)
    # Limpiar frames anteriores
    for f in frames_dir.glob("*.png"):
        f.unlink()

    items = sorted(content["items"], key=lambda x: x["posicion"], reverse=True)
    titulo = content["titulo_viral"]
    unidad = content.get("unidad", "")
    max_value = max(item["valor"] for item in items)

    frames = []

    def _draw_gradient_bg(image):
        """Fondo con gradiente vertical para más vida"""
        draw = ImageDraw.Draw(image)
        top = (10, 10, 30)
        bottom = (30, 10, 60)
        for y in range(H):
            t = y / H
            r = int(top[0] * (1 - t) + bottom[0] * t)
            g = int(top[1] * (1 - t) + bottom[1] * t)
            b = int(top[2] * (1 - t) + bottom[2] * t)
            draw.line([(0, y), (W, y)], fill=(r, g, b))
        return image

    # FRAME 1: Intro (titulo)
    img = Image.new('RGB', (W, H), BG)
    _draw_gradient_bg(img)
    d = ImageDraw.Draw(img)
    # Titulo central
    bbox = d.textbbox((0, 0), titulo, font=font_title)
    tw = bbox[2] - bbox[0]
    th = bbox[3] - bbox[1]
    # Wrap titulo si es muy largo
    words = titulo.split()
    lines = []
    current = []
    for w in words:
        test = " ".join(current + [w])
        if d.textbbox((0, 0), test, font=font_title)[2] > W - 100:
            if current:
                lines.append(" ".join(current))
                current = [w]
            else:
                lines.append(w)
        else:
            current.append(w)
    if current:
        lines.append(" ".join(current))

    y = (H - len(lines) * 100) // 2
    for line in lines:
        bbox = d.textbbox((0, 0), line, font=font_title)
        tw = bbox[2] - bbox[0]
        d.text(((W - tw) // 2, y), line, font=font_title, fill=ACCENT)
        y += 100

    intro_path = frames_dir / "frame_00_intro.png"
    img.save(intro_path)
    frames.append(str(intro_path))

    # FRAMES de cada posicion (con animacion de barra creciendo)
    for idx, item in enumerate(items):
        pos = item["posicion"]
        nombre = item["nombre"]
        valor = item["valor"]
        desc = item["descripcion"]

        # Color segun posicion
        if pos == 1:
            color = GOLD
        elif pos == 2:
            color = SILVER
        elif pos == 3:
            color = BRONZE
        else:
            color = ACCENT

        img = Image.new('RGB', (W, H), BG)
        _draw_gradient_bg(img)
        d = ImageDraw.Draw(img)

        if vertical:
            # Layout vertical (Shorts)
            # Numero de posicion grande arriba
            pos_text = f"#{pos}"
            bbox = d.textbbox((0, 0), pos_text, font=font_position)
            tw = bbox[2] - bbox[0]
            d.text(((W - tw) // 2, 150), pos_text, font=font_position, fill=color)

            # Nombre del item
            bbox = d.textbbox((0, 0), nombre, font=font_name)
            tw = bbox[2] - bbox[0]
            # Wrap si es muy largo
            if tw > W - 100:
                words = nombre.split()
                line1 = " ".join(words[:len(words)//2])
                line2 = " ".join(words[len(words)//2:])
                bbox1 = d.textbbox((0, 0), line1, font=font_name)
                bbox2 = d.textbbox((0, 0), line2, font=font_name)
                d.text(((W - (bbox1[2] - bbox1[0])) // 2, 400), line1, font=font_name, fill=TEXT)
                d.text(((W - (bbox2[2] - bbox2[0])) // 2, 490), line2, font=font_name, fill=TEXT)
                y_value = 650
            else:
                d.text(((W - tw) // 2, 450), nombre, font=font_name, fill=TEXT)
                y_value = 600

            # Barra de progreso animada (en posicion final)
            bar_width = int((W - 200) * (valor / max_value))
            bar_y = y_value + 200
            bar_height = 80
            # Fondo barra
            d.rounded_rectangle([100, bar_y, W - 100, bar_y + bar_height], radius=20, fill="#1a1a2e")
            # Barra rellena
            d.rounded_rectangle([100, bar_y, 100 + bar_width, bar_y + bar_height], radius=20, fill=color)

            # Valor numerico
            valor_text = f"{valor:,}" if valor >= 1000 else str(valor)
            valor_full = f"{valor_text} {unidad}"
            bbox = d.textbbox((0, 0), valor_full, font=font_value)
            tw = bbox[2] - bbox[0]
            d.text(((W - tw) // 2, bar_y + 130), valor_full, font=font_value, fill=color)

            # Descripcion
            desc_words = desc.split()
            desc_lines = []
            current = []
            for w in desc_words:
                test = " ".join(current + [w])
                if d.textbbox((0, 0), test, font=font_desc)[2] > W - 100:
                    if current:
                        desc_lines.append(" ".join(current))
                        current = [w]
                else:
                    current.append(w)
            if current:
                desc_lines.append(" ".join(current))

            y = bar_y + 290
            for line in desc_lines:
                bbox = d.textbbox((0, 0), line, font=font_desc)
                tw = bbox[2] - bbox[0]
                d.text(((W - tw) // 2, y), line, font=font_desc, fill=GRAY)
                y += 60

        else:
            # Layout horizontal (video largo)
            pos_text = f"#{pos}"
            bbox = d.textbbox((0, 0), pos_text, font=font_position)
            d.text((100, 200), pos_text, font=font_position, fill=color)

            d.text((400, 250), nombre, font=font_name, fill=TEXT)

            # Barra horizontal
            bar_y = 600
            bar_width = int((W - 600) * (valor / max_value))
            d.rounded_rectangle([400, bar_y, W - 200, bar_y + 80], radius=20, fill="#1a1a2e")
            d.rounded_rectangle([400, bar_y, 400 + bar_width, bar_y + 80], radius=20, fill=color)

            valor_text = f"{valor:,} {unidad}"
            d.text((400, bar_y + 120), valor_text, font=font_value, fill=color)

            # Descripcion
            d.text((400, bar_y + 280), desc, font=font_desc, fill=GRAY)

        frame_path = frames_dir / f"frame_{idx+1:02d}.png"
        img.save(frame_path)
        frames.append(str(frame_path))

    print(f"[OK] Generados {len(frames)} frames")
    return frames


def create_ranking_narration(content: dict) -> str:
    """Crea el texto de narracion del ranking"""
    parts = [content["intro"]]

    items = sorted(content["items"], key=lambda x: x["posicion"], reverse=True)
    for item in items:
        pos = item["posicion"]
        if pos == 1:
            text = f"Y el numero uno es: {item['nombre']}. Con {item['valor']:,} {content.get('unidad', '')}. {item['descripcion']}"
        else:
            text = f"En la posicion numero {pos}: {item['nombre']}. {item['valor']:,} {content.get('unidad', '')}. {item['descripcion']}"
        parts.append(text)

    parts.append(content["outro"])
    return ". ".join(parts)


def assemble_ranking_video(frames: list, audio_path: str, output_path: str, vertical: bool = True):
    """Ensambla el video del ranking usando FFmpeg"""
    print("[*] Ensamblando video del ranking...")

    if not frames:
        print("[ERROR] No hay frames")
        return False

    # Buscar FFmpeg
    ffmpeg_bin = "ffmpeg"
    for p in [r"C:\ffmpeg\ffmpeg-8.1.1-essentials_build\bin\ffmpeg.exe", r"C:\ffmpeg\bin\ffmpeg.exe"]:
        if os.path.exists(p):
            ffmpeg_bin = p
            break

    # Obtener duracion del audio
    ffprobe_bin = ffmpeg_bin.replace("ffmpeg", "ffprobe")
    try:
        probe = subprocess.run(
            [ffprobe_bin, "-v", "quiet", "-of", "csv=p=0", "-show_entries", "format=duration", audio_path],
            capture_output=True, text=True
        )
        audio_duration = float(probe.stdout.strip())
    except:
        audio_duration = 60.0

    # Calcular duracion por frame
    duration_per_frame = audio_duration / len(frames)

    W, H = (1080, 1920) if vertical else (1920, 1080)

    cmd = [ffmpeg_bin, "-y"]
    for f in frames:
        cmd.extend(["-loop", "1", "-t", str(duration_per_frame), "-i", f])
    cmd.extend(["-i", audio_path])

    # Filtro: escalar y concatenar
    filter_parts = []
    concat_parts = []
    for i in range(len(frames)):
        filter_parts.append(f"[{i}:v]scale={W}:{H}:force_original_aspect_ratio=increase,crop={W}:{H},setsar=1[img{i}]")
        concat_parts.append(f"[img{i}]")
    full_filter = ";".join(filter_parts) + ";" + "".join(concat_parts) + f"concat=n={len(frames)}:v=1:a=0[v]"

    cmd.extend([
        "-filter_complex", full_filter,
        "-map", "[v]",
        "-map", f"{len(frames)}:a",
        "-c:v", "libx264",
        "-preset", "medium",
        "-c:a", "aac",
        "-shortest",
        output_path
    ])

    try:
        result = subprocess.run(cmd, capture_output=True, check=True)
        print(f"[OK] Video ranking creado: {output_path}")
        return True
    except subprocess.CalledProcessError as e:
        print(f"[ERROR] FFmpeg fallo: {e.stderr.decode()[:500]}")
        return False


def main():
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--long", action="store_true", help="Video largo (Top 10) en lugar de Short")
    args = parser.parse_args()

    is_long = args.long
    num_items = 10 if is_long else 5
    vertical = not is_long

    print("\n" + "="*60)
    print(f"GENERADOR DE RANKING - {'VIDEO LARGO (Top 10)' if is_long else 'SHORT (Top 5)'}")
    print("="*60 + "\n")

    # 1. Generar contenido del ranking
    content = generate_ranking_data(num_items=num_items)
    print(f"\n[*] Titulo: {content['titulo_viral']}")
    print(f"[*] Items: {len(content['items'])}\n")

    # 2. Crear frames
    frames = create_ranking_frames(content, vertical=vertical)
    if not frames:
        print("[ERROR] No se generaron frames")
        return False

    # 3. Crear narracion
    narration = create_ranking_narration(content)
    print(f"\n[*] Narracion: {len(narration.split())} palabras")

    # 4. Generar voz
    audio_path = TEMP_DIR / ("ranking_long.mp3" if is_long else "ranking_short.mp3")
    if not generate_speech_with_edge_tts(narration, str(audio_path)):
        print("[ERROR] No se pudo generar voz")
        return False

    # 5. Ensamblar video
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    prefix = "ranking_long" if is_long else "ranking_short"
    video_path = OUTPUT_DIR / f"{prefix}_{timestamp}.mp4"

    if not assemble_ranking_video(frames, str(audio_path), str(video_path), vertical=vertical):
        print("[ERROR] No se pudo ensamblar")
        return False

    # 6. Subir a YouTube
    upload_to_youtube(
        str(video_path),
        content['titulo_viral'],
        content.get('descripcion', content['titulo_viral']),
        content.get('hashtags', '#shorts #ranking #top'),
        content.get('tags_seo', '')
    )

    print("\n" + "="*60)
    print("[OK] RANKING COMPLETADO")
    print("="*60)
    print(f"\n  Tipo: {'Video largo' if is_long else 'Short'}")
    print(f"  Video: {video_path}")
    print(f"  Titulo: {content['titulo_viral']}\n")

    return True


if __name__ == "__main__":
    main()
