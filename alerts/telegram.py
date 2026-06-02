# ArbitrajeIntegral/alerts/telegram.py
import requests

class TelegramNotifier:
    def __init__(self, token="YOUR_BOT_TOKEN", chat_id="YOUR_CHAT_ID"):
        self.token = token
        self.chat_id = chat_id
        self.base_url = f"https://api.telegram.org/bot{self.token}/sendMessage"

    def send_alert(self, message):
        """Envía un mensaje genérico."""
        print(f"[ALERTA TELEGRAM]: {message}")
        try:
            # Descomentar para producción
            # requests.post(self.base_url, data={"chat_id": self.chat_id, "text": message})
            pass
        except Exception as e:
            print(f"Error enviando Telegram: {e}")

    def notify_low_stock(self, platform, asset, current_val, threshold):
        """Alerta específica de liquidez crítica."""
        msg = (f"⚠️ ¡LIQUIDEZ CRÍTICA!\n"
               f"Plataforma: {platform}\n"
               f"Activo: {asset}\n"
               f"Saldo actual: {current_val}\n"
               f"Umbral mínimo: {threshold}\n"
               f"Por favor, recarga para continuar operando.")
        self.send_alert(msg)
