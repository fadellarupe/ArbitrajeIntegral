# ArbitrajeIntegral/engine/decision_engine.py
from config import BINANCE_MAKER_FEE, BINANCE_TAKER_FEE_FIXED, MIN_SPREAD_ARS, MIN_SPREAD_GOLDEN_RULE

class DecisionEngine:
    def __init__(self, inventory_manager=None):
        self.inventory_manager = inventory_manager

    def calculate_net_roi(self, buy_price, sell_price, buy_exchange="Binance", sell_exchange="Binance", mode="TAKER", amount_usdt=100.0):
        """
        Calcula el ROI neto real.
        Si es TAKER:
            - Compramos al cartel (Advertiser Sell). Costo = buy_price.
            - Vendemos al cartel (Advertiser Buy). Ingreso = sell_price.
            - Si es Binance, Taker aplica un fee de 0.05 USDT por operación.
        Si es MAKER:
            - Ponemos un anuncio de Compra en buy_exchange a buy_price. Costo = buy_price * fee maker.
            - Ponemos un anuncio de Venta en sell_exchange a sell_price. Ingreso = sell_price * fee maker.
        """
        # --- CÁLCULO DE COSTO DE ENTRADA (COMPRA) ---
        costo_ars = buy_price * amount_usdt
        fee_buy_ars = 0.0
        
        if mode == "TAKER":
            # Taker compra en Binance aplica fee fijo en USDT
            if buy_exchange == "Binance":
                fee_buy_ars = BINANCE_TAKER_FEE_FIXED * buy_price
        else: # MAKER
            # Maker compra en Binance aplica % de comisión maker
            if buy_exchange == "Binance":
                fee_buy_ars = costo_ars * BINANCE_MAKER_FEE
                
        costo_total_ars = costo_ars + fee_buy_ars

        # --- CÁLCULO DE INGRESO DE SALIDA (VENTA) ---
        ingreso_ars = sell_price * amount_usdt
        fee_sell_ars = 0.0
        
        if mode == "TAKER":
            # Taker vende en Binance aplica fee fijo en USDT
            if sell_exchange == "Binance":
                fee_sell_ars = BINANCE_TAKER_FEE_FIXED * sell_price
        else: # MAKER
            # Maker vende en Binance aplica % de comisión maker
            if sell_exchange == "Binance":
                fee_sell_ars = ingreso_ars * BINANCE_MAKER_FEE

        venta_neta_ars = ingreso_ars - fee_sell_ars
        profit_ars = venta_neta_ars - costo_total_ars
        roi_pct = (profit_ars / costo_total_ars) * 100 if costo_total_ars > 0 else 0.0
        
        return {
            "profit_ars": round(profit_ars, 2),
            "roi_pct": round(roi_pct, 3),
            "mode": mode,
            "costo_total_ars": round(costo_total_ars, 2),
            "venta_neta_ars": round(venta_neta_ars, 2),
            "fee_buy_ars": round(fee_buy_ars, 2),
            "fee_sell_ars": round(fee_sell_ars, 2)
        }

    def get_all_opportunities(self, unified_state, amount_usdt=100.0) -> list:
        """
        Encuentra todas las oportunidades de arbitraje TAKER y MAKER cruzando los 3 exchanges.
        Retorna la lista ordenada por ROI neto descendente.
        """
        opportunities = []
        exchanges = list(unified_state.keys())

        # Delta de competencia Maker (para posicionarse en el top 1 +/- $0.10 ARS)
        DELTA_COMPETENCIA = 0.10

        for buy_ex in exchanges:
            # 1. anuncios de VENTA (donde el anunciante vende, por lo tanto nosotros compramos -> Taker Compra)
            sell_ads = unified_state[buy_ex].get("sell_ads", [])
            if not sell_ads: continue
            best_sell_ad = sell_ads[0] # El anunciante que vende más barato (Top 1)
            
            # 2. anuncios de COMPRA (donde el anunciante compra, por lo tanto nosotros vendemos -> Taker Venta)
            buy_ads = unified_state[buy_ex].get("buy_ads", [])
            if not buy_ads: continue
            best_buy_ad = buy_ads[0] # El anunciante que compra más caro (Top 1)

            for sell_ex in exchanges:
                sell_ex_buy_ads = unified_state[sell_ex].get("buy_ads", [])
                sell_ex_sell_ads = unified_state[sell_ex].get("sell_ads", [])
                if not sell_ex_buy_ads or not sell_ex_sell_ads: continue
                
                opp_best_buy_ad = sell_ex_buy_ads[0] # Top 1 comprador en exchange de venta
                opp_best_sell_ad = sell_ex_sell_ads[0] # Top 1 vendedor en exchange de venta

                # =========================================================================
                # ESCENARIO A: ARBITRAJE TAKER (DIRECTO)
                # =========================================================================
                # Compramos directo al anunciante vendedor en buy_ex (best_sell_ad['price'])
                # Vendemos directo al anunciante comprador en sell_ex (opp_best_buy_ad['price'])
                taker_buy_price = best_sell_ad["price"]
                taker_sell_price = opp_best_buy_ad["price"]
                
                # Para ser rentable, el precio al que compramos debe ser MENOR al que vendemos
                taker_res = self.calculate_net_roi(
                    buy_price=taker_buy_price,
                    sell_price=taker_sell_price,
                    buy_exchange=buy_ex,
                    sell_exchange=sell_ex,
                    mode="TAKER",
                    amount_usdt=amount_usdt
                )
                
                spread_bruto_taker = taker_sell_price - taker_buy_price

                opportunities.append({
                    "type": "TAKER",
                    "buy_exchange": buy_ex,
                    "sell_exchange": sell_ex,
                    "buy_price": taker_buy_price,
                    "sell_price": taker_sell_price,
                    "best_buy_ad": opp_best_buy_ad,
                    "best_sell_ad": best_sell_ad,
                    "spread_bruto": round(spread_bruto_taker, 2),
                    "profit_ars": taker_res["profit_ars"],
                    "roi_pct": taker_res["roi_pct"],
                    "fee_buy_ars": taker_res["fee_buy_ars"],
                    "fee_sell_ars": taker_res["fee_sell_ars"],
                    "color": "success" if taker_res["roi_pct"] >= 0.4 else ("warning" if taker_res["roi_pct"] > 0 else "danger"),
                    "status_label": "Taker OK" if taker_res["roi_pct"] >= 0.4 else ("Taker Pérdida" if taker_res["roi_pct"] < 0 else "Taker Neutro")
                })

                # =========================================================================
                # ESCENARIO B: ARBITRAJE MAKER (ESTRATEGIA DE PESCA)
                # =========================================================================
                # Publicamos anuncio de Compra en buy_ex (nuestro precio = top 1 comprador + delta)
                # Publicamos anuncio de Venta en sell_ex (nuestro precio = top 1 vendedor - delta)
                maker_buy_price = best_buy_ad["price"] + DELTA_COMPETENCIA  # Compramos un poco más caro que el top 1
                maker_sell_price = opp_best_sell_ad["price"] - DELTA_COMPETENCIA # Vendemos un poco más barato que el top 1
                
                maker_res = self.calculate_net_roi(
                    buy_price=maker_buy_price,
                    sell_price=maker_sell_price,
                    buy_exchange=buy_ex,
                    sell_exchange=sell_ex,
                    mode="MAKER",
                    amount_usdt=amount_usdt
                )
                
                spread_bruto_maker = maker_sell_price - maker_buy_price

                opportunities.append({
                    "type": "MAKER",
                    "buy_exchange": buy_ex,
                    "sell_exchange": sell_ex,
                    "buy_price": maker_buy_price,
                    "sell_price": maker_sell_price,
                    "best_buy_ad": best_buy_ad,
                    "best_sell_ad": opp_best_sell_ad,
                    "spread_bruto": round(spread_bruto_maker, 2),
                    "profit_ars": maker_res["profit_ars"],
                    "roi_pct": maker_res["roi_pct"],
                    "fee_buy_ars": maker_res["fee_buy_ars"],
                    "fee_sell_ars": maker_res["fee_sell_ars"],
                    "color": "success" if maker_res["roi_pct"] >= 0.6 else ("warning" if maker_res["roi_pct"] > 0 else "danger"),
                    "status_label": "Maker Pesca" if maker_res["roi_pct"] >= 0.6 else ("Maker Bajo" if maker_res["roi_pct"] > 0 else "Maker Pérdida")
                })

        # Ordenar por ROI descendente
        opportunities.sort(key=lambda x: x["roi_pct"], reverse=True)
        return opportunities

    def get_action_suggestion(self, best_buy_ad, best_sell_ad):
        """
        Mantiene compatibilidad con la firma anterior (solo para Binance).
        """
        taker = self.calculate_net_roi(best_sell_ad['price'], best_buy_ad['price'], mode="TAKER")
        spread_bruto = best_buy_ad['price'] - best_sell_ad['price']
        
        if taker['roi_pct'] >= 0.4:
            return {
                "type": "TAKER",
                "label": "EJECUTAR TAKER (ROI OK)",
                "roi": f"{taker['roi_pct']}%",
                "profit": f"${taker['profit_ars']} ARS / 100u",
                "color": "success"
            }
        
        if spread_bruto >= MIN_SPREAD_ARS:
            return {
                "type": "MAKER",
                "label": "ESTRATEGIA DE PESCA (MAKER)",
                "roi": "Variable",
                "profit": f"Brecha: ${spread_bruto:.2f}",
                "color": "primary"
            }
        
        return {
            "type": "WAIT",
            "label": "MERCADO PLANCHADO (CAPTAR CLIENTES)",
            "roi": "N/A",
            "profit": "Foco en Outreach",
            "color": "secondary"
        }


