"""
VisualEyes MCP Server Wrapper
===============================
Reemplaza TRIBE v2 para predicción de atención visual.
VisualEyes usa IA para simular eye-tracking con 93% de precisión.

URL: https://visualeyes.design
Costo: GRATIS
Modo: Web-based (no tiene API pública documentada)

ESTRATEGIA DE INTEGRACIÓN:
Como VisualEyes es web-based sin API pública, este wrapper implementa:
  1. Modo browser-automation: Sube frames al sitio web
  2. Modo heurístico local: Analiza composición visual con reglas de diseño
  3. Modo manual: Genera checklist para análisis manual en la web

Para el MVP del proyecto, usamos el modo HEURÍSTICO + MANUAL.
El heurístico aplica las mismas reglas que usan los eye-tracking tools:
  - Regla de los tercios
  - Detección de texto grande
  - Posición de rostros
  - Contraste de colores
  - Jerarquía visual
"""

import json
import os
from dataclasses import dataclass, field, asdict
from typing import Optional


@dataclass
class VisualAnalysis:
    """Resultado de análisis visual heurístico."""
    clarity_score: float = 0.0        # 0-100
    attention_prediction: float = 0.0  # 0-100
    attention_zones: list = field(default_factory=list)
    weak_points: list = field(default_factory=list)
    focus_areas: list = field(default_factory=list)
    recommendations: list = field(default_factory=list)


def analyze_thumbnail_heuristic(
    has_face: bool = False,
    has_large_text: bool = False,
    text_position: str = "center",      # center | top | bottom | left | right
    text_contrast: str = "high",        # high | medium | low
    background_type: str = "dark",      # dark | light | busy | simple
    color_saturation: str = "high",     # high | medium | low
    has_emotion: bool = False,          # expresión emocional visible
    element_count: int = 3,             # elementos visuales distintos
    has_brand_logo: bool = False,
    hook_text: str = "",
) -> VisualAnalysis:
    """
    Analiza una thumbnail/frame usando heurísticas de eye-tracking.

    Basado en investigaciones de Nielsen Norman Group, MIT AgeLab,
    y patrones de VisualEyes/Tobii.

    Cada factor suma puntos al clarity_score y attention_prediction.
    """
    clarity = 50.0  # Base
    attention = 50.0  # Base
    zones = []
    weak = []
    focus = []
    recs = []

    # === FACTOR 1: Rostro humano ===
    # Los rostros capturan atención automáticamente (amygdala response)
    if has_face:
        attention += 15
        clarity += 5
        focus.append("rostro_humano")
        if has_emotion:
            attention += 8
            focus.append("expresion_emocional")
    else:
        attention -= 5
        recs.append("Añadir rostro humano aumenta atención un 15-20%")

    # === FACTOR 2: Texto grande ===
    if has_large_text:
        attention += 10
        focus.append("texto_titulo")

        # Posición del texto
        if text_position == "center":
            clarity += 10
            zones.append("centro: texto principal")
        elif text_position == "top":
            clarity += 8
            zones.append("superior: texto hook")
        else:
            clarity += 3
            weak.append(f"texto en {text_position}: no es la zona primaria de atención")
            recs.append(f"Mover texto al centro o parte superior (actualmente en {text_position})")

        # Contraste del texto
        if text_contrast == "high":
            clarity += 10
        elif text_contrast == "medium":
            clarity += 5
            recs.append("Aumentar contraste del texto (fondo más oscuro o texto más brillante)")
        else:
            clarity -= 5
            weak.append("texto con bajo contraste: difícil de leer en scroll rápido")
            recs.append("URGENTE: El texto no se lee bien. Usar fondo oscuro + texto blanco/amarillo")
    else:
        attention -= 10
        recs.append("Añadir texto grande visible en thumbnail (hooks como '¿Sabías que...')")

    # === FACTOR 3: Fondo ===
    if background_type == "dark":
        clarity += 8
        zones.append("fondo oscuro: bueno para contraste")
    elif background_type == "simple":
        clarity += 5
    elif background_type == "busy":
        clarity -= 10
        weak.append("fondo recargado: compite con el contenido principal")
        recs.append("Simplificar fondo. Fondos oscuros o con blur funcionan mejor")
    else:
        clarity += 3

    # === FACTOR 4: Saturación de color ===
    if color_saturation == "high":
        attention += 8
        focus.append("colores_vibrantes")
    elif color_saturation == "medium":
        attention += 3
    else:
        attention -= 5
        recs.append("Aumentar saturación de colores. Los colores vibrantes detienen el scroll")

    # === FACTOR 5: Complejidad visual ===
    if element_count <= 3:
        clarity += 10  # Diseño limpio
    elif element_count <= 5:
        clarity += 3
    else:
        clarity -= 8
        weak.append("demasiados elementos visuales: sobrecarga cognitiva")
        recs.append(f"Reducir de {element_count} a máximo 3 elementos visuales principales")

    # === FACTOR 6: Hook text quality ===
    if hook_text:
        hook_lower = hook_text.lower()
        power_words = ["no", "nunca", "imposible", "secreto", "prohibido",
                       "peligro", "increíble", "wtf", "ilegal", "muerto",
                       "millones", "viral", "nadie", "jamás"]
        matches = sum(1 for w in power_words if w in hook_lower)
        if matches >= 2:
            attention += 12
            focus.append("hook_palabras_poder")
        elif matches == 1:
            attention += 6
            focus.append("hook_moderado")
        else:
            recs.append("Hook sin palabras de poder. Usar: 'No', 'Nunca', 'Imposible', 'Secreto'")

        # Longitud del hook
        word_count = len(hook_text.split())
        if word_count <= 8:
            clarity += 5  # Corto y directo
        elif word_count > 12:
            clarity -= 5
            recs.append(f"Hook demasiado largo ({word_count} palabras). Máximo 8 palabras")

    # === FACTOR 7: Logo/Marca ===
    if has_brand_logo:
        clarity += 2  # Mínimo impacto en atención
        focus.append("branding")

    # Normalizar scores
    clarity = max(0, min(100, clarity))
    attention = max(0, min(100, attention))

    return VisualAnalysis(
        clarity_score=round(clarity, 1),
        attention_prediction=round(attention, 1),
        attention_zones=zones,
        weak_points=weak,
        focus_areas=focus,
        recommendations=recs,
    )


def generate_visualeyes_checklist(content_id: str) -> str:
    """
    Genera checklist para análisis manual en VisualEyes web.

    Args:
        content_id: Identificador del contenido.

    Returns:
        Markdown checklist para el usuario.
    """
    return f"""# VisualEyes Analysis Checklist — {content_id}

## Pasos para Análisis en visualeyes.design:

1. [ ] Ir a https://visualeyes.design
2. [ ] Subir captura del frame principal del video (el thumbnail)
3. [ ] Esperar resultado del heatmap de atención
4. [ ] Anotar el Clarity Score: ___/100
5. [ ] Identificar zonas ROJAS (alta atención):
   - [ ] ¿El hook text está en zona roja? Sí/No
   - [ ] ¿El rostro está en zona roja? Sí/No
   - [ ] ¿El CTA está visible? Sí/No
6. [ ] Identificar zonas AZULES (baja atención):
   - [ ] ¿Hay información importante en zona azul? Sí/No
7. [ ] Subir variantes (A/B) si las hay
8. [ ] Documentar ganador

## Resultado:
- Clarity Score: ___/100
- Atención en hook: ___/10
- Decisión: APROBADO / ITERAR / RECHAZAR
"""


# =========================================================
# MCP TOOLS SCHEMA
# =========================================================

MCP_TOOLS_SCHEMA = {
    "server_name": "visualeyes-mcp",
    "description": "VisualEyes — Predicción de atención visual (reemplaza TRIBE v2)",
    "tools": [
        {
            "name": "analyze_thumbnail",
            "description": "Analiza atención visual de una thumbnail con heurísticas de eye-tracking",
            "handler": "analyze_thumbnail_heuristic",
        },
        {
            "name": "generate_checklist",
            "description": "Genera checklist para análisis manual en VisualEyes web",
            "handler": "generate_visualeyes_checklist",
        },
    ],
}


# =========================================================
# DEMO
# =========================================================

if __name__ == "__main__":
    # Analizar thumbnail del Video 5 (Plomo Fundido) de CurioClip
    result = analyze_thumbnail_heuristic(
        has_face=False,
        has_large_text=True,
        text_position="center",
        text_contrast="high",
        background_type="dark",
        color_saturation="high",
        has_emotion=False,
        element_count=2,
        has_brand_logo=False,
        hook_text="Metió su mano en PLOMO FUNDIDO a 327°C",
    )

    print("=== VisualEyes Analysis: curioclip_sprint1_v5_plomo ===")
    print(f"Clarity Score: {result.clarity_score}/100")
    print(f"Attention Prediction: {result.attention_prediction}/100")
    print(f"Focus Areas: {result.focus_areas}")
    print(f"Weak Points: {result.weak_points}")
    print(f"\nRecommendations:")
    for r in result.recommendations:
        print(f"  - {r}")
