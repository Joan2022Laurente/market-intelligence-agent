import asyncio
import json
import sys
import os

# Asegurar que importamos desde src
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from collectors.crypto import MockCryptoCollector
from collectors.sports import MockSportsCollector
from collectors.news import MockNewsCollector

from agents.crypto_analyst import CryptoAnalyst
from agents.sports_analyst import SportsAnalyst
from agents.news_analyst import NewsAnalyst

from synthesis.llm_client import LocalLLMClient
from report.markdown_gen import MarkdownGenerator
from db.duckdb_client import DuckDBClient

async def main():
    print("Iniciando pipeline Market Intelligence Agent...")
    
    # 1. Recolección en paralelo (Async)
    print("Recolectando datos en paralelo...")
    collectors = [
        MockCryptoCollector(),
        MockSportsCollector(),
        MockNewsCollector()
    ]
    raw_data = await asyncio.gather(*(c.collect() for c in collectors))
    
    precios = raw_data[0]
    cuotas = raw_data[1]
    noticias = raw_data[2]
    
    # 2. Guardar datos crudos en DuckDB
    print("Guardando datos crudos en DuckDB...")
    db = DuckDBClient()
    db.insert_precios(precios)
    db.insert_cuotas(cuotas)
    db.insert_noticias(noticias)
    
    # 3. Análisis Matemático (CPU/Determinístico)
    print("Ejecutando Agentes de Análisis determinísticos...")
    indicadores_cripto = CryptoAnalyst.calculate_technical_indicators(precios)
    analisis_deportivo = SportsAnalyst.analyze_odds(cuotas)
    noticias_agrupadas = NewsAnalyst.deduplicate_and_group(noticias)
    
    # 4. Preparar contexto puro para el LLM
    context_para_llm = {
        "crypto_indicators": [i.model_dump() for i in indicadores_cripto],
        "sports_analysis": [a.model_dump() for a in analisis_deportivo],
        "news_groups": {k: [n.model_dump() for n in v] for k, v in noticias_agrupadas.items()}
    }
    
    # 5. Síntesis LLM (Aquí se llama al modelo local)
    print("Generando síntesis narrativa con LLM Local...")
    llm = LocalLLMClient(model_name="llama3") # Ajustable a Qwen2.5 u otro local
    narrativa = await llm.generate_synthesis(context_para_llm)
    
    # 6. Generar el reporte final
    print("Generando reporte final...")
    reporte_md = MarkdownGenerator.generate_report(
        llm_narrative=narrativa, 
        raw_context=context_para_llm
    )
    
    # 7. Salida
    MarkdownGenerator.save_to_file(reporte_md)
    print("✅ Pipeline finalizado exitosamente.")

if __name__ == "__main__":
    asyncio.run(main())
