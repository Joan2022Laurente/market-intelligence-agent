import asyncio
import json
import sys
import os
import aiohttp
from dotenv import load_dotenv

# Asegurar que importamos desde src
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Cargar variables del .env
load_dotenv()

from collectors.crypto import BinanceCollector
from collectors.sports import RealSportsCollector
from collectors.news import RSSNewsCollector
from collectors.portfolio import BinancePortfolioCollector
from collectors.predictions import PredictionMarketsCollector

from agents.crypto_analyst import CryptoAnalyst
from agents.sports_analyst import SportsAnalyst
from agents.news_analyst import NewsAnalyst

from synthesis.llm_client import LocalLLMClient
from report.markdown_gen import MarkdownReportGenerator
from db.duckdb_client import DuckDBClient

OUTPUT_FILE = "reporte_diario.md"

async def main():
    print("Iniciando pipeline Market Intelligence Agent...")

    # 1. Recolección en paralelo (Async)
    print("Recolectando datos en paralelo...")
    
    async def fetch_usd_pen(session: aiohttp.ClientSession) -> float:
        try:
            async with session.get("https://open.er-api.com/v6/latest/USD") as resp:
                data = await resp.json()
                return data.get("rates", {}).get("PEN", 3.75) # 3.75 como fallback
        except Exception:
            return 3.75

    async with aiohttp.ClientSession() as session:
        usd_pen_task = fetch_usd_pen(session)
        collectors = [
            BinanceCollector(),
            RealSportsCollector(),
            RSSNewsCollector(),
            BinancePortfolioCollector(),
            PredictionMarketsCollector()
        ]
        
        # Ejecutar todos incluyendo el tipo de cambio
        results = await asyncio.gather(usd_pen_task, *(c.collect() for c in collectors))
        
    usd_to_pen = results[0]
    raw_data = results[1:]

    precios = raw_data[0]
    cuotas = raw_data[1]
    noticias = raw_data[2]
    portfolio = raw_data[3]
    predicciones = raw_data[4]

    total_spot_usd = sum(
        val for asset, val in portfolio.get("spot", {}).items() if asset == "USDT"
    )
    total_earn_usd = portfolio.get("earn", {})

    print(f"  [+] Cripto: {len(precios)} activos")
    print(f"  [+] Deportes: {len(cuotas)} partidos {'(REALES)' if cuotas and not cuotas[0].es_simulado else '(Simulados)'}")
    print(f"  [+] Noticias: {len(noticias)} artículos de {len(set(n.fuente for n in noticias))} fuentes")
    print(f"  [+] Portafolio Binance: Spot={portfolio.get('spot', {})}, Earn={total_earn_usd}")

    # 2. Guardar datos crudos en DuckDB
    print("Guardando datos crudos en DuckDB...")
    db = DuckDBClient()
    db.insert_precios(precios)
    db.insert_cuotas(cuotas)
    db.insert_noticias(noticias)

    # 3. Análisis Matemático (Determinístico, sin LLM)
    print("Ejecutando Agentes de Análisis determinísticos...")
    indicadores_cripto = CryptoAnalyst.calculate_technical_indicators(precios)
    analisis_deportivo = SportsAnalyst.analyze_odds(cuotas)
    noticias_agrupadas = NewsAnalyst.deduplicate_and_group(noticias)
    sentimiento_noticias = NewsAnalyst.get_sentiment_summary(noticias_agrupadas)

    # Log indicadores calculados
    for ind in indicadores_cripto:
        print(f"  {ind.simbolo}: RSI={ind.rsi:.1f}, MACD={ind.macd:+.4f}, Tendencia={ind.tendencia}, Rec={ind.recomendacion}")

    # 4. Preparar contexto enriquecido para el LLM
    # Nota: stripeamos precios_historicos para no malgastar tokens del LLM
    def _clean_for_llm(ind_dict):
        d = ind_dict.copy()
        d.pop('precios_historicos', None)  # El LLM solo necesita indicadores, no el historial raw
        return d

    context_para_llm = {
        "usuario": "Joan Joaquin Callañaupa Laurente",
        "portfolio_binance": {
            "spot": portfolio.get("spot", {}),
            "earn": portfolio.get("earn", {}),
            "pnl_data": portfolio.get("pnl_data", {}),
            "tipo_cambio_pen": usd_to_pen,
            "nota": "Saldos extraídos en tiempo real desde la API de Binance. Usa tipo_cambio_pen para mostrar el valor total del portafolio en Soles (PEN)."
        },
        "predicciones_activas": predicciones,
        "crypto_indicators": [_clean_for_llm(i.model_dump()) for i in indicadores_cripto],
        "sports_analysis": [a.model_dump() for a in analisis_deportivo],
        "news_groups": {k: [n.model_dump() for n in v] for k, v in noticias_agrupadas.items()},
        "sentimiento_noticias": sentimiento_noticias
    }

    # 5. Síntesis LLM
    print("Generando síntesis narrativa con LLM Local (Qwen2.5 32B)...")
    llm = LocalLLMClient()  # Usa el modelo configurado en llm_client.py
    narrativa = await llm.generate_synthesis(context_para_llm)

    # 6. Generar el reporte final
    print("Generando reporte final...")
    reporte_md = MarkdownReportGenerator.generate(
        synthesis=narrativa,
        raw_context=context_para_llm
    )

    # 7. Guardar en archivo
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        f.write(reporte_md)
    print(f"Reporte guardado en {OUTPUT_FILE}")
    print("[SUCCESS] Pipeline finalizado exitosamente.")

if __name__ == "__main__":
    asyncio.run(main())
