"""
Análisis de P2P Binance: Comisiones, Spreads y Sugerencias de Arbitraje.

Este módulo reutiliza la lógica de binance_p2p_monitor.py para analizar
oportunidades de arbitraje y sugerir precios competitivos para anuncios propios.
"""

from typing import Optional
from config import (
    BINANCE_P2P_COMMISSION_RATE,
    MIN_SPREAD_GOLDEN_RULE,
    AD_PRICE_DELTA,
)


# ============================================================================
# ANSI Color Codes
# ============================================================================

class C:
    """Códigos ANSI para colores en terminal."""
    RESET = "\033[0m"
    BOLD = "\033[1m"
    DIM = "\033[2m"
    GREEN = "\033[92m"
    YELLOW = "\033[93m"
    RED = "\033[91m"
    CYAN = "\033[96m"


def color(text: str, *codes) -> str:
    """Aplica códigos ANSI de color al texto."""
    return "".join(codes) + str(text) + C.RESET if codes else str(text)


# ============================================================================
# Funciones de Cálculo de Comisiones
# ============================================================================

def calculate_commission_impact(usdt_cantidad: float, price_ars: float) -> dict:
    """
    Calcula impacto de comisión Binance 0.20% sin KYC.

    Args:
        usdt_cantidad: Cantidad de USDT
        price_ars: Precio en ARS por USDT

    Returns:
        Dict con comision_usdt y comision_ars
    """
    comision_usdt = usdt_cantidad * BINANCE_P2P_COMMISSION_RATE
    comision_ars = comision_usdt * price_ars
    return {"comision_usdt": comision_usdt, "comision_ars": comision_ars}


def get_real_buy_cost(precio_nominal: float, usdt_cantidad: float = 1.0) -> float:
    """
    Calcula precio real después de comisión en compra.

    Cuando compras USDT, pagas comisión adicional sobre el monto total.

    Args:
        precio_nominal: Precio nominal por USDT en ARS
        usdt_cantidad: Cantidad de USDT a comprar (default 1.0)

    Returns:
        Precio real (ARS por USDT neto recibido)
    """
    comision = calculate_commission_impact(usdt_cantidad, precio_nominal)
    costo_total = precio_nominal * usdt_cantidad + comision["comision_ars"]
    usdt_neto = usdt_cantidad - comision["comision_usdt"]
    return costo_total / usdt_neto if usdt_neto > 0 else precio_nominal


def get_real_sell_price(precio_nominal: float, usdt_cantidad: float = 1.0) -> float:
    """
    Calcula precio neto después de comisión en venta.

    Cuando vendes USDT, la comisión se descuenta del ingreso.

    Args:
        precio_nominal: Precio nominal por USDT en ARS
        usdt_cantidad: Cantidad de USDT a vender (default 1.0)

    Returns:
        Precio neto (ARS por USDT después de comisión)
    """
    comision = calculate_commission_impact(usdt_cantidad, precio_nominal)
    ingreso_total = precio_nominal * usdt_cantidad
    neto_recibido = ingreso_total - comision["comision_ars"]
    return neto_recibido / usdt_cantidad


# ============================================================================
# Funciones de Búsqueda y Análisis
# ============================================================================

def find_best_match(buy_ads: list[dict], sell_ads: list[dict]) -> Optional[dict]:
    """
    Encuentra mejor oportunidad de arbitraje analizando spreads.

    buy_ads: Anuncios donde anunciantes compran USDT (precio más alto = mejor venta)
    sell_ads: Anuncios donde anunciantes venden USDT (precio más bajo = mejor compra)

    Returns:
        Dict con análisis completo o None si no hay datos
    """
    # Filtrar anuncios con precio válido
    buy_valid = [ad for ad in buy_ads if ad.get("price") is not None]
    sell_valid = [ad for ad in sell_ads if ad.get("price") is not None]

    if not buy_valid or not sell_valid:
        return None

    best_buy = max(buy_valid, key=lambda x: x["price"])
    best_sell = min(sell_valid, key=lambda x: x["price"])

    # Spreads brutos
    spread_bruto = best_buy["price"] - best_sell["price"]
    spread_pct_bruto = (
        (spread_bruto / best_sell["price"] * 100) if best_sell["price"] else None
    )

    # Precios reales tras comisión
    costo_real_compra = get_real_buy_cost(best_sell["price"])
    neto_real_venta = get_real_sell_price(best_buy["price"])

    # Spreads netos
    spread_neto = neto_real_venta - costo_real_compra
    spread_neto_pct = (
        (spread_neto / costo_real_compra * 100) if costo_real_compra > 0 else 0
    )

    # Comisiones por ciclo
    comision_compra = calculate_commission_impact(1.0, best_sell["price"])[
        "comision_ars"
    ]
    comision_venta = calculate_commission_impact(1.0, best_buy["price"])[
        "comision_ars"
    ]
    comision_total_ciclo = comision_compra + comision_venta

    cumple_regla_oro = spread_bruto >= MIN_SPREAD_GOLDEN_RULE

    return {
        "best_buy": best_buy,
        "best_sell": best_sell,
        "spread_bruto": spread_bruto,
        "spread_pct_bruto": spread_pct_bruto,
        "spread_neto": spread_neto,
        "spread_neto_pct": spread_neto_pct,
        "costo_real_compra": costo_real_compra,
        "neto_real_venta": neto_real_venta,
        "comision_compra": comision_compra,
        "comision_venta": comision_venta,
        "comision_total_ciclo": comision_total_ciclo,
        "cumple_regla_oro": cumple_regla_oro,
    }


def suggest_ad_price(best_price: float, action: str, delta: float = None) -> float:
    """
    Sugiere precio competitivo para anuncio propio.

    Si acción es "sell", resta delta (vender más barato que competencia).
    Si acción es "buy", suma delta (comprar más caro que competencia).

    Args:
        best_price: Precio del mejor anunciante competidor
        action: "sell" o "buy"
        delta: Margen en ARS (default AD_PRICE_DELTA)

    Returns:
        Precio sugerido
    """
    if delta is None:
        delta = AD_PRICE_DELTA
    if action == "sell":
        return max(best_price - delta, 0.01)
    return best_price + delta


def orderable_usdt_range(ad: dict) -> tuple[Optional[float], Optional[float]]:
    """
    Calcula rango de USDT ordenable según límites de ARS del anuncio.

    Args:
        ad: Anuncio con límites min/max en ARS

    Returns:
        Tupla (min_usdt, max_usdt) o (None, None)
    """
    precio = ad.get("price")
    limite_min = ad.get("min_limit")
    limite_max = ad.get("max_limit")

    if (
        precio is not None
        and limite_min is not None
        and limite_max is not None
    ):
        return limite_min / precio, limite_max / precio
    return None, None


# ============================================================================
# Funciones de Formateo
# ============================================================================

def format_price(value: Optional[float]) -> str:
    """Formatea valor como precio en ARS con $ y decimales."""
    return f"${value:,.2f}" if value is not None else "N/D"


def format_usdt(value: Optional[float]) -> str:
    """Formatea valor como cantidad en USDT."""
    return f"{value:,.2f} USDT" if value is not None else "N/D"


# ============================================================================
# Funciones de Visualización (Consola)
# ============================================================================

def print_append_section(title: str):
    """Imprime encabezado de sección con formato cyan y separador."""
    print(color(f"\n  {title}", C.CYAN, C.BOLD))
    print(color("  " + "-" * 68, C.DIM))


def print_suggestions(
    best_match: Optional[dict], threshold: float = 10.80, min_volume: float = 50.0
):
    """
    Imprime análisis completo de comisiones y sugerencias de arbitraje.

    Args:
        best_match: Dict retornado por find_best_match() o None
        threshold: Spread mínimo requerido (default MIN_SPREAD_GOLDEN_RULE)
        min_volume: Volumen mínimo de USDT para operar
    """
    print_append_section("ANÁLISIS DE COMISIONES Y SUGERENCIAS")

    if best_match is None:
        print(
            color(
                "  No hay datos suficientes para generar sugerencias.", C.YELLOW
            )
        )
        return

    best_buy = best_match["best_buy"]
    best_sell = best_match["best_sell"]

    # Precios nominales
    print(color("  PRECIOS NOMINALES", C.DIM))
    print(f"  Mejor para comprar (SELL): {format_price(best_sell['price'])}")
    print(f"  Mejor para vender  (BUY):  {format_price(best_buy['price'])}")
    print(
        color(
            f"  Spread bruto: {format_price(best_match['spread_bruto'])} ({best_match['spread_pct_bruto']:.3f}%)",
            C.BOLD,
        )
    )

    # Impacto de comisiones
    print(color("\n  IMPACTO DE COMISIÓN (0.20% Binance P2P - sin KYC)", C.DIM))
    print(f"  Comisión en compra:  {format_price(best_match['comision_compra'])} ARS")
    print(f"  Comisión en venta:   {format_price(best_match['comision_venta'])} ARS")
    comision_pct_spread = (
        (best_match["comision_total_ciclo"] / best_match["spread_bruto"] * 100)
        if best_match["spread_bruto"] > 0
        else 0
    )
    print(
        color(
            f"  Total ciclo: {format_price(best_match['comision_total_ciclo'])} ARS ({comision_pct_spread:.1f}% del spread)",
            C.RED,
            C.BOLD,
        )
    )

    # Precios reales tras comisiones
    print(color("\n  PRECIOS REALES (tras comisiones)", C.DIM))
    print(f"  Costo real de compra: {format_price(best_match['costo_real_compra'])}")
    print(f"  Neto real de venta:   {format_price(best_match['neto_real_venta'])}")
    print(
        color(
            f"  Spread neto: {format_price(best_match['spread_neto'])} ({best_match['spread_neto_pct']:.3f}%)",
            C.BOLD,
        )
    )

    # Regla de Oro
    print(color("\n  REGLA DE ORO (Academia de Arbitraje)", C.BOLD))
    print(f"  Spread mínimo requerido: ${threshold:.2f} ARS")
    print(
        f"  Spread actual:           {format_price(best_match['spread_bruto'])} "
        + (
            color("OK", C.GREEN)
            if best_match["cumple_regla_oro"]
            else color("INSUFICIENTE", C.RED)
        )
    )

    # Sugerencia de arbitraje
    puede_operar = (
        best_match["cumple_regla_oro"]
        and best_buy.get("available") is not None
        and best_buy.get("available") >= min_volume
    )

    print()
    if puede_operar:
        print(
            color(
                "  SUGERENCIA DE ARBITRAJE (ROL USUARIO):", C.GREEN, C.BOLD
            )
        )
        print(
            color(
                f"  Comprar USDT al mejor vendedor: {best_sell.get('advertiser_name', 'N/A')}",
                C.BOLD,
            )
        )
        print(
            f"    Precio: {format_price(best_sell['price'])} | "
            f"Disponible: {format_usdt(best_sell.get('available'))} | "
            f"Límite: {format_price(best_sell.get('min_limit'))} - {format_price(best_sell.get('max_limit'))}"
        )
        print(
            color(
                f"  Vender USDT al mejor comprador: {best_buy.get('advertiser_name', 'N/A')}",
                C.BOLD,
            )
        )
        print(
            f"    Precio: {format_price(best_buy['price'])} | "
            f"Disponible: {format_usdt(best_buy.get('available'))} | "
            f"Límite: {format_price(best_buy.get('min_limit'))} - {format_price(best_buy.get('max_limit'))}"
        )
        print(
            color(
                f"  Ganancia neta estimada: {format_price(best_match['spread_neto'])} por USDT",
                C.GREEN,
            )
        )
    else:
        print(color("  NO OPERAR:", C.RED))
        if not best_match["cumple_regla_oro"]:
            diferencia = threshold - best_match["spread_bruto"]
            print(
                color(
                    f"  Falta ${diferencia:.2f} de spread mínimo",
                    C.YELLOW,
                )
            )
        if (
            best_buy.get("available") is None
            or best_buy.get("available") < min_volume
        ):
            print(
                color(
                    f"  Volumen insuficiente (< {min_volume:.0f} USDT)",
                    C.YELLOW,
                )
            )

    # Simulación de anuncio propio
    print_append_section("SIMULACIÓN DE ANUNCIO PROPIO (ROL ANUNCIANTE)")
    sell_recommended = suggest_ad_price(best_sell["price"], "sell")
    buy_recommended = suggest_ad_price(best_buy["price"], "buy")

    print(color("  Si querés vender USDT como anunciante:", C.BOLD))
    print(
        f"    Compite con: {best_sell.get('advertiser_name', 'N/A')} @ {format_price(best_sell['price'])}"
    )
    print(f"    Precio sugerido: {format_price(sell_recommended)} ARS")

    print(color("\n  Si querés comprar USDT como anunciante:", C.BOLD))
    print(
        f"    Compite con: {best_buy.get('advertiser_name', 'N/A')} @ {format_price(best_buy['price'])}"
    )
    print(f"    Precio sugerido: {format_price(buy_recommended)} ARS")

    # Rangos de órdenes
    min_usdt_sell, max_usdt_sell = orderable_usdt_range(best_sell)
    min_usdt_buy, max_usdt_buy = orderable_usdt_range(best_buy)
    if min_usdt_sell or min_usdt_buy:
        print(color("\n  Rango de órdenes posibles:", C.DIM))
        if min_usdt_sell is not None and max_usdt_sell is not None:
            print(f"    Vender: {min_usdt_sell:.2f} - {max_usdt_sell:.2f} USDT")
        if min_usdt_buy is not None and max_usdt_buy is not None:
            print(f"    Comprar: {min_usdt_buy:.2f} - {max_usdt_buy:.2f} USDT")


def print_market_overview(buy_ads: list[dict], sell_ads: list[dict], top_n: int = 5):
    """
    Imprime resumen del mercado con mejores anuncios de compra/venta.

    Args:
        buy_ads: Anuncios donde compran USDT
        sell_ads: Anuncios donde venden USDT
        top_n: Cantidad de top anuncios a mostrar
    """
    print_append_section("MERCADO P2P USDT/ARS")

    # Mejores para vender (sell_ads - precios más bajos)
    print(color("  VENDER USDT (mejores precios para comprar):", C.BOLD))
    sell_sorted = sorted(
        [ad for ad in sell_ads if ad.get("price") is not None],
        key=lambda x: x["price"],
    )[:top_n]

    if sell_sorted:
        for i, ad in enumerate(sell_sorted, 1):
            print(
                f"    {i}. {ad.get('advertiser_name', 'N/A'):<20} "
                f"{format_price(ad['price']):<14} "
                f"({format_usdt(ad.get('available'))})"
            )
    else:
        print("    No hay datos")

    # Mejores para comprar (buy_ads - precios más altos)
    print(color("\n  COMPRAR USDT (mejores precios para vender):", C.BOLD))
    buy_sorted = sorted(
        [ad for ad in buy_ads if ad.get("price") is not None],
        key=lambda x: x["price"],
        reverse=True,
    )[:top_n]

    if buy_sorted:
        for i, ad in enumerate(buy_sorted, 1):
            print(
                f"    {i}. {ad.get('advertiser_name', 'N/A'):<20} "
                f"{format_price(ad['price']):<14} "
                f"({format_usdt(ad.get('available'))})"
            )
    else:
        print("    No hay datos")
