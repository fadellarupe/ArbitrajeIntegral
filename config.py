# ArbitrajeIntegral/config.py

# Configuración de Seguridad y Filtros (Estándar ADA)
MIN_REPUTATION = 98.0
MIN_ORDERS_PRO = 350    # Requisito para verificado
MIN_ORDERS_BASIC = 100
MAX_RELEASE_TIME = 15   # minutos

# Configuración de Comisiones Reales (Merchant Bronce)
BINANCE_MAKER_FEE = 0.0016  # 0.16%
BINANCE_TAKER_FEE_FIXED = 0.05 # 0.05 USDT por orden

# Comisión Binance P2P sin KYC (para análisis de anuncios)
BINANCE_P2P_COMMISSION_RATE = 0.002  # 0.20%

# Parámetros de "Pesca" (Spread Oculto)
DEEP_SCAN_PAGES = 10
MIN_SPREAD_ARS = 5.0    # 5 pesos es el mínimo operable según Franco

# Regla de Oro (Academia de Arbitraje)
MIN_SPREAD_GOLDEN_RULE = 10.80  # ARS, spread mínimo para operar

# Delta para sugerencias de precios competitivos
AD_PRICE_DELTA = 0.50  # ARS, margen de competencia

# Umbrales de Alerta (Stock Bajo)
THRESHOLD_ARS = 100000.0
THRESHOLD_USDT = 100.0
DRY_RUN = True
