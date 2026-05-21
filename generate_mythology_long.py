#!/usr/bin/env python3
"""
MYTHOLOGY LONG VIDEO GENERATOR (Spanish)
Genera videos largos de 5-10 min de mitologia griega con imagenes IA animadas
Sube al canal Unveiled en formato horizontal 1920x1080
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

ssl._create_default_https_context = ssl._create_unverified_context
os.environ['PYTHONHTTPSVERIFY'] = '0'

try:
    import httplib2
    _orig = httplib2.Http.__init__
    def _patched(self, *a, **kw):
        kw['disable_ssl_certificate_validation'] = True
        _orig(self, *a, **kw)
    httplib2.Http.__init__ = _patched
except ImportError:
    pass

load_dotenv()

sys.path.insert(0, str(Path(__file__).parent))
from generate_content import _get_gemini_client, _get_groq_client
from generate_content import generate_speech_with_edge_tts
from pollinations_helper import generate_image_batch
from video_utils import (
    find_ffmpeg,
    get_audio_duration,
    upload_to_cinematic_channel,
)

OUTPUT_DIR = Path(os.getenv("OUTPUT_DIR", "./videos_output"))
TEMP_DIR = Path(os.getenv("TEMP_DIR", "./temp"))
OUTPUT_DIR.mkdir(exist_ok=True)
TEMP_DIR.mkdir(exist_ok=True)

# Temas extendidos para videos largos de mitologia griega
MYTHOLOGY_LONG_TOPICS = [
    "La historia completa de Hércules: los 12 trabajos imposibles",
    "La guerra de Troya: 10 años de batalla, traicion y destino",
    "Odiseo y su regreso: 20 años de aventuras y monstruos míticos",
    "El origen de los dioses del Olimpo: como Zeus venció a los Titanes",
    "Edipo Rey: la tragedia mas oscura de la mitología griega",
    "Jason y los Argonautas: la búsqueda del Vellocino de Oro",
    "Teseo: de príncipe desconocido a rey de Atenas",
    "Perseo: el héroe que venció a Medusa y salvó a Andrómeda",
    "Prometeo: el titan que desafió a los dioses y pagó el precio eterno",
    "Perséfone y el origen del invierno: el rapto que cambió el mundo",
    "Dédalo e Ícaro: la historia completa del maestro inventor y su hijo",
    "Aquiles en la guerra de Troya: el guerrero más grande y su tragedia",
    "Medea: la historia completa de la hechicera que todo lo sacrificó",
    "El origen del universo griego: del Caos primordial al Olimpo",
    "Dioniso: el dios más extraño del Olimpo y sus misterios",
    "Ares y Afrodita: el escándalo más grande del Olimpo",
    "Poseidón contra Atenas: la batalla por la ciudad más poderosa",
    "El laberinto de Creta: Dédalo, Minotauro, Ariadna y Teseo",
    "Las Musas y el Monte Helicón: el origen de todo arte y poesia",
    "Hades y el inframundo: el reino de los muertos en la mitologia griega",
]

# Estilo visual consistente para mitologia griega
VISUAL_STYLE = (
    "ancient Greek mythology, dramatic cinematic style, "
    "marble temples, golden hour lighting, epic atmosphere, "
    "hyperrealistic, 4k, professional cinematography, "
    "dramatic shadows, mythological setting"
)


def generate_mythology_long_story(num_scenes: int = 20) -> dict:
    """Genera historia larga de mitologia griega con estructura documental"""
    topic = random.choice(MYTHOLOGY_LONG_TOPICS)
    print(f"[*] Tema seleccionado: {topic}")

    prompt = f"""
    Eres un maestro narrador de documentales mitológicos para YouTube en ESPAÑOL.
    Creas contenido con millones de visualizaciones por su profundidad y drama.

    TEMA: {topic}
    FORMATO: Documental largo de 5-8 minutos con exactamente {num_scenes} escenas

    ESTRUCTURA NARRATIVA:
    - Escenas 1-3: GANCHO DRAMATICO (pregunta impactante, dato sorprendente)
    - Escenas 4-8: CONTEXTO E INICIO (personajes, mundo, conflicto inicial)
    - Escenas 9-14: DESARROLLO Y TENSION (giros, desafíos, revelaciones)
    - Escenas 15-18: CLIMAX (el momento mas intenso y dramatico)
    - Escenas 19-{num_scenes}: DESENLACE Y REFLEXION (moraleja, pregunta final)

    REGLAS:
    1. Cada escena tiene 3-5 frases de narracion en ESPAÑOL (40-60 palabras)
    2. Total narracion: minimo 800 palabras para 5-8 minutos de video
    3. Cada escena tiene un prompt de imagen detallado en INGLES para IA
    4. Voz: documental serio y apasionante, como National Geographic en español
    5. Incluye datos historicos reales mezclados con la mitologia
    6. Termina con reflexion filosofica sobre la condicion humana

    Para los prompts de imagen incluye siempre:
    - Personajes especificos con ropa y atributos griegos correctos
    - Escenario detallado (templo especifico, monte Olimpo, Estigia, etc.)
    - Iluminacion cinematografica (dorada epica, tormentosa, cavernosa)
    - Angulo cinematografico variado (plano general, contrapicado, aereo)
    - Accion especifica (combate, vuelo, transformacion, etc.)
    - Estilo: {VISUAL_STYLE}

    Responde SOLO en JSON sin texto extra:
    {{
        "titulo_viral": "titulo epico max 80 chars en español",
        "escenas": [
            {{
                "narracion": "3-5 frases en ESPAÑOL (40-60 palabras) de narracion documental",
                "prompt_imagen": "Highly detailed cinematic English prompt for AI image generation"
            }}
        ],
        "hashtags": "#mitologia #grecia #documental #historia #unveiled",
        "tags_seo": "mitologia griega, documental, historia antigua, grecia, dioses griegos",
        "descripcion": "Descripcion SEO completa en español con marcas de tiempo aproximadas y CTA"
    }}
    """

    response_text = None
    try:
        print("[*] Generando historia larga con Gemini...")
        client = _get_gemini_client()
        response = client.models.generate_content(
            model="gemini-2.0-flash", contents=prompt
        )
        response_text = response.text
    except Exception as e:
        if "429" in str(e) or "RESOURCE_EXHAUSTED" in str(e) or "quota" in str(e).lower():
            print("[WARN] Gemini sin cuota, usando Groq con prompt reducido...")
            # Prompt reducido para Groq (evitar limite de tokens)
            prompt_groq = f"""Crea un documental mitologico sobre: {topic}

Genera exactamente 12 escenas en español. Para cada escena:
- narracion: 3-4 frases dramaticas en ESPAÑOL (40-50 palabras)
- prompt_imagen: descripcion cinematografica detallada en INGLES para generar imagen IA

Responde SOLO en JSON:
{{
    "titulo_viral": "titulo epico max 80 chars",
    "escenas": [
        {{"narracion": "...", "prompt_imagen": "cinematic detailed English prompt..."}},
        {{"narracion": "...", "prompt_imagen": "cinematic detailed English prompt..."}},
        {{"narracion": "...", "prompt_imagen": "cinematic detailed English prompt..."}},
        {{"narracion": "...", "prompt_imagen": "cinematic detailed English prompt..."}},
        {{"narracion": "...", "prompt_imagen": "cinematic detailed English prompt..."}},
        {{"narracion": "...", "prompt_imagen": "cinematic detailed English prompt..."}},
        {{"narracion": "...", "prompt_imagen": "cinematic detailed English prompt..."}},
        {{"narracion": "...", "prompt_imagen": "cinematic detailed English prompt..."}},
        {{"narracion": "...", "prompt_imagen": "cinematic detailed English prompt..."}},
        {{"narracion": "...", "prompt_imagen": "cinematic detailed English prompt..."}},
        {{"narracion": "...", "prompt_imagen": "cinematic detailed English prompt..."}},
        {{"narracion": "...", "prompt_imagen": "cinematic detailed English prompt..."}}
    ],
    "hashtags": "#mitologia #grecia #documental #historia",
    "tags_seo": "mitologia griega, documental, historia antigua",
    "descripcion": "Descripcion SEO en español con CTA"
}}"""
            groq = _get_groq_client()
            for groq_model in ["llama-3.3-70b-versatile", "llama-3.1-8b-instant"]:
                try:
                    print(f"[*] Probando Groq: {groq_model}...")
                    response = groq.chat.completions.create(
                        model=groq_model,
                        messages=[{"role": "user", "content": prompt_groq}],
                        temperature=0.8,
                        max_tokens=4000,
                    )
                    response_text = response.choices[0].message.content
                    print(f"[OK] Groq respondio con {groq_model}")
                    break
                except Exception as groq_err:
                    print(f"[WARN] {groq_model} fallo: {groq_err}")
                    continue
        else:
            raise

    if not response_text:
        print("[ERROR] No se obtuvo respuesta de ningun modelo")
        return None

    try:
        match = re.search(r'\{.*\}', response_text, re.DOTALL)
        content = json.loads(match.group())
    except Exception as e:
        print(f"[ERROR] JSON parse error: {e}")
        return None

    if not content or "escenas" not in content:
        return None

    print(f"[OK] Historia generada: {len(content['escenas'])} escenas")
    print(f"[*] Titulo: {content['titulo_viral']}")

    # Contar palabras totales de narracion
    total_words = sum(len(s["narracion"].split()) for s in content["escenas"])
    print(f"[*] Palabras narracion: {total_words} (~{total_words//130:.0f}-{total_words//100:.0f} min)")

    return content, topic


def assemble_mythology_long_video(
    clips: list,
    images: list,
    audio_path: str,
    output_path: str,
    srt_path: str = None,
):
    """
    Ensambla video largo horizontal en un solo comando FFmpeg.
    Sin clips intermedios — concat directo + audio + subtitulos.
    """
    print("\n[*] Ensamblando video largo de mitologia...")
    ffmpeg = find_ffmpeg()
    W, H = 1920, 1080
    fps = 24

    audio_duration = get_audio_duration(audio_path)
    num_images = len(images)
    dur = audio_duration / num_images
    dur = max(dur, 5.0)

    print(f"[*] Audio: {audio_duration:.1f}s | {num_images} imagenes x {dur:.1f}s")

    has_srt = srt_path and Path(srt_path).exists() and Path(srt_path).stat().st_size > 10
    subtitle_style = (
        "FontName=Liberation Sans,FontSize=36,PrimaryColour=&H00FFFFFF,"
        "Bold=1,OutlineColour=&H00000000,Outline=2,Shadow=1,"
        "Alignment=2,MarginL=100,MarginR=100,MarginV=60,WrapStyle=2"
    )

    filter_parts = []
    for i in range(num_images):
        filter_parts.append(
            f"[{i}:v]scale={W}:{H}:force_original_aspect_ratio=increase,"
            f"crop={W}:{H}:(ow-iw)/2:(oh-ih)/2,setsar=1,fps={fps}[v{i}]"
        )
    concat_inputs = "".join(f"[v{i}]" for i in range(num_images))
    filter_complex = (
        ";".join(filter_parts) +
        f";{concat_inputs}concat=n={num_images}:v=1:a=0[vraw]"
    )

    if has_srt:
        srt_escaped = srt_path.replace("\\", "/").replace(":", "\\:")
        filter_complex += f";[vraw]subtitles='{srt_escaped}':force_style='{subtitle_style}'[v]"
    else:
        filter_complex += ";[vraw]copy[v]"

    cmd = [ffmpeg, "-y"]
    for img in images:
        cmd.extend(["-loop", "1", "-t", str(dur), "-i", img])
    cmd.extend(["-i", audio_path])
    cmd.extend([
        "-filter_complex", filter_complex,
        "-map", "[v]",
        "-map", f"{num_images}:a",
        "-c:v", "libx264", "-preset", "fast", "-pix_fmt", "yuv420p",
        "-c:a", "aac", "-b:a", "192k",
        "-shortest",
        output_path
    ])

    try:
        subprocess.run(cmd, capture_output=True, check=True)
        size_mb = Path(output_path).stat().st_size / 1024 / 1024
        print(f"[OK] Video largo creado: {output_path} ({size_mb:.1f}MB)")
        return True
    except subprocess.CalledProcessError as e:
        print(f"[WARN] FFmpeg con subtitulos fallo, reintentando sin subtitulos...")
        filter_simple = (
            ";".join(filter_parts) +
            f";{concat_inputs}concat=n={num_images}:v=1:a=0[v]"
        )
        cmd2 = [ffmpeg, "-y"]
        for img in images:
            cmd2.extend(["-loop", "1", "-t", str(dur), "-i", img])
        cmd2.extend(["-i", audio_path])
        cmd2.extend([
            "-filter_complex", filter_simple,
            "-map", "[v]",
            "-map", f"{num_images}:a",
            "-c:v", "libx264", "-preset", "fast", "-pix_fmt", "yuv420p",
            "-c:a", "aac", "-b:a", "192k",
            "-shortest",
            output_path
        ])
        try:
            subprocess.run(cmd2, capture_output=True, check=True)
            print(f"[OK] Video creado (sin subtitulos): {output_path}")
            return True
        except subprocess.CalledProcessError as e2:
            print(f"[ERROR] Fallo total: {e2.stderr.decode()[:500]}")
            return False


def main():
    print("\n" + "=" * 60)
    print("GENERADOR MITOLOGIA GRIEGA - VIDEO LARGO (Español)")
    print("=" * 60 + "\n")

    # 1. Generar historia larga (15 escenas para ~5-7 min, mas rapido de generar)
    result = generate_mythology_long_story(num_scenes=15)
    if not result:
        return False
    content, topic = result

    # 2. Generar imagenes cinematograficas horizontales (1920x1080)
    prompts = [s["prompt_imagen"] for s in content["escenas"]]
    images_dir = TEMP_DIR / "mythology_long_images"
    images = generate_image_batch(
        prompts, str(images_dir),
        width=1920, height=1080,
        prefix="myth_long_scene"
    )

    if len(images) < len(prompts) // 2:
        print("[ERROR] Demasiados fallos de imagen")
        return False

    # 3. Videos largos usan Ken Burns directamente (HF SVD es demasiado lento para 15+ escenas)
    # Ken Burns queda fluido y profesional en formato documental
    clips = [None] * len(images)
    print(f"[*] Video largo: usando Ken Burns para {len(images)} escenas")

    # 4. Construir narracion completa
    narracion = " ".join([s["narracion"] for s in content["escenas"]])
    word_count = len(narracion.split())
    print(f"\n[*] Narracion: {word_count} palabras (~{word_count//130:.0f}-{word_count//100:.0f} min)")

    # 5. Generar voz en español
    audio_path = str(TEMP_DIR / "mythology_long_audio.mp3")
    srt_path = audio_path.replace(".mp3", ".srt")

    if not generate_speech_with_edge_tts(narracion, audio_path):
        print("[ERROR] Fallo generacion de voz")
        return False

    # 6. Ensamblar video horizontal con transiciones
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    video_path = str(OUTPUT_DIR / f"mythology_long_{timestamp}.mp4")

    srt = srt_path if Path(srt_path).exists() else None
    if not assemble_mythology_long_video(clips, images, audio_path, video_path, srt):
        return False

    # 7. Subir al canal Unveiled
    upload_to_cinematic_channel(
        video_path,
        content["titulo_viral"],
        content.get("descripcion", content["titulo_viral"]),
        content.get("hashtags", "#mitologia #grecia #documental"),
        content.get("tags_seo", ""),
    )

    print("\n" + "=" * 60)
    print("[OK] MITOLOGIA LARGO COMPLETADO")
    print("=" * 60)
    print(f"\n  Tema: {topic}")
    print(f"  Titulo: {content['titulo_viral']}")
    print(f"  Video: {video_path}\n")
    return True


if __name__ == "__main__":
    main()
