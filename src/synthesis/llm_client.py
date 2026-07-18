import json
import aiohttp
from typing import Dict, Any

class LocalLLMClient:
    """
    Cliente para comunicarse con un LLM local compatible con OpenAI API
    (como vLLM, Ollama o LM Studio) corriendo en la GPU L4/L40S.
    """
    def __init__(self, base_url: str = "http://localhost:11434/api/chat", model_name: str = "llama3"):
        self.base_url = base_url
        self.model_name = model_name

    async def generate_synthesis(self, context_data: Dict[str, Any]) -> str:
        """
        Toma los datos puros (ya calculados y analizados) y pide al LLM
        que redacte el informe. El LLM NO calcula nada.
        """
        system_prompt = (
            "Eres un analista cuantitativo redactando un informe de mercado. "
            "Tu única tarea es tomar los datos y conclusiones matemáticas proporcionadas "
            "y redactarlas en un lenguaje profesional, claro y objetivo. "
            "REGLA ESTRICTA: NO inventes números. NO opines. NO cambies las probabilidades. "
            "Limítate a explicar por qué el sistema llegó a esas conclusiones basándote "
            "exclusivamente en los datos proporcionados."
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
