from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field

class CuotaDeportiva(BaseModel):
    evento: str = Field(..., description="Nombre del evento o partido (ej. Real Madrid vs Barcelona)")
    equipo_local: str = Field(..., description="Nombre del equipo local")
    equipo_visitante: str = Field(..., description="Nombre del equipo visitante")
    cuota_local: float = Field(..., description="Cuota decimal para victoria local")
    cuota_empate: Optional[float] = Field(None, description="Cuota decimal para empate (si aplica)")
    cuota_visitante: float = Field(..., description="Cuota decimal para victoria visitante")
    fuente: str = Field(..., description="Casa de apuestas o proveedor de datos")
    es_simulado: bool = Field(False, description="True si los datos son simulados, False si son reales")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Fecha y hora de lectura")

class AnalisisPartido(BaseModel):
    evento: str
    probabilidad_local: float = Field(..., description="Probabilidad real estimada para el local (0-1)")
    probabilidad_empate: Optional[float] = Field(None, description="Probabilidad real estimada empate")
    probabilidad_visitante: float = Field(..., description="Probabilidad real estimada visitante")
    value_bet_detectada: bool = Field(False, description="¿Existe una apuesta de valor?")
    recomendacion: Optional[str] = Field(None, description="Recomendación específica de apuesta")
    confianza: float = Field(..., description="Nivel de confianza en la predicción (0-1)")
    es_simulado: bool = Field(False, description="True si está basado en datos simulados")
    timestamp: datetime = Field(default_factory=datetime.utcnow)
