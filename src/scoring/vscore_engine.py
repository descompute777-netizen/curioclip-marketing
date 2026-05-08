"""
V-Score Engine — Motor de Puntuación de Viralización
=====================================================
Combina VisualEyes (atención visual simulada) + MiroFish (propagación social)
en un score único (0-10) que decide si un contenido se publica o no.

GO/NO-GO:
  - GREEN  (V-Score ≥ 8.0): Publicar
  - YELLOW (6.0 ≤ V-Score < 8.0): Iterar
  - RED    (V-Score < 6.0): Descartar o rediseñar
"""

import json
import os
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from typing import Optional


CONFIG_PATH = os.path.join(os.path.dirname(__file__), "..", "..", "config", "settings.json")


@dataclass
class VisualEyesResult:
    """Resultado del análisis de VisualEyes (eye-tracking simulado)."""
    clarity_score: float = 0.0        # Clarity score (0-100)
    attention_prediction: float = 0.0  # % atención predicha (0-100)
    attention_heatmap: list = field(default_factory=list)  # zones de atención
    weak_points: list = field(default_factory=list)  # zonas de baja atención
    focus_areas: list = field(default_factory=list)  # áreas de alto enfoque


@dataclass
class MiroFishResult:
    """Resultado de simulación MiroFish."""
    spread_score: float = 0.0       # Score de propagación (0-10)
    sentiment_score: float = 0.0    # Sentimiento neto (0-10)
    predicted_shares: int = 0
    virality_probability: float = 0.0  # 0-1
    dominant_narrative: str = ""
    tipping_points: list = field(default_factory=list)
    risk_factors: list = field(default_factory=list)


@dataclass
class VScore:
    """V-Score compuesto que combina VisualEyes + MiroFish."""
    score: float = 0.0
    decision: str = "RED"        # GREEN | YELLOW | RED
    visualeyes_component: float = 0.0
    mirofish_spread_component: float = 0.0
    mirofish_sentiment_component: float = 0.0
    hook_component: float = 0.0
    timestamp: str = ""
    content_id: str = ""
    recommendations: list = field(default_factory=list)


def load_config() -> dict:
    """Carga configuración desde settings.json."""
    config_path = os.path.normpath(CONFIG_PATH)
    if not os.path.exists(config_path):
        raise FileNotFoundError(f"Config no encontrado: {config_path}")
    with open(config_path, "r", encoding="utf-8") as f:
        return json.load(f)


def normalize_to_10(value: float, max_val: float = 100.0) -> float:
    """Normaliza un valor al rango 0-10."""
    return min(10.0, max(0.0, (value / max_val) * 10))


def calculate_vscore(
    visualeyes: VisualEyesResult,
    mirofish: MiroFishResult,
    hook_rate: float = 0.0,
    content_id: str = "",
    config: Optional[dict] = None
) -> VScore:
    """
    Calcula el V-Score compuesto.

    Fórmula:
      V = (w1 × VE_attention) + (w2 × MF_spread) + (w3 × MF_sentiment) + (w4 × hook)

    Args:
        visualeyes: Resultado de VisualEyes
        mirofish: Resultado de MiroFish
        hook_rate: Hook rate predicho (0-100%)
        content_id: Identificador del contenido
        config: Configuración (si None, carga de settings.json)

    Returns:
        VScore con decision GO/NO-GO
    """
    if config is None:
        try:
            config = load_config()
        except FileNotFoundError:
            # Fallback a pesos por defecto
            config = {
                "vscore": {
                    "weights": {
                        "visualeyes_attention": 0.35,
                        "mirofish_spread": 0.30,
                        "mirofish_sentiment": 0.20,
                        "hook_rate_predicted": 0.15,
                    },
                    "thresholds": {"green": 8.0, "yellow": 6.0},
                }
            }

    weights = config["vscore"]["weights"]
    thresholds = config["vscore"]["thresholds"]

    # Normalizar componentes al rango 0-10
    ve_norm = normalize_to_10(visualeyes.attention_prediction, max_val=100.0)
    spread_norm = mirofish.spread_score  # ya en 0-10
    sentiment_norm = mirofish.sentiment_score  # ya en 0-10
    hook_norm = normalize_to_10(hook_rate, max_val=100.0)

    # Calcular componentes ponderados
    ve_comp = weights["visualeyes_attention"] * ve_norm
    spread_comp = weights["mirofish_spread"] * spread_norm
    sentiment_comp = weights["mirofish_sentiment"] * sentiment_norm
    hook_comp = weights["hook_rate_predicted"] * hook_norm

    raw_score = ve_comp + spread_comp + sentiment_comp + hook_comp

    # Decisión GO/NO-GO
    if raw_score >= thresholds["green"]:
        decision = "GREEN"
    elif raw_score >= thresholds["yellow"]:
        decision = "YELLOW"
    else:
        decision = "RED"

    # Generar recomendaciones
    recommendations = []
    if ve_norm < 6.0:
        recommendations.append(
            f"⚠️ Atención visual baja ({visualeyes.attention_prediction:.0f}%). "
            "Revisar zonas de baja atención con heatmap VisualEyes."
        )
    if spread_norm < 6.0:
        recommendations.append(
            f"⚠️ Propagación social baja ({mirofish.spread_score:.1f}/10). "
            "Ajustar título/thumbnail/caption según simulación MiroFish."
        )
    if sentiment_norm < 5.0:
        recommendations.append(
            f"⚠️ Sentimiento negativo alto ({mirofish.sentiment_score:.1f}/10). "
            "Revisar tono emocional y CTA."
        )
    if hook_norm < 6.5:
        recommendations.append(
            f"⚠️ Hook débil (predicción: {hook_rate:.0f}%). "
            "Rediseñar los primeros 3 segundos."
        )
    if visualeyes.weak_points:
        wp_list = ", ".join(str(wp) for wp in visualeyes.weak_points[:5])
        recommendations.append(
            f"📍 Zonas de baja atención: {wp_list}. Reubicar elementos clave."
        )
    if mirofish.risk_factors:
        recommendations.append(
            f"🔴 Riesgos detectados por MiroFish: {'; '.join(mirofish.risk_factors[:3])}"
        )

    return VScore(
        score=round(raw_score, 2),
        decision=decision,
        visualeyes_component=round(ve_comp, 3),
        mirofish_spread_component=round(spread_comp, 3),
        mirofish_sentiment_component=round(sentiment_comp, 3),
        hook_component=round(hook_comp, 3),
        timestamp=datetime.now(timezone.utc).isoformat(),
        content_id=content_id,
        recommendations=recommendations,
    )


def format_vscore_report(vscore: VScore) -> str:
    """Genera reporte markdown del V-Score."""
    emoji = {"GREEN": "🟢", "YELLOW": "🟡", "RED": "🔴"}.get(vscore.decision, "⚪")

    lines = [
        f"# V-Score Report — {vscore.content_id}",
        f"**Fecha:** {vscore.timestamp}",
        "",
        f"## Resultado: {emoji} {vscore.decision} ({vscore.score}/10.0)",
        "",
        "## Desglose de Componentes",
        "| Componente | Peso | Score |",
        "|-----------|------|-------|",
        f"| VisualEyes Atención | 0.35 | {vscore.visualeyes_component:.3f} |",
        f"| MiroFish Propagación | 0.30 | {vscore.mirofish_spread_component:.3f} |",
        f"| MiroFish Sentimiento | 0.20 | {vscore.mirofish_sentiment_component:.3f} |",
        f"| Hook Rate | 0.15 | {vscore.hook_component:.3f} |",
        f"| **TOTAL** | **1.0** | **{vscore.score}** |",
        "",
    ]

    if vscore.recommendations:
        lines.append("## Recomendaciones")
        for rec in vscore.recommendations:
            lines.append(f"- {rec}")
        lines.append("")

    action_map = {
        "GREEN": "✅ **PUBLICAR** — El contenido pasó el umbral de viralización.",
        "YELLOW": "🔄 **ITERAR** — Aplicar recomendaciones y re-evaluar.",
        "RED": "❌ **DESCARTAR** — Rediseñar desde cero o cambiar concepto.",
    }
    lines.append(f"## Acción: {action_map.get(vscore.decision, 'Indefinido')}")

    return "\n".join(lines)


def save_vscore_to_obsidian(vscore: VScore, vault_path: str) -> str:
    """Guarda V-Score como nota en Obsidian vault."""
    report = format_vscore_report(vscore)

    # Frontmatter YAML
    frontmatter = (
        "---\n"
        f"agente: Motor_VScore\n"
        f"fecha: {vscore.timestamp}\n"
        f"tags: [vscore, {vscore.decision.lower()}, simulacion]\n"
        f"estado: {vscore.decision}\n"
        f"score: {vscore.score}\n"
        f"content_id: {vscore.content_id}\n"
        "---\n\n"
    )

    full_content = frontmatter + report
    filename = f"{vscore.content_id}_vscore.md"
    filepath = os.path.join(vault_path, "30_Contenido", "simulaciones", filename)

    os.makedirs(os.path.dirname(filepath), exist_ok=True)
    with open(filepath, "w", encoding="utf-8") as f:
        f.write(full_content)

    return filepath


# --- Ejemplo de uso ---
if __name__ == "__main__":
    # Simular resultados de los motores
    ve = VisualEyesResult(
        clarity_score=78.0,
        attention_prediction=72.0,
        attention_heatmap=["centro", "texto_titulo", "rostro"],
        weak_points=["esquina_inferior_derecha", "fondo_oscuro"],
        focus_areas=["hook_text", "thumbnail_face"],
    )
    mirofish = MiroFishResult(
        spread_score=8.2,
        sentiment_score=7.5,
        predicted_shares=340,
        virality_probability=0.73,
        dominant_narrative="Contenido educativo con hook emocional fuerte",
        tipping_points=["Hora 6: primer influencer comparte"],
        risk_factors=[],
    )

    result = calculate_vscore(
        visualeyes=ve,
        mirofish=mirofish,
        hook_rate=68.0,
        content_id="curioclip_sprint1_v5_plomo",
    )

    print(format_vscore_report(result))
    print(f"\nDecisión: {result.decision} ({result.score}/10)")
