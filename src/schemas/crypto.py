from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field

class PrecioActivo(BaseModel):
    simbolo: str = Field(..., description="Símbolo del activo (ej. BTC, ETH)")
    precio: float = Field(..., description="Precio actual en USD")
    volumen_24h: float = Field(..., description="Volumen de transacciones en 24h")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Fecha y hora de la lectura")
    fuente: str = Field(..., description="Fuente de los datos (ej. CoinGecko, Binance)")

class IndicadorTecnico(BaseModel):
    simbolo: str = Field(..., description="Símbolo del activo")
    rsi: float = Field(..., description="Relative Strength Index (RSI) a 14 periodos")
    macd: float = Field(..., description="Moving Average Convergence Divergence (MACD)")
    dominancia: Optional[float] = Field(None, description="Dominancia en el mercado (%)")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Fecha y hora del cálculo")
