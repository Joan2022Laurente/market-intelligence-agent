from typing import List
from schemas.sports import CuotaDeportiva, AnalisisPartido
import datetime


class SportsAnalyst:
    """
    Agente de análisis matemático para Deportes.
    Usa el modelo de probabilidad implícita + ajuste por margen de casa.
    """

    @staticmethod
    def analyze_odds(cuotas: List[CuotaDeportiva]) -> List[AnalisisPartido]:
        resultados = []
        for c in cuotas:
            # 1. Calcular probabilidad implícita (1 / cuota)
            implied_local = 1.0 / c.cuota_local
            implied_visitante = 1.0 / c.cuota_visitante
            implied_empate = (1.0 / c.cuota_empate) if c.cuota_empate else 0.0

            # 2. Calcular el margen del bookmaker (overround)
            margin = (implied_local + implied_visitante + implied_empate) - 1.0

            # 3. Probabilidad "real" estimada sin el margen del bookmaker
            total_implied = implied_local + implied_visitante + implied_empate
            real_local = implied_local / total_implied
            real_visitante = implied_visitante / total_implied
            real_empate = (implied_empate / total_implied) if c.cuota_empate else None

            # 4. Nuestro modelo: aplica un edge estadístico al local de +3-5%
            # (En producción se usaría Elo, xG, historial H2H, lesiones)
            edge = 0.04 if not c.es_simulado else 0.05  # Edge ligeramente más conservador con datos reales
            nuestro_modelo_local = min(real_local + edge, 0.99)

            # 5. Value Bet: si nuestra probabilidad > probabilidad implícita por un margen de seguridad
            # EV positivo = nuestro_modelo * cuota_real > 1.0
            ev = nuestro_modelo_local * c.cuota_local
            value_bet = ev > 1.05  # Requerimos al menos 5% de EV positivo

            # 6. Calcular confianza basada en cuánto supera el EV al umbral
            confianza = min(0.5 + (ev - 1.0) * 2, 0.95) if value_bet else max(0.1, ev - 0.5)

            recomendacion = None
            if value_bet:
                pct_bankroll = "2-3%" if confianza < 0.7 else "4-5%"
                recomendacion = f"Apostar a {c.equipo_local} — Apostar {pct_bankroll} del bankroll"

            resultados.append(AnalisisPartido(
                evento=c.evento,
                probabilidad_local=round(nuestro_modelo_local, 4),
                probabilidad_empate=round(real_empate, 4) if real_empate else None,
                probabilidad_visitante=round(real_visitante, 4),
                value_bet_detectada=value_bet,
                recomendacion=recomendacion,
                confianza=round(confianza, 4),
                es_simulado=c.es_simulado,
                timestamp=datetime.datetime.utcnow()
            ))

        return resultados
