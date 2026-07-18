import asyncio
import json
import sys
import os
import json
from typing import Dict, Any

# Asegurar que importamos desde src
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import aiohttp

class LocalLLMClient:
    """
    Cliente para comunicarse con un LLM local compatible con la API de Ollama
    (Ollama) corriendo en la GPU L4/L40S.
    """
    def __init__(self, base_url: str = "http://localhost:11434/api/chat", model_name: str = "qwen2.5:32b-instruct-q4_K_M"):
        self.base_url = base_url
        self.model_name = model_name

    async def generate_synthesis(self, context_data: Dict[str, Any]) -> str:
        """
        Toma los datos pre-calculados (RSI real, MACD real, cuotas reales, noticias clasificadas)
        y pide al LLM que redacte el análisis como un asesor profesional.
        El LLM NO calcula nada — solo interpreta y comunica.
        """
        system_prompt = (
            "Eres un asesor de inversiones cuantitativo de máximo nivel especializado en criptomonedas y apuestas deportivas. "
            "Tus clientes son principiantes que necesitan guía clara, en español, con lenguaje accesible pero profesional. "
            "Tu objetivo es que cualquier persona sin conocimientos financieros entienda QUÉ está pasando y QUÉ debe hacer HOY.\n\n"
            "ESTRUCTURA OBLIGATORIA DE TU RESPUESTA:\n\n"
            "### 🌍 Contexto del Mercado\n"
            "Explica en 2-3 frases si el mercado cripto está en fase alcista (bull), bajista (bear) o lateral (sideways). "
            "Menciona el sentimiento de las noticias del día.\n\n"
            "### 💰 Análisis Cripto Detallado\n"
            "Para CADA activo proporcionado:\n"
            "- **[SÍMBOLO] — $[PRECIO]** (Cambio 24h: [%])\n"
            "  - RSI [valor]: explica qué significa para un novato. ¿Sobrecomprado? ¿Sobrevendido? ¿Neutral?\n"
            "  - MACD: ¿está cruzando al alza o a la baja? ¿Qué implica?\n"
            "  - **Veredicto: [COMPRAR/MANTENER/ESPERAR/REDUCIR]** — justifica en 1 frase\n\n"
            "### ⚽ Análisis Deportivo\n"
            "Para CADA partido proporcionado:\n"
            "- Si hay value bet: explica el concepto de 'valor esperado' para un novato, por qué ESTA apuesta tiene EV positivo, "
            "y cuánto arriesgar (nunca más del 2-5% del bankroll). Indica si el partido es REAL o SIMULADO.\n"
            "- Si NO hay value bet: explica brevemente por qué no es recomendable apostar.\n\n"
            "### 📰 Impacto de las Noticias\n"
            "Menciona solo las noticias de impacto ALTO o MEDIO y explica cómo podrían afectar el precio de los activos. "
            "¿Es positivo o negativo para el mercado? ¿A corto o largo plazo?\n\n"
            "### ✅ Plan de Acción — 3 Pasos Concretos para HOY\n"
            "Bullet points con acciones específicas, ordenadas por prioridad.\n\n"
            "⚠️ REGLAS CRÍTICAS:\n"
            "- USA SOLO los números proporcionados en el JSON. Cítalos exactamente.\n"
            "- Si los datos deportivos están marcados como 'es_simulado: true', ADVIÉRTELO explícitamente.\n"
            "- No des consejos que excedan el alcance de los datos recibidos.\n"
            "- Responde SIEMPRE en español."
        )

        user_prompt = (
            f"Analiza los siguientes datos de mercado pre-calculados y redacta el informe de asesoría:\n\n"
            f"{json.dumps(context_data, indent=2, default=str)}"
        )

        payload = {
            "model": self.model_name,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            "stream": False,
            "options": {
                "temperature": 0.3,   # Bajo para análisis factual consistente
                "num_predict": 1500   # Respuesta suficientemente larga
            }
        }

        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(self.base_url, json=payload, timeout=300) as response:
                    if response.status == 200:
                        data = await response.json()
                        return data.get("message", {}).get("content", "Error leyendo respuesta del LLM.")
                    else:
                        body = await response.text()
                        return f"Error en LLM API: Status {response.status} — {body[:200]}"
        except Exception as e:
            print(f"[Error LLM] {repr(e)}")
            return "⚠️ No se pudo generar la síntesis narrativa. El LLM local no está disponible. Revisa los datos crudos en las secciones de abajo."
