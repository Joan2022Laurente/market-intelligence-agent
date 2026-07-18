from typing import List
from schemas.crypto import PrecioActivo, IndicadorTecnico
import datetime

class CryptoAnalyst:
    """
    Agente de análisis determinístico para Cripto.
    NO usa LLM. Todo es matemática pura.
    """
    
    @staticmethod
    def calculate_technical_indicators(precios: List[PrecioActivo]) -> List[IndicadorTecnico]:
        """
        En un escenario real, esto tomaría un historial de precios para calcular
        el RSI y MACD real (usando pandas/ta-lib).
        Aquí simulamos la lógica matemática pura.
        """
        indicadores = []
        for p in precios:
            # Lógica determinística: por ejemplo, si el precio subió muy rápido (simulado)
            # En producción esto usaría datos históricos de 14 periodos.
            pseudo_rsi = 50.0 
            if p.precio > 65000 and p.simbolo == "BTC":
                pseudo_rsi = 75.0
            
            pseudo_macd = (p.precio * 0.05) - (p.precio * 0.04)
            
            indicadores.append(IndicadorTecnico(
                simbolo=p.simbolo,
                rsi=pseudo_rsi,
                macd=pseudo_macd,
                dominancia=55.0 if p.simbolo == "BTC" else None,
                timestamp=datetime.datetime.utcnow()
            ))
        return indicadores
