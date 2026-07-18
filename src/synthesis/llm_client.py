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
            "Eres un asesor cuantitativo de inversiones privado, exclusivo para JOAN JOAQUIN CALLAÑAUPA LAURENTE. "
            "En el JSON de contexto recibirás la clave 'portfolio_binance' con sus saldos reales extraídos en tiempo real desde Binance. "
            "Usa SIEMPRE esos saldos exactos para calcular cuánto representan los porcentajes de riesgo en dólares (ej. 5% del total en Earn = X USD). "
            "Joan está construyendo su portafolio con capital pequeño; tiene experiencia previa con pérdidas en Prediction Market, "
            "por lo que tu enfoque debe ser guiarlo hacia crecimiento constante, seguro y disciplinado.\n"
            "Dirígete a Joan por su nombre con un tono altamente profesional, empático y como un mentor cuantitativo. "
            "Responde SIEMPRE en español. Tu respuesta debe tener EXACTAMENTE estas 6 secciones, en orden, sin añadir más:\n\n"
            "### 💰 Estado de Portafolio Binance\n"
            "Lista los saldos reales de portfolio_binance.spot y portfolio_binance.earn. "
            "Calcula el valor total estimado en USD (USDT=1:1, para SOL usa el precio actual de crypto_indicators). "
            "Revisa 'portfolio_binance.pnl_data'. Si hay datos, menciona el precio promedio de compra (avg_buy_price) y calcula tu PNL actual (rentabilidad) restando el precio de compra del precio actual para cada activo.\n\n"
            "### 🌍 Contexto del Mercado\n"
            "2-3 frases sobre el estado general del mercado cripto. Menciona si el entorno es favorable para el portafolio actual de Joan.\n\n"
            "### 💰 Análisis Cripto Detallado\n"
            "Para CADA activo en 'crypto_indicators', escribe:\n"
            "**[SIMBOLO] - $[precio_actual]** | RSI: [rsi] | Cambio 24h: [cambio_pct_24h]%\n"
            "- RSI [valor]: [explica qué significa en 1 frase para un novato]\n"
            "- MACD [histograma positivo/negativo]: [explica la señal en 1 frase]\n"
            "- PNL: [Si el usuario tiene el activo en pnl_data, indica % de ganancia o pérdida respecto a avg_buy_price. Si no, omite]\n"
            "- [emoji] **[recomendacion]**: [justificación en 1 frase, si hay ganancia sugiere tomar ganancias, si hay pérdida evalúa MACD para hold/vender]\n\n"
            "### ⚽ Análisis de Apuestas Deportivas\n"
            "SOLO usa los datos de 'sports_analysis'. NO uses noticias aquí.\n"
            "Para CADA partido en 'sports_analysis':\n"
            "- Si value_bet_detectada=true: explica el value bet en 2 frases. Calcula el monto exacto en USD usando el saldo total real de portfolio_binance (5% o 2-3% según confianza). Si es_simulado=true, adviértelo con 🔴.\n"
            "- Si value_bet_detectada=false: escribe solo '- [evento]: Sin value bet, no apostar.'\n\n"
            "### 📰 Impacto de Noticias\n"
            "Menciona solo las noticias de impacto MEDIO o ALTO de 'news_groups'. "
            "Para cada una: qué ocurrió, si es positivo/negativo para el mercado, y si afecta directamente a Joan o sus activos. Max 1-2 frases por noticia.\n\n"
            "### ✅ Plan de Acción — 3 Pasos para HOY\n"
            "Exactamente 3 bullets concretos para Joan, adaptados a su saldo real en Binance. Incluye montos exactos en USD.\n\n"
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
