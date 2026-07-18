from typing import List
from schemas.sports import CuotaDeportiva, AnalisisPartido
import datetime

class SportsAnalyst:
    """
    Agente de análisis matemático para Deportes.
    """
    
    @staticmethod
    def analyze_odds(cuotas: List[CuotaDeportiva]) -> List[AnalisisPartido]:
        resultados = []
        for c in cuotas:
            # 1. Calcular probabilidad implícita (1 / cuota)
            # 2. Ajustar por el margen de la casa de apuestas (overround)
            implied_local = 1 / c.cuota_local
            implied_visitante = 1 / c.cuota_visitante
            implied_empate = (1 / c.cuota_empate) if c.cuota_empate else 0
            
            margin = (implied_local + implied_visitante + implied_empate) - 1.0
            
            # Probabilidad "real" estimada quitando el margen (forma simple)
            real_local = implied_local / (1 + margin)
            real_visitante = implied_visitante / (1 + margin)
            real_empate = (implied_empate / (1 + margin)) if c.cuota_empate else None
            
            # Modelo estadístico propio (en producción usaría Elo, xG, lesiones)
            # Para el mock, asumimos que nuestro modelo predice un 5% más a favor del local
            nuestro_modelo_local = real_local + 0.05
            
            # ¿Es value bet? Si nuestro modelo dice que la prob es mayor a la implícita real + un margen
            value_bet = nuestro_modelo_local > (implied_local + 0.02)
            
            recomendacion = f"Apostar a {c.equipo_local}" if value_bet else "No apostar"
            
            resultados.append(AnalisisPartido(
                evento=c.evento,
                probabilidad_local=nuestro_modelo_local,
                probabilidad_empate=real_empate,
                probabilidad_visitante=real_visitante,
                value_bet_detectada=value_bet,
                recomendacion=recomendacion if value_bet else None,
                confianza=0.85, # Confianza del modelo matemático
                timestamp=datetime.datetime.utcnow()
            ))
            
        return resultados
