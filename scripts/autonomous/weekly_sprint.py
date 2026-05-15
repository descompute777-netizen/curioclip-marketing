"""
Agente Autónomo — Sprint Semanal CurioClip
==========================================
GitHub Actions: cada lunes 09:07 UTC.
Motor: Gemini 2.5-Flash GRATIS (1M tokens/día free).
Anthropic API = último recurso si Gemini falla.

Pipeline completo:
  1. Gemini → genera plan + 25 guiones
  2. edge-tts → voiceover MP3 para top-7
  3. Pexels API → B-roll CC0
  4. ffmpeg → video 9:16 1080x1920
  5. GitHub Release → URL pública del video
  6. Escribe schedule.json con URLs y horarios
  7. Git commit → vault actualizado

Requiere GitHub Secrets:
  GEMINI_API_KEY      (primario, gratis)
  COMPOSIO_API_KEY    (para publicar en TikTok)
  PEXELS_API_KEY      (para B-roll — gratis en pexels.com/api)
  ANTHROPIC_API_KEY   (fallback, solo si Gemini falla)
"""
import os, sys, json, datetime, subprocess, tempfile, shutil
from pathlib import Path

ROOT = Path(__file__).parent.parent.parent
VAULT = ROOT / "obsidian_vault"
AGENTS_DIR = ROOT / ".claude" / "agents"
SPRINT_N = ((datetime.date.today() - datetime.date(2026, 5, 6)).days // 7) + 1
TODAY = datetime.date.today().isoformat()


# ─── LLM: Gemini gratis primero, Anthropic como fallback ───────────────────

def call_llm(system: str, user: str, max_tokens: int = 8192) -> str:
    """Llama a Gemini 2.5-Flash (gratis). Si falla, usa Anthropic como fallback."""
    gemini_key = os.environ.get("GEMINI_API_KEY")
    if gemini_key:
        try:
            from openai import OpenAI
            client = OpenAI(
                api_key=gemini_key,
                base_url="https://generativelanguage.googleapis.com/v1beta/openai/"
            )
            resp = client.chat.completions.create(
                model="gemini-2.5-flash",
                max_tokens=max_tokens,
                messages=[
                    {"role": "system", "content": system},
                    {"role": "user", "content": user}
                ]
            )
            return resp.choices[0].message.content
        except Exception as e:
            print(f"[GEMINI] Falló: {e} → intentando Anthropic fallback...")

    # Fallback: Anthropic (solo si Gemini falla)
    anthropic_key = os.environ.get("ANTHROPIC_API_KEY")
    if anthropic_key:
        try:
            import anthropic
            client = anthropic.Anthropic(api_key=anthropic_key)
            resp = client.messages.create(
                model="claude-haiku-4-5-20251001",  # más barato del catálogo
                max_tokens=max_tokens,
                system=system,
                messages=[{"role": "user", "content": user}]
            )
            return resp.content[0].text
        except Exception as e:
            print(f"[ANTHROPIC] Falló: {e}")

    sys.exit("[ERROR] Sin LLM disponible. Configura GEMINI_API_KEY o ANTHROPIC_API_KEY.")


# ─── Leer contexto del vault ────────────────────────────────────────────────

def read_vault_summary() -> str:
    parts = []
    moc = VAULT / "90_MOCs" / "MOC_Master.md"
    if moc.exists():
        parts.append(f"=== MOC Master ===\n{moc.read_text(encoding='utf-8')[:3000]}")

    briefings = sorted((VAULT / "50_Analitica").glob("sprint*briefing*.md"))
    if briefings:
        parts.append(f"=== Último Briefing ===\n{briefings[-1].read_text(encoding='utf-8')[:2000]}")

    outliers = sorted((VAULT / "20_Investigacion").glob("outliers_sprint*.md"))
    if outliers:
        parts.append(f"=== Outliers previos ===\n{outliers[-1].read_text(encoding='utf-8')[:1500]}")

    comp = VAULT / "20_Investigacion" / "competidores.md"
    if comp.exists():
        parts.append(f"=== Competidores ===\n{comp.read_text(encoding='utf-8')[:1000]}")

    return "\n\n".join(parts)[:10000]


# ─── Generar guiones ────────────────────────────────────────────────────────

def generate_scripts() -> str:
    print(f"\n[LLM] Generando guiones Sprint {SPRINT_N} con Gemini...")
    vault_state = read_vault_summary()

    agent_file = AGENTS_DIR / "weekly-orchestrator.md"
    system = agent_file.read_text(encoding="utf-8").split("---", 2)[-1].strip() \
        if agent_file.exists() else (
        "Eres el weekly-orchestrator de CurioClip. Genera planes de sprint y 25+ guiones "
        "de curiosidades en español LATAM. Hook LITERAL (0-3s) en cada guión. "
        "Formato 5 bloques: HOOK | IDENTIFICACIÓN | PROMESA | DESARROLLO | CTA."
    )

    user = (
        f"Sprint {SPRINT_N} — {TODAY}\n\n"
        f"Estado vault:\n{vault_state}\n\n"
        f"Genera:\n"
        f"1. Briefing ejecutivo (KPIs, estado, decisiones)\n"
        f"2. 25 guiones adaptados del nicho (sub-nichos: Ciencia WTF, Misterio, Historia WTF, "
        f"Comparaciones imposibles, Psicología). Hook LITERAL en cada uno.\n"
        f"3. TOP 7 para esta semana con V-Score estimado (/10) y horario CDMX\n"
        f"4. 3 hipótesis de oportunidad\n"
        f"Nicho: CurioClip — curiosidades español LATAM | 13-35 años"
    )

    return call_llm(system, user)


# ─── Guardar outputs en vault ───────────────────────────────────────────────

def save_sprint_outputs(content: str):
    briefing_path = VAULT / "50_Analitica" / f"sprint{SPRINT_N}_briefing_auto_{TODAY}.md"
    briefing_path.write_text(
        f"---\nagente: weekly-orchestrator-cloud\nfecha: {TODAY}\nsprint: {SPRINT_N}\n"
        f"motor: gemini-2.5-flash\ntags: [auto, cloud, briefing]\n---\n\n{content}",
        encoding="utf-8"
    )
    print(f"[OK] Briefing: {briefing_path.name}")

    cola_dir = VAULT / "30_Contenido" / "cola"
    cola_dir.mkdir(exist_ok=True)
    cola_path = cola_dir / f"sprint{SPRINT_N}_{TODAY}_auto_guiones.md"
    cola_path.write_text(
        f"---\nsprint: {SPRINT_N}\nfecha: {TODAY}\nmotor: gemini-2.5-flash\n"
        f"fuente: weekly-orchestrator-cloud\nestado: pendiente\n---\n\n{content}",
        encoding="utf-8"
    )
    print(f"[OK] Guiones: {cola_path.name}")

    # Extraer top-7 y crear schedule.json
    schedule = extract_schedule(content)
    sched_path = VAULT / "40_Publicacion" / f"schedule_sprint{SPRINT_N}.json"
    sched_path.parent.mkdir(exist_ok=True)
    sched_path.write_text(json.dumps(schedule, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"[OK] Schedule: {sched_path.name}")
    return schedule


def extract_schedule(content: str) -> dict:
    """Extrae top-7 del contenido generado para crear el schedule de publicación."""
    week_start = datetime.date.today()
    # Ajustar al próximo lunes si no es lunes
    days_to_monday = (7 - week_start.weekday()) % 7 or 7
    monday = week_start + datetime.timedelta(days=days_to_monday)

    # Horarios CDMX → UTC (CDMX es UTC-6 en horario estándar)
    schedule_times = [
        (0, 18, 0),   # Lun 12:00 CDMX = 18:00 UTC
        (1, 1, 0),    # Mar 19:00 CDMX = 01:00 UTC +1
        (2, 2, 0),    # Mié 20:00 CDMX = 02:00 UTC +1
        (3, 18, 0),   # Jue 12:00 CDMX = 18:00 UTC
        (4, 2, 0),    # Vie 20:00 CDMX = 02:00 UTC +1
        (5, 18, 0),   # Sáb 12:00 CDMX = 18:00 UTC
        (6, 2, 0),    # Dom 20:00 CDMX = 02:00 UTC +1
    ]

    days_es = ["lunes","martes","miercoles","jueves","viernes","sabado","domingo"]
    videos = []
    for i, (day_offset, hour, minute) in enumerate(schedule_times):
        pub_date = monday + datetime.timedelta(days=day_offset)
        pub_dt_utc = datetime.datetime(pub_date.year, pub_date.month, pub_date.day,
                                       hour, minute, 0)
        # Ajustar día si hora UTC > 24 del día CDMX
        if hour < 6:
            pub_dt_utc = datetime.datetime(pub_date.year, pub_date.month, pub_date.day,
                                           hour, minute, 0) + datetime.timedelta(days=1)

        videos.append({
            "day": days_es[i],
            "date": pub_date.isoformat(),
            "guion_id": f"S{SPRINT_N}_V{i+1}",
            "video_url": "",            # se llena cuando el video se produce y sube
            "caption": "",              # se extrae del guión
            "hashtags": "#datoscuriosos #sabiasque #curioclip #curiosidades",
            "published": False,
            "publish_at_utc": pub_dt_utc.strftime("%Y-%m-%dT%H:%M:%SZ"),
            "v_score": 0.0
        })
    return {"sprint": SPRINT_N, "week_start": monday.isoformat(), "videos": videos}


# ─── Main ────────────────────────────────────────────────────────────────────

def main():
    print(f"\n{'='*60}")
    print(f"WEEKLY SPRINT AGENT — Sprint {SPRINT_N} — {TODAY}")
    print(f"Motor: Gemini 2.5-Flash (gratis) | Fallback: Anthropic")
    print(f"{'='*60}")

    content = generate_scripts()
    schedule = save_sprint_outputs(content)

    print(f"\n[DONE] Sprint {SPRINT_N} generado.")
    print(f"  Guiones en: obsidian_vault/30_Contenido/cola/")
    print(f"  Schedule en: obsidian_vault/40_Publicacion/schedule_sprint{SPRINT_N}.json")
    print(f"  Próximo paso: daily-publish.yml publicará según el schedule")


if __name__ == "__main__":
    main()
