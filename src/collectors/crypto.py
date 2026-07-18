import asyncio
import aiohttp
from typing import List
from schemas.crypto import PrecioActivo
from collectors.base import BaseCollector
import datetime

class CoinGeckoCollector(BaseCollector):
    def __init__(self):
        super().__init__(name="CoinGecko", timeout=15)
        self.url = "https://api.coingecko.com/api/v3/simple/price"
        self.coin_mapping = {
            "bitcoin": "BTC",
            "ethereum": "ETH",
            "solana": "SOL"
        }

    async def fetch_data(self) -> List[PrecioActivo]:
        params = {
            "ids": ",".join(self.coin_mapping.keys()),
            "vs_currencies": "usd",
            "include_24hr_vol": "true"
        }
        
        async with aiohttp.ClientSession() as session:
            async with session.get(self.url, params=params) as response:
                if response.status != 200:
                    print(f"[Error CoinGecko] Status {response.status}")
                    return []
                
                data = await response.json()
                
        resultados = []
        for coin_id, symbol in self.coin_mapping.items():
            if coin_id in data:
                resultados.append(
                    PrecioActivo(
                        simbolo=symbol,
                        precio=data[coin_id].get("usd", 0.0),
                        volumen_24h=data[coin_id].get("usd_24h_vol", 0.0),
                        fuente="CoinGecko API",
                        timestamp=datetime.datetime.utcnow()
                    )
                )
                
        return resultados
