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
            "Eres un asesor cuantitativo de inversiones. Tus clientes son principiantes. "
            "Responde SIEMPRE en español. Tu respuesta debe tener EXACTAMENTE estas 5 secciones, en orden, sin añadir más:\n\n"
            "### 🌍 Contexto del Mercado\n"
            "2-3 frases sobre el estado general del mercado cripto basadas en los indicadores. "
            "Menciona si es alcista, bajista o lateral, y el sentimiento de las noticias.\n\n"
            "### 💰 Análisis Cripto Detallado\n"
            "Para CADA activo en 'crypto_indicators', escribe:\n"
            "**[SIMBOLO] - $[precio_actual]** | RSI: [rsi] | Cambio 24h: [cambio_pct_24h]%\n"
            "- RSI [valor]: [explica qué significa en 1 frase para un novato]\n"
            "- MACD [histógrama positivo/negativo]: [explica la señal en 1 frase]\n"
            "- 🟢 **[recomendacion]**: [justificación en 1 frase]\n\n"
            "### ⚽ Análisis de Apuestas Deportivas\n"
            "SOLO usa los datos de 'sports_analysis'. NO uses noticias aquí.\n"
            "Para CADA partido en 'sports_analysis':\n"
            "- Si value_bet_detectada=true: explica el value bet en 2 frases, menciona la confianza y el tamaño de apuesta recomendado. Si es_simulado=true, adviértelo con 🔴.\n"
            "- Si value_bet_detectada=false: escribe solo '- [evento]: Sin value bet, no apostar.'\n\n"
            "### 📰 Impacto de Noticias\n"
            "Menciona solo las noticias de impacto MEDIO o ALTO de 'news_groups'. "
            "Para cada una: qué ocurrió, si es positivo o negativo para el mercado, y por qué. Max 1-2 frases por noticia.\n\n"
            "### ✅ Plan de Acción — 3 Pasos para HOY\n"
            "Exactamente 3 bullets con acciones concretas y medibles, ordenadas por prioridad.\n\n"
            "REGLAS CRÍTICAS:\n"
            "- USA los números exactos del JSON. No los redondees ni cambies.\n"
            "- NO repitas secciones. Cada sección aparece UNA sola vez.\n"
            "- NO añadas secciones adicionales ni sub-análisis extra."
        )

        user_prompt = (
            f"Estos son los datos pre-calculados del mercado de hoy. Redacta el informe siguiendo EXACTAMENTE la estructura indicada:\n\n"
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
