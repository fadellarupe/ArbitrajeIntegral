import google.generativeai as genai
import os

genai.configure(api_key="AIzaSyCwVKhs2jUPhYBcbmfVsWogvbgutavJfmw")

print("--- LISTADO DE MODELOS DISPONIBLES ---")
try:
    for m in genai.list_models():
        if 'generateContent' in m.supported_generation_methods:
            print(f"MODELO: {m.name} | VERSION: {m.version}")
except Exception as e:
    print(f"Error al listar: {e}")
