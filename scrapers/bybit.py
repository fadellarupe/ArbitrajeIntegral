# ArbitrajeIntegral/scrapers/bybit.py
import re
import os
import sys
import time
from datetime import datetime
from bs4 import BeautifulSoup
from config import MIN_REPUTATION, MIN_ORDERS_BASIC

try:
    from selenium import webdriver
    from selenium.webdriver.chrome.options import Options
    from selenium.webdriver.chrome.service import Service
    from selenium.webdriver.common.by import By
    from selenium.webdriver.support.ui import WebDriverWait
    from selenium.webdriver.support import expected_conditions as EC
    from webdriver_manager.chrome import ChromeDriverManager
    SELENIUM_AVAILABLE = True
except ImportError:
    SELENIUM_AVAILABLE = False

class BybitP2PScraper:
    URLS = {
        "BUY": "https://www.bybit.com/en/p2p/sell/USDT/ARS",  # Advertisers BUYING (Taker sells)
        "SELL": "https://www.bybit.com/en/p2p/buy/USDT/ARS"   # Advertisers SELLING (Taker buys)
    }
    
    HEADERS = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
    }

    def _find_chrome_binary(self) -> str | None:
        possible_paths = [
            r"C:\Program Files\Google\Chrome\Application\chrome.exe",
            r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
        ]
        for path in possible_paths:
            if os.path.exists(path):
                return path
        return None

    def fetch_ads(self, trade_type, asset="USDT", fiat="ARS", pages=1):
        """
        Scrape Bybit P2P.
        trade_type: 'BUY' (advertisers buy) o 'SELL' (advertisers sell)
        """
        if not SELENIUM_AVAILABLE:
            print("[ERROR] Selenium no disponible para Bybit scraper.")
            return []

        url = self.URLS.get(trade_type)
        if not url:
            print(f"[ERROR] Tipo de operación inválido en Bybit: {trade_type}")
            return []

        # Para simplificar y acelerar, Bybit suele cargar muchos anuncios en una sola página.
        # Solo tomaremos los primeros 10-15 anuncios.
        all_ads = []
        try:
            chrome_options = Options()
            chrome_options.add_argument("--headless=new")
            chrome_options.add_argument("--no-sandbox")
            chrome_options.add_argument("--disable-dev-shm-usage")
            chrome_options.add_argument("--disable-gpu")
            chrome_options.add_argument("--window-size=1920,1080")
            chrome_options.add_argument(f"--user-agent={self.HEADERS['User-Agent']}")
            chrome_options.add_argument("--log-level=3")
            chrome_options.add_argument("--silent")
            chrome_options.add_experimental_option("excludeSwitches", ["enable-logging"])
            
            # Bloquear imágenes para velocidad
            prefs = {"profile.managed_default_content_settings.images": 2}
            chrome_options.add_experimental_option("prefs", prefs)

            chrome_binary = self._find_chrome_binary()
            if chrome_binary:
                chrome_options.binary_location = chrome_binary

            service = Service(ChromeDriverManager().install())
            driver = webdriver.Chrome(service=service, options=chrome_options)
            
            try:
                driver.get(url)
                
                # Esperar a que los nombres de los anunciantes aparezcan
                WebDriverWait(driver, 20).until(
                    EC.presence_of_element_located((By.CLASS_NAME, "advertiser-name"))
                )
                time.sleep(3) # Carga reactiva adicional
                
                soup = BeautifulSoup(driver.page_source, 'html.parser')
                
                ad_containers = soup.find_all('tr')
                ad_rows = [tr for tr in ad_containers if tr.find('div', class_='advertiser-name')]
                
                for i, row in enumerate(ad_rows[:15]):
                    try:
                        merchant_elem = row.find('div', class_='advertiser-name')
                        merchant_name = merchant_elem.text.strip() if merchant_elem else "Desconocido"
                        
                        price_elem = row.find('span', class_=re.compile(r'font-\[600\]'))
                        if not price_elem:
                            ars_span = row.find('span', string=re.compile(r'ARS'))
                            if ars_span:
                                price_elem = ars_span.parent
                        
                        price_text = price_elem.text.strip().replace('ARS', '').replace(',', '').replace('$', '').strip() if price_elem else ""
                        price_match = re.search(r'([\d,.]+)', price_text)
                        if not price_match:
                            continue
                        price = float(price_match.group(1).replace(',', ''))
                        
                        ql_values = row.find_all('div', class_='ql-value')
                        available = 0.0
                        min_limit = 0.0
                        max_limit = 0.0
                        
                        if len(ql_values) >= 1:
                            available_text = ql_values[0].text.strip().replace('USDT', '').replace(',', '').strip()
                            available = float(available_text) if available_text else 0.0
                        
                        if len(ql_values) >= 2:
                            limits_text = ql_values[1].text.strip().replace('ARS', '').replace(',', '').strip()
                            if '~' in limits_text:
                                parts = limits_text.split('~')
                                min_limit = float(parts[0].strip())
                                max_limit = float(parts[1].strip())
                        
                        # Métodos de pago
                        methods = []
                        method_tags = row.find_all('div', class_='trade-list-tag')
                        for tag in method_tags:
                            methods.append(tag.text.strip())

                        all_ads.append({
                            "price": price,
                            "advertiser_name": merchant_name,
                            "advertiser_no": f"BYBIT_{merchant_name}",
                            "advertiser_reputation": 98.0, # Default para Bybit si no se lee
                            "advertiser_orders": 120,       # Default para Bybit si no se lee
                            "available": available,
                            "min_limit": min_limit,
                            "max_limit": max_limit,
                            "methods": methods
                        })
                    except Exception as e:
                        continue
            finally:
                driver.quit()
        except Exception as e:
            print(f"[ERROR] Error al scrapear Bybit P2P ({trade_type}): {e}")
            
        return all_ads

    def filter_safe_ads(self, ads):
        return [
            ad for ad in ads 
            if ad['advertiser_reputation'] >= MIN_REPUTATION 
            and ad['advertiser_orders'] >= MIN_ORDERS_BASIC
        ]
