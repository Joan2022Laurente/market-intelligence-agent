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
    Cliente para comunicarse con la API de OpenRouter, utilizando el modelo
    gratuito tencent/hy3:free (Tencent Hunyuan 3).
    """
    def __init__(self, model_name: str = "tencent/hy3:free"):
        self.base_url = "https://openrouter.ai/api/v1/chat/completions"
        self.model_name = model_name
        self.api_key = os.environ.get("OPENROUTER_API_KEY")

    async def generate_synthesis(self, context_data: Dict[str, Any]) -> str:
        """
        Toma los datos pre-calculados (RSI real, MACD real, cuotas reales, noticias clasificadas)
        y pide al LLM que redacte el análisis como un asesor profesional.
        El LLM NO calcula nada — solo interpreta y comunica.
        """
        system_prompt = (
            "Eres un asesor cuantitativo de inversiones privado, exclusivo para tu cliente JOAN JOAQUIN CALLAÑAUPA LAURENTE. "
            "Conoces su contexto financiero a la perfección: Joan está construyendo su portafolio con un micro-bankroll inicial de aprox. $10.69 USD (S/ 36.18 PEN). "
            "Sabes que actualmente Joan tiene sus ahorros distribuidos en ~4.38 USDT y ~0.084 SOL, ambos generando interés en Binance Simple Earn Flexible. "
            "También sabes que Joan experimentó antes con el Prediction Market y tuvo pérdidas/bloqueos menores (~0.88 USDT), por lo que tu enfoque con él debe ser guiarlo hacia un crecimiento constante, seguro y disciplinado, alejándolo de apuestas a ciegas.\n"
            "Dirígete a Joan por su nombre con un tono altamente profesional, empático y como un mentor cuantitativo. "
            "Responde SIEMPRE en español. Tu respuesta debe tener EXACTAMENTE estas 5 secciones, en orden, sin añadir más:\n\n"
            "### 🌍 Contexto del Mercado (Resumen para Joan)\n"
            "2-3 frases sobre el estado general del mercado cripto. Menciona si es un buen entorno para su micro-portafolio actual.\n\n"
            "### 💰 Análisis Cripto Detallado\n"
            "Para CADA activo en 'crypto_indicators', escribe:\n"
            "**[SIMBOLO] - $[precio_actual]** | RSI: [rsi] | Cambio 24h: [cambio_pct_24h]%\n"
            "- RSI [valor]: [explica qué significa en 1 frase para un novato]\n"
            "- MACD [histógrama positivo/negativo]: [explica la señal en 1 frase]\n"
            "- 🟢 **[recomendacion]**: [justificación en 1 frase]\n\n"
            "### ⚽ Análisis de Apuestas Deportivas\n"
            "SOLO usa los datos de 'sports_analysis'. NO uses noticias aquí.\n"
            "Para CADA partido en 'sports_analysis':\n"
            "- Si value_bet_detectada=true: explica el value bet en 2 frases. Menciona a Joan cuánto sería en centavos de dólar si le aconsejas apostar (ej. 5% de su bankroll de $10 = $0.50). Si es_simulado=true, adviértelo con 🔴.\n"
            "- Si value_bet_detectada=false: escribe solo '- [evento]: Sin value bet, no apostar.'\n\n"
            "### 📰 Impacto de Noticias\n"
            "Menciona solo las noticias de impacto MEDIO o ALTO de 'news_groups'. "
            "Para cada una: qué ocurrió, si es positivo o negativo para el mercado, y por qué. Max 1-2 frases por noticia.\n\n"
            "### ✅ Plan de Acción — 3 Pasos para HOY\n"
            "Exactamente 3 bullets con acciones concretas para Joan, adaptadas a sus $10 de capital y a la protección de sus fondos en Simple Earn.\n\n"
            "REGLAS CRÍTICAS:\n"
            "- USA los números exactos del JSON. No los redondees ni cambies.\n"
            "- NO repitas secciones. Cada sección aparece UNA sola vez.\n"
            "- NO añadas secciones adicionales ni sub-análisis extra.\n"
            "- Al terminar el paso 3 del Plan de Acción, escribe EXACTAMENTE: 'FIN DEL INFORME'."
        )

        user_prompt = (
            f"Estos son los datos pre-calculados del mercado de hoy. Redacta el informe siguiendo EXACTAMENTE la estructura indicada:\n\n"
            f"{json.dumps(context_data, indent=2, default=str)}"
        )

        if not self.api_key:
            return "⚠️ ERROR: No se encontró OPENROUTER_API_KEY en las variables de entorno."

        payload = {
            "model": self.model_name,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            "temperature": 0.2,
            "max_tokens": 1500,
            "frequency_penalty": 1.0,
            "stop": ["FIN DEL INFORME", "---", "### 🟢", "### 🟡"]
        }

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "HTTP-Referer": "https://github.com/Joan2022Laurente/market-intelligence-agent",
            "X-Title": "Market Intelligence Agent"
        }

        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(self.base_url, headers=headers, json=payload, timeout=300) as response:
                    if response.status == 200:
                        data = await response.json()
                        return data.get("choices", [{}])[0].get("message", {}).get("content", "Error leyendo respuesta del LLM.")
                    else:
                        body = await response.text()
                        return f"Error en API OpenRouter: Status {response.status} — {body[:200]}"
        except Exception as e:
            print(f"[Error LLM] {repr(e)}")
            return "⚠️ No se pudo generar la síntesis narrativa. Revisa tu conexión a OpenRouter y tu API Key."
