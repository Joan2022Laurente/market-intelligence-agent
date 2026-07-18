import pytest
import asyncio
from collectors.crypto import CoinGeckoCollector
from collectors.sports import RealSportsCollector
from collectors.news import RSSNewsCollector

@pytest.mark.asyncio
async def test_concurrent_collectors():
    """
    Verifica que los recolectores se ejecuten de manera asíncrona concurrente
    y que todos devuelvan resultados estructurados válidos.
    """
    collectors = [
        CoinGeckoCollector(),
        RealSportsCollector(),
        RSSNewsCollector()
    ]
    
    # asyncio.gather ejecuta las rutinas en paralelo
    results = await asyncio.gather(*(c.collect() for c in collectors))
    
    crypto_data = results[0]
    sports_data = results[1]
    news_data = results[2]
    
    assert len(crypto_data) > 0
    assert crypto_data[0].simbolo in ["BTC", "ETH", "SOL"]
    
    assert len(sports_data) > 0
    assert sports_data[0].fuente.startswith("TheOddsAPI") or sports_data[0].fuente == "MockBet"
    
    assert len(news_data) > 0
    assert news_data[0].fuente == "Cointelegraph"
