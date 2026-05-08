"""
M2 — ANALYZE: Scoring de oportunidad + verificacion de derechos.
Pipeline: DISCOVER → ANALYZE → PRODUCE → PREDICT → PUBLISH → LEARN

Qué hace:
  - Evalua oportunidades de M1 contra scoring framework
  - CHECKPOINT DE DERECHOS: verifica licencias ANTES de producir (R2)
  - Selecciona top 5 y genera brief de produccion
  - Output → Obsidian: 10_Estrategia/briefs/brief_[id].md

Agentes: A3 Algoritmico (scoring) + A9 Compliance (derechos)
"""

import os
from dataclasses import dataclass, field
from datetime import datetime, timezone


VAULT_PATH = os.path.join(os.path.dirname(__file__), "..", "..", "obsidian_vault")

# Fuentes con licencia libre verificada para uso comercial
FUENTES_LIBRES = [
    "pexels.com", "unsplash.com", "coverr.co", "pixabay.com",
    "nasa.gov", "wikipedia.org", "commons.wikimedia.org",
    "freesound.org",  # audio CC
    "youtube.com/commons",  # Creative Commons
]

# Fuentes de alto riesgo de copyright
FUENTES_RIESGO = [
    "youtube.com",  # videos normales
    "instagram.com", "tiktok.com",  # clips de otros creadores
    "netflix", "disney", "hbo", "amazon prime",
    "reddit.com", "twitter.com",
]


@dataclass
class RightsCheck:
    """Resultado de la verificacion de derechos (A9 Compliance)."""
    aprobado: bool = False
    fuentes_ok: list = field(default_factory=list)
    fuentes_riesgo: list = field(default_factory=list)
    riesgos: list = field(default_factory=list)
    alternativas: list = field(default_factory=list)
    notas_a9: str = ""


@dataclass
class ContentBrief:
    """Brief de produccion generado por M2 ANALYZE para M3 PRODUCE."""
    id: str = ""
    fecha: str = ""
    titulo: str = ""
    concepto: str = ""
    hook: str = ""
    duracion_target: int = 20
    sub_nicho: str = ""
    formato: str = ""
    hashtags: list = field(default_factory=list)
    horario: str = ""

    # Scoring
    opportunity_score: float = 0.0   # 0-100
    hook_score_estimado: float = 0.0  # 0-10

    # Derechos (A9)
    fuentes_material: list = field(default_factory=list)
    rights_check: RightsCheck = field(default_factory=RightsCheck)

    # Decision
    pasa_a_produce: bool = False
    razon_rechazo: str = ""


def verify_rights(fuentes: list) -> RightsCheck:
    """
    Verifica derechos de uso de las fuentes.
    R2: 'Dar creditos' NO equivale a licencia. Se necesita licencia verificable.
    Ejecutado por A9 Compliance en M2.
    """
    fuentes_ok, fuentes_riesgo, riesgos, alternativas = [], [], [], []

    for fuente in fuentes:
        fl = fuente.lower()
        if any(f in fl for f in FUENTES_LIBRES):
            fuentes_ok.append(fuente)
        elif any(f in fl for f in FUENTES_RIESGO):
            fuentes_riesgo.append(fuente)
            riesgos.append(
                f"RIESGO ALTO: '{fuente}' — usar clip de terceros sin licencia "
                f"puede causar DMCA strike y suspension de cuenta."
            )
            alternativas.append(
                f"Alternativa para '{fuente}': buscar visual equivalente en "
                f"pexels.com o unsplash.com (licencia libre, sin atribucion)."
            )
        else:
            riesgos.append(
                f"ADVERTENCIA: '{fuente}' — verificar licencia manualmente. "
                f"Si no tiene licencia CC o libre, NO usar."
            )

    return RightsCheck(
        aprobado=len(fuentes_riesgo) == 0,
        fuentes_ok=fuentes_ok,
        fuentes_riesgo=fuentes_riesgo,
        riesgos=riesgos,
        alternativas=alternativas,
        notas_a9=("Todas las fuentes aprobadas." if len(fuentes_riesgo) == 0
                  else f"{len(fuentes_riesgo)} fuentes rechazadas. Ver alternativas.")
    )


def score_opportunity(
    hook_strength: float,        # 0-10
    audience_size: float,        # 0-10 normalizado
    competition_inverse: float,  # 0-10 (10 = sin competencia)
    brand_alignment: float,      # 0-10
    production_viability: float  # 0-10
) -> float:
    """
    Calcula score de oportunidad (0-100).
    Pesos: audience 30%, competition 20%, brand 25%, production 25%.
    Hook fuerte (>=9) aplica boost del 20%.
    """
    base = (
        (audience_size * 0.30) +
        (competition_inverse * 0.20) +
        (brand_alignment * 0.25) +
        (production_viability * 0.25)
    ) * 10

    if hook_strength >= 9:
        base = min(100, base * 1.20)
    elif hook_strength >= 7:
        base = min(100, base * 1.10)

    return round(base, 1)


def format_brief(brief: ContentBrief) -> str:
    """Formatea brief como nota Markdown para Obsidian."""
    go = "✅ APROBADO → M3 PRODUCE" if brief.pasa_a_produce else f"❌ RECHAZADO — {brief.razon_rechazo}"
    rights = "✅ Derechos OK" if brief.rights_check.aprobado else "⚠️ Derechos PENDIENTES"

    lines = [
        "---",
        "agente: M2_ANALYZE",
        "modulo: M2_ANALYZE",
        f"fecha: {brief.fecha}",
        f"id: {brief.id}",
        f"tags: [brief, produccion, m2-analyze]",
        f"estado: {'aprobado' if brief.pasa_a_produce else 'rechazado'}",
        "---",
        "",
        f"# Brief de Produccion — {brief.id}",
        f"## {go}",
        "",
        "## Concepto",
        f"**Titulo:** {brief.titulo}",
        f"**Sub-nicho:** {brief.sub_nicho}",
        f"**Formato:** {brief.formato}",
        f"**Duracion target:** {brief.duracion_target}s",
        f"**Horario optimo:** {brief.horario}",
        "",
        "## Hook Propuesto",
        f"> {brief.hook}",
        "",
        "## Scores",
        "| Metrica | Valor |",
        "|---------|-------|",
        f"| Oportunidad | {brief.opportunity_score}/100 |",
        f"| Hook estimado | {brief.hook_score_estimado}/10 |",
        "",
        f"## {rights}",
        f"**A9 Compliance:** {brief.rights_check.notas_a9}",
    ]
    for fuente in brief.fuentes_material:
        ok = "✅" if any(f in fuente.lower() for f in FUENTES_LIBRES) else "⚠️"
        lines.append(f"- {ok} {fuente}")

    if brief.rights_check.alternativas:
        lines += ["", "**Alternativas sugeridas:**"]
        for alt in brief.rights_check.alternativas:
            lines.append(f"- {alt}")

    lines += [
        "",
        "## Hashtags",
        " ".join(f"#{h}" for h in brief.hashtags),
        "",
        "---",
        f"**Siguiente paso:** {'A2+A4 ejecutan M3 PRODUCE' if brief.pasa_a_produce else 'Revisar fuentes y resubmitir a M2'}",
        f"**Linked desde:** [[20_Investigacion/trend_reports/trend_{brief.fecha}]]"
    ]
    return "\n".join(lines)


def save_brief(brief: ContentBrief, vault_path: str = VAULT_PATH) -> str:
    """Guarda el brief en Obsidian."""
    content = format_brief(brief)
    folder = os.path.join(vault_path, "10_Estrategia", "briefs")
    os.makedirs(folder, exist_ok=True)
    filename = f"brief_{brief.id}.md"
    filepath = os.path.join(folder, filename)
    with open(filepath, "w", encoding="utf-8") as f:
        f.write(content)
    return filepath


if __name__ == "__main__":
    # Ejemplo: brief para V5 Plomo Fundido
    rc = verify_rights(["pexels.com/videos/plomo", "youtube.com/watch?v=xyz"])
    brief = ContentBrief(
        id="sprint1_v5_plomo",
        fecha=datetime.now(timezone.utc).strftime("%Y-%m-%d"),
        titulo="Que pasa si metes tu mano en PLOMO fundido",
        concepto="Efecto Leidenfrost — la fisica que permite meter la mano en metal liquido",
        hook="Metio su mano en PLOMO FUNDIDO a 327°C",
        duracion_target=25,
        sub_nicho="Ciencia WTF",
        formato="Experimento cientifico extremo",
        hashtags=["ciencia", "fisica", "experimento", "plomofundido", "leidenfrost", "curioclip"],
        horario="Viernes 19:00-20:00 LATAM",
        opportunity_score=score_opportunity(10, 8, 7, 9, 9),
        hook_score_estimado=10.0,
        fuentes_material=["pexels.com/videos/plomo", "youtube.com/watch?v=xyz"],
        rights_check=rc,
        pasa_a_produce=rc.aprobado,
        razon_rechazo="" if rc.aprobado else "Fuentes con riesgo de copyright"
    )
    path = save_brief(brief)
    print(f"Brief guardado: {path}")
    print(f"Pasa a M3 PRODUCE: {brief.pasa_a_produce}")
    if not brief.pasa_a_produce:
        print(f"Alternativas: {brief.rights_check.alternativas}")
