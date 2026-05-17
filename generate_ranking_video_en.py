#!/usr/bin/env python3
"""
ENGLISH ranking video generator
Top 5 (Shorts) or Top 10 (long videos) - uploads to English channel
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
from generate_content_en import generate_speech_english, upload_to_youtube_en
from generate_ranking_video import create_ranking_frames, assemble_ranking_video

OUTPUT_DIR = Path(os.getenv("OUTPUT_DIR", "./videos_output"))
TEMP_DIR = Path(os.getenv("TEMP_DIR", "./temp"))
OUTPUT_DIR.mkdir(exist_ok=True)
TEMP_DIR.mkdir(exist_ok=True)

# Viral ranking topics in English (US market focused)
RANKING_TOPICS_EN = [
    {"topic": "Top {n} AI tools that will make you rich in 2026", "unit": "$/month", "type": "ai"},
    {"topic": "Top {n} cryptocurrencies set to explode in 2026", "unit": "% forecast", "type": "crypto"},
    {"topic": "Top {n} richest people in the world", "unit": "$ billion", "type": "rich"},
    {"topic": "Top {n} ways to make money with AI in 2026", "unit": "$/month potential", "type": "ai"},
    {"topic": "Top {n} millionaire habits that change your life", "unit": "% adoption", "type": "habits"},
    {"topic": "Top {n} most profitable side hustles 2026", "unit": "$/month", "type": "business"},
    {"topic": "Top {n} best performing stocks of 2026", "unit": "% return", "type": "investment"},
    {"topic": "Top {n} best investments for 2026", "unit": "% annual ROI", "type": "investment"},
    {"topic": "Top {n} financial mistakes that ruin your life", "unit": "% affected", "type": "finance"},
    {"topic": "Top {n} books that will change your life in 2026", "unit": "million sold", "type": "education"},
    {"topic": "Top {n} apps that pay you real money in 2026", "unit": "$ avg/month", "type": "apps"},
    {"topic": "Top {n} online businesses with zero investment", "unit": "$/month potential", "type": "business"},
    {"topic": "Top {n} highest paying remote jobs in 2026", "unit": "$ yearly", "type": "jobs"},
    {"topic": "Top {n} countries to retire rich in 2026", "unit": "$ cost/month", "type": "lifestyle"},
]


def generate_ranking_data_en(num_items: int = 5):
    """Generate ranking data in English using AI"""
    template = random.choice(RANKING_TOPICS_EN)
    topic = template["topic"].format(n=num_items)
    unit = template["unit"]
    type_ = template["type"]

    print(f"[*] Generating ranking: {topic}")

    prompt = f"""
    You are an expert in creating viral YouTube ranking videos for US audiences.

    Topic: {topic}
    Type: {type_}
    Measurement unit: {unit}

    Create a TOP {num_items} with REALISTIC data (do not invent crazy numbers).
    Each item must have:
    - "posicion": number (1 = best, {num_items} = last)
    - "nombre": item name (short, max 2-4 words)
    - "valor": number (no symbols, just the number)
    - "descripcion": 5-10 word phrase describing it

    RULES:
    1. Values must have COHERENT progression (highest at #1)
    2. Names must be RECOGNIZABLE (real brands, known concepts)
    3. Descriptions must create CURIOSITY
    4. ALL TEXT IN ENGLISH

    Also generate:
    - "titulo_viral": video title (max 60 chars, strong hook, ENGLISH)
    - "intro": opening hook phrase 10-15 words (ENGLISH)
    - "outro": closing CTA with subscribe call 10-15 words (ENGLISH)

    Respond ONLY in JSON, no extra text:
    {{
        "titulo_viral": "...",
        "intro": "Powerful hook to start the video",
        "items": [
            {{"posicion": {num_items}, "nombre": "Last item", "valor": 1000, "descripcion": "..."}},
            {{"posicion": {num_items-1}, "nombre": "...", "valor": 2000, "descripcion": "..."}},
            ...
            {{"posicion": 1, "nombre": "The best", "valor": 10000, "descripcion": "..."}}
        ],
        "outro": "Final CTA with subscribe call",
        "hashtags": "#shorts #top #ranking #ai #money #viral",
        "tags_seo": "top 10, ranking, viral, money, ai, 2026, best, comparison, list",
        "descripcion": "SEO description with keywords and CTA"
    }}
    """

    response_text = None
    try:
        print("[*] Trying Gemini...")
        gemini_client = _get_gemini_client()
        response = gemini_client.models.generate_content(
            model="gemini-2.0-flash",
            contents=prompt
        )
        response_text = response.text
    except Exception as e:
        if "429" in str(e) or "RESOURCE_EXHAUSTED" in str(e) or "quota" in str(e).lower():
            print(f"[WARN] Gemini quota exceeded, falling back to Groq...")
            groq_client = _get_groq_client()
            response = groq_client.chat.completions.create(
                model="llama-3.1-8b-instant",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.7,
                max_tokens=2000,
            )
            response_text = response.choices[0].message.content
        else:
            raise

    try:
        json_match = re.search(r'\{.*\}', response_text, re.DOTALL)
        content = json.loads(json_match.group())
    except:
        content = None

    if not content or "items" not in content:
        raise Exception("Could not generate ranking")

    content["unidad"] = unit
    content["tipo"] = type_
    return content


def create_ranking_narration_en(content: dict) -> str:
    """Build English narration text from ranking data"""
    parts = [content["intro"]]

    items = sorted(content["items"], key=lambda x: x["posicion"], reverse=True)
    for item in items:
        pos = item["posicion"]
        valor_fmt = f"{item['valor']:,}"
        unit = content.get("unidad", "")
        if pos == 1:
            text = f"And number one is: {item['nombre']}. With {valor_fmt} {unit}. {item['descripcion']}"
        else:
            text = f"At number {pos}: {item['nombre']}. {valor_fmt} {unit}. {item['descripcion']}"
        parts.append(text)

    parts.append(content["outro"])
    return ". ".join(parts)


def main():
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--long", action="store_true", help="Long video (Top 10) instead of Short")
    args = parser.parse_args()

    is_long = args.long
    num_items = 10 if is_long else 5
    vertical = not is_long

    print("\n" + "="*60)
    print(f"RANKING GENERATOR EN - {'LONG VIDEO (Top 10)' if is_long else 'SHORT (Top 5)'}")
    print("="*60 + "\n")

    # 1. Generate ranking content
    content = generate_ranking_data_en(num_items=num_items)
    print(f"\n[*] Title: {content['titulo_viral']}")
    print(f"[*] Items: {len(content['items'])}\n")

    # 2. Create frames (reuse from Spanish version - visuals are language-agnostic)
    frames = create_ranking_frames(content, vertical=vertical)
    if not frames:
        print("[ERROR] No frames generated")
        return False

    # 3. Create English narration
    narration = create_ranking_narration_en(content)
    print(f"\n[*] Narration: {len(narration.split())} words")

    # 4. Generate English voice
    audio_path = TEMP_DIR / ("ranking_long_en.mp3" if is_long else "ranking_short_en.mp3")
    if not generate_speech_english(narration, str(audio_path)):
        print("[ERROR] Could not generate English voice")
        return False

    # 5. Assemble video
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    prefix = "ranking_long_en" if is_long else "ranking_short_en"
    video_path = OUTPUT_DIR / f"{prefix}_{timestamp}.mp4"

    if not assemble_ranking_video(frames, str(audio_path), str(video_path), vertical=vertical):
        print("[ERROR] Could not assemble video")
        return False

    # 6. Upload to YouTube (English channel)
    upload_to_youtube_en(
        str(video_path),
        content['titulo_viral'],
        content.get('descripcion', content['titulo_viral']),
        content.get('hashtags', '#shorts #ranking #top'),
        content.get('tags_seo', '')
    )

    print("\n" + "="*60)
    print("[OK] ENGLISH RANKING COMPLETED")
    print("="*60)
    print(f"\n  Type: {'Long video' if is_long else 'Short'}")
    print(f"  Video: {video_path}")
    print(f"  Title: {content['titulo_viral']}\n")

    return True


if __name__ == "__main__":
    main()
