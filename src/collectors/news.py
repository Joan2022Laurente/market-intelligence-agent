import asyncio
import random
from typing import List
from schemas.news import EventoNoticia
from collectors.base import BaseCollector

class MockNewsCollector(BaseCollector):
    def __init__(self):
        super().__init__(name="MockNews", timeout=10)

    async def fetch_data(self) -> List[EventoNoticia]:
        # Simula latencia de red
        await asyncio.sleep(random.uniform(0.5, 2.0))
        
        return [
            EventoNoticia(
                titulo="Aprobación de nuevo ETF de Crypto",
                resumen="La SEC ha aprobado un nuevo fondo cotizado...",
                fuente="MockNews Network",
                url="http://mocknews.com/1",
                impacto_estimado="alto",
                categoria="Cripto"
            ),
            EventoNoticia(
                titulo="Lesión del delantero estrella",
                resumen="El jugador se perderá el próximo clásico por lesión de rodilla...",
                fuente="Mock Sports News",
                url="http://mocksports.com/1",
                impacto_estimado="alto",
                categoria="Deportes"
            )
        ]
