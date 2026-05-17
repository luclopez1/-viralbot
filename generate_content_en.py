#!/usr/bin/env python3
"""
ENGLISH version - YouTube Shorts automation system
Generates viral content in English for international audience
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

# Importar funciones compartidas
sys.path.insert(0, str(Path(__file__).parent))
from generate_content import (
    _get_gemini_client,
    _get_groq_client,
    download_images_from_pexels,
    create_video_with_ffmpeg,
)

# Configuración EN
YOUTUBE_API_KEY = os.getenv("YOUTUBE_API_KEY")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
PEXELS_API_KEY = os.getenv("PEXELS_API_KEY")
OUTPUT_DIR = Path(os.getenv("OUTPUT_DIR", "./videos_output"))
TEMP_DIR = Path(os.getenv("TEMP_DIR", "./temp"))
VIDEO_DURATION = int(os.getenv("VIDEO_DURATION_SECONDS", 58))

OUTPUT_DIR.mkdir(exist_ok=True)
TEMP_DIR.mkdir(exist_ok=True)


NICHES_EN = [
    "make money with AI 2026",
    "crypto bitcoin ethereum 2026",
    "personal finance investing 2026",
    "millionaire habits mindset success 2026",
    "psychology manipulation body language",
    "productivity remote work side hustle 2026",
]

FALLBACK_TOPICS_EN = [
    # AI
    {"title": "How to Make Money with AI in 2026", "niche": "AI"},
    {"title": "This AI Makes Me $1000 a Day", "niche": "AI"},
    {"title": "Top AI Tools to Make Money Online", "niche": "AI"},
    # Crypto
    {"title": "Will Bitcoin Go Up or Down in 2026?", "niche": "Crypto"},
    {"title": "Ethereum Will Beat Bitcoin This Year", "niche": "Crypto"},
    {"title": "Altcoins That Will Explode in 2026", "niche": "Crypto"},
    # Finance
    {"title": "3 Investments That Will Make You Rich", "niche": "Finance"},
    {"title": "How to Invest $100 and Multiply It", "niche": "Finance"},
    {"title": "Financial Mistake 90% of People Make", "niche": "Finance"},
    # Mindset
    {"title": "5 Habits All Millionaires Have", "niche": "Mindset"},
    {"title": "How Rich People Think vs Poor People", "niche": "Mindset"},
    {"title": "Why 99% Will Never Be Rich", "niche": "Mindset"},
    # Psychology
    {"title": "3 Signs Someone Is Lying to You", "niche": "Psychology"},
    {"title": "How to Spot Manipulators in 30 Seconds", "niche": "Psychology"},
    {"title": "Psychology Tricks to Make Everyone Like You", "niche": "Psychology"},
    # Productivity
    {"title": "Morning Routine of Millionaire CEOs", "niche": "Productivity"},
    {"title": "3 Side Hustles That Pay More Than Your Job", "niche": "Productivity"},
    {"title": "Remote Jobs That Pay $5000 a Month", "niche": "Productivity"},
]


def get_trending_topics_en():
    """Get trending YouTube topics in English"""
    import random

    print("[*] Looking for trending topics on YouTube (EN)...")
    niche_query = random.choice(NICHES_EN)
    print(f"[*] Selected niche: {niche_query}")

    try:
        url = "https://www.googleapis.com/youtube/v3/search"
        params = {
            "part": "snippet",
            "type": "video",
            "maxResults": 10,
            "order": "viewCount",
            "q": niche_query,
            "regionCode": "US",
            "relevanceLanguage": "en",
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
            topics.append({
                "title": title,
                "description": item["snippet"]["description"][:200],
            })

        if topics:
            return topics[:3]
        raise Exception("No results")
    except Exception as e:
        print(f"[WARN] YouTube API error: {e}")
        return [random.choice(FALLBACK_TOPICS_EN)]


def generate_script_en(topic: str):
    """Generate viral English script using Gemini (fallback Groq)"""
    print(f"[*] Generating English script for: {topic}")

    prompt = f"""
    You are the best viral YouTube Shorts creator in the world. Your videos have +10M views.
    Your goal: maximum retention and subscribers.

    Topic: {topic}

    CRITICAL VIRAL RULES:

    TITLE (most important - decides clicks):
    - Max 60 characters
    - Use ONE of these PROVEN VIRAL FORMULAS (with millions of views):

      FORMULA 1 - Personal storytelling (1M+ views):
        * "ChatGPT Made Me Rich: My AI Trading Story"
        * "How I Made $5000 with This AI in 30 Days"

      FORMULA 2 - Negation + Alternative (600K+ views):
        * "DON'T Invest in Bitcoin in 2026 (Do THIS Instead)"
        * "DON'T Use This AI (Use This One Instead)"

      FORMULA 3 - Shock statistic (3M+ views):
        * "Why 95% of People Lose Money with AI"
        * "Why 99% Will Never Be Rich"

      FORMULA 4 - FREE (1.8M+ views):
        * "5 Free AI Tools That Change Everything"
        * "How to Make Money FREE with AI"

      FORMULA 5 - Authority + Drama (550K+ views):
        * "YouTube Just KILLED AI Channels"
        * "Google Just Changed EVERYTHING with This AI"

      FORMULA 6 - Warning (high retention):
        * "Beware of This AI SCAM"
        * "DON'T Buy This Crypto: It's a Scam"

    - Use hook words: SECRET, NOBODY, ERROR, TRICK, NEVER, ALWAYS, FAST, FREE, SCAM, BEWARE, KILLED, DESTROYED

    HOOK (first 2 seconds - critical):
    - "STOP scrolling and watch this..."
    - "If you don't do this, you'll lose money..."
    - "This will change your life in 60 seconds"
    - "99% of people don't know this..."

    SCRIPT:
    - Max 100 words total
    - SHORT punchy sentences (3-7 words each)
    - Tone: urgent, energetic, direct, authoritative
    - Build TENSION: problem → solution
    - No emojis

    MANDATORY CTA AT END (last sentence - critical for subscribers):
    The script MUST ALWAYS end with a clear subscribe CTA.
    Rotate between:
    - "Subscribe for more tips like this"
    - "Follow me for more secrets"
    - "Hit subscribe and turn on notifications"
    - "Like and subscribe for more content like this"
    - "Subscribe to learn more about [topic]"

    YOUTUBE SEO:

    HASHTAGS (5-7 max):
    - ALWAYS include: #shorts
    - Mix broad (#money #ai) + specific (#crypto2026 #aitools)

    SEO TAGS (15-20 tags):
    - 5 main keyword variations: "make money with ai", "ai to make money", "how to make money ai"
    - 5 secondary: "ai 2026", "ai tools", "ai free"
    - 5 long-tail: "how to make 1000 dollars with ai", "best ai for making money 2026"
    - 5 broad: "shorts", "youtube shorts", "viral", "tutorial", "english"

    Respond ONLY in JSON, no extra text:
    {{
        "titulo": "VIRAL TITLE with proven hook (max 60 chars with KEYWORD)",
        "guion": "POWERFUL HOOK in 2 seconds. Tension-building development. Strong final CTA.",
        "hashtags": "#shorts #money #ai #investing #finance #crypto",
        "tags_seo": "tag1, tag2, tag3, tag4, tag5, tag6, tag7, tag8, tag9, tag10, tag11, tag12, tag13, tag14, tag15",
        "descripcion": "Line 1 with title+keyword. Line 2-3 summary with natural keywords. Subscribe CTA. Hashtags at end."
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
        error_msg = str(e)
        if "429" in error_msg or "RESOURCE_EXHAUSTED" in error_msg or "quota" in error_msg.lower():
            print(f"[WARN] Gemini out of quota, using Groq as fallback...")
            try:
                groq_client = _get_groq_client()
                response = groq_client.chat.completions.create(
                    model="llama-3.1-8b-instant",
                    messages=[{"role": "user", "content": prompt}],
                    temperature=0.7,
                    max_tokens=2000,
                )
                response_text = response.choices[0].message.content
            except Exception as groq_error:
                print(f"[ERROR] Groq also failed: {groq_error}")
                raise
        else:
            print(f"[ERROR] Gemini error: {e}")
            raise

    try:
        json_match = re.search(r'\{.*\}', response_text, re.DOTALL)
        if json_match:
            content = json.loads(json_match.group())
        else:
            content = {
                "titulo": topic,
                "guion": response_text,
                "hashtags": "#shorts #money #ai #youtube",
                "tags_seo": "shorts, money, ai, finance, viral",
                "descripcion": topic,
            }
    except json.JSONDecodeError:
        content = {
            "titulo": topic,
            "guion": response_text,
            "hashtags": "#shorts #money #ai #youtube",
            "tags_seo": "shorts, money, ai, finance, viral",
            "descripcion": topic,
        }

    return content


def generate_speech_english(text: str, output_path: str):
    """Generate English voice using Edge TTS (natural Microsoft voice)"""
    print("[*] Generating English voice with Edge TTS...")
    try:
        import edge_tts
        import asyncio

        srt_path = output_path.replace(".mp3", ".srt")

        async def generate():
            # Voz inglés americano natural masculino
            communicate = edge_tts.Communicate(text, voice="en-US-AndrewNeural")
            submaker = edge_tts.SubMaker()
            with open(output_path, "wb") as audio_file:
                async for chunk in communicate.stream():
                    if chunk["type"] == "audio":
                        audio_file.write(chunk["data"])
                    elif chunk["type"] == "SentenceBoundary":
                        submaker.feed(chunk)

            try:
                with open(srt_path, "w", encoding="utf-8") as f:
                    f.write(submaker.get_srt())
            except:
                pass

        asyncio.run(generate())
        print(f"[OK] Voice generated: {output_path}")
        return True
    except Exception as e:
        print(f"[ERROR] Voice generation failed: {e}")
        # Fallback to gTTS English
        try:
            from gtts import gTTS
            tts = gTTS(text=text, lang='en', slow=False)
            tts.save(output_path)
            print(f"[OK] Voice generated with gTTS fallback")
            return True
        except Exception as e2:
            print(f"[ERROR] gTTS also failed: {e2}")
            return False


def upload_to_youtube_en(video_path: str, title: str, description: str, tags: str, seo_tags: str = ""):
    """Upload to YouTube using ENGLISH channel credentials"""
    from google.oauth2.credentials import Credentials
    from google.auth.transport.requests import Request
    from googleapiclient.discovery import build
    from googleapiclient.http import MediaFileUpload

    print(f"[*] Uploading to YouTube (EN channel)...")
    print(f"   Title: {title}")

    # Token específico para canal en inglés
    TOKEN_FILE = 'youtube_token_en.json'
    SCOPES = ['https://www.googleapis.com/auth/youtube.upload']

    try:
        token_env = os.getenv("YOUTUBE_TOKEN_EN")
        if token_env:
            raw = token_env.strip().strip("'\"")
            creds = Credentials.from_authorized_user_info(json.loads(raw), SCOPES)
        else:
            if not os.path.exists(TOKEN_FILE):
                print("[ERROR] No English channel token found")
                return False
            with open(TOKEN_FILE, 'r', encoding='utf-8') as f:
                raw = f.read().strip().strip("'\"")
            creds = Credentials.from_authorized_user_info(json.loads(raw), SCOPES)

        if creds.expired and creds.refresh_token:
            print(f"[*] Refreshing token...")
            refresh_session = requests.Session()
            refresh_session.verify = False
            creds.refresh(Request(session=refresh_session))
            with open(TOKEN_FILE, 'w') as f:
                f.write(creds.to_json())

        youtube = build('youtube', 'v3', credentials=creds)

        shorts_title = (title + ' #Shorts')[:100]
        shorts_description = description[:4900] + '\n\n' + tags + ' #Shorts'

        tag_list = [t.lstrip('#') for t in tags.split()] + ['Shorts']
        if seo_tags:
            seo_tag_list = [t.strip() for t in seo_tags.split(",") if t.strip()]
            tag_list.extend(seo_tag_list)
        tag_list = list(dict.fromkeys(tag_list))[:30]

        body = {
            'snippet': {
                'title': shorts_title,
                'description': shorts_description,
                'tags': tag_list,
                'categoryId': '28',
                'defaultLanguage': 'en',
                'defaultAudioLanguage': 'en',
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
                print(f"  Uploading... {int(status.progress() * 100)}%")

        video_id = response['id']
        print(f"[OK] Video uploaded!")
        print(f"   URL: https://www.youtube.com/watch?v={video_id}")
        return True

    except Exception as e:
        print(f"[WARN] Upload failed: {e}")
        return False


def main():
    print("\n" + "="*60)
    print("YOUTUBE SHORTS GENERATION SYSTEM (ENGLISH)")
    print("="*60 + "\n")

    topics = get_trending_topics_en()
    topic = topics[0]["title"] if topics else "Make money with AI"
    print(f"\n[*] Selected topic: {topic}\n")

    content = generate_script_en(topic)
    print(f"\n[*] Script generated:\n{content['guion']}\n")

    audio_path = TEMP_DIR / "voice_en.mp3"
    if not generate_speech_english(content['guion'], str(audio_path)):
        print("[ERROR] Voice generation failed")
        return False

    images = download_images_from_pexels(topic, count=10)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    video_path = OUTPUT_DIR / f"video_en_{timestamp}.mp4"

    srt_path = str(audio_path).replace(".mp3", ".srt")
    if not create_video_with_ffmpeg(images, str(audio_path), str(video_path), srt_path):
        print("[ERROR] Video creation failed")
        return False

    upload_to_youtube_en(
        str(video_path),
        content['titulo'],
        content['descripcion'],
        content['hashtags'],
        content.get('tags_seo', '')
    )

    print("\n" + "="*60)
    print("[OK] ENGLISH PROCESS COMPLETED")
    print("="*60)
    print(f"\n  Video: {video_path}")
    print(f"  Title: {content['titulo']}\n")

    return True


if __name__ == "__main__":
    main()
