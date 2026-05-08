"""
M6 — LEARN: Retroalimentacion post-publicacion y calibracion del predictor.
Pipeline: DISCOVER → ANALYZE → PRODUCE → PREDICT → PUBLISH → LEARN

Qué hace:
  - A las 24h y 72h post-publicacion, consulta metricas reales (Meta MCP + TikTok MCP)
  - Compara prediccion de M4 vs. resultado real
  - Registra aciertos y errores del predictor
  - Actualiza MOCs de Obsidian con lecciones aprendidas
  - Alimenta a M1 del siguiente sprint con patrones aprendidos

El predictor se considera CALIBRADO cuando:
  - >= 20 publicaciones analizadas
  - Error medio en hook rate < 15%

Agentes: A7 Supervision + A1 (ajusta M1 del siguiente sprint)
Output → Obsidian: 60_Aprendizaje/retros/retro_sprint[N]_YYYY-MM-DD.md
"""

import os
from dataclasses import dataclass, field
from datetime import datetime, timezone


VAULT_PATH = os.path.join(os.path.dirname(__file__), "..", "..", "obsidian_vault")


@dataclass
class PublicationResult:
    """Metricas reales de una publicacion para comparar con prediccion de M4."""
    content_id: str = ""
    plataforma: str = "TikTok"
    fecha_publicacion: str = ""
    horas_medicion: int = 24   # 24 o 72

    # Metricas reales (de TikTok Analytics / Meta Insights)
    views: int = 0
    likes: int = 0
    comments: int = 0
    shares: int = 0
    hook_rate_real: float = 0.0    # % retencion >3s
    retention_real: float = 0.0    # % retencion completa
    er_real: float = 0.0

    # Prediccion de M4 (para comparar)
    vscore_predicho: float = 0.0
    hook_rate_predicho: float = 0.0

    # Calibracion
    hook_error: float = 0.0         # |hook_real - hook_predicho|
    prediccion_acertada: bool = False  # True si error < 15%


@dataclass
class SprintLearning:
    """Reporte de aprendizaje del sprint para M6 LEARN."""
    sprint: int = 0
    fecha: str = ""
    publicaciones: list = field(default_factory=list)  # Lista de PublicationResult

    # Calibracion acumulada del predictor
    total_historico: int = 0
    error_medio_hook: float = 0.0
    precision_acumulada: float = 0.0
    calibrado: bool = False
    publicaciones_para_calibrar: int = 20

    # Lecciones
    top_lecciones: list = field(default_factory=list)
    formatos_ganadores: list = field(default_factory=list)
    formatos_a_evitar: list = field(default_factory=list)

    # Ajustes para M1 del proximo sprint
    ajustes_discover: list = field(default_factory=list)


def compute_calibration(results: list) -> dict:
    """
    Calcula metricas de calibracion del predictor.
    Predictor calibrado: >= 20 publicaciones con error medio < 15%.
    """
    if not results:
        return {
            "calibrado": False, "error_medio": 0.0,
            "precision": 0.0, "total": 0,
            "faltan": 20
        }
    errors = [abs(r.hook_rate_real - r.hook_rate_predicho) for r in results]
    error_medio = sum(errors) / len(errors)
    correctas = sum(1 for e in errors if e < 15)
    precision = (correctas / len(results)) * 100
    return {
        "calibrado": len(results) >= 20 and error_medio < 15,
        "error_medio": round(error_medio, 1),
        "precision": round(precision, 1),
        "total": len(results),
        "faltan": max(0, 20 - len(results))
    }


def add_publication_result(
    sc: SprintLearning,
    result: PublicationResult
) -> SprintLearning:
    """Registra el resultado real de una publicacion y recalcula calibracion."""
    result.hook_error = abs(result.hook_rate_real - result.hook_rate_predicho)
    result.prediccion_acertada = result.hook_error < 15

    sc.publicaciones.append(result)
    cal = compute_calibration(sc.publicaciones)
    sc.total_historico = cal["total"]
    sc.error_medio_hook = cal["error_medio"]
    sc.precision_acumulada = cal["precision"]
    sc.calibrado = cal["calibrado"]
    return sc


def format_learning_report(sc: SprintLearning) -> str:
    """Formatea el reporte de aprendizaje como nota Markdown para Obsidian."""
    cal_icon = "✅" if sc.calibrado else f"⏳ (faltan {max(0, 20 - sc.total_historico)} publicaciones)"

    lines = [
        "---",
        "agente: A7_Supervision",
        "modulo: M6_LEARN",
        f"fecha: {sc.fecha}",
        f"sprint: {sc.sprint}",
        f"tags: [learn, calibracion, retro, m6-learn]",
        "---",
        "",
        f"# M6 LEARN — Retro Sprint {sc.sprint} — {sc.fecha}",
        "",
        "## Estado del Predictor (M4 PREDICT)",
        "| Metrica | Valor | Meta |",
        "|---------|-------|------|",
        f"| Publicaciones analizadas | {sc.total_historico} | >= 20 |",
        f"| Error medio hook rate | {sc.error_medio_hook:.1f}% | < 15% |",
        f"| Precision acumulada | {sc.precision_acumulada:.1f}% | >= 85% |",
        f"| Predictor calibrado | {cal_icon} | — |",
        "",
    ]

    if sc.publicaciones:
        lines += [
            "## Resultados del Sprint",
            "| Video | Hook predicho | Hook real | Error | Acertada |",
            "|-------|--------------|-----------|-------|---------|",
        ]
        for r in sc.publicaciones:
            ok = "✅" if r.prediccion_acertada else "❌"
            lines.append(
                f"| {r.content_id} | {r.hook_rate_predicho:.0f}% | "
                f"{r.hook_rate_real:.0f}% | {r.hook_error:.1f}% | {ok} |"
            )
        lines.append("")

    if sc.top_lecciones:
        lines += ["## Top 3 Lecciones del Sprint"]
        for i, l in enumerate(sc.top_lecciones[:3], 1):
            lines.append(f"{i}. {l}")
        lines.append("")

    if sc.formatos_ganadores:
        lines += ["## Formatos Ganadores (replicar en M1 proximo sprint)"]
        for f in sc.formatos_ganadores:
            lines.append(f"- ✅ {f}")
        lines.append("")

    if sc.formatos_a_evitar:
        lines += ["## Formatos a Evitar o Reformular"]
        for f in sc.formatos_a_evitar:
            lines.append(f"- ❌ {f}")
        lines.append("")

    if sc.ajustes_discover:
        lines += ["## Ajustes para M1 DISCOVER (proximo sprint)"]
        for a in sc.ajustes_discover:
            lines.append(f"→ {a}")
        lines.append("")

    lines += [
        "---",
        "**Siguiente paso:** A1 incorpora ajustes en M1 DISCOVER del Sprint "
        f"{sc.sprint + 1}.",
        f"**Ver metricas:** [[50_Analitica/sprint{sc.sprint}_briefing]]",
        "**Ver MOC:** [[90_MOCs/MOC_Aprendizaje]]"
    ]

    return "\n".join(lines)


def save_learning_report(sc: SprintLearning, vault_path: str = VAULT_PATH) -> str:
    """Guarda el reporte en Obsidian."""
    content = format_learning_report(sc)
    folder = os.path.join(vault_path, "60_Aprendizaje", "retros")
    os.makedirs(folder, exist_ok=True)
    filename = f"retro_sprint{sc.sprint}_{sc.fecha}.md"
    filepath = os.path.join(folder, filename)
    with open(filepath, "w", encoding="utf-8") as f:
        f.write(content)
    return filepath


if __name__ == "__main__":
    # Ejemplo de reporte de aprendizaje al cerrar Sprint 1
    sc = SprintLearning(
        sprint=1,
        fecha=datetime.now(timezone.utc).strftime("%Y-%m-%d"),
        top_lecciones=[
            "El sub-nicho 'Ciencia WTF' supero el benchmark de hook rate en todos los videos",
            "Los videos de 20-25s retienen mejor que los de 28s+ en TikTok",
            "Publicar viernes 19-20h LATAM genera 2x mas alcance no-followers"
        ],
        formatos_ganadores=["Ciencia WTF (10/10 hook)", "Misterio sin resolver"],
        formatos_a_evitar=["Leyes absurdas sin gancho visual fuerte"],
        ajustes_discover=[
            "Priorizar sub-nicho ciencia WTF en busqueda de tendencias",
            "Buscar especificamente 'efecto fisico increible' y 'experimento peligroso'",
            "Revisar sounds trending de ciencia/educacion cada semana"
        ]
    )
    path = save_learning_report(sc)
    print(f"Reporte guardado: {path}")
