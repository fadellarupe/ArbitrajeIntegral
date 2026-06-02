# ArbitrajeIntegral/portfolio/movements.py
import json
import os
from datetime import datetime

LOG_PATH = os.path.join(os.path.dirname(__file__), "../db/movements.log")

class MovementLogger:
    def __init__(self):
        if not os.path.exists(os.path.dirname(LOG_PATH)):
            os.makedirs(os.path.dirname(LOG_PATH))
        if not os.path.exists(LOG_PATH):
            with open(LOG_PATH, "w") as f:
                pass

    def log(self, platform, asset, amount, op_type, notes="", timestamp=None):
        entry = {
            "timestamp": timestamp if timestamp else datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "platform": platform,
            "asset": asset,
            "amount": amount,
            "type": op_type,
            "notes": notes
        }
        with open(LOG_PATH, "a") as f:
            f.write(json.dumps(entry) + "\n")

    def get_recent(self, limit=10):
        movements = []
        if not os.path.exists(LOG_PATH): return []
        with open(LOG_PATH, "r") as f:
            lines = f.readlines()
            for line in lines[-limit:]:
                try:
                    movements.append(json.loads(line))
                except:
                    continue
        return list(reversed(movements))
