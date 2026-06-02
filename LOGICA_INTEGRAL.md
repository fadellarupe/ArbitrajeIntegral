# Lógica Integral de Arbitraje P2P (USDT/ARS)

Este sistema centraliza la operativa de arbitraje profesional, priorizando la seguridad del capital y la eficiencia del spread.

## 1. Captura de Datos y Detección de Oportunidades
* **Spread de Pizarra vs. Profundidad:** El sistema monitorea los primeros anuncios para liquidez inmediata (Taker) y las páginas 5 a 10 para detectar "diamantes" o anuncios desfasados (Spread Oculto).
* **Visión Multi-Exchange:** Se integra CriptoYa para identificar si el precio de salida en otros exchanges (Lemon, Ripio, etc.) ofrece un ROI superior a la venta directa en Binance.
* **Análisis de Volumen (Data Grounding):** Los datos se estructuran para BigQuery, permitiendo identificar en qué horas el volumen de los "Merchants" disminuye, abriendo brechas de precio para perfiles Maker.

## 2. Gestión de Riesgos y Filtros
* **Validación de Contraparte:** No se interactúa con usuarios que no cumplan el estándar de confianza (>98% éxito / >100 órdenes) para evitar estafas triangulares o demoras en la liberación.
* **Calce de Inventario:** El motor de decisiones solo sugerirá un arbitraje si el stock en la billetera de origen (ej. MercadoPago) cubre el monto mínimo del anuncio detectado.

## 3. Estrategia de Ejecución (Maker/Taker)
* **ROI Neto:** Todas las sugerencias restan automáticamente la comisión de Binance (0.1% o variable según anuncio) y el costo impositivo estimado de los movimientos bancarios.
* **Ciclo de Reinversión:** El sistema prioriza el volumen de transacciones para escalar hacia el estatus de "Merchant", lo que reducirá comisiones y aumentará la visibilidad de nuestros anuncios propios.

## 4. Dashboard de Control
* **Action Cards:** Mensajes directos para ejecución rápida: "COMPRAR TAKER (Binance) -> VENDER MAKER (Lemon)".
* **Conciliación:** Botones de ajuste manual para reflejar acreditaciones externas y mantener el `inventory.json` siempre sincronizado con la realidad financiera.
