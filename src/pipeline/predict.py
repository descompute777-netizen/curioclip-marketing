"""
M4 — PREDICT: Analisis predictivo pre-publicacion.
Pipeline: DISCOVER → ANALYZE → PRODUCE → PREDICT → PUBLISH → LEARN

DISCLAIMER OBLIGATORIO (R4):
  Este modulo ESTIMA probabilidad. NO garantiza resultados.
  La viralidad tiene un componente estocastico irreducible.
  El predictor acumula precision real despues de 20+ publicaciones.

Qué hace:
  - Calcula V-Score (VisualEyes + MiroFish)
  - Compara contra benchmarks del nicho (de M1 DISCOVER)
  - GO si score >= umbral_minimo (default 60/100) → M5 PUBLISH
  - NO-GO → devuelve a M3 PRODUCE con recomendaciones
  - Output → Obsidian: 30_Contenido/[id]_vscore.md

Agente: A8 Prediccion
"""

import os
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from scoring.vscore_engine import (
    VisualEyesResult, MiroFishResult, VScore,
    calculate_vscore, format_vscore_report, save_vscore_to_obsidian
)
from dataclasses import dataclass, field
from datetime import datetime, timezone


VAULT_PATH = os.path.join(os.path.dirname(__file__), "..", "..", "obsidian_vault")

# Benchmarks del nicho CurioClip (se actualizan con datos reales de M6 LEARN)
DEFAULT_BENCHMARKS = {
    "hook_rate": 65.0,   # % retencion >3s — meta del sistema
    "er": 6.0,           # engagement rate promedio objetivo
    "retention_full": 30.0  # % retencion completa
}


@dataclass
class PredictScorecard:
    """Scorecard completo del modulo M4 PREDICT con disclaimer de margen de error."""
    content_id: str = ""
    fecha: str = ""

    # V-Score
    vscore: float = 0.0
    vscore_decision: str = "RED"     # GREEN | YELLOW | RED

    # Comparacion con benchmarks
    hook_rate_predicted: float = 0.0
    hook_benchmark: float = 65.0
    retention_predicted: float = 0.0
    er_predicted: float = 0.0
    er_benchmark: float = 6.0

    # Margen de error declarado SIEMPRE (R4)
    margin_of_error: float = 15.0  # +/-15% hasta calibracion
    calibrated: bool = False        # True despues de 20+ publicaciones reales

    # Decision pipeline
    umbral_minimo: float = 60.0     # score/100 para pasar a M5
    passes_threshold: bool = False

    # Feedback para M3
    recommendations: list = field(default_factory=list)
    risk_areas: list = field(default_factory=list)


def run_predict(
    content_id: str,
    visualeyes: VisualEyesResult,
    mirofish: MiroFishResult,
    hook_rate: float,
    umbral_minimo: float = 60.0,
    benchmarks: dict = None,
    n_historical_publications: int = 0
) -> PredictScorecard:
    """
    Ejecuta analisis predictivo completo.

    DISCLAIMER (R4): Estima probabilidad, NO garantiza resultados.

    Args:
        content_id: ID del contenido (ej: 'sprint1_v5_plomo').
        visualeyes: Resultado de VisualEyes (atencion visual).
        mirofish: Resultado de MiroFish (propagacion social).
        hook_rate: Hook rate predicho (0-100).
        umbral_minimo: Score minimo para pasar a M5 PUBLISH.
        benchmarks: Benchmarks del nicho (de M1 DISCOVER).
        n_historical_publications: Numero de publicaciones previas analizadas.

    Returns:
        PredictScorecard con decision GO/NO-GO y disclaimer de precision.
    """
    vscore = calculate_vscore(
        visualeyes=visualeyes,
        mirofish=mirofish,
        hook_rate=hook_rate,
        content_id=content_id
    )

    bm = benchmarks or DEFAULT_BENCHMARKS
    score_100 = vscore.score * 10
    passes = score_100 >= umbral_minimo
    calibrated = n_historical_publications >= 20

    er_est = min(25.0, hook_rate * 0.09)  # heuristica: ~9% del hook rate

    risks = []
    if hook_rate < bm.get("hook_rate", 65):
        risks.append(
            f"Hook rate predicho ({hook_rate:.0f}%) por debajo del benchmark "
            f"({bm.get('hook_rate', 65):.0f}%). Redisenar los primeros 3 segundos."
        )
    if not passes:
        risks.append(
            f"V-Score ({score_100:.0f}/100) < umbral ({umbral_minimo:.0f}/100). "
            f"Aplicar recomendaciones y re-evaluar en M3 PRODUCE."
        )

    return PredictScorecard(
        content_id=content_id,
        fecha=datetime.now(timezone.utc).strftime("%Y-%m-%d"),
        vscore=vscore.score,
        vscore_decision=vscore.decision,
        hook_rate_predicted=hook_rate,
        hook_benchmark=bm.get("hook_rate", 65),
        retention_predicted=visualeyes.attention_prediction,
        er_predicted=round(er_est, 1),
        er_benchmark=bm.get("er", 6.0),
        margin_of_error=15.0,
        calibrated=calibrated,
        umbral_minimo=umbral_minimo,
        passes_threshold=passes,
        recommendations=vscore.recommendations,
        risk_areas=risks
    )


def format_scorecard(sc: PredictScorecard) -> str:
    """Genera nota Markdown con disclaimer prominente para Obsidian."""
    icon = {"GREEN": "🟢", "YELLOW": "🟡", "RED": "🔴"}.get(sc.vscore_decision, "⚪")
    go_icon = "✅ GO → M5 PUBLISH" if sc.passes_threshold else "❌ NO-GO → M3 PRODUCE"
    cal = "✅ Calibrado" if sc.calibrated else f"⏳ No calibrado (necesita {max(0, 20 - int(sc.umbral_minimo))} publicaciones mas)"

    lines = [
        "---",
        "agente: A8_Prediccion",
        "modulo: M4_PREDICT",
        f"fecha: {sc.fecha}",
        f"content_id: {sc.content_id}",
        f"vscore: {sc.vscore}",
        f"decision: {sc.vscore_decision}",
        f"tags: [predict, vscore, m4-predict]",
        "---",
        "",
        f"# M4 PREDICT — Scorecard — {sc.content_id}",
        "",
        f"> ⚠️ **DISCLAIMER OBLIGATORIO (R4):** Este scorecard ESTIMA probabilidad "
        f"con margen de error de ±{sc.margin_of_error:.0f}%. "
        f"**NO garantiza** resultados. La viralidad tiene un componente estocastico irreducible. "
        f"Estado del predictor: {cal}",
        "",
        f"## {icon} V-Score: {sc.vscore}/10.0 ({sc.vscore * 10:.0f}/100)",
        f"## {go_icon}",
        "",
        "## Predicciones vs. Benchmark del Nicho",
        "| Metrica | Prediccion | Benchmark | Delta |",
        "|---------|-----------|-----------|-------|",
        f"| Hook rate (>3s) | {sc.hook_rate_predicted:.0f}% | {sc.hook_benchmark:.0f}% | {sc.hook_rate_predicted - sc.hook_benchmark:+.0f}% |",
        f"| Retencion visual | {sc.retention_predicted:.0f}% | — | — |",
        f"| ER estimado | {sc.er_predicted:.1f}% | {sc.er_benchmark:.1f}% | {sc.er_predicted - sc.er_benchmark:+.1f}% |",
        "",
    ]

    if sc.recommendations:
        lines += ["## Recomendaciones A8 → A4 (M3)"]
        for r in sc.recommendations:
            lines.append(f"- {r}")
        lines.append("")

    if sc.risk_areas:
        lines += ["## Areas de Riesgo"]
        for r in sc.risk_areas:
            lines.append(f"⚠️ {r}")
        lines.append("")

    next_step = "A9 Compliance → M5 PUBLISH" if sc.passes_threshold else "A4 aplica recomendaciones → re-evaluar M4"
    lines.append(f"**Siguiente paso:** {next_step}")
    lines.append(f"**Linked desde:** [[30_Contenido/{sc.content_id}]]")

    return "\n".join(lines)


def save_scorecard(sc: PredictScorecard, vault_path: str = VAULT_PATH) -> str:
    """Guarda el scorecard en Obsidian."""
    content = format_scorecard(sc)
    folder = os.path.join(vault_path, "30_Contenido", "simulaciones")
    os.makedirs(folder, exist_ok=True)
    filename = f"{sc.content_id}_vscore.md"
    filepath = os.path.join(folder, filename)
    with open(filepath, "w", encoding="utf-8") as f:
        f.write(content)
    return filepath


if __name__ == "__main__":
    # Ejemplo con datos simulados para V5 Plomo Fundido
    ve = VisualEyesResult(
        clarity_score=85.0,
        attention_prediction=78.0,
        attention_heatmap=["hook_text", "rostro", "efecto_visual"],
        weak_points=["esquina_inferior"],
        focus_areas=["hook_text_plomo", "efecto_leidenfrost"]
    )
    mf = MiroFishResult(
        spread_score=8.5,
        sentiment_score=7.8,
        predicted_shares=420,
        virality_probability=0.78,
        dominant_narrative="Contenido cientifico extremo con hook de peligro",
        tipping_points=["Hora 4: primer compartir masivo"],
        risk_factors=[]
    )
    sc = run_predict(
        content_id="sprint1_v5_plomo",
        visualeyes=ve,
        mirofish=mf,
        hook_rate=72.0,
        umbral_minimo=60.0
    )
    path = save_scorecard(sc)
    print(f"Scorecard guardado: {path}")
    print(f"Decision: {sc.vscore_decision} | Pasa umbral: {sc.passes_threshold}")
