# 🚀 Inicio Rápido: ArbitrajeIntegral PRO v3

## Ejecutar el Sistema (Dashboard Centralizado)

El sistema ahora está centralizado en un servidor FastAPI que maneja el monitoreo de 3 exchanges, alertas de Telegram, logging a BigQuery y control de stock de forma concurrente.

```powershell
# Ejecutar desde la raíz del workspace (D:\Python_Workspace)
.\ArbitrajeIntegral\.venv\Scripts\python.exe .\ArbitrajeIntegral\dashboard\server.py
```

**Resultado automático:**
- ✓ Monitoreo concurrente: Binance (12s), Bybit (50s), OKX (50s).
- ✓ Auditoría IA: Gemini/Ollama integrada en el Dashboard.
- ✓ Logging a BigQuery: Registro automático de datos de Binance.
- ✓ Alertas Telegram: Notificaciones de oportunidades ROI > 0.8% y stock bajo.
- ✓ **Sin Basura**: No se generan más archivos HTML físicos.

## Acceso al Dashboard

Una vez iniciado el servidor, abre tu navegador en:
`http://localhost:8000`

**Funcionalidades Clave:**
- **Tabla Consolidada**: Precios Taker/Maker de todos los exchanges.
- **Oportunidades Cross-Exchange**: Las mejores rutas de compra/venta ordenadas por ROI.
- **Desglose de Comisiones**: Haz clic en cualquier fila para ver el impacto de los fees.
- **Auditor IA**: Obtén un veredicto en tiempo real sobre la situación del mercado.
- **Gestión de Saldos**: Controla tus carteras y registra nuevas operaciones.

## Configuración

### Alertas y Stock
Ajusta los umbrales en `config.py`:
```python
THRESHOLD_ARS = 100000.0  # Alerta si baja de 100k
THRESHOLD_USDT = 100.0    # Alerta si baja de 100u
```

### IA
El sistema soporta Ollama (local), Gemini y Groq. Configura los proveedores en `dashboard/server.py`.

## Validación

### Verificar módulos:

```powershell
.\ArbitrajeIntegral\.venv\Scripts\python.exe .\ArbitrajeIntegral\test_p2p_analysis.py
```

---
*Nota: main.py ha sido depreciado en favor del servidor centralizado.*
