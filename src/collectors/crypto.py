import asyncio
import aiohttp
from typing import List
from schemas.crypto import PrecioActivo
from collectors.base import BaseCollector
import datetime

class CoinGeckoCollector(BaseCollector):
    def __init__(self):
        super().__init__(name="CoinGecko", timeout=30)
        self.price_url = "https://api.coingecko.com/api/v3/simple/price"
        self.history_url = "https://api.coingecko.com/api/v3/coins/{coin_id}/market_chart"
        self.coin_mapping = {
            "bitcoin": "BTC",
            "ethereum": "ETH",
            "solana": "SOL"
        }

    async def _fetch_history(self, session: aiohttp.ClientSession, coin_id: str) -> List[float]:
        """Descarga el historial de precios de los últimos 30 días (datos diarios)."""
        url = self.history_url.format(coin_id=coin_id)
        params = {"vs_currency": "usd", "days": "30", "interval": "daily"}
        try:
            async with session.get(url, params=params) as resp:
                if resp.status != 200:
                    return []
                data = await resp.json()
                # data["prices"] es una lista de [timestamp_ms, precio]
                return [entry[1] for entry in data.get("prices", [])]
        except Exception as e:
            print(f"[Error historial {coin_id}] {e}")
            return []

    async def fetch_data(self) -> List[PrecioActivo]:
        params = {
            "ids": ",".join(self.coin_mapping.keys()),
            "vs_currencies": "usd",
            "include_24hr_vol": "true",
            "include_24hr_change": "true",
            "include_7d_change": "true"
        }

        async with aiohttp.ClientSession() as session:
            # Precios actuales + historial de los 3 activos en paralelo
            price_task = session.get(self.price_url, params=params)
            history_tasks = {
                coin_id: self._fetch_history(session, coin_id)
                for coin_id in self.coin_mapping.keys()
            }

            async with price_task as response:
                if response.status != 200:
                    print(f"[Error CoinGecko] Status {response.status}")
                    return []
                price_data = await response.json()

            # Descargar historiales en paralelo
            histories = {}
            for coin_id, task in history_tasks.items():
                histories[coin_id] = await task

        resultados = []
        for coin_id, symbol in self.coin_mapping.items():
            if coin_id in price_data:
                d = price_data[coin_id]
                hist = histories.get(coin_id, [])

                # Calcular cambio 7d desde el historial si CoinGecko no lo incluye
                cambio_7d = d.get("usd_7d_change")
                if cambio_7d is None and len(hist) >= 8:
                    precio_hace_7d = hist[-8]
                    if precio_hace_7d > 0:
                        cambio_7d = ((d.get("usd", 0) - precio_hace_7d) / precio_hace_7d) * 100

                resultados.append(
                    PrecioActivo(
                        simbolo=symbol,
                        precio=d.get("usd", 0.0),
                        volumen_24h=d.get("usd_24h_vol", 0.0),
                        cambio_pct_24h=d.get("usd_24h_change"),
                        cambio_pct_7d=cambio_7d,
                        precios_historicos=hist,
                        fuente="CoinGecko API",
                        timestamp=datetime.datetime.utcnow()
                    )
                )

        return resultados
