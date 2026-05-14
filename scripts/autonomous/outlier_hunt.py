"""
Agente Autónomo — Outlier Hunter (Outlier Cloning 5 Fases)
============================================================
Llamado por GitHub Actions cada domingo 20:03 UTC.
Ejecuta las 5 fases del protocolo Outlier Cloning y escribe resultados al vault.

Requiere:
  ANTHROPIC_API_KEY
"""
import os
import sys
import datetime
from pathlib import Path

try:
    import anthropic
except ImportError:
    os.system("pip install anthropic -q")
    import anthropic

ROOT = Path(__file__).parent.parent.parent
VAULT = ROOT / "obsidian_vault"
AGENTS_DIR = ROOT / ".claude" / "agents"


def get_sprint_number() -> int:
    start = datetime.date(2026, 5, 6)
    return (datetime.date.today() - start).days // 7 + 1


def read_research_context() -> str:
    """Lee competidores + outliers previos + tendencias para contexto."""
    parts = []

    comp = VAULT / "20_Investigacion" / "competidores.md"
    if comp.exists():
        parts.append(comp.read_text(encoding="utf-8")[:3000])

    prev_outliers = sorted((VAULT / "20_Investigacion").glob("outliers_sprint*.md"))
    if prev_outliers:
        last = prev_outliers[-1]
        parts.append(f"Outliers previos ({last.name}):\n" + last.read_text(encoding="utf-8")[:2000])

    trend_dir = VAULT / "20_Investigacion" / "trend_reports"
    if trend_dir.exists():
        trends = sorted(trend_dir.glob("trend_*.md"))
        if trends:
            parts.append(f"Tendencias recientes:\n" + trends[-1].read_text(encoding="utf-8")[:1500])

    return "\n\n".join(parts)[:8000]


def main():
    print(f"[START] Outlier Hunter — {datetime.date.today()}")

    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        print("[FAIL] ANTHROPIC_API_KEY no configurada")
        sys.exit(1)

    client = anthropic.Anthropic(api_key=api_key)
    sprint_n = get_sprint_number()
    today = datetime.date.today().isoformat()
    context = read_research_context()

    agent_file = AGENTS_DIR / "outlier-hunter.md"
    if agent_file.exists():
        system = agent_file.read_text(encoding="utf-8")
        if "---" in system:
            parts = system.split("---", 2)
            system = parts[2].strip() if len(parts) >= 3 else system
    else:
        system = (
            "Eres el outlier-hunter del sistema CurioClip. Ejecutas el protocolo "
            "Outlier Cloning en 5 fases para identificar y adaptar contenido viral "
            "del nicho curiosidades/datos curiosos en español LATAM."
        )

    prompt = (
        f"Ejecuta Outlier Cloning Sprint {sprint_n} — {today}.\n\n"
        f"Contexto de investigación previa:\n{context}\n\n"
        f"FASE 1: Identifica 5 cuentas referentes del nicho (>50K seg, ER>5%, activas 14 días)\n"
        f"FASE 2: Para cada cuenta, extrae 5 outliers (≥3x promedio de vistas). "
        f"Total 25 outliers mínimo. Registra: URL/cuenta, vistas aprox, ER, formato, duración.\n"
        f"FASE 3: Analiza cada outlier: a) problema que resuelve b) hook literal 0-3s "
        f"c) estructura d) CTA e) por qué funciona\n"
        f"FASE 4: Adapta cada outlier a un guión CurioClip con 5 bloques "
        f"(HOOK literal | IDENTIFICACIÓN | PROMESA | DESARROLLO | CTA)\n"
        f"FASE 5: Selecciona top 7 guiones con V-Score estimado y horario sugerido\n\n"
        f"Canal: CurioClip | Nicho: curiosidades, datos curiosos | Idioma: español LATAM | "
        f"Audiencia: 13-35 años | Plataforma: TikTok (principal), Facebook (secundario)"
    )

    print(f"[API] Ejecutando Outlier Cloning Sprint {sprint_n}...")
    response = client.messages.create(
        model="claude-opus-4-7",
        max_tokens=8192,
        system=system,
        messages=[{"role": "user", "content": prompt}]
    )

    content = response.content[0].text
    sprint_dir = VAULT / "20_Investigacion"
    sprint_dir.mkdir(exist_ok=True)

    # Guardar referentes
    ref_path = sprint_dir / f"referentes_sprint_{sprint_n}.md"
    ref_path.write_text(
        f"---\nsprint: {sprint_n}\nfecha: {today}\nagente: outlier-hunter-cloud\n---\n\n"
        + content,
        encoding="utf-8"
    )

    # Guardar outliers (mismo contenido, separar más tarde con edición manual)
    out_path = sprint_dir / f"outliers_sprint_{sprint_n}.md"
    out_path.write_text(
        f"---\nsprint: {sprint_n}\nfecha: {today}\nagente: outlier-hunter-cloud\n---\n\n"
        + content,
        encoding="utf-8"
    )

    # Guardar guiones en cola
    cola_dir = VAULT / "30_Contenido" / "cola"
    cola_dir.mkdir(exist_ok=True)
    cola_path = cola_dir / f"sprint{sprint_n}_{today}_outlier_guiones.md"
    cola_path.write_text(
        f"---\nsprint: {sprint_n}\nfecha: {today}\nfuente: outlier-cloning\nestado: pendiente\n---\n\n"
        + content,
        encoding="utf-8"
    )

    print(f"[OK] Guardado en:")
    print(f"  {ref_path}")
    print(f"  {out_path}")
    print(f"  {cola_path}")
    print(f"[DONE] Outlier Cloning Sprint {sprint_n} completado.")


if __name__ == "__main__":
    main()
