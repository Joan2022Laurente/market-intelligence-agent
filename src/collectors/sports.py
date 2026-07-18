import asyncio
import random
from typing import List
from schemas.sports import CuotaDeportiva
from collectors.base import BaseCollector

class MockSportsCollector(BaseCollector):
    def __init__(self):
        super().__init__(name="MockSports", timeout=10)

    async def fetch_data(self) -> List[CuotaDeportiva]:
        # Simula latencia de red
        await asyncio.sleep(random.uniform(0.5, 2.0))
        
        return [
            CuotaDeportiva(
                evento="Real Madrid vs Barcelona",
                equipo_local="Real Madrid",
                equipo_visitante="Barcelona",
                cuota_local=random.uniform(1.8, 2.5),
                cuota_empate=random.uniform(3.0, 4.5),
                cuota_visitante=random.uniform(2.5, 3.5),
                fuente="MockBet"
            ),
            CuotaDeportiva(
                evento="Arsenal vs Manchester City",
                equipo_local="Arsenal",
                equipo_visitante="Manchester City",
                cuota_local=random.uniform(2.5, 3.5),
                cuota_empate=random.uniform(3.0, 4.0),
                cuota_visitante=random.uniform(1.8, 2.5),
                fuente="MockBet"
            )
        ]
