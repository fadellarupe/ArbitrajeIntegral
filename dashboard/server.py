# ArbitrajeIntegral/dashboard/server.py
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
import uvicorn
import os
import sys
import json
import requests
import asyncio
from contextlib import asynccontextmanager
from google import genai
from google.genai import types

# Añadir raíz al path para imports
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from portfolio.inventory import InventoryManager
from portfolio.movements import MovementLogger
from scrapers.binance import BinanceP2PScraper
from scrapers.bybit import BybitP2PScraper
from scrapers.okx import OKXP2PScraper
from engine.decision_engine import DecisionEngine
from state.state_registry import state_registry
from analytics.bq_client import BigQueryManager
from alerts.telegram import TelegramNotifier

import config

# Instanciar Scrapers
binance_scraper = BinanceP2PScraper()
bybit_scraper = BybitP2PScraper()
okx_scraper = OKXP2PScraper()

# Instanciar Managers
inv_manager = InventoryManager()
mov_logger = MovementLogger()
engine = DecisionEngine(inv_manager)
bq_manager = BigQueryManager()
notifier = TelegramNotifier()

# --- BUCLES DE MONITOREO CONCURRENTE ---

async def run_binance_loop():
    print("[INFO] Iniciando bucle concurrente Binance P2P...")
    while True:
        try:
            buy_ads = await asyncio.to_thread(binance_scraper.fetch_ads, "BUY", pages=1)
            sell_ads = await asyncio.to_thread(binance_scraper.fetch_ads, "SELL", pages=1)
            state_registry.update_exchange("Binance", buy_ads, sell_ads, "Activo")
            
            # Logging a BigQuery (Solo Binance por ahora para histórico consistente)
            if buy_ads and sell_ads:
                best_buy = buy_ads[0]['price']
                best_sell = sell_ads[0]['price']
                spread = best_buy - best_sell
                await asyncio.to_thread(bq_manager.log_market_data, spread, best_buy, best_sell, "Binance")
                
        except Exception as e:
            state_registry.update_status("Binance", f"Error: {e}")
            print(f"[ERROR] Binance loop: {e}")
        await asyncio.sleep(12) # Actualiza cada 12 segundos

async def run_bybit_loop():
    print("[INFO] Iniciando bucle concurrente Bybit P2P...")
    while True:
        try:
            buy_ads = await asyncio.to_thread(bybit_scraper.fetch_ads, "BUY", pages=1)
            sell_ads = await asyncio.to_thread(bybit_scraper.fetch_ads, "SELL", pages=1)
            state_registry.update_exchange("Bybit", buy_ads, sell_ads, "Activo")
        except Exception as e:
            state_registry.update_status("Bybit", f"Error: {e}")
            print(f"[ERROR] Bybit loop: {e}")
        await asyncio.sleep(50) # Actualiza cada 50 segundos (Selenium)

async def run_okx_loop():
    print("[INFO] Iniciando bucle concurrente OKX P2P...")
    while True:
        try:
            buy_ads = await asyncio.to_thread(okx_scraper.fetch_ads, "BUY", pages=1)
            sell_ads = await asyncio.to_thread(okx_scraper.fetch_ads, "SELL", pages=1)
            state_registry.update_exchange("OKX", buy_ads, sell_ads, "Activo")
        except Exception as e:
            state_registry.update_status("OKX", f"Error: {e}")
            print(f"[ERROR] OKX loop: {e}")
        await asyncio.sleep(50) # Actualiza cada 50 segundos (Selenium)

async def run_alert_and_stock_check():
    print("[INFO] Iniciando bucle de alertas y stock...")
    while True:
        try:
            # 1. Alertas de Arbitraje Rentable
            state = state_registry.get_state()
            opportunities = engine.get_all_opportunities(state)
            if opportunities:
                best = opportunities[0]
                if best["roi_pct"] >= 0.8: # Umbral alto para no saturar Telegram
                    msg = f"🚀 OPORTUNIDAD {best['type']}: {best['buy_exchange']} -> {best['sell_exchange']} | ROI: {best['roi_pct']}% | Spread: ${best['spread_bruto']}"
                    await asyncio.to_thread(notifier.send_alert, msg)

            # 2. Chequeo de Stock
            stock = inv_manager.get_stock()
            for platform, assets in stock.items():
                if platform == "last_update": continue
                for asset, val in assets.items():
                    threshold = config.THRESHOLD_ARS if asset == "ARS" else config.THRESHOLD_USDT
                    if val < threshold:
                        await asyncio.to_thread(notifier.notify_low_stock, platform, asset, val, threshold)
                        
        except Exception as e:
            print(f"[ERROR] Alert loop: {e}")
        await asyncio.sleep(60) # Chequeo cada minuto

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Crear e iniciar tareas en segundo plano al arrancar la app
    bg_tasks = [
        asyncio.create_task(run_binance_loop()),
        asyncio.create_task(run_bybit_loop()),
        asyncio.create_task(run_okx_loop()),
        asyncio.create_task(run_alert_and_stock_check())
    ]
    yield
    # Cancelar tareas al detener el servidor
    for task in bg_tasks:
        task.cancel()
    await asyncio.gather(*bg_tasks, return_exceptions=True)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
app = FastAPI(lifespan=lifespan)
templates = Jinja2Templates(directory=os.path.join(BASE_DIR, "templates"))

# --- CONFIGURACIÓN DE IA (Orquestador Failover Profesional) ---
GEMINI_API_KEY = "AIzaSyCwVKhs2jUPhYBcbmfVsWogvbgutavJfmw"
GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")
OLLAMA_URL = "http://localhost:11434/api/generate"

# Nuevo cliente de Gemini
client_gemini = genai.Client(api_key=GEMINI_API_KEY) if GEMINI_API_KEY else None

# Intentar detectar la carpeta de reglas MD en el workspace
MD_PATH = os.path.join(os.path.dirname(BASE_DIR), "Arbitraje_MD")
if not os.path.exists(MD_PATH):
    # Fallback al path absoluto original si existe
    ALT_MD_PATH = r"D:\Python_Projects\Arbitraje_MD"
    MD_PATH = ALT_MD_PATH if os.path.exists(ALT_MD_PATH) else os.path.join(os.path.dirname(BASE_DIR), "docs")

def load_md_rules():
    rules = {}
    files = ["ESTRATEGIA.md", "GESTION_RIESGO.md", "ERRORES_FRECUENTES.md"]
    for f_name in files:
        path = os.path.join(MD_PATH, f_name)
        if os.path.exists(path):
            with open(path, "r", encoding="utf-8") as f:
                rules[f_name] = f.read()
    return rules

@app.get("/", response_class=HTMLResponse)
async def read_item(request: Request):
    return templates.TemplateResponse(request=request, name="index.html")

@app.get("/api/dashboard_data")
async def get_dashboard_data():
    inv_manager.stock = inv_manager._load()
    stock = inv_manager.get_stock()
    
    # Obtener estado unificado
    unified_state = state_registry.get_state()
    
    # Si Binance no ha cargado anuncios aún, forzamos un raspado inicial síncrono rápido
    if not unified_state["Binance"]["buy_ads"] or not unified_state["Binance"]["sell_ads"]:
        try:
            buy_ads = binance_scraper.fetch_ads("BUY", pages=1)
            sell_ads = binance_scraper.fetch_ads("SELL", pages=1)
            state_registry.update_exchange("Binance", buy_ads, sell_ads, "Activo")
            unified_state = state_registry.get_state()
        except Exception as e:
            print(f"[WARN] Inicialización síncrona fallida: {e}")

    # Binance para compatibilidad anterior y cálculo de stock de referencia
    binance_buy = unified_state["Binance"]["buy_ads"]
    binance_sell = unified_state["Binance"]["sell_ads"]
    
    best_buy = binance_buy[0] if binance_buy else None
    best_sell = binance_sell[0] if binance_sell else None
    
    ref_price = best_buy['price'] if best_buy else 1000.0
    total_ars = 0.0
    total_usdt_equiv = 0.0
    for platform, assets in stock.items():
        if platform == "last_update": continue
        total_ars += assets.get("ARS", 0.0)
        total_ars += assets.get("USDT", 0.0) * ref_price
        total_usdt_equiv += assets.get("USDT", 0.0)
        total_usdt_equiv += assets.get("ARS", 0.0) / ref_price

    # Encontrar oportunidades de arbitraje cruzado
    opportunities = engine.get_all_opportunities(unified_state)

    # Si hay oportunidades, actualizar la mejor de todas para compatibilidad con widgets globales
    if opportunities:
        best_opp = opportunities[0]
        # Si el ROI es positivo, lo tomamos como punta de referencia
        if best_opp["roi_pct"] > 0:
            best_buy = best_opp["best_buy_ad"]
            best_sell = best_opp["best_sell_ad"]

    return {
        "stock": stock,
        "buy_ads": binance_buy[:10], # Compatibilidad
        "sell_ads": binance_sell[:10], # Compatibilidad
        "best_buy": best_buy,
        "best_sell": best_sell,
        "unified_state": unified_state,
        "opportunities": opportunities,
        "metrics": {
            "total_ars": round(total_ars, 2),
            "total_usdt": round(total_usdt_equiv, 2),
            "spread": round(best_buy['price'] - best_sell['price'], 2) if best_buy and best_sell else 0,
            "ref_price": ref_price,
            "min_spread": config.MIN_SPREAD_GOLDEN_RULE
        },
        "movements": [m for m in mov_logger.get_recent(limit=100) if m.get("type") in ["COMPRA", "VENTA", "TRADE"]]
    }

@app.get("/api/ai_verdict")
async def get_ai_verdict(provider: str = "auto"):
    data = await get_dashboard_data()
    rules = load_md_rules()
    
    # Prompt de Sistema Maestro adaptado para múltiples exchanges
    system_instruction = f"""
    ESTABLECER ROL: Eres "ArbitrajeIntegral-Core", un motor de inferencia lógica basado en Visual FoxPro/VB. Tu misión es auditar el mercado P2P.
    
    REGLAS DE NEGOCIO (D:\\Arbitraje_MD):
    1. UMBRAL DE PROFIT: El spread neto (Precio Venta - Precio Compra - 0.40% Fees) DEBE ser > $10.80 ARS.
    2. LÓGICA DE POSICIONAMIENTO: No compitas por $0.01 si el margen es bajo. Si el spread es menor al umbral, tu sugerencia es "PESCA" (lejos del Top 1).
    3. PRIORIDAD DE ACCIÓN: 
       - Si Stock USDT > 10 -> Objetivo primordial: VENDER.
       - Si Saldo ARS > 50,000 -> Objetivo primordial: COMPRAR.
    
    CONTEXTO ESTRATÉGICO (.md):
    - ESTRATEGIA: {rules.get('ESTRATEGIA.md')}
    - RIESGO: {rules.get('GESTION_RIESGO.md')}
    - ERRORES: {rules.get('ERRORES_FRECUENTES.md')}

    DATOS MULTI-EXCHANGE ACTUALES (Binance, Bybit, OKX):
    - SALDOS: {json.dumps(data['stock'])}
    - OPORTUNIDADES DETECTADAS (ordenadas por ROI): {json.dumps(data['opportunities'][:5])}
    - ESTADO UNIFICADO: {json.dumps({ex: {"best_buy": ads["buy_ads"][0] if ads["buy_ads"] else None, "best_sell": ads["sell_ads"][0] if ads["sell_ads"] else None} for ex, ads in data["unified_state"].items()})}
    """

    user_prompt = """
    PROCESO DE PENSAMIENTO (CADENA DE LÓGICA MULTI-EXCHANGE):
    A) Identificar qué exchange ofrece la mejor compra y cuál la mejor venta según las oportunidades detectadas.
    B) Sugerir en qué exchange conviene COMPRAR y en cuál VENDER para maximizar spread y minimizar comisiones.
    C) Evaluar el "Spread Neto Real" de la mejor oportunidad cruzada.
    D) SI Spread < $10.80 -> Sugerir precio de PESCA en el exchange ideal.
    E) SI Spread > $10.80 -> Sugerir precio de COMPETENCIA (EJECUTAR en las puntas indicadas).

    RESPUESTA REQUERIDA (JSON PURO):
    {
      "estado": "PESCA | EJECUTAR | STAY",
      "sugerencia_compra": { "precio": 0.00, "exchange": "NombreExchange", "vs_top1": "diff" },
      "sugerencia_venta": { "precio": 0.00, "exchange": "NombreExchange", "vs_top1": "diff" },
      "spread_neto": 0.00,
      "alerta": "msg/null (indicar si hay stock insuficiente en la wallet de origen para realizar el cruce)",
      "sintesis": "Explicación breve de la oportunidad cruzada seleccionada (ej: Comprar en Bybit y vender en Binance)."
    }
    """

    # --- FUNCIONES DE LOS PROVEEDORES ---

    async def try_ollama():
        print("[DEBUG] Intentando Ollama (Master Prompt)...")
        payload = {
            "model": "llama3",
            "system": system_instruction,
            "prompt": user_prompt,
            "stream": False,
            "format": "json"
        }
        r = requests.post(OLLAMA_URL, json=payload, timeout=60)
        res_text = r.json().get('response', '')
        res = json.loads(res_text)
        res["fuente"] = "Local (Ollama)"
        return res

    async def try_gemini():
        print("[DEBUG] Intentando Gemini (Nueva Librería)...")
        if not client_gemini: raise Exception("No Gemini Client")
        full_prompt = f"{system_instruction}\n\n{user_prompt}"
        response = client_gemini.models.generate_content(
            model="gemini-1.5-flash",
            contents=full_prompt,
            config=types.GenerateContentConfig(
                response_mime_type="application/json"
            )
        )
        res = json.loads(response.text)
        res["fuente"] = "Gemini (Cloud)"
        return res

    async def try_groq():
        print("[DEBUG] Intentando Groq...")
        if not GROQ_API_KEY: raise Exception("No GROQ_API_KEY")
        headers = {"Authorization": f"Bearer {GROQ_API_KEY}", "Content-Type": "application/json"}
        full_prompt = f"{system_instruction}\n\n{user_prompt}"
        payload = {
            "model": "llama3-70b-8192",
            "messages": [{"role": "system", "content": "Responde solo JSON"}, {"role": "user", "content": full_prompt}],
            "response_format": {"type": "json_object"}
        }
        r = requests.post("https://api.groq.com/openai/v1/chat/completions", json=payload, headers=headers, timeout=10)
        res = json.loads(r.json()['choices'][0]['message']['content'])
        res["fuente"] = "Groq (Llama-3)"
        return res

    # --- LÓGICA DE ORQUESTACIÓN (Ollama Prioridad) ---
    if provider == "ollama":
        try: return await try_ollama()
        except Exception as e: return {"error": f"Ollama falló: {str(e)}"}
    elif provider == "gemini":
        try: return await try_gemini()
        except Exception as e: return {"error": f"Gemini falló: {str(e)}"}
    elif provider == "groq":
        try: return await try_groq()
        except Exception as e: return {"error": f"Groq falló: {str(e)}"}

    # AUTO (Failover)
    try: return await try_ollama()
    except:
        try: return await try_gemini()
        except:
            try: return await try_groq()
            except: return {"error": "Todos los servicios de IA están caídos"}

@app.post("/api/execute_trade")
async def execute_trade(trade_type: str, usdt_amount: float, ars_amount: float, usdt_platform: str, ars_platform: str, timestamp: str = None):
    success = inv_manager.execute_trade(trade_type, usdt_amount, ars_amount, usdt_platform, ars_platform, timestamp)
    return {"success": success}

@app.post("/api/delete_wallet")
async def delete_wallet(platform: str):
    success = inv_manager.delete_platform(platform)
    return {"success": success}

@app.post("/api/update_stock")
async def update_stock(platform: str, asset: str, amount: float, op: str = "SET"):
    success = inv_manager.update_balance(platform, asset, amount, operation=op)
    return {"success": success}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
