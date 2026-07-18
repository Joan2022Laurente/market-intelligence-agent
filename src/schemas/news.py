from datetime import datetime
from typing import Literal
from pydantic import BaseModel, Field

class EventoNoticia(BaseModel):
    titulo: str = Field(..., description="Título de la noticia")
    resumen: str = Field(..., description="Resumen breve o contenido")
    fuente: str = Field(..., description="Portal o medio que lo publicó")
    url: str = Field(..., description="Enlace original")
    impacto_estimado: Literal["alto", "medio", "bajo"] = Field(..., description="Estimación de impacto en el mercado")
    categoria: str = Field(..., description="Categoría (ej. Cripto, Regulación, Deportes, Macro)")
    timestamp: datetime = Field(default_factory=datetime.utcnow)
