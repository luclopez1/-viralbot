#!/usr/bin/env python3
"""
CINEMATIC LONG VIDEO GENERATOR (English)
Generates 5-10 min cinematic documentary-style videos
Uses Pollinations.ai for images + Ken Burns for movement
Uploads to dedicated cinematic YouTube channel
"""

import os
import json
import re
import random
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
from generate_cinematic_short import (
    assemble_cinematic_video,
    upload_to_cinematic_channel,
)

OUTPUT_DIR = Path(os.getenv("OUTPUT_DIR", "./videos_output"))
TEMP_DIR = Path(os.getenv("TEMP_DIR", "./temp"))
OUTPUT_DIR.mkdir(exist_ok=True)
TEMP_DIR.mkdir(exist_ok=True)


# Long video documentary formats (5-10 minutes)
LONG_CINEMATIC_FORMATS = [
    {
        "format": "deep_dive_mystery",
        "topics": [
            "the unsolved mystery of the Voynich Manuscript",
            "what really lies beneath Antarctica",
            "the hidden truth about ancient pyramids worldwide",
            "the lost city of Atlantis - new evidence",
            "the dark side of the Moon revealed",
            "the abandoned Soviet space program",
        ],
    },
    {
        "format": "future_prediction",
        "topics": [
            "the world in 2050 if AI keeps evolving this fast",
            "what humans will look like in 1 million years",
            "Earth after climate change reaches critical point",
            "first human colony on Mars - the real story",
            "what happens when quantum computers break encryption",
            "the day AI becomes smarter than all humans combined",
        ],
    },
    {
        "format": "historical_what_if",
        "topics": [
            "what if the Roman Empire never fell",
            "what if Nikola Tesla won the war of currents",
            "what if dinosaurs never went extinct",
            "what if Columbus never sailed to America",
            "what if the Library of Alexandria survived",
            "what if Einstein never existed",
        ],
    },
    {
        "format": "extreme_survival",
        "topics": [
            "100 days lost in the Amazon rainforest",
            "the man who survived 76 days in the Atlantic Ocean",
            "stranded in Antarctica for an entire winter",
            "trapped 700 meters underground for 69 days",
            "surviving a plane crash in the Andes mountains",
            "the impossible escape from a Soviet gulag",
        ],
    },
    {
        "format": "scientific_explained",
        "topics": [
            "what's actually inside a black hole",
            "the true scale of the universe explained",
            "how time works at the speed of light",
            "the multiverse theory - is it real",
            "the deepest mysteries of human consciousness",
            "what happens during the moment of death",
        ],
    },
]


def generate_long_cinematic_story(num_scenes: int = 25):
    """Generate long cinematic documentary story"""
    fmt = random.choice(LONG_CINEMATIC_FORMATS)
    topic = random.choice(fmt["topics"])

    print(f"[*] Format: {fmt['format']}")
    print(f"[*] Topic: {topic}")

    prompt = f"""
    You are a master documentary script writer for YouTube cinematic channels with millions of views.

    TOPIC: {topic}
    FORMAT: {fmt['format']}

    Create a 5-7 minute cinematic documentary script with EXACTLY {num_scenes} scenes.

    STRUCTURE (must follow):
    - SCENES 1-3: HOOK (immediate intrigue, mystery, big question)
    - SCENES 4-10: SETUP (background, context, characters/elements)
    - SCENES 11-18: REVELATION (discoveries, twists, evidence)
    - SCENES 19-22: CLIMAX (most dramatic moment)
    - SCENES 23-{num_scenes}: CONCLUSION (resolution + cliffhanger for next video)

    RULES:
    1. Each scene must have a DRAMATIC, hyperrealistic cinematic image prompt (English, very detailed)
    2. Each scene must have 2-4 sentences of NARRATION (25-50 words)
    3. Build TENSION progressively - never let viewer lose interest
    4. Use cinematic vocabulary: "imagine if...", "what scientists discovered...", "the truth was..."
    5. Image prompts must be MOVIE-QUALITY, dramatic lighting, professional composition

    For image prompts include:
    - Specific location/setting (detailed)
    - Subject with action (not static)
    - Lighting: dramatic, cinematic, golden hour, blue hour, dark mysterious
    - Mood: tense, hopeful, eerie, awe-inspiring
    - Camera technique: low angle, extreme wide, intimate close-up, aerial view
    - Style: hyperrealistic, photorealistic, cinematic film still

    Respond ONLY in JSON, no extra text:
    {{
        "viral_title": "max 70 chars, intriguing hook title",
        "scenes": [
            {{
                "narration": "2-4 sentences (25-50 words) of dramatic narration",
                "image_prompt": "Highly detailed cinematic English prompt"
            }},
            ... ({num_scenes} scenes total)
        ],
        "hashtags": "#documentary #cinematic #mystery #ai #story",
        "tags_seo": "comma separated SEO tags for long-form video",
        "description": "Full SEO description with chapters/timestamps and CTA"
    }}
    """

    response_text = None
    try:
        print("[*] Generating long story with Gemini...")
        gemini_client = _get_gemini_client()
        response = gemini_client.models.generate_content(
            model="gemini-2.0-flash",
            contents=prompt
        )
        response_text = response.text
    except Exception as e:
        if "429" in str(e) or "RESOURCE_EXHAUSTED" in str(e) or "quota" in str(e).lower():
            print("[WARN] Gemini quota exceeded, using Groq with short prompt...")
            # Prompt corto especifico para Groq (max 4000 tokens)
            prompt_groq = f"""Create a cinematic documentary about: {topic}

Generate exactly 10 scenes. For each scene provide:
- narration: 2-3 dramatic sentences (30-40 words)
- image_prompt: detailed cinematic description for AI image generation

Respond ONLY in JSON:
{{
    "viral_title": "compelling title under 70 chars",
    "scenes": [
        {{"narration": "...", "image_prompt": "cinematic detailed prompt..."}},
        {{"narration": "...", "image_prompt": "cinematic detailed prompt..."}},
        {{"narration": "...", "image_prompt": "cinematic detailed prompt..."}},
        {{"narration": "...", "image_prompt": "cinematic detailed prompt..."}},
        {{"narration": "...", "image_prompt": "cinematic detailed prompt..."}},
        {{"narration": "...", "image_prompt": "cinematic detailed prompt..."}},
        {{"narration": "...", "image_prompt": "cinematic detailed prompt..."}},
        {{"narration": "...", "image_prompt": "cinematic detailed prompt..."}},
        {{"narration": "...", "image_prompt": "cinematic detailed prompt..."}},
        {{"narration": "...", "image_prompt": "cinematic detailed prompt..."}}
    ],
    "hashtags": "#documentary #cinematic #history #mystery",
    "tags_seo": "documentary, cinematic, history, mystery, ai",
    "description": "SEO description with CTA"
}}"""
            groq_client = _get_groq_client()
            for groq_model in ["llama-3.3-70b-versatile", "llama-3.1-8b-instant"]:
                try:
                    print(f"[*] Trying Groq model: {groq_model}...")
                    response = groq_client.chat.completions.create(
                        model=groq_model,
                        messages=[{"role": "user", "content": prompt_groq}],
                        temperature=0.8,
                        max_tokens=4000,
                    )
                    response_text = response.choices[0].message.content
                    print(f"[OK] Groq responded with {groq_model}")
                    break
                except Exception as groq_err:
                    print(f"[WARN] {groq_model} failed: {groq_err}")
                    continue
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

    print(f"[OK] Long story generated: {len(content['scenes'])} scenes")
    print(f"[*] Title: {content['viral_title']}")
    return content


def main():
    print("\n" + "=" * 60)
    print("CINEMATIC LONG VIDEO GENERATOR (English)")
    print("=" * 60 + "\n")

    # 1. Generate long story (25 scenes for 5-7 min video)
    content = generate_long_cinematic_story(num_scenes=25)
    if not content:
        return False

    # 2. Generate cinematic images (horizontal 1920x1080)
    prompts = [s["image_prompt"] for s in content["scenes"]]
    images_dir = TEMP_DIR / "cinematic_long_images"
    images = generate_image_batch(
        prompts, str(images_dir),
        width=1920, height=1080,
        prefix="long_scene"
    )

    if len(images) < len(prompts) // 2:
        print("[ERROR] Too many image failures")
        return False

    # 3. Build narration
    narration = " ".join([s["narration"] for s in content["scenes"]])
    print(f"\n[*] Narration ({len(narration.split())} words)")

    # 4. Generate English voice
    audio_path = TEMP_DIR / "cinematic_long_audio.mp3"
    if not generate_speech_english(narration, str(audio_path)):
        print("[ERROR] Voice generation failed")
        return False

    # 5. Assemble video with Ken Burns (HORIZONTAL)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    video_path = OUTPUT_DIR / f"cinematic_long_{timestamp}.mp4"
    if not assemble_cinematic_video(images, str(audio_path), str(video_path), vertical=False):
        return False

    # 6. Upload to cinematic channel
    upload_to_cinematic_channel(
        str(video_path),
        content["viral_title"],
        content.get("description", content["viral_title"]),
        content.get("hashtags", "#documentary #cinematic"),
        content.get("tags_seo", ""),
    )

    print("\n" + "=" * 60)
    print("[OK] CINEMATIC LONG VIDEO COMPLETED")
    print("=" * 60)
    return True


if __name__ == "__main__":
    main()
