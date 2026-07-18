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

    async def fetch_data(self) -> Dict[str, Any]:
        if not self.api_key or not self.api_secret:
            return {"activas": [], "historial": []}

        result = {"activas": [], "historial": []}

        async with aiohttp.ClientSession() as session:
            timestamp = await self._get_timestamp(session)
            
            # 1. Obtener la dirección de la billetera de predicción
            wallet_address = None
            query_wallet = f"timestamp={timestamp}"
            sig_wallet = self._sign(query_wallet)
            url_wallet = f"{self.base_url}/sapi/v1/w3w/wallet/prediction/wallet/list?{query_wallet}&signature={sig_wallet}"
            
            try:
                async with session.get(url_wallet, headers=self._get_headers()) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        wallets = data.get("wallets", [])
                        if wallets:
                            wallet_address = wallets[0].get("walletAddress")
            except Exception as e:
                print(f"[PredictionMarkets] Error obteniendo wallet: {e}")

            # 2. Obtener posiciones activas
            query_pos = f"timestamp={timestamp}"
            sig_pos = self._sign(query_pos)
            url_pos = f"{self.base_url}/sapi/v1/w3w/wallet/prediction/position/list?{query_pos}&signature={sig_pos}"
            try:
                async with session.get(url_pos, headers=self._get_headers()) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        result["activas"] = data.get("positions", data.get("data", []))
                    elif resp.status == 401:
                        data = await resp.json()
                        if data.get("code") == -1002:
                            print(f"[PredictionMarkets] [!] Error -1002: Acceso bloqueado (Falta IP Blanca o autorización SAS).")
            except Exception as e:
                print(f"[PredictionMarkets] Error obteniendo activas: {e}")

            # 3. Obtener historial de posiciones cerradas (órdenes)
            if wallet_address:
                query_hist = f"walletAddress={wallet_address}&timestamp={timestamp}"
                sig_hist = self._sign(query_hist)
                url_hist = f"{self.base_url}/sapi/v1/w3w/wallet/prediction/order/list?{query_hist}&signature={sig_hist}"
                try:
                    async with session.get(url_hist, headers=self._get_headers()) as resp:
                        if resp.status == 200:
                            data = await resp.json()
                            orders = data.get("orders", [])
                            # Filtramos solo las cerradas/liquidadas si el API devuelve todas
                            # Asumimos que podemos pasarlas todas o filtrar por estado 'SETTLED' o 'CLOSED'
                            result["historial"] = orders
                except Exception as e:
                    print(f"[PredictionMarkets] Error obteniendo historial: {e}")
            
            return result

    async def collect(self) -> Dict[str, Any]:
        return await self.fetch_data()
