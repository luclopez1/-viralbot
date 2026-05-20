#!/usr/bin/env python3
"""
VIDEO UTILITIES
Funciones compartidas de FFmpeg y subida a YouTube (canal Unveiled)
"""

import os
import subprocess
from pathlib import Path


def find_ffmpeg():
    """Encuentra el binario de FFmpeg"""
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
    """Devuelve la duracion del audio en segundos"""
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


def upload_to_cinematic_channel(video_path: str, title: str, description: str, tags: str, seo_tags: str = ""):
    """Sube video al canal Unveiled (credenciales cinematic)"""
    from google.oauth2.credentials import Credentials
    from google.auth.transport.requests import Request
    from googleapiclient.discovery import build
    from googleapiclient.http import MediaFileUpload

    print(f"\n[*] Subiendo a YouTube (canal Unveiled)...")
    print(f"   Titulo: {title}")

    TOKEN_FILE = 'youtube_token_cinematic.json'
    SCOPES = ['https://www.googleapis.com/auth/youtube.upload']

    try:
        # GitHub Actions: token desde variable de entorno
        token_env = os.getenv("YOUTUBE_TOKEN_CINEMATIC")
        if token_env and not os.path.exists(TOKEN_FILE):
            raw = token_env.strip().strip("'\"")
            with open(TOKEN_FILE, 'w') as f:
                f.write(raw)

        creds = Credentials.from_authorized_user_file(TOKEN_FILE, SCOPES)

        if creds.expired and creds.refresh_token:
            print("[*] Renovando token...")
            creds.refresh(Request())
            with open(TOKEN_FILE, 'w') as f:
                f.write(creds.to_json())

        youtube = build('youtube', 'v3', credentials=creds)

        # Preparar tags
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
        print(f"[OK] Subido! https://youtube.com/watch?v={video_id}")
        return video_id

    except Exception as e:
        print(f"[ERROR] Fallo la subida: {e}")
        return None
