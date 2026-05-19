#!/usr/bin/env python3
"""
CINEMATIC SHORT GENERATOR (English)
Generates viral cinematic Shorts with Pollinations.ai images + Ken Burns
Uploads to dedicated cinematic YouTube channel
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
    _orig_httplib2_init = httplib2.Http.__init__
    def _patched_httplib2_init(self, *args, **kwargs):
        kwargs['disable_ssl_certificate_validation'] = True
        _orig_httplib2_init(self, *args, **kwargs)
    httplib2.Http.__init__ = _patched_httplib2_init
except ImportError:
    pass

load_dotenv()

sys.path.insert(0, str(Path(__file__).parent))
from generate_content import _get_gemini_client, _get_groq_client
from generate_content_en import generate_speech_english
from pollinations_helper import generate_image_batch

OUTPUT_DIR = Path(os.getenv("OUTPUT_DIR", "./videos_output"))
TEMP_DIR = Path(os.getenv("TEMP_DIR", "./temp"))
OUTPUT_DIR.mkdir(exist_ok=True)
TEMP_DIR.mkdir(exist_ok=True)


# Viral cinematic Short formats (proven to work)
CINEMATIC_FORMATS = [
    {
        "format": "progression",
        "topic_template": "What happens to your body if you {action} every day",
        "actions": [
            "do extreme exercise", "eat only sugar", "skip sleep",
            "drink only coffee", "stay in zero gravity", "drink only water",
            "eat only protein", "meditate for hours", "swim in icy water",
        ],
        "structure": "Hour 1, Day 3, Week 1, Month 1, Month 2 progression"
    },
    {
        "format": "what_if",
        "topic_template": "What if {scenario}",
        "actions": [
            "you fell into a black hole", "humans lived on Mars",
            "the dinosaurs never went extinct", "you could see through time",
            "AI took over in 2030", "you found alien technology",
            "you woke up in the year 3000", "gravity stopped tomorrow",
        ],
        "structure": "Initial event, immediate consequences, escalation, climax"
    },
    {
        "format": "survival",
        "topic_template": "Surviving {situation} alone",
        "actions": [
            "the Mariana Trench", "Antarctica for 30 days",
            "the Amazon jungle", "a deserted island",
            "Mount Everest", "the Sahara desert",
            "an abandoned space station", "the deep ocean",
        ],
        "structure": "Setup, struggle, discovery, climax"
    },
    {
        "format": "mystery",
        "topic_template": "The dark secret of {subject}",
        "actions": [
            "the Bermuda Triangle", "Area 51",
            "the bottom of the ocean", "ancient Egyptian tombs",
            "the dark side of the Moon", "lost civilizations",
            "unexplored caves", "abandoned cities",
        ],
        "structure": "Hook, mystery setup, revelation, twist"
    },
]


def generate_cinematic_story(num_scenes: int = 8):
    """Generate viral cinematic story with image prompts and narration"""
    fmt = random.choice(CINEMATIC_FORMATS)
    action = random.choice(fmt["actions"])
    topic = fmt["topic_template"].format(action=action, scenario=action, situation=action, subject=action)

    print(f"[*] Format: {fmt['format']}")
    print(f"[*] Topic: {topic}")

    prompt = f"""
    You are an expert viral YouTube Shorts script writer with millions of views.

    TOPIC: {topic}
    FORMAT: {fmt['format']}
    STRUCTURE: {fmt['structure']}

    Create a 60-90 second cinematic Short with EXACTLY {num_scenes} scenes.

    RULES:
    1. Each scene must have a DRAMATIC, cinematic image prompt (in English, very detailed)
    2. Each scene must have 2-3 sentences of narration (20-30 words minimum per scene)
    3. Total narration across ALL scenes must be AT LEAST 150 words (target 60-90 seconds audio)
    4. The narration must build TENSION and CURIOSITY progressively
    5. Image prompts must be HYPERREALISTIC, CINEMATIC, dramatic lighting
    6. Use consistent character/setting across scenes
    7. END with a question or cliffhanger to drive comments and subscriptions

    For image prompts, describe in detail:
    - The scene (location, atmosphere)
    - The subject (person, object, creature)
    - Lighting (dramatic, golden hour, blue hour, neon)
    - Mood (mysterious, intense, eerie, hopeful)
    - Camera angle (low angle, close-up, wide shot)

    Respond ONLY in JSON, no extra text:
    {{
        "viral_title": "max 60 chars, strong hook",
        "scenes": [
            {{
                "narration": "Short line, max 15 words",
                "image_prompt": "Detailed cinematic English prompt for AI image generation"
            }},
            ... ({num_scenes} scenes total)
        ],
        "hashtags": "#shorts #viral #ai #cinematic #story",
        "tags_seo": "comma separated SEO tags",
        "description": "SEO description with keywords and CTA"
    }}
    """

    response_text = None
    try:
        print("[*] Generating story with Gemini...")
        gemini_client = _get_gemini_client()
        response = gemini_client.models.generate_content(
            model="gemini-2.0-flash",
            contents=prompt
        )
        response_text = response.text
    except Exception as e:
        if "429" in str(e) or "RESOURCE_EXHAUSTED" in str(e) or "quota" in str(e).lower():
            print("[WARN] Gemini quota exceeded, using Groq...")
            groq_client = _get_groq_client()
            response = groq_client.chat.completions.create(
                model="llama-3.1-8b-instant",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.8,
                max_tokens=3000,
            )
            response_text = response.choices[0].message.content
        else:
            raise

    try:
        json_match = re.search(r'\{.*\}', response_text, re.DOTALL)
        content = json.loads(json_match.group())
    except Exception as e:
        print(f"[ERROR] Could not parse JSON: {e}")
        return None

    if not content or "scenes" not in content:
        print("[ERROR] No scenes generated")
        return None

    print(f"[OK] Story generated: {len(content['scenes'])} scenes")
    print(f"[*] Title: {content['viral_title']}")
    return content


def find_ffmpeg():
    """Find FFmpeg binary"""
    candidates = [
        r"C:\ffmpeg\ffmpeg-8.1.1-essentials_build\bin\ffmpeg.exe",
        r"C:\ffmpeg\bin\ffmpeg.exe",
        "ffmpeg",
    ]
    for c in candidates:
        if c == "ffmpeg" or os.path.exists(c):
            return c
    return "ffmpeg"


def get_audio_duration(audio_path: str) -> float:
    """Get audio duration in seconds"""
    ffmpeg = find_ffmpeg()
    ffprobe = ffmpeg.replace("ffmpeg", "ffprobe")
    try:
        result = subprocess.run(
            [ffprobe, "-v", "quiet", "-of", "csv=p=0",
             "-show_entries", "format=duration", audio_path],
            capture_output=True, text=True, check=True
        )
        return float(result.stdout.strip())
    except Exception:
        return 60.0


def assemble_cinematic_video(images: list, audio_path: str, output_path: str, vertical: bool = True):
    """Assemble cinematic video with Ken Burns effect + burned subtitles"""
    print("\n[*] Assembling cinematic video with Ken Burns + subtitles...")

    if not images:
        print("[ERROR] No images to assemble")
        return False

    ffmpeg = find_ffmpeg()
    W, H = (1080, 1920) if vertical else (1920, 1080)
    fps = 30

    audio_duration = get_audio_duration(audio_path)
    duration_per_image = audio_duration / len(images)
    frames_per_image = int(duration_per_image * fps)

    print(f"[*] Audio duration: {audio_duration:.1f}s")
    print(f"[*] {len(images)} images x {duration_per_image:.1f}s each")

    # Check for SRT subtitle file (generated by Edge TTS)
    srt_path = audio_path.replace(".mp3", ".srt")
    has_subtitles = os.path.exists(srt_path) and os.path.getsize(srt_path) > 10
    if has_subtitles:
        print(f"[*] Subtitles found: {srt_path}")
        # Escape path for FFmpeg filter (Windows backslashes)
        srt_escaped = srt_path.replace("\\", "/").replace(":", "\\:")
    else:
        print("[WARN] No subtitles file found, skipping")

    # Font size and margins based on orientation
    # Vertical (Shorts 1080x1920): menos espacio horizontal → fuente pequeña + márgenes
    # Horizontal (Long 1920x1080): mucho espacio horizontal → fuente grande sin márgenes
    if vertical:
        font_size = 36
        margin_l, margin_r, margin_v = 60, 60, 100
    else:
        font_size = 52
        margin_l, margin_r, margin_v = 80, 80, 60

    # Build FFmpeg command with Ken Burns zoompan
    cmd = [ffmpeg, "-y"]
    for img in images:
        cmd.extend(["-loop", "1", "-t", str(duration_per_image), "-i", img])
    cmd.extend(["-i", audio_path])

    filter_parts = []
    concat_parts = []
    for i in range(len(images)):
        # Alternate zoom in / zoom out for variety
        if i % 2 == 0:
            zoom_expr = (
                f"z='min(zoom+0.0008,1.2)':d={frames_per_image}:"
                f"x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)'"
            )
        else:
            zoom_expr = (
                f"z='if(lte(zoom,1.0),1.2,max(1.0,zoom-0.0008))':d={frames_per_image}:"
                f"x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)'"
            )

        # Scale to double size for quality, crop centered, apply Ken Burns
        filter_parts.append(
            f"[{i}:v]"
            f"scale={W*2}:{H*2}:force_original_aspect_ratio=increase,"
            f"crop={W*2}:{H*2}:(ow-iw)/2:(oh-ih)/2,"
            f"zoompan={zoom_expr}:s={W}x{H}:fps={fps},"
            f"setsar=1[v{i}]"
        )
        concat_parts.append(f"[v{i}]")

    # Concatenate all clips
    filter_complex = (
        ";".join(filter_parts) + ";" +
        "".join(concat_parts) +
        f"concat=n={len(images)}:v=1:a=0[vraw]"
    )

    # Add subtitles on top of concatenated video
    if has_subtitles:
        subtitle_style = (
            f"FontName=Liberation Sans,"
            f"FontSize={font_size},"
            f"PrimaryColour=&H00FFFFFF,"
            f"Bold=1,"
            f"OutlineColour=&H00000000,"
            f"Outline=3,"
            f"Shadow=2,"
            f"Alignment=2,"
            f"MarginL={margin_l},"
            f"MarginR={margin_r},"
            f"MarginV={margin_v},"
            f"WrapStyle=0"
        )
        filter_complex += f";[vraw]subtitles='{srt_escaped}':force_style='{subtitle_style}'[v]"
    else:
        filter_complex += ";[vraw]copy[v]"

    cmd.extend([
        "-filter_complex", filter_complex,
        "-map", "[v]",
        "-map", f"{len(images)}:a",
        "-c:v", "libx264",
        "-preset", "medium",
        "-pix_fmt", "yuv420p",
        "-c:a", "aac",
        "-b:a", "192k",
        "-shortest",
        output_path
    ])

    try:
        print("[*] Running FFmpeg with subtitles (2-3 minutes)...")
        result = subprocess.run(cmd, capture_output=True, check=True)
        print(f"[OK] Video assembled with subtitles: {output_path}")
        return True
    except subprocess.CalledProcessError as e:
        print(f"[ERROR] FFmpeg failed, retrying without subtitles...")
        # Retry without subtitles
        filter_simple = (
            ";".join(filter_parts) + ";" +
            "".join(concat_parts) +
            f"concat=n={len(images)}:v=1:a=0[v]"
        )
        cmd_simple = [ffmpeg, "-y"]
        for img in images:
            cmd_simple.extend(["-loop", "1", "-t", str(duration_per_image), "-i", img])
        cmd_simple.extend(["-i", audio_path])
        cmd_simple.extend([
            "-filter_complex", filter_simple,
            "-map", "[v]",
            "-map", f"{len(images)}:a",
            "-c:v", "libx264",
            "-preset", "medium",
            "-pix_fmt", "yuv420p",
            "-c:a", "aac",
            "-b:a", "192k",
            "-shortest",
            output_path
        ])
        try:
            subprocess.run(cmd_simple, capture_output=True, check=True)
            print(f"[OK] Video assembled (no subtitles): {output_path}")
            return True
        except subprocess.CalledProcessError as e2:
            print(f"[ERROR] FFmpeg failed: {e2.stderr.decode()[:1000]}")
            return False


def upload_to_cinematic_channel(video_path: str, title: str, description: str, tags: str, seo_tags: str = ""):
    """Upload to dedicated CINEMATIC YouTube channel"""
    from google.oauth2.credentials import Credentials
    from google.auth.transport.requests import Request
    from googleapiclient.discovery import build
    from googleapiclient.http import MediaFileUpload

    print(f"\n[*] Uploading to YouTube (CINEMATIC channel)...")
    print(f"   Title: {title}")

    TOKEN_FILE = 'youtube_token_cinematic.json'
    SCOPES = ['https://www.googleapis.com/auth/youtube.upload']

    try:
        # GitHub Actions: token from env var
        token_env = os.getenv("YOUTUBE_TOKEN_CINEMATIC")
        if token_env and not os.path.exists(TOKEN_FILE):
            raw = token_env.strip().strip("'\"")
            with open(TOKEN_FILE, 'w') as f:
                f.write(raw)

        creds = Credentials.from_authorized_user_file(TOKEN_FILE, SCOPES)

        if creds.expired and creds.refresh_token:
            print("[*] Refreshing token...")
            creds.refresh(Request())
            with open(TOKEN_FILE, 'w') as f:
                f.write(creds.to_json())

        youtube = build('youtube', 'v3', credentials=creds)

        # Prepare tags
        tag_list = [t.strip() for t in (tags + ',' + seo_tags).split(',') if t.strip()]
        tag_list = [t.replace('#', '') for t in tag_list][:25]

        body = {
            'snippet': {
                'title': title[:100],
                'description': description[:5000],
                'tags': tag_list,
                'categoryId': '24',  # Entertainment
            },
            'status': {
                'privacyStatus': 'public',
                'selfDeclaredMadeForKids': False,
            }
        }

        media = MediaFileUpload(video_path, chunksize=-1, resumable=True)
        request = youtube.videos().insert(
            part='snippet,status',
            body=body,
            media_body=media
        )

        response = request.execute()
        video_id = response['id']
        print(f"[OK] Uploaded! https://youtube.com/watch?v={video_id}")
        return video_id

    except Exception as e:
        print(f"[ERROR] Upload failed: {e}")
        return None


def main():
    print("\n" + "=" * 60)
    print("CINEMATIC SHORT GENERATOR (English)")
    print("=" * 60 + "\n")

    # 1. Generate story
    content = generate_cinematic_story(num_scenes=8)
    if not content:
        return False

    # 2. Generate cinematic images
    prompts = [s["image_prompt"] for s in content["scenes"]]
    images_dir = TEMP_DIR / "cinematic_images"
    images = generate_image_batch(prompts, str(images_dir), width=1080, height=1920, prefix="scene")

    if len(images) < len(prompts) // 2:
        print("[ERROR] Too many image failures")
        return False

    # 3. Build narration
    narration = ". ".join([s["narration"] for s in content["scenes"]])
    print(f"\n[*] Narration ({len(narration.split())} words):")
    print(f"    {narration[:200]}...")

    # 4. Generate English voice
    audio_path = TEMP_DIR / "cinematic_short_audio.mp3"
    if not generate_speech_english(narration, str(audio_path)):
        print("[ERROR] Voice generation failed")
        return False

    # 5. Assemble video with Ken Burns
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    video_path = OUTPUT_DIR / f"cinematic_short_{timestamp}.mp4"
    if not assemble_cinematic_video(images, str(audio_path), str(video_path), vertical=True):
        return False

    # 6. Upload to cinematic channel
    upload_to_cinematic_channel(
        str(video_path),
        content["viral_title"],
        content.get("description", content["viral_title"]),
        content.get("hashtags", "#shorts #cinematic #ai"),
        content.get("tags_seo", ""),
    )

    print("\n" + "=" * 60)
    print("[OK] CINEMATIC SHORT COMPLETED")
    print("=" * 60)
    return True


if __name__ == "__main__":
    main()
