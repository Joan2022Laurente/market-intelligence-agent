import asyncio
import aiohttp
import hashlib
import hmac
import time
import os
from typing import Dict, Any, List

from collectors.base import BaseCollector

class PredictionMarketsCollector(BaseCollector):
    """
    Colector de Binance Prediction Markets API.
    Extrae las posiciones activas de predicción del usuario.
    Requiere permiso "Prediction Trading" y SAS.
    """
    def __init__(self):
        super().__init__(name="BinancePredictions", timeout=20)
        self.api_key = os.environ.get("BINANCE_API_KEY")
        self.api_secret = os.environ.get("BINANCE_API_SECRET")
        self.base_url = "https://api.binance.com"
        self._time_offset = None

    async def _get_timestamp(self, session: aiohttp.ClientSession) -> int:
        if self._time_offset is None:
            try:
                async with session.get(f"{self.base_url}/api/v3/time") as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        self._time_offset = data.get("serverTime", int(time.time() * 1000)) - int(time.time() * 1000)
                    else:
                        self._time_offset = 0
            except:
                self._time_offset = 0
        return int(time.time() * 1000) + self._time_offset

    def _sign(self, query_string: str) -> str:
        return hmac.new(
            self.api_secret.encode("utf-8"),
            query_string.encode("utf-8"),
            hashlib.sha256
        ).hexdigest()

    def _get_headers(self) -> Dict[str, str]:
        return {"X-MBX-APIKEY": self.api_key}

    async def fetch_data(self) -> List[Dict[str, Any]]:
        if not self.api_key or not self.api_secret:
            return []

        async with aiohttp.ClientSession() as session:
            timestamp = await self._get_timestamp(session)
            # Endpoints: /position/list (if available) or /position/token etc. 
            # We will use /position/list or /trade/list as general approach.
            # Depending on exact Binance API implementation, these might vary.
            query = f"timestamp={timestamp}"
            signature = self._sign(query)
            
            endpoints_to_try = [
                "/sapi/v1/w3w/wallet/prediction/position/list",
                "/sapi/v1/w3w/wallet/prediction/account/portfolio"
            ]
            
            for endpoint in endpoints_to_try:
                url = f"{self.base_url}{endpoint}?{query}&signature={signature}"
                try:
                    async with session.get(url, headers=self._get_headers()) as resp:
                        if resp.status == 200:
                            data = await resp.json()
                            print(f"[PredictionMarkets] [+] Posiciones extraídas: {data}")
                            # Normalizamos a una lista de posiciones
                            return data.get("positions", data.get("data", []))
                        elif resp.status == 401:
                            data = await resp.json()
                            if data.get("code") == -1002:
                                print(f"[PredictionMarkets] [!] Error -1002 en {endpoint}: Acceso bloqueado (Falta IP Blanca o autorización SAS).")
                except Exception as e:
                    print(f"[PredictionMarkets] Error en {endpoint}: {e}")
            
            return []

    async def collect(self) -> List[Dict[str, Any]]:
        return await self.fetch_data()
