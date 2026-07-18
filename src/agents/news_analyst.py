from typing import List, Dict
from schemas.news import EventoNoticia

class NewsAnalyst:
    """
    Agente para deduplicar y agrupar noticias.
    """
    
    @staticmethod
    def deduplicate_and_group(noticias: List[EventoNoticia]) -> Dict[str, List[EventoNoticia]]:
        """
        Agrupa noticias por categoría y elimina duplicados exactos o muy similares.
        """
        grupos = {}
        vistos = set()
        
        for n in noticias:
            # Lógica simple de deduplicación: si el título es casi igual
            # En producción usar embeddings o TF-IDF
            tit_lower = n.titulo.lower()[:30] # Primeros 30 chars
            
            if tit_lower in vistos:
                continue
                
            vistos.add(tit_lower)
            
            if n.categoria not in grupos:
                grupos[n.categoria] = []
            grupos[n.categoria].append(n)
            
        return grupos
