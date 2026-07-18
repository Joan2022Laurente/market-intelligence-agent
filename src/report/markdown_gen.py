import datetime

class MarkdownGenerator:
    @staticmethod
    def generate_report(llm_narrative: str, raw_context: dict) -> str:
        """
        Ensambla el reporte final. La narrativa del LLM va intercalada con tablas
        determinísticas generadas aquí.
        """
        date_str = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
        
        md = f"# AI Market Intelligence Report\n**Generado:** {date_str}\n\n"
        
        md += "## Síntesis Ejecutiva\n"
        md += f"{llm_narrative}\n\n"
        
        md += "---\n## Datos Crudos de Respaldo\n\n"
        
        # Tabla de apuestas de valor puro
        md += "### Apuestas de Valor Detectadas\n"
        md += "| Evento | Recomendación | Prob. Estimada | Confianza |\n"
        md += "|---|---|---|---|\n"
        
        sports_data = raw_context.get("sports_analysis", [])
        value_bets = [s for s in sports_data if s["value_bet_detectada"]]
        
        if value_bets:
            for vb in value_bets:
                prob = f"{vb.get('probabilidad_local', 0)*100:.1f}%"
                conf = f"{vb.get('confianza', 0)*100:.1f}%"
                md += f"| {vb['evento']} | {vb['recomendacion']} | {prob} | {conf} |\n"
        else:
            md += "| *Ninguna detectada* | - | - | - |\n"
            
        md += "\n"
        
        # Tabla de Cripto
        md += "### Indicadores Crypto\n"
        md += "| Activo | RSI Estimado | MACD | Dominancia |\n"
        md += "|---|---|---|---|\n"
        
        crypto_data = raw_context.get("crypto_indicators", [])
        if crypto_data:
            for c in crypto_data:
                rsi = f"{c.get('rsi', 0):.1f}"
                macd = f"{c.get('macd', 0):.2f}"
                dom = f"{c.get('dominancia', 0):.1f}%" if c.get('dominancia') else "-"
                md += f"| {c['simbolo']} | {rsi} | {macd} | {dom} |\n"
        else:
            md += "| *Sin datos* | - | - | - |\n"
            
        md += "\n"
        
        # Tabla de Noticias
        md += "### Resumen de Noticias (RSS)\n"
        md += "| Categoría | Título | Impacto |\n"
        md += "|---|---|---|\n"
        
        news_data = raw_context.get("news_groups", {})
        if news_data:
            for cat, items in news_data.items():
                for n in items:
                    titulo = n.get('titulo', '')[:60] + "..." if len(n.get('titulo', '')) > 60 else n.get('titulo', '')
                    impacto = n.get('impacto_estimado', '-')
                    url = n.get('url', '#')
                    md += f"| {cat} | [{titulo}]({url}) | {impacto} |\n"
        else:
            md += "| *Sin noticias* | - | - |\n"
            
        md += "\n"
        
        return md

    @staticmethod
    def save_to_file(content: str, filename: str = "reporte_diario.md"):
        with open(filename, "w", encoding="utf-8") as f:
            f.write(content)
        print(f"Reporte guardado en {filename}")
