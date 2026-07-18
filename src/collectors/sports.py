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
        # Usamos soccer_epl (Premier League) o upcoming como ejemplo
        self.url = "https://api.the-odds-api.com/v4/sports/soccer_epl/odds/?regions=eu&markets=h2h"

    async def fetch_data(self) -> List[CuotaDeportiva]:
        if not self.api_key:
            print("[Info] No se encontró ODDS_API_KEY. Usando datos deportivos simulados (Mock).")
            return self._get_mock_data()
            
        async with aiohttp.ClientSession() as session:
            # Agregamos el apiKey a los params
            url_with_key = f"{self.url}&apiKey={self.api_key}"
            async with session.get(url_with_key) as response:
                if response.status != 200:
                    print(f"[Error The-Odds-API] Status {response.status}. Usando Mock.")
                    return self._get_mock_data()
                
                data = await response.json()
                
        resultados = []
        try:
            for game in data[:3]: # Solo los 3 próximos partidos
                evento = f"{game['home_team']} vs {game['away_team']}"
                # Buscamos el primer bookmaker (ej. Pinnacle o Unibet)
                bookmaker = game['bookmakers'][0] if game['bookmakers'] else None
                if not bookmaker:
                    continue
                    
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
                            timestamp=datetime.datetime.utcnow()
                        )
                    )
        except Exception as e:
            print(f"[Error Parseando The-Odds-API] {e}. Usando Mock.")
            return self._get_mock_data()
            
        return resultados

    def _get_mock_data(self) -> List[CuotaDeportiva]:
        return [
            CuotaDeportiva(
                evento="Arsenal vs Manchester City",
                equipo_local="Arsenal",
                equipo_visitante="Manchester City",
                cuota_local=random.uniform(2.5, 3.5),
                cuota_empate=random.uniform(3.0, 4.0),
                cuota_visitante=random.uniform(1.8, 2.5),
                fuente="MockBet",
                timestamp=datetime.datetime.utcnow()
            )
        ]
