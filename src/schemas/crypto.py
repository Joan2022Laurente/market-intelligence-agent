from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field

class PrecioActivo(BaseModel):
    simbolo: str = Field(..., description="Símbolo del activo (ej. BTC, ETH)")
    precio: float = Field(..., description="Precio actual en USD")
    volumen_24h: float = Field(..., description="Volumen de transacciones en 24h")
    cambio_pct_24h: Optional[float] = Field(None, description="Cambio porcentual últimas 24h")
    cambio_pct_7d: Optional[float] = Field(None, description="Cambio porcentual últimos 7 días")
    precios_historicos: Optional[List[float]] = Field(None, description="Lista de precios diarios (30 días)")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Fecha y hora de la lectura")
    fuente: str = Field(..., description="Fuente de los datos (ej. CoinGecko, Binance)")

class IndicadorTecnico(BaseModel):
    simbolo: str = Field(..., description="Símbolo del activo")
    precio_actual: float = Field(0.0, description="Precio actual en USD")
    rsi: float = Field(..., description="Relative Strength Index (RSI) a 14 periodos")
    macd: float = Field(..., description="Línea MACD")
    macd_signal: float = Field(0.0, description="Línea de señal MACD")
    macd_histograma: float = Field(0.0, description="Histograma MACD (MACD - Signal)")
    tendencia: str = Field("NEUTRAL", description="ALCISTA / BAJISTA / NEUTRAL")
    recomendacion: str = Field("ESPERAR", description="COMPRAR / MANTENER / ESPERAR / REDUCIR")
    cambio_pct_24h: Optional[float] = Field(None, description="Cambio % en 24h")
    dominancia: Optional[float] = Field(None, description="Dominancia en el mercado (%)")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Fecha y hora del cálculo")
