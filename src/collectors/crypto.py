import asyncio
import aiohttp
from typing import List
from schemas.crypto import PrecioActivo
from collectors.base import BaseCollector
import datetime
import json

class BinanceCollector(BaseCollector):
    def __init__(self):
        super().__init__(name="Binance API", timeout=30)
        self.ticker_url = "https://api.binance.us/api/v3/ticker/24hr"
        self.klines_url = "https://api.binance.us/api/v3/klines"
        self.coin_mapping = {
            "BTCUSDT": "BTC",
            "ETHUSDT": "ETH",
            "SOLUSDT": "SOL"
        }

    async def _fetch_history(self, session: aiohttp.ClientSession, symbol: str) -> List[float]:
        """Descarga el historial de precios de los últimos 30 días (velas diarias) desde Binance."""
        params = {
            "symbol": symbol,
            "interval": "1d",
            "limit": 30
        }
        try:
            async with session.get(self.klines_url, params=params) as resp:
                if resp.status != 200:
                    print(f"[Error Binance Klines {symbol}] Status {resp.status}")
                    return []
                data = await resp.json()
                # data es una lista de velas. El índice 4 es el precio de cierre (Close).
                return [float(kline[4]) for kline in data]
        except Exception as e:
            print(f"[Error historial {symbol}] {e}")
            return []

    async def _fetch_ticker(self, session: aiohttp.ClientSession, symbol: str) -> dict:
        """Descarga el precio actual y el cambio de 24h para un símbolo."""
        params = {"symbol": symbol}
        try:
            async with session.get(self.ticker_url, params=params) as resp:
                if resp.status != 200:
                    print(f"[Error Binance Ticker {symbol}] Status {resp.status}")
                    return {}
                return await resp.json()
        except Exception as e:
            print(f"[Error ticker {symbol}] {e}")
            return {}

    async def fetch_data(self) -> List[PrecioActivo]:
        async with aiohttp.ClientSession() as session:
            # Lanzamos todas las peticiones en paralelo (tickers y klines)
            ticker_tasks = {
                sym: self._fetch_ticker(session, sym) for sym in self.coin_mapping.keys()
            }
            history_tasks = {
                sym: self._fetch_history(session, sym) for sym in self.coin_mapping.keys()
            }

            tickers = {}
            for sym, task in ticker_tasks.items():
                tickers[sym] = await task

            histories = {}
            for sym, task in history_tasks.items():
                histories[sym] = await task

        resultados = []
        for symbol, display_name in self.coin_mapping.items():
            d = tickers.get(symbol, {})
            hist = histories.get(symbol, [])

            if not d:
                continue

            precio_actual = float(d.get("lastPrice", 0.0))
            volumen_24h = float(d.get("quoteVolume", 0.0)) # Volumen en USDT
            cambio_pct_24h = float(d.get("priceChangePercent", 0.0))

            # Calcular cambio 7d desde el historial (hace 7 días)
            cambio_7d = None
            if len(hist) >= 8:
                precio_hace_7d = hist[-8]
                if precio_hace_7d > 0:
                    cambio_7d = ((precio_actual - precio_hace_7d) / precio_hace_7d) * 100

            resultados.append(
                PrecioActivo(
                    simbolo=display_name,
                    precio=precio_actual,
                    volumen_24h=volumen_24h,
                    cambio_pct_24h=cambio_pct_24h,
                    cambio_pct_7d=cambio_7d,
                    precios_historicos=hist,
                    fuente="Binance API",
                    timestamp=datetime.datetime.utcnow()
                )
            )

        return resultados
