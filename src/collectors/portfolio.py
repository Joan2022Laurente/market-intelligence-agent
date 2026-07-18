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
        self._time_offset = None

    async def _get_timestamp(self, session: aiohttp.ClientSession) -> int:
        """Sincroniza el reloj local con el servidor de Binance para evitar errores 400 (Timestamp ahead)."""
        if self._time_offset is None:
            try:
                async with session.get(f"{self.base_url}/api/v3/time") as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        server_time = data.get("serverTime", int(time.time() * 1000))
                        local_time = int(time.time() * 1000)
                        self._time_offset = server_time - local_time
                        print(f"[Portfolio] Reloj sincronizado con Binance. Offset: {self._time_offset}ms")
                    else:
                        self._time_offset = 0
            except Exception:
                self._time_offset = 0
                
        return int(time.time() * 1000) + self._time_offset

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
        timestamp = await self._get_timestamp(session)
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
        timestamp = await self._get_timestamp(session)
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

    async def _get_trade_history(self, session: aiohttp.ClientSession, asset: str) -> Dict[str, Any]:
        """Obtiene el historial de compras recientes para un activo contra USDT."""
        # Limpiar prefijo LD si viene de Earn (ej: LDSOL -> SOL)
        clean_asset = asset.replace("LD", "") if asset.startswith("LD") else asset
        if clean_asset == "USDT":
            return {}
            
        symbol = f"{clean_asset}USDT"
        timestamp = await self._get_timestamp(session)
        query = f"symbol={symbol}&limit=20&timestamp={timestamp}"
        signature = self._sign(query)
        url = f"{self.base_url}/api/v3/myTrades?{query}&signature={signature}"
        
        try:
            async with session.get(url, headers=self._get_headers()) as resp:
                if resp.status == 200:
                    trades = await resp.json()
                    # Filtrar solo compras
                    buys = [t for t in trades if t.get("isBuyer") == True]
                    if buys:
                        total_qty = sum(float(b["qty"]) for b in buys)
                        total_cost = sum(float(b["qty"]) * float(b["price"]) for b in buys)
                        avg_price = total_cost / total_qty if total_qty > 0 else 0
                        return {
                            "avg_buy_price": round(avg_price, 4),
                            "total_bought_recently": round(total_qty, 4),
                            "last_buy_date": buys[-1]["time"]
                        }
        except Exception as e:
            print(f"[Portfolio Trade History] Excepción para {symbol}: {e}")
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

        # Obtener historial de compras para calcular PNL
        pnl_data = {}
        all_assets = set(spot.keys()).union(set(earn.keys()))
        async with aiohttp.ClientSession() as session:
            for asset in all_assets:
                history = await self._get_trade_history(session, asset)
                if history:
                    pnl_data[asset] = history

        print(f"[BinancePortfolio] [+] Saldos: Spot={spot} | Earn={earn} | PNL={pnl_data}")
        return {"spot": spot, "earn": earn, "pnl_data": pnl_data, "fuente": "Binance API (tiempo real)"}

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
