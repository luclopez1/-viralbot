#!/usr/bin/env python3
"""
POLLINATIONS.AI HELPER
Modulo compartido para generar imagenes IA cinematograficas
Gratis, sin API key, sin limites
"""

import os
import time
import urllib.parse
import requests
from pathlib import Path


POLLINATIONS_URL = "https://image.pollinations.ai/prompt/{prompt}"


def generate_cinematic_image(
    prompt: str,
    output_path: str,
    width: int = 1080,
    height: int = 1920,
    model: str = "flux",
    seed: int = None,
    enhance: bool = True,
    max_retries: int = 3,
) -> bool:
    """
    Genera una imagen cinematografica con Pollinations.ai

    Args:
        prompt: Descripcion en ingles de la imagen
        output_path: Donde guardar la imagen
        width: 1080 (Shorts) o 1920 (largos)
        height: 1920 (Shorts) o 1080 (largos)
        model: "flux" (calidad), "turbo" (rapido), "kontext" (consistencia)
        seed: Para reproducibilidad (None = aleatorio)
        enhance: Mejora automatica del prompt
        max_retries: Reintentos si falla

    Returns:
        True si se genero, False si fallo
    """
    # Anadir refuerzo cinematografico al prompt
    cinematic_prompt = (
        f"{prompt}, cinematic shot, dramatic lighting, hyperrealistic, "
        f"professional photography, high detail, 4k, depth of field, "
        f"film grain, color graded"
    )

    encoded = urllib.parse.quote(cinematic_prompt)
    url = POLLINATIONS_URL.format(prompt=encoded)

    params = {
        "width": width,
        "height": height,
        "model": model,
        "nologo": "true",
        "enhance": "true" if enhance else "false",
    }
    if seed is not None:
        params["seed"] = seed

    query_str = "&".join([f"{k}={v}" for k, v in params.items()])
    full_url = f"{url}?{query_str}"

    for attempt in range(max_retries):
        try:
            print(f"[*] Pollinations gen (try {attempt+1}/{max_retries})...")
            response = requests.get(full_url, timeout=180)
            if response.status_code == 200 and len(response.content) > 1000:
                with open(output_path, "wb") as f:
                    f.write(response.content)
                print(f"[OK] Imagen guardada: {output_path}")
                return True
            else:
                print(f"[WARN] HTTP {response.status_code} - reintentando...")
                time.sleep(5)
        except Exception as e:
            print(f"[WARN] Error: {e} - reintentando...")
            time.sleep(5)

    print(f"[ERROR] No se pudo generar imagen tras {max_retries} intentos")
    return False


def generate_image_batch(
    prompts: list,
    output_dir: str,
    width: int = 1080,
    height: int = 1920,
    prefix: str = "scene",
) -> list:
    """
    Genera multiples imagenes en bach (con coherencia visual)
    Returns: lista de paths a las imagenes generadas
    """
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    # Seed compartido para mantener estilo coherente entre escenas
    import random
    shared_seed = random.randint(1, 999999)

    generated = []
    for i, prompt in enumerate(prompts):
        img_path = output_dir / f"{prefix}_{i+1:02d}.jpg"
        # Variamos seed por imagen pero base similar
        scene_seed = shared_seed + i
        if generate_cinematic_image(
            prompt, str(img_path),
            width=width, height=height,
            seed=scene_seed
        ):
            generated.append(str(img_path))
        else:
            print(f"[WARN] Escena {i+1} fallo, continuando...")

    print(f"\n[OK] {len(generated)}/{len(prompts)} imagenes generadas")
    return generated


if __name__ == "__main__":
    # Test rapido
    print("Test de Pollinations.ai")
    test_path = "test_pollinations_image.jpg"
    success = generate_cinematic_image(
        "futuristic astronaut on alien planet, two suns in sky, dramatic atmosphere",
        test_path,
        width=1080,
        height=1920
    )
    if success:
        print(f"[OK] Test exitoso. Mira: {test_path}")
    else:
        print("[ERROR] Test fallo")
