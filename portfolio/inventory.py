# ArbitrajeIntegral/portfolio/inventory.py
import json
import os
from datetime import datetime
from .movements import MovementLogger

DB_PATH = os.path.join(os.path.dirname(__file__), "../db/inventory.json")

class InventoryManager:
    def __init__(self):
        self.logger = MovementLogger()
        self.stock = self._load()

    def _load(self):
        if not os.path.exists(DB_PATH):
            initial_stock = {
                "Binance": {"USDT": 0.0, "ARS": 0.0},
                "Naranja X": {"ARS": 0.0},
                "Personal Pay": {"ARS": 0.0},
                "Lemon": {"USDT": 0.0, "ARS": 0.0},
                "MercadoPago": {"ARS": 0.0},
                "last_update": ""
            }
            self._save(initial_stock)
            return initial_stock
        with open(DB_PATH, "r") as f:
            return json.load(f)

    def _save(self, data):
        data["last_update"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        with open(DB_PATH, "w") as f:
            json.dump(data, f, indent=4)

    def get_stock(self):
        return self.stock

    def update_balance(self, platform, asset, amount, operation="SET", notes=""):
        if platform not in self.stock: 
            # Permitir agregar nuevas plataformas dinámicamente
            self.stock[platform] = {}
        
        old_val = self.stock[platform].get(asset, 0.0)
        
        if operation == "SET":
            new_val = float(amount)
        elif operation == "ADD":
            new_val = old_val + float(amount)
        else:
            return False

        self.stock[platform][asset] = new_val
        self._save(self.stock)
        
        diff = new_val - old_val
        op_type = "AJUSTE" if operation == "SET" else ("COMPRA" if diff > 0 else "VENTA")
        self.logger.log(platform, asset, diff, op_type, notes)
        
        return True

    def execute_trade(self, trade_type, usdt_amount, ars_amount, usdt_platform, ars_platform, timestamp=None):
        """
        Ejecuta una operación de compra o venta actualizando ambas wallets.
        COMPRA: +USDT en usdt_platform, -ARS en ars_platform
        VENTA: -USDT en usdt_platform, +ARS en ars_platform
        """
        if usdt_platform not in self.stock: self.stock[usdt_platform] = {}
        if ars_platform not in self.stock: self.stock[ars_platform] = {}

        old_usdt = self.stock[usdt_platform].get("USDT", 0.0)
        old_ars = self.stock[ars_platform].get("ARS", 0.0)

        if trade_type == "COMPRA":
            new_usdt = old_usdt + float(usdt_amount)
            new_ars = old_ars - float(ars_amount)
        elif trade_type == "VENTA":
            new_usdt = old_usdt - float(usdt_amount)
            new_ars = old_ars + float(ars_amount)
        else:
            return False

        self.stock[usdt_platform]["USDT"] = new_usdt
        self.stock[ars_platform]["ARS"] = new_ars
        self._save(self.stock)

        # Log de la operación consolidada
        trade_note = f"{trade_type} | {usdt_amount} USDT @ {ars_amount} ARS | {usdt_platform}/{ars_platform}"
        self.logger.log(f"{usdt_platform}/{ars_platform}", "TRADE", usdt_amount, trade_type, trade_note, timestamp)
        
        return True

    def delete_platform(self, platform):
        if platform in self.stock:
            del self.stock[platform]
            self._save(self.stock)
            return True
        return False
