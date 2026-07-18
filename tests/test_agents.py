from schemas.crypto import PrecioActivo
from schemas.sports import CuotaDeportiva
from agents.crypto_analyst import CryptoAnalyst
from agents.sports_analyst import SportsAnalyst
import datetime

def test_crypto_analyst_math():
    precios = [
        PrecioActivo(
            simbolo="BTC",
            precio=68000.0,
            volumen_24h=1000,
            fuente="Mock",
            timestamp=datetime.datetime.utcnow()
        )
    ]
    indicadores = CryptoAnalyst.calculate_technical_indicators(precios)
    assert len(indicadores) == 1
    # Verifica que detecte el over 65000 y asigne RSI=75
    assert indicadores[0].rsi == 75.0
    # Verifica MACD: (68000*0.05) - (68000*0.04) = 3400 - 2720 = 680
    assert abs(indicadores[0].macd - 680.0) < 0.1

def test_sports_analyst_value_bet():
    cuotas = [
        CuotaDeportiva(
            evento="Test vs Test",
            equipo_local="Test",
            equipo_visitante="Test",
            cuota_local=2.0,       # Implied 50%
            cuota_empate=3.0,      # Implied 33.3%
            cuota_visitante=4.0,   # Implied 25%
            fuente="MockBet",
            timestamp=datetime.datetime.utcnow()
        )
    ]
    analisis = SportsAnalyst.analyze_odds(cuotas)
    assert len(analisis) == 1
    
    # Margin = (0.5 + 0.333 + 0.25) - 1 = 1.0833 - 1 = 0.0833
    # Real local = 0.5 / 1.0833 = 0.4615
    # Nuestro modelo local = 0.4615 + 0.05 = 0.5115
    # Implied local + 0.02 = 0.52
    # 0.5115 > 0.52 => False => No value bet
    assert analisis[0].value_bet_detectada == False
