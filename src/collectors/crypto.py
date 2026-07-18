import asyncio
import random
from typing import List
from schemas.crypto import PrecioActivo
from collectors.base import BaseCollector

class MockCryptoCollector(BaseCollector):
    def __init__(self):
        super().__init__(name="MockCrypto", timeout=10)

    async def fetch_data(self) -> List[PrecioActivo]:
        # Simula latencia de red
        await asyncio.sleep(random.uniform(0.5, 2.0))
        
        return [
            PrecioActivo(
                simbolo="BTC",
                precio=random.uniform(60000, 70000),
                volumen_24h=random.uniform(20_000_000, 50_000_000),
                fuente="MockAPI"
            ),
            PrecioActivo(
                simbolo="ETH",
                precio=random.uniform(3000, 4000),
                volumen_24h=random.uniform(10_000_000, 20_000_000),
                fuente="MockAPI"
            ),
            PrecioActivo(
                simbolo="SOL",
                precio=random.uniform(100, 200),
                volumen_24h=random.uniform(1_000_000, 5_000_000),
                fuente="MockAPI"
            )
        ]
