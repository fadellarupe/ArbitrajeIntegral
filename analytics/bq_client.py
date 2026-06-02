# ArbitrajeIntegral/analytics/bq_client.py
from google.cloud import bigquery
from datetime import datetime
import os

class BigQueryManager:
    """
    Gestiona la inserción de datos en Google BigQuery.
    Requiere GOOGLE_APPLICATION_CREDENTIALS en el entorno.
    """
    def __init__(self, dataset_id="arbitraje_p2p", table_id="historico_anuncios"):
        try:
            self.client = bigquery.Client()
            self.dataset_id = dataset_id
            self.table_id = table_id
            # Path completo: proyecto.dataset.tabla
            self.full_table_path = f"{self.client.project}.{dataset_id}.{table_id}"
            self.active = True
        except Exception as e:
            print(f"[WARN BQ] No se pudo inicializar BigQuery (¿Faltan credenciales?): {e}")
            self.active = False

    def log_market_data(self, spread, best_buy, best_sell, source="Binance"):
        """
        Prepara e inserta una fila con los precios detectados.
        """
        if not self.active:
            return

        row = {
            "timestamp": datetime.now().isoformat(),
            "source": source,
            "spread": float(spread),
            "best_buy": float(best_buy),
            "best_sell": float(best_sell)
        }

        try:
            errors = self.client.insert_rows_json(self.full_table_path, [row])
            if errors == []:
                print(f"   -> [BQ] Fila insertada en {self.table_id}")
            else:
                print(f"   -> [BQ ERROR] Errores: {errors}")
        except Exception as e:
            print(f"   -> [BQ ERROR] Fallo al enviar: {e}")
