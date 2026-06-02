# Guía de Análisis P2P - Funcionalidades Integradas

## Descripción General

Se han integrado dos nuevos módulos para análisis avanzado de oportunidades de arbitraje P2P en Binance:

1. **`analytics/p2p_analysis.py`** - Módulo de cálculos y análisis
2. **`analytics/p2p_html_report.py`** - Generador de reportes HTML

## Configuración

Las siguientes constantes se han añadido a `config.py`:

```python
# Comisión Binance P2P sin KYC (0.20%)
BINANCE_P2P_COMMISSION_RATE = 0.002

# Regla de Oro - Spread mínimo para operar
MIN_SPREAD_GOLDEN_RULE = 10.80  # ARS

# Delta para sugerencias de precios competitivos
AD_PRICE_DELTA = 0.50  # ARS
```

## Módulo `p2p_analysis.py`

### Funciones de Cálculo

#### `calculate_commission_impact(usdt_cantidad, price_ars)`
Calcula el impacto de la comisión del 0.20% en ARS y USDT.

```python
from analytics.p2p_analysis import calculate_commission_impact

comision = calculate_commission_impact(100.0, 1000.0)
# {
#   'comision_usdt': 0.2,
#   'comision_ars': 200.0
# }
```

#### `get_real_buy_cost(precio_nominal, usdt_cantidad=1.0)`
Retorna el precio real de compra después de aplicar comisiones. El precio sube porque el comprador paga comisión adicional.

#### `get_real_sell_price(precio_nominal, usdt_cantidad=1.0)`
Retorna el precio neto de venta después de aplicar comisiones. El precio baja porque el vendedor pierde comisión.

#### `find_best_match(buy_ads, sell_ads)`
Analiza todos los anuncios y retorna un diccionario con:
- `best_buy` / `best_sell` - Mejores oportunidades
- `spread_bruto` / `spread_neto` - Diferenciales antes/después comisiones
- `comision_compra` / `comision_venta` - Comisiones por operación
- `comision_total_ciclo` - Comisión total del ciclo completo
- `cumple_regla_oro` - Booleano si el spread >= $10.80 ARS

```python
from analytics.p2p_analysis import find_best_match

match = find_best_match(buy_ads, sell_ads)
if match and match['cumple_regla_oro']:
    ganancia = match['spread_neto']  # Ganancia por USDT
    print(f"Ganancia neta: ${ganancia:.2f} por USDT")
```

#### `suggest_ad_price(best_price, action, delta=None)`
Sugiere un precio competitivo para anuncio propio.
- `action="sell"` → resta delta (vender más barato)
- `action="buy"` → suma delta (comprar más caro)

```python
mejor_vendedor = 1000.0
mi_precio = suggest_ad_price(mejor_vendedor, "sell")  # 999.50
```

#### `orderable_usdt_range(ad)`
Convierte los límites ARS de un anuncio a USDT ordenables.

```python
ad = {
    "price": 1000.0,
    "min_limit": 50000.0,
    "max_limit": 500000.0
}
min_usdt, max_usdt = orderable_usdt_range(ad)
# (50.0, 500.0) USDT
```

### Funciones de Visualización (Consola)

#### `print_suggestions(best_match, threshold=10.80, min_volume=50.0)`
Imprime análisis completo en consola con colores ANSI:
- Precios nominales y spreads brutos
- Impacto de comisiones (0.20%)
- Precios reales tras comisiones
- Regla de Oro y validación
- Sugerencias de arbitraje (ROL USUARIO)
- Simulación de anuncio propio (ROL ANUNCIANTE)
- Rango de órdenes posibles

```python
from analytics.p2p_analysis import print_suggestions, find_best_match

match = find_best_match(buy_ads, sell_ads)
print_suggestions(match, min_volume=50.0)
```

#### `print_market_overview(buy_ads, sell_ads, top_n=5)`
Muestra resumen del mercado con top N mejores anuncios de compra/venta.

### Funciones de Formateo

- `format_price(value)` → `"$1,000.00"`
- `format_usdt(value)` → `"100.00 USDT"`

## Módulo `p2p_html_report.py`

### Función Principal

#### `generate_html_report(buy_ads, sell_ads, min_volume=50.0, output_file=None)`

Genera reporte HTML completo con:
- **Resumen del Mercado**: Mejores precios de compra/venta
- **Análisis de Comisiones**: Tabla con precios nominales vs reales
- **Spreads**: Visualización gráfica de impacto de comisiones
- **Regla de Oro**: Validación y estado
- **Sugerencias de Arbitraje**: Condiciones y ganancia estimada
- **Simulación de Anuncio Propio**: Precios sugeridos con competencia
- **Top 5 Anuncios**: Tablas de mejores ofertas

```python
from analytics.p2p_html_report import generate_html_report

html = generate_html_report(
    buy_ads, sell_ads,
    output_file="dashboard/reporte.html"
)
```

### Estilos HTML

- **Tema**: Fondo gradiente oscuro azul/negro
- **Colores**: Cyan (#00d4ff) para títulos, verde para OK, naranja para warning, rojo para error
- **Layout**: Responsivo (1 col en móvil, 2 cols en desktop)
- **Tipografía**: Fuentes monoespaciadas para precios

## Integración en `main.py`

El script principal ahora:

1. **Scraping**: Obtiene anuncios de 5 primeras páginas
2. **Análisis P2P**: Calcula spreads y comisiones
3. **Visualización Consola**: Imprime análisis con colores ANSI
4. **Generación HTML**: Crea reporte con timestamp
5. **Alertas**: Envía notificaciones si hay oportunidades

```python
from analytics.p2p_analysis import find_best_match, print_suggestions, print_market_overview
from analytics.p2p_html_report import generate_html_report

# Después de fetch_ads()
if safe_buy and safe_sell:
    print_market_overview(safe_buy, safe_sell)
    best_match = find_best_match(safe_buy, safe_sell)
    print_suggestions(best_match)
    generate_html_report(safe_buy, safe_sell, output_file="dashboard/report.html")
```

## Validación de Datos

Los anuncios esperan los siguientes campos:

```python
ad = {
    "price": float,                    # Precio nominal en ARS
    "advertiser_name": str,           # Nombre del anunciante
    "available": float,               # USDT disponibles
    "min_limit": float,               # Límite mínimo en ARS
    "max_limit": float,               # Límite máximo en ARS
}
```

## Ejemplo de Uso Completo

```python
from analytics.p2p_analysis import (
    find_best_match,
    print_suggestions,
    print_market_overview,
    calculate_commission_impact,
)
from analytics.p2p_html_report import generate_html_report

# Datos de anuncios (ejemplo)
buy_ads = [...]  # Anunciantes que compran USDT
sell_ads = [...] # Anunciantes que venden USDT

# 1. Mostrar resumen del mercado
print_market_overview(buy_ads, sell_ads, top_n=3)

# 2. Encontrar mejor oportunidad
match = find_best_match(buy_ads, sell_ads)

# 3. Mostrar análisis detallado
if match:
    print_suggestions(match, min_volume=50.0)
    
    # 4. Generar reporte HTML
    generate_html_report(
        buy_ads, sell_ads,
        output_file="dashboard/analisis.html"
    )
    
    # 5. Tomar decisión
    if match['cumple_regla_oro'] and match['best_buy']['available'] >= 50:
        print(f"✓ Operación rentable: ${match['spread_neto']:.2f} por USDT")
    else:
        print("✗ No cumple condiciones mínimas")
```

## Cálculos Clave

### Comisión (0.20% P2P sin KYC)
```
comisión_usdt = cantidad_usdt * 0.002
comisión_ars = comisión_usdt * precio_ars
```

### Precio Real de Compra
```
costo_total = precio_nominal * cantidad + comisión_ars
usdt_neto = cantidad - comisión_usdt
precio_real = costo_total / usdt_neto
```

### Precio Neto de Venta
```
ingreso_total = precio_nominal * cantidad
neto_recibido = ingreso_total - comisión_ars
precio_neto = neto_recibido / cantidad
```

### Spread Neto
```
spread_neto = precio_neto_venta - precio_real_compra
```

### Regla de Oro
```
operación_válida = spread_bruto >= 10.80 ARS AND volumen >= 50 USDT
```

## Pruebas

Se incluye `test_p2p_analysis.py` con 8 casos de prueba:

```bash
python test_p2p_analysis.py
```

Verifica:
- Cálculos de comisiones
- Precios reales (compra/venta)
- Búsqueda de mejor match
- Sugerencias de precio
- Rangos de órdenes
- Visualización consola
- Generación HTML

## Notas Técnicas

- **Comisión fija**: 0.20% (sin KYC) para todos los cálculos
- **Spread mínimo**: $10.80 ARS (Regla de Oro - Academia de Arbitraje)
- **Delta competencia**: $0.50 ARS para sugerencias de anuncios propios
- **Volumen mínimo operado**: 50 USDT (configurable)
- **Colores ANSI**: Verde (OK), Rojo (error), Cyan (títulos), Amarillo (warning)
- **HTML responsive**: Adaptable a móvil, tablet y desktop

## Mejoras Futuras

Posibles extensiones:
- [ ] Integración con histórico de precios en BigQuery
- [ ] Alertas por email/webhook cuando hay oportunidades
- [ ] Dashboard en vivo con WebSockets
- [ ] Análisis de volatilidad y tendencias
- [ ] Simulación de estrategias Maker/Taker
- [ ] Export a CSV/JSON de análisis histórico
