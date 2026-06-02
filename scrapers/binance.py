# ArbitrajeIntegral/scrapers/binance.py
import requests
from config import MIN_REPUTATION, MIN_ORDERS_BASIC

class BinanceP2PScraper:
    URL = "https://p2p.binance.com/bapi/c2c/v2/friendly/c2c/adv/search"
    HEADERS = {
        "Content-Type": "application/json",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
    }
    
    def fetch_ads(self, trade_type, asset="USDT", fiat="ARS", pages=5):
        all_ads = []
        for page in range(1, pages + 1):
            payload = {
                "fiat": fiat, "asset": asset, "tradeType": trade_type,
                "page": page, "rows": 20, "publisherType": None, "payTypes": [],
                "classifies": ["mass", "profession", "fiat_merchant", "crypto_merchant"]
            }
            try:
                response = requests.post(self.URL, json=payload, headers=self.HEADERS, timeout=10)
                data = response.json()
                if data.get("code") == "000000":
                    page_ads = data.get("data", [])
                    all_ads.extend(self._parse_ads(page_ads))
                else:
                    print(f"[ERROR] API Binance: {data.get('message')}")
            except Exception as e:
                print(f"[ERROR] Fallo en scraping página {page}: {e}")
        return all_ads

    def _parse_ads(self, raw_ads):
        parsed = []
        for item in raw_ads:
            adv = item.get("adv", {})
            advertiser = item.get("advertiser", {})
            parsed.append({
                "price": float(adv.get("price")),
                "advertiser_name": advertiser.get("nickName"),
                "advertiser_no": advertiser.get("userNo"),
                "advertiser_reputation": float(advertiser.get("monthFinishRate", 0)) * 100,
                "advertiser_orders": int(advertiser.get("monthOrderCount", 0)),
                "available": float(adv.get("tradableQuantity")),
                "min_limit": float(adv.get("minSingleTransAmount")),
                "max_limit": float(adv.get("maxSingleTransAmount")),
                "methods": [m.get("tradeMethodName") for m in adv.get("tradeMethods", [])]
            })
        return parsed

    def filter_safe_ads(self, ads):
        return [
            ad for ad in ads 
            if ad['advertiser_reputation'] >= MIN_REPUTATION 
            and ad['advertiser_orders'] >= MIN_ORDERS_BASIC
        ]
