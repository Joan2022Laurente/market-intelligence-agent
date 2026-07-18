import asyncio
import aiohttp
import hashlib
import hmac
import time
from typing import Dict, Any, Optional
import os

from collectors.base import BaseCollector


class BinancePortfolioCollector(BaseCollector):
    """
    Colector de patrimonio privado de Binance usando la API firmada (HMAC SHA256).
    Solo requiere permisos de LECTURA (Enable Reading) en la API Key.
    Extrae:
      - Saldos Spot (activos con saldo > 0)
      - Saldos en Simple Earn Flexible (posiciones suscritas)
    """
    def __init__(self):
        super().__init__(name="BinancePortfolio", timeout=20)
        self.api_key = os.environ.get("BINANCE_API_KEY")
        self.api_secret = os.environ.get("BINANCE_API_SECRET")
        # Usamos api.binance.us para evadir restricciones geográficas en servidores de EEUU
        self.base_url = "https://api.binance.us"

    def _sign(self, query_string: str) -> str:
        """Genera la firma HMAC SHA256 requerida por la API privada de Binance."""
        return hmac.new(
            self.api_secret.encode("utf-8"),
            query_string.encode("utf-8"),
            hashlib.sha256
        ).hexdigest()

    def _get_headers(self) -> Dict[str, str]:
        return {"X-MBX-APIKEY": self.api_key}

    async def _get_spot_balances(self, session: aiohttp.ClientSession) -> Dict[str, float]:
        """Obtiene los saldos libres en la billetera Spot (excluye ceros)."""
        timestamp = int(time.time() * 1000)
        query = f"timestamp={timestamp}&omitZeroBalances=true"
        signature = self._sign(query)
        url = f"{self.base_url}/api/v3/account?{query}&signature={signature}"

        try:
            async with session.get(url, headers=self._get_headers()) as resp:
                if resp.status != 200:
                    body = await resp.text()
                    print(f"[Portfolio Spot] Error {resp.status}: {body[:150]}")
                    return {}
                data = await resp.json()
                return {
                    b["asset"]: float(b["free"]) + float(b["locked"])
                    for b in data.get("balances", [])
                    if float(b["free"]) + float(b["locked"]) > 0
                }
        except Exception as e:
            print(f"[Portfolio Spot] Excepción: {e}")
            return {}

    async def _get_earn_balances(self, session: aiohttp.ClientSession) -> Dict[str, float]:
        """Obtiene las posiciones activas en Binance Simple Earn Flexible."""
        timestamp = int(time.time() * 1000)
        query = f"timestamp={timestamp}"
        signature = self._sign(query)
        url = f"{self.base_url}/sapi/v1/simple-earn/flexible/position?{query}&signature={signature}"

        try:
            async with session.get(url, headers=self._get_headers()) as resp:
                if resp.status != 200:
                    body = await resp.text()
                    print(f"[Portfolio Earn] Error {resp.status}: {body[:150]}")
                    return {}
                data = await resp.json()
                earn_balances = {}
                for pos in data.get("rows", []):
                    asset = pos.get("asset", "")
                    total = float(pos.get("totalAmount", 0))
                    if total > 0:
                        earn_balances[asset] = earn_balances.get(asset, 0) + total
                return earn_balances
        except Exception as e:
            print(f"[Portfolio Earn] Excepción: {e}")
            return {}

    async def fetch_data(self) -> Dict[str, Any]:
        """
        Consolida el patrimonio completo del usuario.
        Retorna un diccionario con saldos Spot, Earn y el total estimado en USD.
        """
        if not self.api_key or not self.api_secret:
            print("[Portfolio] No se encontraron BINANCE_API_KEY o BINANCE_API_SECRET.")
            return {"error": "API Key no configurada", "spot": {}, "earn": {}, "total_usd_estimado": None}

        async with aiohttp.ClientSession() as session:
            spot_task = self._get_spot_balances(session)
            earn_task = self._get_earn_balances(session)
            spot, earn = await asyncio.gather(spot_task, earn_task)

        print(f"[BinancePortfolio] Spot: {spot} | Earn: {earn}")
        return {
            "spot": spot,
            "earn": earn,
        }

    # BaseCollector espera el método collect() que llama a fetch_data()
    async def collect(self) -> Dict[str, Any]:
        return await self.fetch_data()
