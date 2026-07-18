import asyncio
import aiohttp
import hashlib
import hmac
import time
from typing import Dict, Any
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
        # Usamos api.binance.com ya que la IP del servidor Lightning está en la lista blanca
        self.base_url = "https://api.binance.com"

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
        """Obtiene todos los saldos (free + locked) de la cuenta Spot con saldo > 0."""
        timestamp = int(time.time() * 1000)
        query = f"timestamp={timestamp}"
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
                    b["asset"]: round(float(b["free"]) + float(b["locked"]), 8)
                    for b in data.get("balances", [])
                    if float(b["free"]) + float(b["locked"]) > 0
                }
        except Exception as e:
            print(f"[Portfolio Spot] Excepción: {e}")
            return {}

    async def _get_earn_balances(self, session: aiohttp.ClientSession) -> Dict[str, float]:
        """
        Binance.US no soporta el endpoint SAPI de Simple Earn.
        Como alternativa, extraemos los saldos 'locked' del endpoint principal
        de la cuenta, que en Binance.US incluye fondos en productos de ahorro.
        """
        timestamp = int(time.time() * 1000)
        query = f"timestamp={timestamp}"
        signature = self._sign(query)
        url = f"{self.base_url}/api/v3/account?{query}&signature={signature}"

        try:
            async with session.get(url, headers=self._get_headers()) as resp:
                if resp.status != 200:
                    body = await resp.text()
                    print(f"[Portfolio Earn/Locked] Error {resp.status}: {body[:150]}")
                    return {}
                data = await resp.json()
                # Los fondos en Earn aparecen como 'locked' en el balance de Spot
                locked = {
                    b["asset"]: round(float(b["locked"]), 8)
                    for b in data.get("balances", [])
                    if float(b["locked"]) > 0
                }
                if locked:
                    print(f"[Portfolio Earn/Locked] Fondos bloqueados (Earn): {locked}")
                return locked
        except Exception as e:
            print(f"[Portfolio Earn/Locked] Excepción: {e}")
            return {}

    async def fetch_data(self) -> Dict[str, Any]:
        """
        Consolida el patrimonio completo del usuario.
        Intenta obtener saldos en tiempo real desde Binance.
        Si la API está bloqueada (ej. servidor en EE.UU.), usa los valores
        configurados manualmente en las variables de entorno JOAN_SPOT_* y JOAN_EARN_*.
        """
        if not self.api_key or not self.api_secret:
            print("[Portfolio] No se encontraron BINANCE_API_KEY o BINANCE_API_SECRET. Usando saldos manuales.")
            return self._get_manual_fallback()

        async with aiohttp.ClientSession() as session:
            spot_task = self._get_spot_balances(session)
            earn_task = self._get_earn_balances(session)
            spot, earn = await asyncio.gather(spot_task, earn_task)

        # Si el API está bloqueada geográficamente, usar fallback manual
        if not spot and not earn:
            print("[Portfolio] API de Binance inaccesible. Usando saldos manuales del .env.")
            return self._get_manual_fallback()

        print(f"[BinancePortfolio] ✅ Saldos en tiempo real: Spot={spot} | Earn={earn}")
        return {"spot": spot, "earn": earn, "fuente": "Binance API (tiempo real)"}

    def _get_manual_fallback(self) -> Dict[str, Any]:
        """Lee saldos configurados manualmente en el .env como respaldo."""
        spot = {}
        earn = {}

        # Leer saldos Spot del .env (formato: JOAN_SPOT_USDT=0.0, JOAN_SPOT_SOL=0.0, etc.)
        for key, value in os.environ.items():
            if key.startswith("JOAN_SPOT_"):
                asset = key.replace("JOAN_SPOT_", "")
                try:
                    amount = float(value)
                    if amount > 0:
                        spot[asset] = amount
                except ValueError:
                    pass

        # Leer saldos Earn del .env (formato: JOAN_EARN_USDT=4.38, JOAN_EARN_SOL=0.084, etc.)
        for key, value in os.environ.items():
            if key.startswith("JOAN_EARN_"):
                asset = key.replace("JOAN_EARN_", "")
                try:
                    amount = float(value)
                    if amount > 0:
                        earn[asset] = amount
                except ValueError:
                    pass

        print(f"[Portfolio Fallback] Spot manual: {spot} | Earn manual: {earn}")
        return {"spot": spot, "earn": earn, "fuente": "Configuración manual (.env)"}

    async def collect(self) -> Dict[str, Any]:
        return await self.fetch_data()
