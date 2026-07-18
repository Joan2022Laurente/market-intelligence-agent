import pytest
import asyncio
from collectors.crypto import MockCryptoCollector
from collectors.sports import MockSportsCollector
from collectors.news import MockNewsCollector

@pytest.mark.asyncio
async def test_concurrent_collectors():
    """
    Verifica que los recolectores se ejecuten de manera asíncrona concurrente
    y que todos devuelvan resultados estructurados válidos.
    """
    collectors = [
        MockCryptoCollector(),
        MockSportsCollector(),
        MockNewsCollector()
    ]
    
    # asyncio.gather ejecuta las rutinas en paralelo
    results = await asyncio.gather(*(c.collect() for c in collectors))
    
    crypto_data = results[0]
    sports_data = results[1]
    news_data = results[2]
    
    assert len(crypto_data) > 0
    assert crypto_data[0].simbolo in ["BTC", "ETH", "SOL"]
    
    assert len(sports_data) > 0
    assert sports_data[0].equipo_local == "Real Madrid"
    
    assert len(news_data) > 0
    assert news_data[0].impacto_estimado == "alto"
