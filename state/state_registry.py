# ArbitrajeIntegral/state/state_registry.py
import threading
from datetime import datetime

class StateRegistry:
    def __init__(self):
        self._lock = threading.Lock()
        self._state = {
            "Binance": {
                "buy_ads": [],
                "sell_ads": [],
                "last_update": None,
                "status": "Inactivo"
            },
            "Bybit": {
                "buy_ads": [],
                "sell_ads": [],
                "last_update": None,
                "status": "Inactivo"
            },
            "OKX": {
                "buy_ads": [],
                "sell_ads": [],
                "last_update": None,
                "status": "Inactivo"
            }
        }

    def update_exchange(self, exchange: str, buy_ads: list, sell_ads: list, status: str = "Activo"):
        """Actualiza el estado de un exchange específico de forma segura para hilos."""
        with self._lock:
            if exchange in self._state:
                self._state[exchange]["buy_ads"] = buy_ads
                self._state[exchange]["sell_ads"] = sell_ads
                self._state[exchange]["last_update"] = datetime.now().isoformat()
                self._state[exchange]["status"] = status

    def update_status(self, exchange: str, status: str):
        """Actualiza solo el estado (status) de un exchange."""
        with self._lock:
            if exchange in self._state:
                self._state[exchange]["status"] = status

    def get_state(self) -> dict:
        """Devuelve una copia del estado actual de todos los exchanges."""
        with self._lock:
            # Hacemos una copia superficial rápida de los campos principales
            return {
                exchange: {
                    "buy_ads": list(data["buy_ads"]),
                    "sell_ads": list(data["sell_ads"]),
                    "last_update": data["last_update"],
                    "status": data["status"]
                }
                for exchange, data in self._state.items()
            }

    def get_exchange_state(self, exchange: str) -> dict:
        """Devuelve el estado de un exchange específico."""
        with self._lock:
            if exchange in self._state:
                data = self._state[exchange]
                return {
                    "buy_ads": list(data["buy_ads"]),
                    "sell_ads": list(data["sell_ads"]),
                    "last_update": data["last_update"],
                    "status": data["status"]
                }
            return {}

# Instancia global única
state_registry = StateRegistry()
