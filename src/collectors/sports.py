import asyncio
import aiohttp
import random
import os
from typing import List
from schemas.sports import CuotaDeportiva
from collectors.base import BaseCollector
import datetime

class RealSportsCollector(BaseCollector):
    def __init__(self):
        super().__init__(name="TheOddsAPI", timeout=15)
        self.api_key = os.environ.get("ODDS_API_KEY")
        # soccer_epl = Premier League, puedes cambiar a soccer_epl, americanfootball_nfl, basketball_nba, etc.
        self.sport = "soccer_epl"
        self.base_url = "https://api.the-odds-api.com/v4"

    async def fetch_data(self) -> List[CuotaDeportiva]:
        if not self.api_key:
            print("[Info] No se encontró ODDS_API_KEY. Usando datos deportivos simulados (Mock).")
            return self._get_mock_data()

        url = f"{self.base_url}/sports/{self.sport}/odds/"
        params = {
            "apiKey": self.api_key,
            "regions": "eu",
            "markets": "h2h",
            "oddsFormat": "decimal"
        }

        async with aiohttp.ClientSession() as session:
            async with session.get(url, params=params) as response:
                if response.status == 401:
                    print("[Error The-Odds-API] API Key inválida. Usando Mock.")
                    return self._get_mock_data()
                if response.status == 422:
                    print("[Info] No hay partidos disponibles en este momento. Usando Mock.")
                    return self._get_mock_data()
                if response.status != 200:
                    print(f"[Error The-Odds-API] Status {response.status}. Usando Mock.")
                    return self._get_mock_data()

                data = await response.json()

                # Log de requests restantes
                remaining = response.headers.get("x-requests-remaining", "?")
                used = response.headers.get("x-requests-used", "?")
                print(f"[TheOddsAPI] Requests usados: {used}, restantes: {remaining}")

        if not data:
            print("[Info] No hay partidos disponibles en este momento. Usando Mock.")
            return self._get_mock_data()

        resultados = []
        try:
            for game in data[:5]:  # Los 5 próximos partidos
                evento = f"{game['home_team']} vs {game['away_team']}"
                if not game.get('bookmakers'):
                    continue

                # Usar el primer bookmaker disponible
                bookmaker = game['bookmakers'][0]
                market = bookmaker['markets'][0]
                outcomes = {o['name']: o['price'] for o in market['outcomes']}

                cuota_local = outcomes.get(game['home_team'], 0)
                cuota_visitante = outcomes.get(game['away_team'], 0)
                cuota_empate = outcomes.get('Draw', None)

                if cuota_local and cuota_visitante:
                    resultados.append(
                        CuotaDeportiva(
                            evento=evento,
                            equipo_local=game['home_team'],
                            equipo_visitante=game['away_team'],
                            cuota_local=cuota_local,
                            cuota_empate=cuota_empate,
                            cuota_visitante=cuota_visitante,
                            fuente=f"TheOddsAPI ({bookmaker['title']})",
                            es_simulado=False,
                            timestamp=datetime.datetime.utcnow()
                        )
                    )
        except Exception as e:
            print(f"[Error Parseando The-Odds-API] {e}. Usando Mock.")
            return self._get_mock_data()

        return resultados if resultados else self._get_mock_data()

    def _get_mock_data(self) -> List[CuotaDeportiva]:
        """Datos simulados solo como fallback. Marcados explícitamente como simulados."""
        return [
            CuotaDeportiva(
                evento="Arsenal vs Manchester City [SIMULADO]",
                equipo_local="Arsenal",
                equipo_visitante="Manchester City",
                cuota_local=round(random.uniform(2.5, 3.5), 2),
                cuota_empate=round(random.uniform(3.0, 4.0), 2),
                cuota_visitante=round(random.uniform(1.8, 2.5), 2),
                fuente="Datos Simulados (sin API Key)",
                es_simulado=True,
                timestamp=datetime.datetime.utcnow()
            )
        ]
