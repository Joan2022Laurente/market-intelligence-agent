from typing import List, Optional
from schemas.crypto import PrecioActivo, IndicadorTecnico
import datetime


def _ema_series(prices: List[float], period: int) -> List[float]:
    """Calcula la EMA para una serie de precios."""
    if not prices:
        return []
    k = 2.0 / (period + 1)
    emas = [prices[0]]
    for price in prices[1:]:
        emas.append(price * k + emas[-1] * (1 - k))
    return emas


def calculate_rsi(prices: List[float], period: int = 14) -> float:
    """
    Calcula el RSI real (Wilder's Smoothed RSI) sobre una serie de precios.
    Requiere al menos period+1 puntos de datos.
    """
    if len(prices) < period + 1:
        return 50.0  # Sin datos suficientes: retornamos neutral

    deltas = [prices[i + 1] - prices[i] for i in range(len(prices) - 1)]
    gains = [max(d, 0.0) for d in deltas]
    losses = [max(-d, 0.0) for d in deltas]

    # Primer promedio simple
    avg_gain = sum(gains[:period]) / period
    avg_loss = sum(losses[:period]) / period

    # Suavizado de Wilder para el resto
    for i in range(period, len(gains)):
        avg_gain = (avg_gain * (period - 1) + gains[i]) / period
        avg_loss = (avg_loss * (period - 1) + losses[i]) / period

    if avg_loss == 0:
        return 100.0
    rs = avg_gain / avg_loss
    return round(100.0 - (100.0 / (1.0 + rs)), 2)


def calculate_macd(prices: List[float]) -> tuple:
    """
    Calcula MACD(12,26,9). Devuelve (macd_line, signal_line, histograma).
    """
    if len(prices) < 26:
        return 0.0, 0.0, 0.0

    ema12 = _ema_series(prices, 12)
    ema26 = _ema_series(prices, 26)

    macd_line = [ema12[i] - ema26[i] for i in range(len(prices))]

    if len(macd_line) < 9:
        return macd_line[-1], 0.0, macd_line[-1]

    signal_series = _ema_series(macd_line, 9)
    signal = signal_series[-1]
    macd_val = macd_line[-1]
    histograma = macd_val - signal

    return round(macd_val, 4), round(signal, 4), round(histograma, 4)


def determine_trend_and_recommendation(rsi: float, macd: float, signal: float, cambio_24h: Optional[float]) -> tuple:
    """
    Determina tendencia y recomendación basándose en RSI + MACD cruce + cambio 24h.
    """
    # Señal MACD: cruce alcista si MACD > Signal, bajista si MACD < Signal
    macd_bullish = macd > signal
    macd_bearish = macd < signal

    # RSI: sobrecomprado > 70, sobrevendido < 30
    rsi_overbought = rsi > 70
    rsi_oversold = rsi < 30

    if rsi_oversold and macd_bullish:
        tendencia = "ALCISTA"
        recomendacion = "COMPRAR"
    elif rsi_overbought and macd_bearish:
        tendencia = "BAJISTA"
        recomendacion = "REDUCIR"
    elif macd_bullish and not rsi_overbought:
        tendencia = "ALCISTA"
        recomendacion = "MANTENER" if (cambio_24h and cambio_24h > 5) else "COMPRAR"
    elif macd_bearish and not rsi_oversold:
        tendencia = "BAJISTA"
        recomendacion = "ESPERAR"
    else:
        tendencia = "NEUTRAL"
        recomendacion = "MANTENER"

    return tendencia, recomendacion


class CryptoAnalyst:
    """
    Agente de análisis determinístico para Cripto.
    NO usa LLM. Todo es matemática pura (RSI, MACD).
    """

    @staticmethod
    def calculate_technical_indicators(precios: List[PrecioActivo]) -> List[IndicadorTecnico]:
        indicadores = []
        for p in precios:
            hist = p.precios_historicos or []

            # --- RSI real ---
            rsi = calculate_rsi(hist) if len(hist) >= 15 else 50.0

            # --- MACD real ---
            macd_val, signal_val, histograma = calculate_macd(hist) if len(hist) >= 26 else (0.0, 0.0, 0.0)

            # --- Tendencia y recomendación ---
            tendencia, recomendacion = determine_trend_and_recommendation(
                rsi, macd_val, signal_val, p.cambio_pct_24h
            )

            indicadores.append(IndicadorTecnico(
                simbolo=p.simbolo,
                precio_actual=p.precio,
                rsi=rsi,
                macd=macd_val,
                macd_signal=signal_val,
                macd_histograma=histograma,
                tendencia=tendencia,
                recomendacion=recomendacion,
                cambio_pct_24h=p.cambio_pct_24h,
                dominancia=55.0 if p.simbolo == "BTC" else None,
                timestamp=datetime.datetime.utcnow()
            ))
        return indicadores
