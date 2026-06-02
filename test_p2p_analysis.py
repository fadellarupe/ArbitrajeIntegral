#!/usr/bin/env python3
"""
Script de prueba para verificar funcionalidades de análisis P2P.
"""

import sys
import os

# Asegurar que el proyecto esté en el path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from analytics.p2p_analysis import (
    calculate_commission_impact,
    get_real_buy_cost,
    get_real_sell_price,
    find_best_match,
    suggest_ad_price,
    orderable_usdt_range,
    format_price,
    format_usdt,
    print_suggestions,
    print_market_overview,
)
from analytics.p2p_html_report import generate_html_report
from config import BINANCE_P2P_COMMISSION_RATE, MIN_SPREAD_GOLDEN_RULE, AD_PRICE_DELTA

print("=" * 70)
print("PRUEBA DE MÓDULO P2P ANALYSIS")
print("=" * 70)

# Test 1: Cálculo de comisiones
print("\n[TEST 1] Cálculo de comisiones (0.20%)")
print("-" * 70)
comision = calculate_commission_impact(100.0, 1000.0)
print(f"Comisión en 100 USDT a 1000 ARS/USDT:")
print(f"  - USDT de comisión: {comision['comision_usdt']:.4f}")
print(f"  - ARS de comisión: {format_price(comision['comision_ars'])}")
assert comision['comision_usdt'] == 0.2, "Error en cálculo de comisión USDT"
assert comision['comision_ars'] == 200.0, "Error en cálculo de comisión ARS"
print("✓ PASS")

# Test 2: Precio real de compra
print("\n[TEST 2] Precio real de compra (tras comisión)")
print("-" * 70)
precio_nominal = 1000.0
precio_real = get_real_buy_cost(precio_nominal, 100.0)
print(f"Comprar 100 USDT a {format_price(precio_nominal)}:")
print(f"  - Precio nominal: {format_price(precio_nominal)}")
print(f"  - Precio real: {format_price(precio_real)}")
print(f"  - Diferencia: {format_price(precio_real - precio_nominal)}")
assert precio_real > precio_nominal, "Precio real debe ser mayor (comisión suma)"
print("✓ PASS")

# Test 3: Precio real de venta
print("\n[TEST 3] Precio neto de venta (tras comisión)")
print("-" * 70)
precio_nominal = 1000.0
precio_neto = get_real_sell_price(precio_nominal, 100.0)
print(f"Vender 100 USDT a {format_price(precio_nominal)}:")
print(f"  - Precio nominal: {format_price(precio_nominal)}")
print(f"  - Precio neto: {format_price(precio_neto)}")
print(f"  - Diferencia: {format_price(precio_nominal - precio_neto)}")
assert precio_neto < precio_nominal, "Precio neto debe ser menor (comisión resta)"
print("✓ PASS")

# Test 4: Búsqueda de mejor match
print("\n[TEST 4] Búsqueda de mejor oportunidad de arbitraje")
print("-" * 70)

# Datos de prueba
test_buy_ads = [
    {
        "price": 1010.0,
        "advertiser_name": "Comprador A",
        "available": 100.0,
        "min_limit": 50000.0,
        "max_limit": 500000.0,
    },
    {
        "price": 1000.0,
        "advertiser_name": "Comprador B",
        "available": 200.0,
        "min_limit": 50000.0,
        "max_limit": 500000.0,
    },
]

test_sell_ads = [
    {
        "price": 990.0,
        "advertiser_name": "Vendedor A",
        "available": 150.0,
        "min_limit": 50000.0,
        "max_limit": 500000.0,
    },
    {
        "price": 980.0,
        "advertiser_name": "Vendedor B",
        "available": 300.0,
        "min_limit": 50000.0,
        "max_limit": 500000.0,
    },
]

match = find_best_match(test_buy_ads, test_sell_ads)
assert match is not None, "No se encontró match"
assert match["best_buy"]["price"] == 1010.0, "Best buy incorrecto"
assert match["best_sell"]["price"] == 980.0, "Best sell incorrecto"
assert match["spread_bruto"] == 30.0, "Spread bruto incorrecto"

print(f"Mejor comprador: {match['best_buy']['advertiser_name']} @ {format_price(match['best_buy']['price'])}")
print(f"Mejor vendedor: {match['best_sell']['advertiser_name']} @ {format_price(match['best_sell']['price'])}")
print(f"Spread bruto: {format_price(match['spread_bruto'])} ({match['spread_pct_bruto']:.3f}%)")
print(f"Spread neto: {format_price(match['spread_neto'])} ({match['spread_neto_pct']:.3f}%)")
print(f"Comisión total ciclo: {format_price(match['comision_total_ciclo'])}")
print(f"Cumple Regla de Oro: {'SÍ' if match['cumple_regla_oro'] else 'NO'}")
print("✓ PASS")

# Test 5: Sugerencia de precio
print("\n[TEST 5] Sugerencia de precios competitivos")
print("-" * 70)
best_seller = 1000.0
best_buyer = 1010.0
sell_suggested = suggest_ad_price(best_seller, "sell")
buy_suggested = suggest_ad_price(best_buyer, "buy")

print(f"Mejor vendedor actual: {format_price(best_seller)}")
print(f"  Tu precio sugerido (vender más barato): {format_price(sell_suggested)}")
print(f"  Delta: -{AD_PRICE_DELTA:.2f} ARS")

print(f"\nMejor comprador actual: {format_price(best_buyer)}")
print(f"  Tu precio sugerido (comprar más caro): {format_price(buy_suggested)}")
print(f"  Delta: +{AD_PRICE_DELTA:.2f} ARS")

assert sell_suggested == best_seller - AD_PRICE_DELTA, "Precio sugerido venta incorrecto"
assert buy_suggested == best_buyer + AD_PRICE_DELTA, "Precio sugerido compra incorrecto"
print("✓ PASS")

# Test 6: Rango de órdenes
print("\n[TEST 6] Rango de órdenes ordenables")
print("-" * 70)
ad = {
    "price": 1000.0,
    "min_limit": 50000.0,
    "max_limit": 500000.0,
}
min_usdt, max_usdt = orderable_usdt_range(ad)
print(f"Precio: {format_price(ad['price'])}")
print(f"Límite min ARS: {format_price(ad['min_limit'])}")
print(f"Límite max ARS: {format_price(ad['max_limit'])}")
print(f"USDT ordenable: {format_usdt(min_usdt)} - {format_usdt(max_usdt)}")
assert min_usdt == 50.0, "Min USDT incorrecto"
assert max_usdt == 500.0, "Max USDT incorrecto"
print("✓ PASS")

# Test 7: Visualización en consola
print("\n[TEST 7] Visualización en consola")
print("-" * 70)
print("\nMercado Overview:")
print_market_overview(test_buy_ads, test_sell_ads, top_n=2)

print("\n\nAnálisis de Comisiones y Sugerencias:")
print_suggestions(match, min_volume=50.0)

# Test 8: Generación de HTML
print("\n\n[TEST 8] Generación de reporte HTML")
print("-" * 70)
html_content = generate_html_report(
    test_buy_ads, test_sell_ads, output_file=None
)
print(f"HTML generado: {len(html_content)} caracteres")
assert len(html_content) > 1000, "HTML muy corto"
assert "<!DOCTYPE html>" in html_content, "HTML no contiene DOCTYPE"
assert "Análisis P2P" in html_content, "HTML no contiene título"
print("✓ PASS")

print("\n" + "=" * 70)
print("TODAS LAS PRUEBAS PASARON ✓")
print("=" * 70)
