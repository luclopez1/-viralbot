import os
from dotenv import load_dotenv

load_dotenv()

print(f"GEMINI_API_KEY: {os.getenv('GEMINI_API_KEY', 'NO ENCONTRADO')}")
print(f"Largo de la clave: {len(os.getenv('GEMINI_API_KEY', ''))}")