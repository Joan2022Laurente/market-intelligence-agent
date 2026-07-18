import datetime
from typing import Dict, Any, List


class MarkdownReportGenerator:

    @staticmethod
    def generate(synthesis: str, raw_context: Dict[str, Any]) -> str:
        now = datetime.datetime.utcnow().strftime("%Y-%m-%d %H:%M UTC")
        md = f"# 📊 AI Market Intelligence Report\n"
        md += f"**Generado:** {now}\n\n"

        # --- Síntesis Ejecutiva (LLM) ---
        md += "## 🧠 Análisis Ejecutivo (IA)\n\n"
        md += f"{synthesis}\n\n"
        md += "---\n\n"

        # --- Indicadores Cripto ---
        md += "## 💰 Indicadores Técnicos Cripto\n\n"
        md += "| Activo | Precio USD | Cambio 24h | Cambio 7d | RSI(14) | Señal MACD | Tendencia | Recomendación |\n"
        md += "|---|---|---|---|---|---|---|---|\n"

        crypto_data = raw_context.get("crypto_indicators", [])
        for c in crypto_data:
            precio = f"${c.get('precio_actual', 0):,.2f}"
            cambio_24h = c.get('cambio_pct_24h')
            cambio_7d = c.get('cambio_pct_7d', None)
            cambio_24h_str = f"{cambio_24h:+.2f}%" if cambio_24h is not None else "-"
            cambio_7d_str = f"{cambio_7d:+.2f}%" if cambio_7d is not None else "-"
            rsi = f"{c.get('rsi', 0):.1f}"
            macd_hist = c.get('macd_histograma', 0)
            macd_str = f"{'▲' if macd_hist > 0 else '▼'} {macd_hist:+.4f}"
            tendencia = c.get('tendencia', 'NEUTRAL')
            rec = c.get('recomendacion', 'ESPERAR')
            tendencia_emoji = {"ALCISTA": "🟢", "BAJISTA": "🔴", "NEUTRAL": "🟡"}.get(tendencia, "⚪")
            rec_emoji = {"COMPRAR": "✅", "MANTENER": "🔵", "ESPERAR": "⏳", "REDUCIR": "⚠️"}.get(rec, "")
            md += f"| **{c['simbolo']}** | {precio} | {cambio_24h_str} | {cambio_7d_str} | {rsi} | {macd_str} | {tendencia_emoji} {tendencia} | {rec_emoji} {rec} |\n"

        md += "\n> *RSI > 70 = Sobrecomprado | RSI < 30 = Sobrevendido | MACD ▲ = Impulso alcista*\n\n"
        md += "---\n\n"

        # --- Apuestas Deportivas ---
        md += "## ⚽ Análisis de Apuestas Deportivas\n\n"
        sports_data = raw_context.get("sports_analysis", [])

        value_bets = [s for s in sports_data if s.get("value_bet_detectada")]
        no_value = [s for s in sports_data if not s.get("value_bet_detectada")]

        if value_bets:
            md += "### ✅ Value Bets Detectadas\n\n"
            md += "| Partido | Prob. Local | Prob. Empate | Prob. Visitante | EV | Confianza | Recomendación | Datos |\n"
            md += "|---|---|---|---|---|---|---|---|\n"
            for vb in value_bets:
                prob_l = f"{vb.get('probabilidad_local', 0)*100:.1f}%"
                prob_e = f"{vb.get('probabilidad_empate', 0)*100:.1f}%" if vb.get('probabilidad_empate') else "-"
                prob_v = f"{vb.get('probabilidad_visitante', 0)*100:.1f}%"
                conf = f"{vb.get('confianza', 0)*100:.0f}%"
                rec = vb.get('recomendacion', '-')
                sim = "🔴 Simulado" if vb.get('es_simulado') else "🟢 Real"
                md += f"| {vb['evento']} | {prob_l} | {prob_e} | {prob_v} | ✅ Positivo | {conf} | {rec} | {sim} |\n"
        else:
            md += "### ℹ️ Sin Value Bets hoy\nNo se detectaron apuestas con valor esperado positivo suficiente.\n"

        if no_value:
            md += "\n### ⛔ Partidos sin Value Bet\n"
            md += "| Partido | Recomendación | Datos |\n"
            md += "|---|---|---|\n"
            for s in no_value:
                sim = "🔴 Simulado" if s.get('es_simulado') else "🟢 Real"
                md += f"| {s['evento']} | No apostar | {sim} |\n"

        md += "\n> ⚠️ *Las apuestas marcadas como 🔴 Simulado usan datos ficticios. No apuestes con ellas.*\n\n"
        md += "---\n\n"

        # --- Noticias por impacto ---
        md += "## 📰 Noticias del Mercado\n\n"
        news_data = raw_context.get("news_groups", {})

        if news_data:
            for impacto_label, emoji in [("alto", "🚨 Impacto ALTO"), ("medio", "📌 Impacto MEDIO"), ("bajo", "📎 Impacto BAJO")]:
                items = news_data.get(impacto_label, [])
                if items:
                    md += f"### {emoji}\n\n"
                    for n in items:
                        titulo = n.get('titulo', '')
                        url = n.get('url', '#')
                        fuente = n.get('fuente', '')
                        categoria = n.get('categoria', '')
                        md += f"- **[{titulo}]({url})** _{fuente}_ `{categoria}`\n"
                    md += "\n"
        else:
            md += "_Sin noticias disponibles._\n\n"

        md += "---\n\n"
        md += "*Informe generado automáticamente por el AI Market Intelligence Agent. No constituye asesoría financiera profesional. Invierte con responsabilidad.*\n"

        return md

    @staticmethod
    def group_news(news_list: List[Dict]) -> Dict[str, List[Dict]]:
        """Agrupa noticias por nivel de impacto."""
        groups: Dict[str, List[Dict]] = {"alto": [], "medio": [], "bajo": []}
        for n in news_list:
            impacto = n.get("impacto_estimado", "medio")
            if impacto in groups:
                groups[impacto].append(n)
        return groups
