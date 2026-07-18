from typing import Dict, List
from schemas.news import EventoNoticia


class NewsAnalyst:
    """
    Agente de análisis de noticias.
    Agrupa, deduplica y organiza las noticias por nivel de impacto.
    """

    @staticmethod
    def deduplicate_and_group(noticias: List[EventoNoticia]) -> Dict[str, List[EventoNoticia]]:
        """
        Deduplica noticias por similitud de título y las agrupa por impacto.
        """
        groups: Dict[str, List[EventoNoticia]] = {"alto": [], "medio": [], "bajo": []}
        seen_titles = set()

        for n in noticias:
            title_key = n.titulo.lower()[:60]
            if title_key not in seen_titles:
                seen_titles.add(title_key)
                impacto = n.impacto_estimado
                if impacto in groups:
                    groups[impacto].append(n)

        return groups

    @staticmethod
    def get_sentiment_summary(groups: Dict[str, List[EventoNoticia]]) -> str:
        """
        Genera un resumen de sentimiento del mercado basado en noticias.
        """
        n_alto = len(groups.get("alto", []))
        n_medio = len(groups.get("medio", []))
        n_bajo = len(groups.get("bajo", []))

        if n_alto >= 3:
            return "MUY_NEGATIVO/POSITIVO (alta volatilidad esperada)"
        if n_alto >= 1:
            return "MIXTO (hay eventos de alto impacto)"
        if n_medio >= 3:
            return "NEUTRAL con ruido"
        return "CALMADO"
