"""
M1 — DISCOVER: Investigacion de tendencias y contenido viral.
Pipeline: DISCOVER → ANALYZE → PRODUCE → PREDICT → PUBLISH → LEARN

Qué hace:
  - Web search de trending topics (ultimos 7 dias)
  - Analisis de top 10 competidores del nicho
  - Identificacion de sounds, hashtags, formatos en alza
  - Scoring de oportunidades (0-100)
  - Output → Obsidian: 20_Investigacion/trend_reports/trend_YYYY-MM-DD.md

Agente: A1 Investigacion
Herramientas reales: web_search (nativo Claude), TikTok MCP, Meta MCP
"""

import os
from dataclasses import dataclass, field
from datetime import datetime, timezone


VAULT_PATH = os.path.join(os.path.dirname(__file__), "..", "..", "obsidian_vault")


@dataclass
class TrendOpportunity:
    """Una oportunidad de contenido identificada en DISCOVER."""
    titulo: str = ""
    concepto: str = ""
    sub_nicho: str = ""
    hook_propuesto: str = ""
    duracion_target: int = 20
    fuentes_material: list = field(default_factory=list)
    hashtags_sugeridos: list = field(default_factory=list)
    horario_optimo: str = ""
    opportunity_score: float = 0.0   # 0-100
    hook_score_estimado: float = 0.0  # 0-10
    competencia_nivel: str = "media"  # baja | media | alta


@dataclass
class TrendReport:
    """Reporte completo del modulo M1 DISCOVER."""
    fecha: str = ""
    sprint: int = 1
    nicho: str = "Curiosidades / Ciencia / Datos Curiosos"
    plataformas: list = field(default_factory=lambda: ["TikTok", "Facebook"])
    trending_topics: list = field(default_factory=list)
    competitor_insights: list = field(default_factory=list)
    trending_sounds: list = field(default_factory=list)
    trending_hashtags: list = field(default_factory=list)
    winning_formats: list = field(default_factory=list)
    top_opportunities: list = field(default_factory=list)  # Lista de TrendOpportunity
    fuentes_consultadas: list = field(default_factory=list)


def format_trend_report(report: TrendReport) -> str:
    """Formatea el reporte como nota Markdown con frontmatter YAML para Obsidian."""
    lines = [
        "---",
        "agente: A1_Investigacion",
        "modulo: M1_DISCOVER",
        f"fecha: {report.fecha}",
        f"sprint: {report.sprint}",
        f"nicho: {report.nicho}",
        "tags: [discover, tendencias, m1-discover]",
        "estado: completado",
        "---",
        "",
        f"# M1 DISCOVER — Reporte de Tendencias — {report.fecha}",
        "",
        "## Nicho Analizado",
        f"**{report.nicho}** | Plataformas: {', '.join(report.plataformas)}",
        "",
        "## Trending Topics (Ultimos 7 Dias)",
    ]
    for i, topic in enumerate(report.trending_topics or ["Pendiente — ejecutar web_search"], 1):
        lines.append(f"{i}. {topic}")

    lines += ["", "## Insights de Competidores"]
    for insight in report.competitor_insights or ["Pendiente — analisis de top 10 cuentas"]:
        lines.append(f"- {insight}")

    if report.trending_sounds:
        lines += ["", "## Sounds Trending"]
        for sound in report.trending_sounds:
            lines.append(f"- 🎵 {sound}")

    lines += ["", "## Hashtags Emergentes"]
    if report.trending_hashtags:
        lines.append(" ".join(f"#{h}" for h in report.trending_hashtags))
    else:
        lines.append("Pendiente")

    if report.winning_formats:
        lines += ["", "## Formatos Ganadores del Nicho"]
        for fmt in report.winning_formats:
            lines.append(f"- {fmt}")

    lines += ["", "## Top Oportunidades → Pasar a M2 ANALYZE"]
    for i, opp in enumerate(report.top_opportunities, 1):
        if isinstance(opp, TrendOpportunity):
            lines += [
                f"",
                f"### {i}. {opp.titulo} (Score: {opp.opportunity_score}/100)",
                f"- **Sub-nicho:** {opp.sub_nicho}",
                f"- **Hook propuesto:** {opp.hook_propuesto}",
                f"- **Duracion target:** {opp.duracion_target}s",
                f"- **Hook score estimado:** {opp.hook_score_estimado}/10",
                f"- **Competencia:** {opp.competencia_nivel}",
                f"- **Hashtags:** {' '.join(f'#{h}' for h in opp.hashtags_sugeridos)}",
                f"- **Horario:** {opp.horario_optimo}",
            ]
        else:
            lines.append(f"{i}. {opp}")

    if report.fuentes_consultadas:
        lines += ["", "## Fuentes Consultadas"]
        for fuente in report.fuentes_consultadas:
            lines.append(f"- {fuente}")

    lines += [
        "",
        "---",
        "**Siguiente paso:** A3+A9 ejecutan M2 ANALYZE sobre las Top Oportunidades.",
        f"**Ver briefs en:** [[10_Estrategia/briefs/]]"
    ]

    return "\n".join(lines)


def save_report_to_obsidian(report: TrendReport, vault_path: str = VAULT_PATH) -> str:
    """Guarda el reporte en Obsidian y retorna la ruta del archivo."""
    content = format_trend_report(report)
    folder = os.path.join(vault_path, "20_Investigacion", "trend_reports")
    os.makedirs(folder, exist_ok=True)
    filename = f"trend_{report.fecha}.md"
    filepath = os.path.join(folder, filename)
    with open(filepath, "w", encoding="utf-8") as f:
        f.write(content)
    return filepath


# Instrucciones para A1 — usadas en el prompt del sistema
DISCOVER_PROMPT = """
[DE: A0_Director] [PARA: A1_Investigacion] [TIPO: solicitud]
Ejecutar M1 DISCOVER para el nicho: Curiosidades/Ciencia/Datos Curiosos (Espanol)

PASOS:
1. web_search: "curiosidades TikTok viral esta semana espanol"
2. web_search: "sabias que trending TikTok mayo 2026"
3. Analizar top 10 cuentas del nicho (buscar: #datoscuriosos #sabiasque)
   Para cada cuenta: seguidores, ER estimado, frecuencia, formato ganador
4. Identificar sounds trending en TikTok para el nicho
5. Scoring de oportunidades (0-100):
   - Tamano de audiencia: 30%
   - Nivel de competencia: 20% (menos competencia = mas puntos)
   - Alineacion con CurioClip: 25%
   - Viabilidad de produccion con CapCut: 25%
6. Seleccionar TOP 5 oportunidades
7. Guardar en: obsidian_vault/20_Investigacion/trend_reports/trend_YYYY-MM-DD.md
"""


if __name__ == "__main__":
    # Crear reporte de ejemplo
    report = TrendReport(
        fecha=datetime.now(timezone.utc).strftime("%Y-%m-%d"),
        sprint=1
    )
    filepath = save_report_to_obsidian(report)
    print(f"Reporte guardado en: {filepath}")
    print("\nA1 debe poblar el reporte con datos reales de web_search.")
