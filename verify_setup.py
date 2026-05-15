#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import sys
import subprocess
from pathlib import Path

def check_python():
    """Verifica Python"""
    try:
        version = f"{sys.version_info.major}.{sys.version_info.minor}"
        print(f"[OK] Python {version}")
        return True
    except Exception as e:
        print(f"[ERROR] Python: {e}")
        return False

def check_ffmpeg():
    """Verifica FFmpeg"""
    try:
        result = subprocess.run(['ffmpeg', '-version'], capture_output=True, text=True, timeout=5)
        if result.returncode == 0:
            version_line = result.stdout.split('\n')[0]
            print(f"[OK] FFmpeg encontrado")
            return True
        else:
            print(f"[ERROR] FFmpeg no responde")
            return False
    except FileNotFoundError:
        print(f"[ERROR] FFmpeg no encontrado en PATH")
        print(f"       Instala desde: https://ffmpeg.org/download.html")
        return False
    except Exception as e:
        print(f"[ERROR] FFmpeg: {e}")
        return False

def check_node():
    """Verifica Node.js"""
    try:
        result = subprocess.run(['node', '--version'], capture_output=True, text=True, timeout=5)
        if result.returncode == 0:
            version = result.stdout.strip()
            print(f"[OK] Node.js {version}")
            return True
    except:
        print(f"[WARN] Node.js no encontrado (necesario para n8n)")
        return False

def check_packages():
    """Verifica paquetes Python"""
    packages = [
        'anthropic',
        'requests',
        'dotenv',
        'edge_tts',
        'PIL',
        'google'
    ]

    missing = []
    for pkg in packages:
        try:
            __import__(pkg if pkg != 'PIL' else 'PIL')
            print(f"[OK] {pkg}")
        except ImportError:
            print(f"[ERROR] {pkg} no instalado")
            missing.append(pkg)

    return len(missing) == 0

def check_env():
    """Verifica .env"""
    env_file = Path('.env')
    if env_file.exists():
        with open(env_file) as f:
            content = f.read()
            has_api_key = 'ANTHROPIC_API_KEY' in content and not 'your_' in content
            has_youtube = 'YOUTUBE_API_KEY' in content and not 'your_' in content
            has_pexels = 'PEXELS_API_KEY' in content and not 'your_' in content

            if has_api_key:
                print(f"[OK] ANTHROPIC_API_KEY configurada")
            else:
                print(f"[WARN] ANTHROPIC_API_KEY no configurada")

            if has_youtube:
                print(f"[OK] YOUTUBE_API_KEY configurada")
            else:
                print(f"[WARN] YOUTUBE_API_KEY no configurada")

            if has_pexels:
                print(f"[OK] PEXELS_API_KEY configurada")
            else:
                print(f"[WARN] PEXELS_API_KEY no configurada")

            return has_api_key or has_youtube or has_pexels
    else:
        print(f"[ERROR] .env no encontrado")
        return False

def check_folders():
    """Verifica carpetas"""
    folders = ['videos_output', 'temp', 'assets']
    all_ok = True
    for folder in folders:
        p = Path(folder)
        if p.exists():
            print(f"[OK] Carpeta {folder}/")
        else:
            print(f"[WARN] Carpeta {folder}/ no existe (se creará automáticamente)")
            p.mkdir(exist_ok=True)
            all_ok = False
    return all_ok

def main():
    print("\n" + "="*50)
    print("VERIFICAR SETUP")
    print("="*50 + "\n")

    results = {
        "Python": check_python(),
        "FFmpeg": check_ffmpeg(),
        "Node.js": check_node(),
        "Packages Python": check_packages(),
        ".env": check_env(),
        "Carpetas": check_folders(),
    }

    print("\n" + "="*50)
    print("RESUMEN")
    print("="*50)

    critical_ok = results["Python"] and results["FFmpeg"] and results["Packages Python"]

    if critical_ok:
        print("\n[OK] SETUP CORRECTO - Puedes ejecutar:")
        print("     python generate_content.py")
    else:
        print("\n[ERROR] FALTA INSTALAR:")
        if not results["FFmpeg"]:
            print("   - FFmpeg: https://ffmpeg.org/download.html")
        if not results["Packages Python"]:
            print("   - Paquetes Python: pip install -r requirements.txt")
        if not results["Python"]:
            print("   - Python 3.8+: https://www.python.org")

    if not results[".env"] or results[".env"] == "WARN":
        print("\n[WARN] FALTAN API KEYS EN .env")
        print("   Lee: API_SETUP.md")

    print("\n")
    return critical_ok

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
