import asyncio
import aiohttp
import xml.etree.ElementTree as ET
from typing import List
from schemas.news import EventoNoticia
from collectors.base import BaseCollector
import datetime

class RSSNewsCollector(BaseCollector):
    def __init__(self):
        super().__init__(name="RSSNews", timeout=15)
        # Usaremos el feed RSS público de Cointelegraph
        self.feed_url = "https://cointelegraph.com/rss"

    async def fetch_data(self) -> List[EventoNoticia]:
        async with aiohttp.ClientSession() as session:
            async with session.get(self.feed_url) as response:
                if response.status != 200:
                    print(f"[Error RSS] Status {response.status}")
                    return []
                xml_data = await response.text()
                
        resultados = []
        try:
            root = ET.fromstring(xml_data)
            # En RSS, los items están dentro de channel
            channel = root.find("channel")
            if channel is not None:
                # Tomamos solo las 5 noticias más recientes para no saturar el LLM
                for item in channel.findall("item")[:5]:
                    title = item.find("title").text if item.find("title") is not None else "Sin título"
                    link = item.find("link").text if item.find("link") is not None else ""
                    description = item.find("description").text if item.find("description") is not None else "Sin descripción"
                    
                    # Limpieza básica de HTML en la descripción si lo hubiera
                    description = description.replace("<p>", "").replace("</p>", "").strip()[:200] + "..."
                    
                    resultados.append(
                        EventoNoticia(
                            titulo=title,
                            resumen=description,
                            fuente="Cointelegraph",
                            url=link,
                            impacto_estimado="medio", # Lógica simplificada
                            categoria="Cripto",
                            timestamp=datetime.datetime.utcnow()
                        )
                    )
        except Exception as e:
            print(f"[Error Parseando RSS] {e}")
            
        return resultados
