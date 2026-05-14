"""
Agente Autónomo — Sprint Semanal
==================================
Llamado por GitHub Actions cada lunes 09:07 UTC.
Lee el estado del vault → llama weekly-orchestrator via Anthropic API
→ genera plan de sprint + guiones → escribe en Obsidian vault → commit.

Requiere env vars:
  ANTHROPIC_API_KEY
"""
import os
import sys
import json
import datetime
from pathlib import Path

try:
    import anthropic
except ImportError:
    print("[INSTALL] pip install anthropic")
    os.system("pip install anthropic -q")
    import anthropic

ROOT = Path(__file__).parent.parent.parent
VAULT = ROOT / "obsidian_vault"
AGENTS_DIR = ROOT / ".claude" / "agents"


def read_vault_summary() -> str:
    """Lee los documentos clave del vault para dar contexto al agente."""
    parts = []

    moc_master = VAULT / "90_MOCs" / "MOC_Master.md"
    if moc_master.exists():
        parts.append(f"=== MOC_Master ===\n{moc_master.read_text(encoding='utf-8')}")

    # Último briefing de sprint
    analitica = VAULT / "50_Analitica"
    briefings = sorted(analitica.glob("sprint*briefing*.md")) if analitica.exists() else []
    if briefings:
        last = briefings[-1]
        parts.append(f"=== Último Briefing ({last.name}) ===\n{last.read_text(encoding='utf-8')}")

    # Guiones existentes en cola
    cola = VAULT / "30_Contenido" / "cola"
    if cola.exists():
        cola_files = list(cola.glob("*.md"))
        if cola_files:
            parts.append(f"=== Cola de guiones ({len(cola_files)} en espera) ===")
            for f in cola_files[:5]:
                parts.append(f.read_text(encoding='utf-8')[:500])

    # Competidores
    competidores = VAULT / "20_Investigacion" / "competidores.md"
    if competidores.exists():
        parts.append(f"=== Competidores ===\n{competidores.read_text(encoding='utf-8')[:2000]}")

    return "\n\n".join(parts)[:12000]  # max 12K chars de contexto


def get_sprint_number() -> int:
    """Calcula el sprint actual basado en la fecha de inicio."""
    start = datetime.date(2026, 5, 6)
    today = datetime.date.today()
    weeks_elapsed = (today - start).days // 7
    return weeks_elapsed + 1


def write_sprint_outputs(content: str, sprint_n: int):
    """Parsea el output del agente y escribe los archivos del sprint."""
    today = datetime.date.today().isoformat()
    semana_dir = VAULT / "SEMANAS" / f"SEMANA_{sprint_n:02d}_{today}_auto"
    semana_dir.mkdir(parents=True, exist_ok=True)

    # Guardar el output completo como briefing
    briefing_path = VAULT / "50_Analitica" / f"sprint{sprint_n}_briefing_auto.md"
    briefing_path.write_text(
        f"---\nagente: weekly-orchestrator-cloud\nfecha: {today}\n"
        f"sprint: {sprint_n}\ntags: [auto, cloud, briefing]\n---\n\n"
        + content,
        encoding="utf-8"
    )
    print(f"[OK] Briefing escrito: {briefing_path}")

    # Extraer guiones (bloques entre ``` o secciones ## VIDEO)
    guiones_dir = VAULT / "30_Contenido" / "cola"
    guiones_dir.mkdir(exist_ok=True)

    lines = content.split("\n")
    in_guion = False
    guion_lines = []
    guion_count = 0

    for line in lines:
        if line.startswith("## VIDEO") or line.startswith("## GUION"):
            if guion_lines and guion_count > 0:
                save_guion(guion_lines, guiones_dir, sprint_n, guion_count)
            guion_lines = [line]
            guion_count += 1
            in_guion = True
        elif in_guion:
            guion_lines.append(line)

    if guion_lines and guion_count > 0:
        save_guion(guion_lines, guiones_dir, sprint_n, guion_count)

    print(f"[OK] {guion_count} guiones extraídos → {guiones_dir}")


def save_guion(lines: list, dest_dir: Path, sprint_n: int, idx: int):
    today = datetime.date.today().isoformat()
    path = dest_dir / f"sprint{sprint_n}_{today}_guion_{idx:02d}.md"
    path.write_text(
        f"---\nsprint: {sprint_n}\nfecha: {today}\nestado: pendiente\n---\n\n"
        + "\n".join(lines),
        encoding="utf-8"
    )


def main():
    print(f"[START] Sprint Semanal Autónomo — {datetime.date.today()}")

    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        print("[FAIL] ANTHROPIC_API_KEY no configurada en GitHub Secrets")
        sys.exit(1)

    client = anthropic.Anthropic(api_key=api_key)
    sprint_n = get_sprint_number()
    vault_state = read_vault_summary()

    # Leer system prompt del weekly-orchestrator
    orchestrator_file = AGENTS_DIR / "weekly-orchestrator.md"
    if orchestrator_file.exists():
        system_prompt = orchestrator_file.read_text(encoding="utf-8")
        # Extraer solo la parte del system (después del frontmatter YAML)
        if "---" in system_prompt:
            parts = system_prompt.split("---", 2)
            system_prompt = parts[2].strip() if len(parts) >= 3 else system_prompt
    else:
        system_prompt = (
            "Eres el weekly-orchestrator del sistema CurioClip. "
            "Tu misión: generar el plan de sprint semanal con 25+ guiones adaptados "
            "del nicho de curiosidades/datos curiosos en español LATAM. "
            "Para cada guión incluye: HOOK (0-3s) literal | IDENTIFICACIÓN | PROMESA | "
            "DESARROLLO | CTA. V-Score estimado. Hashtags."
        )

    user_prompt = (
        f"Ejecuta Sprint {sprint_n} — {datetime.date.today()}.\n\n"
        f"Estado actual del vault:\n{vault_state}\n\n"
        f"Genera:\n"
        f"1. Briefing ejecutivo del sprint (KPIs, estado, decisiones)\n"
        f"2. 25+ guiones adaptados del nicho (formato 5 bloques, R8 activo)\n"
        f"3. Top 7 guiones para esta semana con horario asignado\n"
        f"4. Hipótesis de oportunidad (mínimo 3)\n"
        f"5. Trending sounds y hashtags de la semana\n\n"
        f"Contexto del canal: CurioClip — curiosidades en español, audiencia 13-35 años LATAM."
    )

    print(f"[API] Llamando claude-opus-4-7 para Sprint {sprint_n}...")
    response = client.messages.create(
        model="claude-opus-4-7",
        max_tokens=8192,
        system=system_prompt,
        messages=[{"role": "user", "content": user_prompt}]
    )

    content = response.content[0].text
    print(f"[OK] Respuesta: {len(content)} chars")

    write_sprint_outputs(content, sprint_n)
    print(f"[DONE] Sprint {sprint_n} completado.")


if __name__ == "__main__":
    main()
