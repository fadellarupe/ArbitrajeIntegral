# ArbitrajeIntegral/scrapers/okx.py
import re
import os
import sys
import time
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

class OKXP2PScraper:
    URLS = {
        "BUY": "https://www.okx.com/es-ar/p2p-markets/ars/sell-usdt",  # Advertisers BUYING (Taker sells)
        "SELL": "https://www.okx.com/es-ar/p2p-markets/ars/buy-usdt"   # Advertisers SELLING (Taker buys)
    }

    HEADERS = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
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

    def _safe_float(self, value):
        if not value: return 0.0
        try:
            clean = "".join(re.findall(r'[\d.,]+', value))
            if not clean: return 0.0
            if ',' in clean and (clean.find(',') > clean.find('.') or '.' not in clean):
                if len(clean.split(',')[-1]) <= 2: clean = clean.replace('.', '').replace(',', '.')
                else: clean = clean.replace(',', '')
            else:
                clean = clean.replace(',', '')
            return float(clean)
        except:
            return 0.0

    def fetch_ads(self, trade_type, asset="USDT", fiat="ARS", pages=1):
        """
        Scrape OKX P2P.
        trade_type: 'BUY' (advertisers buy) o 'SELL' (advertisers sell)
        """
        if not SELENIUM_AVAILABLE:
            print("[ERROR] Selenium no disponible para OKX scraper.")
            return []

        url = self.URLS.get(trade_type)
        if not url:
            print(f"[ERROR] Tipo de operación inválido en OKX: {trade_type}")
            return []

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
                
                # Esperar a que la tabla o filas carguen
                WebDriverWait(driver, 20).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, ".okui-table-row, [class*='table-row'], .p2p-ad-card"))
                )
                time.sleep(4) # Carga reactiva de OKX es algo lenta
                
                soup = BeautifulSoup(driver.page_source, 'html.parser')
                rows = soup.find_all(class_=re.compile(r'table-row|ad-card|ad-item'))
                
                for i, row in enumerate(rows[:15]):
                    try:
                        text = row.get_text(separator=" ")
                        
                        # 1. Precio
                        p_match = re.search(r'([\d.,]+)\s*ARS', text)
                        if not p_match: continue
                        price = self._safe_float(p_match.group(1))
                        
                        # 2. Mercante
                        m_name = "Desconocido"
                        m_elem = row.find(['a', 'span'], class_=re.compile(r'merchant|name|nick'))
                        if m_elem: 
                            m_name = m_elem.get_text().strip()
                        else: 
                            m_name = text.split()[0]
                            
                        # Limpiar nombre si tiene Stats pegadas
                        m_name = re.split(r'\d+\s*transacciones', m_name, flags=re.IGNORECASE)[0].strip()
                        
                        # 3. Límite mínimo
                        l_min = 0.0
                        l_match = re.search(r'(?:Límite|Limit|Lim.*?)\s*([\d.,]+)', text, re.IGNORECASE)
                        if l_match: 
                            l_min = self._safe_float(l_match.group(1))
                            
                        # 4. Disponible
                        avail = 0.0
                        a_match = re.search(r'(?:Disponible|Available|Dispo.*?)\s*([\d.,]+)', text, re.IGNORECASE)
                        if a_match: 
                            avail = self._safe_float(a_match.group(1))
                        
                        # Métodos de pago (OKX suele ponerlos en celdas o spans de pago)
                        methods = []
                        pay_elements = row.find_all(class_=re.compile(r'payment|pay-method|method'))
                        for elem in pay_elements:
                            methods.append(elem.get_text().strip())
                        if not methods:
                            # Parsear del texto
                            methods = ["Bank Transfer"]

                        all_ads.append({
                            "price": price,
                            "advertiser_name": m_name,
                            "advertiser_no": f"OKX_{m_name}",
                            "advertiser_reputation": 99.0,
                            "advertiser_orders": 150,
                            "available": avail,
                            "min_limit": l_min,
                            "max_limit": avail * price if avail > 0 else 1000000.0,
                            "methods": methods
                        })
                    except Exception as e:
                        continue
            finally:
                driver.quit()
        except Exception as e:
            print(f"[ERROR] Error al scrapear OKX P2P ({trade_type}): {e}")
            
        return all_ads

    def filter_safe_ads(self, ads):
        return [
            ad for ad in ads 
            if ad['advertiser_reputation'] >= MIN_REPUTATION 
            and ad['advertiser_orders'] >= MIN_ORDERS_BASIC
        ]
