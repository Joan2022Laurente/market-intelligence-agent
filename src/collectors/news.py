import asyncio
import aiohttp
import xml.etree.ElementTree as ET
from typing import List
from schemas.news import EventoNoticia
from collectors.base import BaseCollector
import datetime

# Palabras clave para clasificación de impacto
NEGATIVE_KEYWORDS = [
    "hack", "hacked", "exploit", "ban", "banned", "crash", "scam", "fraud",
    "seized", "collapse", "shutdown", "lawsuit", "penalty", "fine", "probe",
    "investigation", "malware", "phishing", "stolen", "theft", "arrest",
    "regulation", "crackdown", "delisted", "delist", "warning", "risk"
]
POSITIVE_KEYWORDS = [
    "etf", "approved", "approval", "rally", "surge", "all-time high", "ath",
    "institutional", "partnership", "launch", "bullish", "adoption", "upgrade",
    "milestone", "record", "invest", "buy", "growth", "gains", "profit",
    "breakthrough", "integration", "listed", "accumulate"
]

FEEDS = [
    ("https://cointelegraph.com/rss", "Cointelegraph"),
    ("https://www.coindesk.com/arc/outboundfeeds/rss/", "CoinDesk"),
    ("https://decrypt.co/feed", "Decrypt"),
]

def _classify_impact(titulo: str, descripcion: str) -> str:
    text = (titulo + " " + descripcion).lower()
    neg_score = sum(1 for kw in NEGATIVE_KEYWORDS if kw in text)
    pos_score = sum(1 for kw in POSITIVE_KEYWORDS if kw in text)
    if neg_score >= 2 or pos_score >= 2:
        return "alto"
    if neg_score == 1 or pos_score == 1:
        return "medio"
    return "bajo"

def _classify_category(titulo: str) -> str:
    text = titulo.lower()
    if any(w in text for w in ["bitcoin", "btc", "ethereum", "eth", "solana", "sol", "crypto", "blockchain", "defi", "nft", "token"]):
        return "Cripto"
    if any(w in text for w in ["regulation", "sec", "cftc", "ban", "law", "legal", "government"]):
        return "Regulación"
    if any(w in text for w in ["hack", "exploit", "malware", "phishing", "stolen", "breach"]):
        return "Hack/Seguridad"
    if any(w in text for w in ["bank", "fed", "inflation", "rate", "gdp", "recession", "macro"]):
        return "Macro"
    return "General"

class RSSNewsCollector(BaseCollector):
    def __init__(self):
        super().__init__(name="RSSNews", timeout=20)

    async def _fetch_feed(self, session: aiohttp.ClientSession, url: str, fuente: str) -> List[EventoNoticia]:
        try:
            async with session.get(url) as response:
                if response.status != 200:
                    return []
                xml_data = await response.text()

            resultados = []
            root = ET.fromstring(xml_data)
            channel = root.find("channel")
            if channel is None:
                return []

            for item in channel.findall("item")[:4]:  # 4 por fuente
                title_el = item.find("title")
                link_el = item.find("link")
                desc_el = item.find("description")

                titulo = title_el.text if title_el is not None else "Sin título"
                link = link_el.text if link_el is not None else ""
                descripcion = desc_el.text if desc_el is not None else ""
                if descripcion:
                    descripcion = descripcion.replace("<p>", "").replace("</p>", "").strip()[:250] + "..."

                impacto = _classify_impact(titulo, descripcion)
                categoria = _classify_category(titulo)

                resultados.append(
                    EventoNoticia(
                        titulo=titulo,
                        resumen=descripcion,
                        fuente=fuente,
                        url=link,
                        impacto_estimado=impacto,
                        categoria=categoria,
                        timestamp=datetime.datetime.utcnow()
                    )
                )
            return resultados
        except Exception as e:
            print(f"[Error RSS {fuente}] {e}")
            return []

    async def fetch_data(self) -> List[EventoNoticia]:
        async with aiohttp.ClientSession() as session:
            tasks = [self._fetch_feed(session, url, fuente) for url, fuente in FEEDS]
            results = await asyncio.gather(*tasks)

        # Combinar y deduplicar por título similar
        all_news: List[EventoNoticia] = []
        seen_titles = set()
        for feed_results in results:
            for noticia in feed_results:
                # Deduplicar: si ya hay un título muy similar, saltar
                title_key = noticia.titulo.lower()[:50]
                if title_key not in seen_titles:
                    seen_titles.add(title_key)
                    all_news.append(noticia)

        # Ordenar: alto impacto primero
        impact_order = {"alto": 0, "medio": 1, "bajo": 2}
        all_news.sort(key=lambda n: impact_order.get(n.impacto_estimado, 1))

        return all_news[:10]  # Máximo 10 noticias al LLM
