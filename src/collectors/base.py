from abc import ABC, abstractmethod
from typing import Any
import asyncio

class BaseCollector(ABC):
    """
    Clase base para todos los recolectores de datos.
    Fuerza a implementar el método collect() de forma asíncrona.
    """
    def __init__(self, name: str, timeout: int = 30):
        self.name = name
        self.timeout = timeout

    @abstractmethod
    async def fetch_data(self) -> Any:
        pass

    async def collect(self) -> Any:
        try:
            # Envolvemos en asyncio.wait_for para asegurar que no se cuelgue el pipeline
            result = await asyncio.wait_for(self.fetch_data(), timeout=self.timeout)
            return result
        except asyncio.TimeoutError:
            print(f"[Error] Collector '{self.name}' excedió el timeout de {self.timeout}s.")
            return []
        except Exception as e:
            print(f"[Error] Fallo en collector '{self.name}': {e}")
            return []
