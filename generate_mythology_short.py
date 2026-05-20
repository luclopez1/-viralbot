#!/usr/bin/env python3
"""
MYTHOLOGY SHORT GENERATOR (Spanish)
Genera Shorts de mitologia griega con imagenes IA animadas
Sube al canal Unveiled
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
from huggingface_video import animate_batch
from video_utils import (
    find_ffmpeg,
    get_audio_duration,
    upload_to_cinematic_channel,
)

OUTPUT_DIR = Path(os.getenv("OUTPUT_DIR", "./videos_output"))
TEMP_DIR = Path(os.getenv("TEMP_DIR", "./temp"))
OUTPUT_DIR.mkdir(exist_ok=True)
TEMP_DIR.mkdir(exist_ok=True)

HF_TOKEN = os.getenv("HF_API_TOKEN", "")

# Historias de mitologia griega para Shorts virales
MYTHOLOGY_SHORTS = [
    "La trágica historia de Ícaro y su vuelo hacia el sol",
    "Perseo contra Medusa: la batalla más épica de la mitología",
    "El Minotauro en el laberinto: el secreto oscuro de Creta",
    "La caja de Pandora: cómo llegó el mal al mundo",
    "Orfeo y Eurídice: el amor que venció a la muerte... casi",
    "Prometeo encadenado: el titán que robó el fuego a los dioses",
    "El caballo de Troya: el engaño que destruyó una ciudad",
    "Narciso: el joven tan hermoso que se enamoró de sí mismo",
    "Sísifo: condenado a empujar una roca eternamente",
    "Aquiles: el guerrero invencible con un solo punto débil",
    "Hércules y el León de Nemea: el primer trabajo imposible",
    "Medea: la hechicera que lo sacrificó todo por amor y venganza",
    "Edipo Rey: el hombre que cumplió la profecía que intentó evitar",
    "Las Sirenas: las criaturas que volvían locos a los marineros",
    "Teseo y el Minotauro: el héroe que entró al laberinto sin retorno",
]

# Estilo visual consistente para mitologia griega
VISUAL_STYLE = (
    "ancient Greek mythology, dramatic cinematic style, "
    "marble temples, golden hour lighting, epic atmosphere, "
    "hyperrealistic, 4k, professional cinematography, "
    "dramatic shadows, mythological setting"
)


def generate_mythology_story(topic: str, num_scenes: int = 8) -> dict:
    """Genera historia de mitologia griega con escenas y prompts de imagen"""
    print(f"[*] Generando historia: {topic}")

    prompt = f"""
    Eres un experto narrador de mitologia griega para YouTube Shorts virales en ESPAÑOL.

    TEMA: {topic}
    FORMATO: Short de 60-90 segundos con {num_scenes} escenas

    Crea una historia DRAMATICA y EMOCIONANTE con exactamente {num_scenes} escenas.

    ESTRUCTURA:
    - Escena 1-2: GANCHO inicial (presenta el conflicto de forma impactante)
    - Escena 3-5: DESARROLLO (accion, tension, giro)
    - Escena 6-7: CLIMAX (el momento mas dramatico)
    - Escena 8: DESENLACE + pregunta al espectador

    REGLAS:
    1. Cada escena tiene 2-3 frases de narracion en ESPAÑOL (20-35 palabras)
    2. Total narracion: minimo 180 palabras para que dure 60-90 segundos
    3. Cada escena tiene un prompt de imagen en INGLES para IA (muy detallado)
    4. Los prompts de imagen deben ser CINEMATOGRAFICOS y consistentes
    5. Voz narrativa: dramatica, misteriosa, como un documentalista
    6. Termina con una pregunta o frase que genere comentarios

    Para los prompts de imagen incluye siempre:
    - Personaje especifico de la historia (Zeus, Perseo, etc.)
    - Escenario griego (templo, mar egeo, olimpo, laberinto)
    - Iluminacion dramatica (dorada, tormentosa, subterranea)
    - Angulo cinematografico (plano picado, contrapicado, primer plano)
    - Estilo: {VISUAL_STYLE}

    Responde SOLO en JSON sin texto extra:
    {{
        "titulo_viral": "titulo impactante max 60 chars en español",
        "escenas": [
            {{
                "narracion": "2-3 frases dramaticas en ESPAÑOL (20-35 palabras)",
                "prompt_imagen": "Detailed cinematic English prompt for AI image"
            }}
        ],
        "hashtags": "#shorts #mitologia #grecia #historia #viral",
        "tags_seo": "mitologia griega, historia antigua, shorts virales, grecia",
        "descripcion": "Descripcion SEO en español con CTA"
    }}
    """

    response_text = None
    try:
        print("[*] Generando con Gemini...")
        client = _get_gemini_client()
        response = client.models.generate_content(
            model="gemini-2.0-flash", contents=prompt
        )
        response_text = response.text
    except Exception as e:
        if "429" in str(e) or "RESOURCE_EXHAUSTED" in str(e) or "quota" in str(e).lower():
            print("[WARN] Gemini sin cuota, usando Groq...")
            groq = _get_groq_client()
            response = groq.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.8,
                max_tokens=3000,
            )
            response_text = response.choices[0].message.content
        else:
            raise

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
    return content


def assemble_mythology_video(
    clips: list,
    images: list,
    audio_path: str,
    output_path: str,
    srt_path: str = None,
):
    """
    Ensambla el video final con clips animados (o Ken Burns) + transiciones xfade
    clips: lista de paths a videos HF (puede haber None si fallo HF → usa Ken Burns)
    images: lista de paths a imagenes originales (fallback Ken Burns)
    """
    print("\n[*] Ensamblando video con transiciones xfade...")
    ffmpeg = find_ffmpeg()
    W, H = 1080, 1920
    fps = 24
    transition_dur = 0.5  # segundos de transicion entre clips

    audio_duration = get_audio_duration(audio_path)
    num_clips = len(clips)
    # Duracion por clip incluyendo overlap de transicion
    clip_duration = (audio_duration + transition_dur * (num_clips - 1)) / num_clips
    clip_duration = max(clip_duration, 4.0)

    print(f"[*] Audio: {audio_duration:.1f}s | {num_clips} clips x {clip_duration:.1f}s")

    # Preparar clips individuales (HF o Ken Burns)
    temp_clips = []
    frames_per_clip = int(clip_duration * fps)

    for i, (clip, img) in enumerate(zip(clips, images)):
        clip_out = TEMP_DIR / f"myth_clip_{i:02d}.mp4"

        if clip and Path(clip).exists() and Path(clip).stat().st_size > 10000:
            # Usar clip animado de HF - escalar y recortar al formato correcto
            cmd = [
                ffmpeg, "-y", "-i", clip,
                "-vf", f"scale={W}:{H}:force_original_aspect_ratio=increase,crop={W}:{H},fps={fps},setsar=1",
                "-t", str(clip_duration),
                "-c:v", "libx264", "-preset", "fast", "-pix_fmt", "yuv420p",
                str(clip_out)
            ]
        else:
            # Ken Burns fallback
            zoom_expr = (
                f"z='min(zoom+0.0008,1.2)':d={frames_per_clip}:"
                f"x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)'"
            )
            cmd = [
                ffmpeg, "-y",
                "-loop", "1", "-t", str(clip_duration), "-i", img,
                "-vf", (
                    f"scale={W*2}:{H*2}:force_original_aspect_ratio=increase,"
                    f"crop={W*2}:{H*2}:(ow-iw)/2:(oh-ih)/2,"
                    f"zoompan={zoom_expr}:s={W}x{H}:fps={fps},setsar=1"
                ),
                "-c:v", "libx264", "-preset", "fast", "-pix_fmt", "yuv420p",
                str(clip_out)
            ]

        try:
            subprocess.run(cmd, capture_output=True, check=True)
            temp_clips.append(str(clip_out))
        except subprocess.CalledProcessError as e:
            print(f"[WARN] Clip {i} fallo: {e.stderr.decode()[:200]}")
            # Ultimo fallback: imagen estatica simple
            cmd_simple = [
                ffmpeg, "-y",
                "-loop", "1", "-t", str(clip_duration), "-i", img,
                "-vf", f"scale={W}:{H}:force_original_aspect_ratio=increase,crop={W}:{H},setsar=1",
                "-c:v", "libx264", "-preset", "fast", "-pix_fmt", "yuv420p",
                str(clip_out)
            ]
            try:
                subprocess.run(cmd_simple, capture_output=True, check=True)
                temp_clips.append(str(clip_out))
            except:
                pass

    if not temp_clips:
        print("[ERROR] No se generaron clips")
        return False

    # Unir clips con transicion xfade (crossfade)
    if len(temp_clips) == 1:
        final_video = temp_clips[0]
    else:
        # Construir filtro xfade encadenado
        xfade_filter = ""
        prev = "[0:v]"
        for i in range(1, len(temp_clips)):
            offset = clip_duration * i - transition_dur * i
            out_label = f"[xf{i}]"
            xfade_filter += (
                f"{prev}[{i}:v]xfade=transition=fade:"
                f"duration={transition_dur}:offset={offset:.2f}{out_label};"
            )
            prev = out_label
        xfade_filter = xfade_filter.rstrip(";")
        # Renombrar ultimo output a [vraw]
        xfade_filter = xfade_filter[:xfade_filter.rfind("]")] + "vraw]"

        joined_path = TEMP_DIR / "myth_joined.mp4"
        cmd_join = [ffmpeg, "-y"]
        for tc in temp_clips:
            cmd_join.extend(["-i", tc])
        cmd_join.extend([
            "-filter_complex", xfade_filter,
            "-map", "[vraw]",
            "-c:v", "libx264", "-preset", "medium", "-pix_fmt", "yuv420p",
            str(joined_path)
        ])
        try:
            subprocess.run(cmd_join, capture_output=True, check=True)
            final_video = str(joined_path)
        except subprocess.CalledProcessError as e:
            print(f"[WARN] xfade fallo, concatenando sin transicion: {e.stderr.decode()[:300]}")
            # Fallback: concat simple
            list_file = TEMP_DIR / "clips_list.txt"
            with open(list_file, "w") as f:
                for tc in temp_clips:
                    f.write(f"file '{tc}'\n")
            concat_path = TEMP_DIR / "myth_concat.mp4"
            subprocess.run([
                ffmpeg, "-y", "-f", "concat", "-safe", "0",
                "-i", str(list_file),
                "-c", "copy", str(concat_path)
            ], capture_output=True, check=True)
            final_video = str(concat_path)

    # Anadir audio + subtitulos
    has_srt = srt_path and Path(srt_path).exists() and Path(srt_path).stat().st_size > 10
    srt_escaped = srt_path.replace("\\", "/").replace(":", "\\:") if has_srt else None

    subtitle_style = (
        "FontName=Liberation Sans,FontSize=18,PrimaryColour=&H00FFFFFF,"
        "Bold=1,OutlineColour=&H00000000,Outline=2,Shadow=1,"
        "Alignment=2,MarginL=80,MarginR=80,MarginV=120,WrapStyle=2"
    )

    if has_srt:
        vf_filter = f"subtitles='{srt_escaped}':force_style='{subtitle_style}'"
    else:
        vf_filter = "copy"

    cmd_final = [
        ffmpeg, "-y",
        "-i", final_video,
        "-i", audio_path,
        "-vf", vf_filter,
        "-map", "0:v",
        "-map", "1:a",
        "-c:v", "libx264", "-preset", "medium", "-pix_fmt", "yuv420p",
        "-c:a", "aac", "-b:a", "192k",
        "-shortest",
        output_path
    ]

    try:
        subprocess.run(cmd_final, capture_output=True, check=True)
        print(f"[OK] Video mitologia creado: {output_path}")
        return True
    except subprocess.CalledProcessError as e:
        print(f"[ERROR] FFmpeg final fallo: {e.stderr.decode()[:500]}")
        # Fallback sin subtitulos
        cmd_nosub = [
            ffmpeg, "-y",
            "-i", final_video, "-i", audio_path,
            "-map", "0:v", "-map", "1:a",
            "-c:v", "libx264", "-preset", "medium", "-pix_fmt", "yuv420p",
            "-c:a", "aac", "-b:a", "192k", "-shortest",
            output_path
        ]
        try:
            subprocess.run(cmd_nosub, capture_output=True, check=True)
            print(f"[OK] Video creado (sin subtitulos): {output_path}")
            return True
        except Exception as e2:
            print(f"[ERROR] {e2}")
            return False


def main():
    print("\n" + "=" * 60)
    print("GENERADOR MITOLOGIA GRIEGA - SHORT (Español)")
    print("=" * 60 + "\n")

    # Elegir tema aleatorio
    topic = random.choice(MYTHOLOGY_SHORTS)

    # 1. Generar historia
    content = generate_mythology_story(topic, num_scenes=8)
    if not content:
        return False

    # 2. Generar imagenes cinematograficas
    prompts = [s["prompt_imagen"] for s in content["escenas"]]
    images_dir = TEMP_DIR / "mythology_images"
    images = generate_image_batch(
        prompts, str(images_dir),
        width=1080, height=1920,
        prefix="myth_scene"
    )

    if len(images) < len(prompts) // 2:
        print("[ERROR] Demasiados fallos de imagen")
        return False

    # 3. Animar imagenes con HF SVD
    clips_dir = TEMP_DIR / "mythology_clips"
    clips = animate_batch(images, str(clips_dir), hf_token=HF_TOKEN, prefix="myth_clip")

    # 4. Generar narracion en español
    narracion = ". ".join([s["narracion"] for s in content["escenas"]])
    print(f"\n[*] Narracion ({len(narracion.split())} palabras)")

    # 5. Generar voz en español
    audio_path = str(TEMP_DIR / "mythology_short_audio.mp3")
    srt_path = audio_path.replace(".mp3", ".srt")

    if not generate_speech_with_edge_tts(narracion, audio_path):
        print("[ERROR] Fallo generacion de voz")
        return False

    # 6. Ensamblar video con transiciones
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    video_path = str(OUTPUT_DIR / f"mythology_short_{timestamp}.mp4")

    srt = srt_path if Path(srt_path).exists() else None
    if not assemble_mythology_video(clips, images, audio_path, video_path, srt):
        return False

    # 7. Subir al canal Unveiled
    upload_to_cinematic_channel(
        video_path,
        content["titulo_viral"],
        content.get("descripcion", content["titulo_viral"]),
        content.get("hashtags", "#shorts #mitologia #grecia"),
        content.get("tags_seo", ""),
    )

    print("\n" + "=" * 60)
    print("[OK] MITOLOGIA SHORT COMPLETADO")
    print("=" * 60)
    print(f"\n  Tema: {topic}")
    print(f"  Titulo: {content['titulo_viral']}")
    print(f"  Video: {video_path}\n")
    return True


if __name__ == "__main__":
    main()
