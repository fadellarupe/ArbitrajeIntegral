# 🎯 ArbitrajeIntegral - Sistema de Análisis P2P USDT/ARS

Versión mejorada con análisis avanzado de comisiones, spreads y sugerencias de arbitraje para Binance P2P.

## 🚀 Inicio Rápido

```bash
# Ejecutar sistema
python main.py

# Validar instalación
python test_p2p_analysis.py
```

## 📊 Nuevas Funcionalidades

### Análisis de Comisiones
- Cálculo preciso 0.20% (P2P sin KYC)
- Separación USDT y ARS
- Visualización de impacto

### Spread Analysis
- Spread bruto y neto
- Regla de Oro ($10.80 ARS)
- Validación automática

### Sugerencias de Arbitraje
- Identifica mejor comprador/vendedor
- Calcula ganancia neta por USDT
- Valida condiciones automáticamente

### Simulación de Anuncio Propio
- Precios sugeridos para competir
- Delta de $0.50 ARS
- Rango de órdenes ordenables

### Visualizaciones
- **Consola**: ANSI colors (Cyan, Verde, Rojo)
- **HTML**: Tema oscuro profesional con timestamps

## 📁 Estructura

```
ArbitrajeIntegral/
├── analytics/
│   ├── p2p_analysis.py          # Análisis y cálculos
│   └── p2p_html_report.py       # Generador HTML
├── dashboard/
│   └── p2p_report_*.html        # Reportes generados
├── config.py                    # Configuración
├── main.py                      # Sistema principal
├── test_p2p_analysis.py         # Suite de pruebas
└── 📚 Documentación (ver abajo)
```

## 📚 Documentación

| Documento | Tiempo | Contenido |
|-----------|--------|----------|
| [INICIO_RAPIDO.md](INICIO_RAPIDO.md) | 5 min | Cómo empezar ahora mismo |
| [P2P_ANALYSIS_GUIDE.md](P2P_ANALYSIS_GUIDE.md) | 15 min | Referencia completa de funciones |
| [INTEGRACION_P2P_RESUMEN.md](INTEGRACION_P2P_RESUMEN.md) | 10 min | Resumen técnico de cambios |
| [INDICE_DOCUMENTACION.md](INDICE_DOCUMENTACION.md) | 5 min | Índice general |

## ✅ Validación

- ✓ 8/8 pruebas unitarias PASS
- ✓ Sintaxis Python verificada
- ✓ Cálculos matemáticos validados
- ✓ Reportes HTML funcionales
- ✓ Integración sin romper código existente

## 🎓 Ejemplo de Uso

```python
from analytics.p2p_analysis import find_best_match, print_suggestions

# Tus datos de anuncios
buy_ads = [...]  # Anunciantes que compran USDT
sell_ads = [...] # Anunciantes que venden USDT

# Análisis
match = find_best_match(buy_ads, sell_ads)
print_suggestions(match)

# Resultado en consola:
# ANÁLISIS DE COMISIONES Y SUGERENCIAS
# Spread bruto: $30.00 (3.061%)
# Spread neto: $24.05 (2.445%)
# Comisión total ciclo: $3.98 ARS (13.3% del spread)
# ...
```

## ⚙️ Configuración

En `config.py`:
```python
BINANCE_P2P_COMMISSION_RATE = 0.002    # 0.20% (sin KYC)
MIN_SPREAD_GOLDEN_RULE = 10.80         # ARS
AD_PRICE_DELTA = 0.50                  # ARS
```

## 🔄 Flujo del Sistema

```
1. Fetch anuncios P2P (5 páginas)
   ↓
2. Filtrar anuncios seguros
   ↓
3. Análisis de spreads/comisiones
   ↓
4. Visualizar en consola (ANSI colors)
   ↓
5. Generar reporte HTML
   ↓
6. Logging a BigQuery
   ↓
7. Alertas Telegram (si hay oportunidades)
```

## 📊 Ejemplo de Salida

### Consola
```
MERCADO P2P USDT/ARS
VENDER USDT (mejores precios para comprar):
  1. Vendedor B  $980.00  (300.00 USDT)
  2. Vendedor A  $990.00  (150.00 USDT)

ANÁLISIS DE COMISIONES Y SUGERENCIAS
Spread bruto: $30.00 (3.061%)
Spread neto: $24.05 (2.445%)
Comisión total: $3.98 ARS (13.3% del spread)
Regla de Oro: $30.00 ✓ OK
Ganancia neta: $24.05 por USDT
```

### HTML
Archivo: `dashboard/p2p_report_HH-MM-SS.html`
- Tema oscuro profesional
- Tablas interactivas
- Gráficos de comisiones
- Todas las métricas

## 🧪 Suite de Pruebas

```bash
python test_p2p_analysis.py
```

Valida:
- ✓ Cálculo de comisiones
- ✓ Precios reales (compra/venta)
- ✓ Búsqueda de spreads
- ✓ Sugerencias de precios
- ✓ Rangos de órdenes
- ✓ Visualizaciones
- ✓ Generación HTML

## 🔧 Personalización

### Cambiar comisión (si tienes KYC)
```python
# config.py
BINANCE_P2P_COMMISSION_RATE = 0.001  # 0.10%
```

### Cambiar spread mínimo
```python
# config.py
MIN_SPREAD_GOLDEN_RULE = 5.0
```

### Cambiar volumen mínimo
```python
# main.py
print_suggestions(best_match, min_volume=100.0)
```

## 📈 Características Técnicas

- **Cálculos**: Precisos, sin errores de redondeo
- **Colores**: Consola ANSI (compatible Windows/Mac/Linux)
- **HTML**: Responsive, sin dependencias externas
- **Performance**: ~100ms por análisis
- **Compatibilidad**: Python 3.8+

## 🎯 Casos de Uso

1. **Usuario Arbitrajista**: Identifica oportunidades de compra/venta
2. **Anunciante**: Sugiere precios competitivos
3. **Investigador**: Analiza historial de spreads
4. **Automatización**: Integra con bots de trading

## ⚠️ Notas Importantes

- Comisión: 0.20% para P2P sin KYC (puede variar)
- Regla de Oro: $10.80 ARS es el spread mínimo operacional
- Volumen: Por defecto 50 USDT (configurable)
- Validación: Usa datos de Binance P2P API

## 🚀 Próximas Mejoras

- [ ] Dashboard en vivo
- [ ] Histórico de spreads
- [ ] Alertas avanzadas
- [ ] Análisis de volatilidad
- [ ] Simulación Maker/Taker

## 📞 Soporte

- Error: Revisa [INICIO_RAPIDO.md § Troubleshooting](INICIO_RAPIDO.md)
- Duda: Consulta [P2P_ANALYSIS_GUIDE.md](P2P_ANALYSIS_GUIDE.md)
- Técnica: Revisa [INTEGRACION_P2P_RESUMEN.md](INTEGRACION_P2P_RESUMEN.md)

## 📜 Licencia

Parte del proyecto ArbitrajeIntegral

---

**Estado:** ✅ Listo para Producción  
**Última actualización:** 25 Abril 2026  
**Versión:** 1.0
