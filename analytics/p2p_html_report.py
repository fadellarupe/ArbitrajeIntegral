"""
Generador de reportes HTML para análisis P2P de Binance.

Crea visualizaciones HTML con análisis de comisiones, spreads, y sugerencias
de arbitraje con estilos responsivos y paleta de colores.
"""

from datetime import datetime
from typing import Optional
from analytics.p2p_analysis import (
    find_best_match,
    calculate_commission_impact,
    get_real_buy_cost,
    get_real_sell_price,
    orderable_usdt_range,
    suggest_ad_price,
)
from config import MIN_SPREAD_GOLDEN_RULE, AD_PRICE_DELTA


def format_price(value: Optional[float]) -> str:
    """Formatea valor como precio en ARS."""
    return f"${value:,.2f}" if value is not None else "N/D"


def format_usdt(value: Optional[float]) -> str:
    """Formatea valor como cantidad en USDT."""
    return f"{value:,.2f}" if value is not None else "N/D"


def html_escape(text: str) -> str:
    """Escapa caracteres especiales para HTML."""
    return (
        str(text)
        .replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
        .replace("'", "&#39;")
    )


def get_spread_status_class(cumple_regla_oro: bool) -> str:
    """Retorna clase CSS para estado de spread."""
    return "status-ok" if cumple_regla_oro else "status-warning"


def get_spread_status_text(cumple_regla_oro: bool) -> str:
    """Retorna texto de estado de spread."""
    return "✓ OK" if cumple_regla_oro else "✗ INSUFICIENTE"


def generate_html_report(
    buy_ads: list[dict],
    sell_ads: list[dict],
    min_volume: float = 50.0,
    output_file: Optional[str] = None,
) -> str:
    """
    Genera reporte HTML completo con análisis P2P.

    Args:
        buy_ads: Anuncios donde compran USDT
        sell_ads: Anuncios donde venden USDT
        min_volume: Volumen mínimo para operar
        output_file: Ruta donde guardar HTML (si None, retorna string)

    Returns:
        String con HTML generado
    """
    best_match = find_best_match(buy_ads, sell_ads)
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    html = f"""<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Análisis P2P USDT/ARS - {timestamp}</title>
    <style>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}
        body {{
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%);
            color: #e0e0e0;
            padding: 20px;
            min-height: 100vh;
        }}
        .container {{
            max-width: 1200px;
            margin: 0 auto;
        }}
        header {{
            text-align: center;
            margin-bottom: 30px;
            border-bottom: 2px solid #00d4ff;
            padding-bottom: 20px;
        }}
        header h1 {{
            color: #00d4ff;
            font-size: 2.2em;
            margin-bottom: 10px;
            text-shadow: 0 0 10px rgba(0, 212, 255, 0.3);
        }}
        header .timestamp {{
            color: #888;
            font-size: 0.9em;
        }}
        .section {{
            background: rgba(30, 40, 60, 0.8);
            border-left: 4px solid #00d4ff;
            padding: 20px;
            margin-bottom: 20px;
            border-radius: 4px;
            box-shadow: 0 4px 6px rgba(0, 0, 0, 0.3);
        }}
        .section h2 {{
            color: #00d4ff;
            font-size: 1.4em;
            margin-bottom: 15px;
            text-transform: uppercase;
            letter-spacing: 1px;
        }}
        .metric-row {{
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 15px;
            margin-bottom: 15px;
        }}
        @media (max-width: 768px) {{
            .metric-row {{
                grid-template-columns: 1fr;
            }}
        }}
        .metric {{
            background: rgba(0, 0, 0, 0.3);
            padding: 12px;
            border-radius: 3px;
            border-left: 3px solid #00d4ff;
        }}
        .metric .label {{
            font-size: 0.85em;
            color: #888;
            text-transform: uppercase;
            letter-spacing: 0.5px;
            margin-bottom: 5px;
        }}
        .metric .value {{
            font-size: 1.3em;
            font-weight: bold;
            color: #fff;
            font-family: 'Courier New', monospace;
        }}
        .status-ok {{
            color: #4caf50;
        }}
        .status-warning {{
            color: #ff9800;
        }}
        .status-error {{
            color: #f44336;
        }}
        table {{
            width: 100%;
            border-collapse: collapse;
            margin-bottom: 15px;
        }}
        table th {{
            background: rgba(0, 212, 255, 0.1);
            color: #00d4ff;
            padding: 12px;
            text-align: left;
            font-size: 0.9em;
            text-transform: uppercase;
            letter-spacing: 0.5px;
            border-bottom: 2px solid #00d4ff;
        }}
        table td {{
            padding: 12px;
            border-bottom: 1px solid #333;
            font-size: 0.95em;
        }}
        table tr:hover {{
            background: rgba(0, 212, 255, 0.05);
        }}
        .warning {{
            background: rgba(255, 152, 0, 0.1);
            border-left: 3px solid #ff9800;
            padding: 12px;
            border-radius: 3px;
            color: #ffb74d;
            margin: 10px 0;
        }}
        .success {{
            background: rgba(76, 175, 80, 0.1);
            border-left: 3px solid #4caf50;
            padding: 12px;
            border-radius: 3px;
            color: #81c784;
            margin: 10px 0;
        }}
        .error {{
            background: rgba(244, 67, 54, 0.1);
            border-left: 3px solid #f44336;
            padding: 12px;
            border-radius: 3px;
            color: #ef5350;
            margin: 10px 0;
        }}
        .ad-card {{
            background: rgba(0, 0, 0, 0.3);
            padding: 15px;
            border-radius: 3px;
            margin-bottom: 10px;
            border-left: 3px solid #00d4ff;
        }}
        .ad-card .advertiser {{
            color: #00d4ff;
            font-weight: bold;
            font-size: 1.1em;
            margin-bottom: 5px;
        }}
        .ad-card .price {{
            font-size: 1.2em;
            color: #fff;
            font-family: 'Courier New', monospace;
            margin-bottom: 5px;
        }}
        .ad-card .details {{
            font-size: 0.85em;
            color: #888;
            margin-top: 8px;
        }}
        .button {{
            display: inline-block;
            background: #00d4ff;
            color: #000;
            padding: 8px 12px;
            border-radius: 3px;
            text-decoration: none;
            font-size: 0.85em;
            font-weight: bold;
            margin-right: 8px;
            margin-top: 8px;
            transition: all 0.3s;
        }}
        .button:hover {{
            background: #00f0ff;
            transform: translate(0, -2px);
        }}
        .chart-bar {{
            display: flex;
            align-items: center;
            margin: 10px 0;
        }}
        .chart-bar .label {{
            width: 150px;
            font-size: 0.9em;
            color: #888;
        }}
        .chart-bar .bar {{
            flex: 1;
            height: 24px;
            background: linear-gradient(90deg, #00d4ff 0%, #0099cc 100%);
            border-radius: 3px;
            margin: 0 10px;
            position: relative;
            min-width: 30px;
        }}
        .chart-bar .value {{
            width: 100px;
            text-align: right;
            font-family: 'Courier New', monospace;
            color: #00d4ff;
            font-weight: bold;
        }}
        footer {{
            text-align: center;
            margin-top: 40px;
            padding-top: 20px;
            border-top: 1px solid #333;
            color: #666;
            font-size: 0.9em;
        }}
        .grid-2 {{
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 20px;
            margin-bottom: 20px;
        }}
        @media (max-width: 968px) {{
            .grid-2 {{
                grid-template-columns: 1fr;
            }}
        }}
    </style>
</head>
<body>
    <div class="container">
        <header>
            <h1>📊 Análisis P2P USDT/ARS</h1>
            <div class="timestamp">Generado: {timestamp}</div>
        </header>
"""

    # Sección 1: Resumen del Mercado
    html += """        <section class="section">
            <h2>📈 Resumen del Mercado</h2>
"""

    if best_match:
        best_buy = best_match["best_buy"]
        best_sell = best_match["best_sell"]

        html += f"""            <div class="grid-2">
                <div class="ad-card">
                    <div class="advertiser">Mejor para COMPRAR USDT (vender ARS)</div>
                    <div class="price">{html_escape(best_sell.get("advertiser_name", "N/A"))}</div>
                    <div class="price">{format_price(best_sell['price'])} ARS</div>
                    <div class="details">
                        Disponible: {format_usdt(best_sell.get('available'))}<br>
                        Límite: {format_price(best_sell.get('min_limit'))} - {format_price(best_sell.get('max_limit'))}
                    </div>
                </div>
                <div class="ad-card">
                    <div class="advertiser">Mejor para VENDER USDT (comprar ARS)</div>
                    <div class="price">{html_escape(best_buy.get("advertiser_name", "N/A"))}</div>
                    <div class="price">{format_price(best_buy['price'])} ARS</div>
                    <div class="details">
                        Disponible: {format_usdt(best_buy.get('available'))}<br>
                        Límite: {format_price(best_buy.get('min_limit'))} - {format_price(best_buy.get('max_limit'))}
                    </div>
                </div>
            </div>
"""
    else:
        html += """            <div class="warning">No hay datos suficientes para generar análisis</div>
"""

    html += """        </section>
"""

    # Sección 2: Análisis de Comisiones y Spreads
    if best_match:
        html += """        <section class="section">
            <h2>💰 Análisis de Comisiones y Spreads</h2>
"""

        best_buy = best_match["best_buy"]
        best_sell = best_match["best_sell"]

        html += f"""            <div class="metric-row">
                <div class="metric">
                    <div class="label">Spread Bruto</div>
                    <div class="value">{format_price(best_match['spread_bruto'])} ({best_match['spread_pct_bruto']:.3f}%)</div>
                </div>
                <div class="metric">
                    <div class="label">Spread Neto (tras comisiones)</div>
                    <div class="value">{format_price(best_match['spread_neto'])} ({best_match['spread_neto_pct']:.3f}%)</div>
                </div>
                <div class="metric">
                    <div class="label">Comisión Compra (0.20%)</div>
                    <div class="value">{format_price(best_match['comision_compra'])}</div>
                </div>
                <div class="metric">
                    <div class="label">Comisión Venta (0.20%)</div>
                    <div class="value">{format_price(best_match['comision_venta'])}</div>
                </div>
            </div>

            <div style="margin: 15px 0;">
                <h3 style="color: #00d4ff; font-size: 1em; margin-bottom: 10px;">Impacto de Comisiones por Ciclo:</h3>
                <div class="chart-bar">
                    <div class="label">Total comisiones:</div>
                    <div class="bar" style="width: calc({(best_match['comision_total_ciclo'] / best_match['spread_bruto'] * 100) if best_match['spread_bruto'] > 0 else 0:.1f}% * 5);"></div>
                    <div class="value">{format_price(best_match['comision_total_ciclo'])}</div>
                </div>
                <div style="font-size: 0.85em; color: #888; margin-top: 5px;">
                    {((best_match['comision_total_ciclo'] / best_match['spread_bruto'] * 100) if best_match['spread_bruto'] > 0 else 0):.1f}% del spread bruto
                </div>
            </div>

            <table>
                <thead>
                    <tr>
                        <th>Operación</th>
                        <th>Precio Nominal</th>
                        <th>Comisión (0.20%)</th>
                        <th>Precio Real</th>
                    </tr>
                </thead>
                <tbody>
                    <tr>
                        <td>Compra (SELL)</td>
                        <td>{format_price(best_sell['price'])}</td>
                        <td>{format_price(best_match['comision_compra'])}</td>
                        <td>{format_price(best_match['costo_real_compra'])}</td>
                    </tr>
                    <tr>
                        <td>Venta (BUY)</td>
                        <td>{format_price(best_buy['price'])}</td>
                        <td>{format_price(best_match['comision_venta'])}</td>
                        <td>{format_price(best_match['neto_real_venta'])}</td>
                    </tr>
                </tbody>
            </table>
        </section>
"""

        # Sección 3: Regla de Oro y Sugerencias de Arbitraje
        puede_operar = (
            best_match["cumple_regla_oro"]
            and best_buy.get("available") is not None
            and best_buy.get("available") >= min_volume
        )

        html += f"""        <section class="section">
            <h2>🎯 Regla de Oro y Sugerencias</h2>

            <div class="metric-row">
                <div class="metric">
                    <div class="label">Spread Mínimo Requerido</div>
                    <div class="value">${MIN_SPREAD_GOLDEN_RULE:.2f} ARS</div>
                </div>
                <div class="metric">
                    <div class="label">Spread Actual</div>
                    <div class="value {get_spread_status_class(best_match['cumple_regla_oro'])}">{format_price(best_match['spread_bruto'])} {get_spread_status_text(best_match['cumple_regla_oro'])}</div>
                </div>
            </div>

            {f'<div class="success">✓ Cumple Regla de Oro - Arbitraje posible</div>' if best_match['cumple_regla_oro'] else f'<div class="warning">✗ No cumple Regla de Oro - Falta ${MIN_SPREAD_GOLDEN_RULE - best_match["spread_bruto"]:.2f} ARS</div>'}

            {f'<div class="success">✓ Volumen suficiente ({format_usdt(best_buy.get("available"))})</div>' if best_buy.get("available") is not None and best_buy.get("available") >= min_volume else f'<div class="warning">✗ Volumen insuficiente (< {min_volume:.0f} USDT)</div>'}
"""

        if puede_operar:
            html += f"""            <div class="success" style="margin-top: 15px; padding: 15px;">
                <strong>🚀 OPORTUNIDAD DE ARBITRAJE</strong><br>
                Ganancia neta estimada: <strong>{format_price(best_match['spread_neto'])} por USDT</strong>
            </div>
"""
        else:
            html += """            <div class="error" style="margin-top: 15px; padding: 15px;">
                <strong>⚠️ NO OPERAR</strong><br>
                Las condiciones actuales no permiten arbitraje rentable.
            </div>
"""

        html += """        </section>
"""

        # Sección 4: Simulación de Anuncio Propio
        sell_recommended = suggest_ad_price(best_sell["price"], "sell")
        buy_recommended = suggest_ad_price(best_buy["price"], "buy")
        min_usdt_sell, max_usdt_sell = orderable_usdt_range(best_sell)
        min_usdt_buy, max_usdt_buy = orderable_usdt_range(best_buy)

        html += f"""        <section class="section">
            <h2>📢 Simulación de Anuncio Propio (Rol Anunciante)</h2>

            <div class="grid-2">
                <div>
                    <h3 style="color: #00d4ff; margin-bottom: 10px;">Vender USDT</h3>
                    <div class="ad-card">
                        <div class="advertiser">Competidor: {html_escape(best_sell.get("advertiser_name", "N/A"))}</div>
                        <div class="price">{format_price(best_sell['price'])} ARS</div>
                        <div style="margin-top: 10px; padding-top: 10px; border-top: 1px solid #555;">
                            <div style="color: #888; font-size: 0.85em; margin-bottom: 5px;">Tu precio sugerido:</div>
                            <div style="font-size: 1.3em; color: #4caf50; font-weight: bold; font-family: 'Courier New', monospace;">
                                {format_price(sell_recommended)} ARS
                            </div>
                            <div style="font-size: 0.85em; color: #888; margin-top: 5px;">
                                (-${AD_PRICE_DELTA:.2f} para competir)
                            </div>
                        </div>
                        {f'<div style="margin-top: 10px; font-size: 0.85em; color: #888;">Rango: {min_usdt_sell:.2f} - {max_usdt_sell:.2f} USDT</div>' if min_usdt_sell and max_usdt_sell else ''}
                    </div>
                </div>

                <div>
                    <h3 style="color: #00d4ff; margin-bottom: 10px;">Comprar USDT</h3>
                    <div class="ad-card">
                        <div class="advertiser">Competidor: {html_escape(best_buy.get("advertiser_name", "N/A"))}</div>
                        <div class="price">{format_price(best_buy['price'])} ARS</div>
                        <div style="margin-top: 10px; padding-top: 10px; border-top: 1px solid #555;">
                            <div style="color: #888; font-size: 0.85em; margin-bottom: 5px;">Tu precio sugerido:</div>
                            <div style="font-size: 1.3em; color: #ff9800; font-weight: bold; font-family: 'Courier New', monospace;">
                                {format_price(buy_recommended)} ARS
                            </div>
                            <div style="font-size: 0.85em; color: #888; margin-top: 5px;">
                                (+${AD_PRICE_DELTA:.2f} para competir)
                            </div>
                        </div>
                        {f'<div style="margin-top: 10px; font-size: 0.85em; color: #888;">Rango: {min_usdt_buy:.2f} - {max_usdt_buy:.2f} USDT</div>' if min_usdt_buy and max_usdt_buy else ''}
                    </div>
                </div>
            </div>

            <div class="warning" style="margin-top: 20px;">
                <strong>💡 Estrategia Recomendada:</strong><br>
                Para ganar visibilidad como nuevo anunciante, considera ofrecer precios ${AD_PRICE_DELTA:.2f} ARS más competitivos.
                Esta diferencia probablemente te permita captar volumen inicial mientras construís reputación.
            </div>
        </section>
"""

    # Sección 5: Tabla de Anuncios Principales
    if best_match:
        html += """        <section class="section">
            <h2>📋 Top 5 Anuncios por Tipo</h2>

            <h3 style="color: #00d4ff; margin: 15px 0 10px 0; font-size: 1.1em;">Para VENDER USDT:</h3>
            <table>
                <thead>
                    <tr>
                        <th>Anunciante</th>
                        <th>Precio (ARS)</th>
                        <th>Disponible (USDT)</th>
                        <th>Límite Min/Max</th>
                    </tr>
                </thead>
                <tbody>
"""

        sell_sorted = sorted(
            [ad for ad in sell_ads if ad.get("price") is not None],
            key=lambda x: x["price"],
        )[:5]

        for ad in sell_sorted:
            html += f"""                    <tr>
                        <td>{html_escape(ad.get("advertiser_name", "N/A"))}</td>
                        <td>{format_price(ad.get("price"))}</td>
                        <td>{format_usdt(ad.get("available"))}</td>
                        <td>{format_price(ad.get("min_limit"))} / {format_price(ad.get("max_limit"))}</td>
                    </tr>
"""

        html += """                </tbody>
            </table>

            <h3 style="color: #00d4ff; margin: 15px 0 10px 0; font-size: 1.1em;">Para COMPRAR USDT:</h3>
            <table>
                <thead>
                    <tr>
                        <th>Anunciante</th>
                        <th>Precio (ARS)</th>
                        <th>Disponible (USDT)</th>
                        <th>Límite Min/Max</th>
                    </tr>
                </thead>
                <tbody>
"""

        buy_sorted = sorted(
            [ad for ad in buy_ads if ad.get("price") is not None],
            key=lambda x: x["price"],
            reverse=True,
        )[:5]

        for ad in buy_sorted:
            html += f"""                    <tr>
                        <td>{html_escape(ad.get("advertiser_name", "N/A"))}</td>
                        <td>{format_price(ad.get("price"))}</td>
                        <td>{format_usdt(ad.get("available"))}</td>
                        <td>{format_price(ad.get("min_limit"))} / {format_price(ad.get("max_limit"))}</td>
                    </tr>
"""

        html += """                </tbody>
            </table>
        </section>
"""

    # Footer
    html += f"""        <footer>
            <p>Datos actualizados: {timestamp}</p>
            <p>Comisión Binance P2P sin KYC: 0.20%</p>
        </footer>
    </div>
</body>
</html>
"""

    # Guardar archivo si se especifica
    if output_file:
        try:
            with open(output_file, "w", encoding="utf-8") as f:
                f.write(html)
            print(f"[INFO] Reporte HTML guardado: {output_file}")
        except Exception as e:
            print(f"[ERROR] No se pudo guardar HTML: {e}")

    return html
