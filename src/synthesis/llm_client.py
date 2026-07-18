import json
import aiohttp
from typing import Dict, Any

class LocalLLMClient:
    """
    Cliente para comunicarse con un LLM local compatible con OpenAI API
    (como vLLM, Ollama o LM Studio) corriendo en la GPU L4/L40S.
    """
    def __init__(self, base_url: str = "http://localhost:11434/api/chat", model_name: str = "qwen2.5:32b-instruct-q4_K_M"):
        self.base_url = base_url
        self.model_name = model_name

    async def generate_synthesis(self, context_data: Dict[str, Any]) -> str:
        """
        Toma los datos puros (ya calculados y analizados) y pide al LLM
        que redacte el informe. El LLM NO calcula nada.
        """
        system_prompt = (
            "Eres un asesor de inversiones y analista cuantitativo de máximo nivel. "
            "Tus clientes son principiantes que necesitan que les expliques, en español, "
            "con lenguaje claro pero profesional, qué está pasando en el mercado y QUÉ DEBEN HACER. "
            "\n\nTu estructura de respuesta SIEMPRE debe ser:\n"
            "1. **Contexto del Mercado**: Explica brevemente el clima general (bullish/bearish, "
            "volátil/estable) basándote en los RSI y MACD proporcionados.\n"
            "2. **Análisis Cripto**: Para cada activo, explica QUÉ SIGNIFICA su RSI y MACD para un "
            "novato. Si RSI ~50 hay neutralidad, si >70 está sobrecomprado, si <30 sobrevendido. "
            "Explica si el MACD es positivo o negativo y su implicación. "
            "Da una recomendación concreta: COMPRAR, MANTENER o ESPERAR con justificación.\n"
            "3. **Análisis Deportivo**: Si hay value bets detectados (probabilidad_implicita < probabilidad_real), "
            "explícale al usuario por qué esa apuesta tiene valor esperado positivo, cuánto "
            "arriesgar (nunca más del 2-5% del bankroll) y qué significa la confianza.\n"
            "4. **Impacto de Noticias**: Analiza las noticias del día y su posible efecto en los precios "
            "de los activos. Si hay noticias regulatorias negativas, údvierte. Si son positivas, indica "
            "el sentimiento del mercado.\n"
            "5. **Resumen Ejecutivo en 3 Bullets**: Tres acciones concretas que el inversor puede tomar "
            "HOY basadas en los datos.\n\n"
            "REGLA CRÍTICA: Usa SOLO los números proporcionados. No inventes precios. Sí puedes e "
            "DEBES dar tu opinión e interpretación profesional sobre esos números."
        )
        
        user_prompt = f"Redacta el informe de hoy basándote en los siguientes datos pre-calculados:\n\n{json.dumps(context_data, indent=2, default=str)}"

        payload = {
            "model": self.model_name,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            "stream": False
        }

        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(self.base_url, json=payload, timeout=180) as response:
                    if response.status == 200:
                        data = await response.json()
                        # Formato Ollama por defecto, ajustar si es vLLM (OpenAI format)
                        return data.get("message", {}).get("content", "Error leyendo respuesta del LLM.")
                    else:
                        return f"Error en LLM API: Status {response.status}"
        except Exception as e:
            # En caso de fallo del LLM, el pipeline no debe caer, devuelve fallback.
            print(f"[Error LLM] {repr(e)}")
            return "No se pudo generar la síntesis narrativa por un error en el LLM local. Revisar logs."
