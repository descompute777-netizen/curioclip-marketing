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

def _load_strategy_context() -> str:
    """Read the evolved content_strategy.json and format as LLM context."""
    strat_path = ROOT / "config" / "content_strategy.json"
    if not strat_path.exists():
        return ""
    try:
        s = json.loads(strat_path.read_text(encoding="utf-8"))
    except Exception:
        return ""

    parts = []

    # Niche weights (data-driven)
    nw = s.get("niche_weights", {})
    if nw:
        ranked = sorted(nw.items(), key=lambda x: -x[1])
        niche_str = ", ".join(f"{k} ({v:.0%})" for k, v in ranked if v > 0.05)
        parts.append(f"DISTRIBUCION DE NICHOS (basada en rendimiento real): {niche_str}")

    # Duration
    dr = s.get("target_duration_range_s")
    if dr:
        parts.append(f"DURACION OBJETIVO: {dr[0]}-{dr[1]} segundos (sweet spot segun datos)")

    # Voice preferences
    vp = s.get("voice_preferences", {})
    if vp.get("top_voices"):
        parts.append(f"VOCES TOP (mayor engagement): {', '.join(vp['top_voices'][:3])}")
    if vp.get("avoid_voices"):
        parts.append(f"VOCES A EVITAR (bajo rendimiento): {', '.join(vp['avoid_voices'])}")

    # Hook patterns
    hp = s.get("hook_patterns", {})
    if hp.get("preferred_starts"):
        parts.append(f"HOOKS QUE FUNCIONAN (primera palabra): {', '.join(hp['preferred_starts'][:5])}")
    if hp.get("avoid_patterns"):
        parts.append(f"HOOKS A EVITAR: {', '.join(hp['avoid_patterns'])}")

    # Growth status
    g = s.get("growth", {})
    if g:
        parts.append(
            f"ESTADO DEL CRECIMIENTO: {g.get('trajectory','?').upper()} — "
            f"{g.get('followers_current',0)}/{g.get('followers_goal',10000)} seguidores, "
            f"{g.get('days_remaining',0)} dias restantes, "
            f"necesitamos {g.get('followers_needed_per_day',0):.0f} seg/dia"
        )

    # Restrictions
    r = s.get("restrictions", {})
    if r.get("detected"):
        codes = [rv["video_code"] for rv in r.get("restricted_videos", [])]
        parts.append(f"ALERTA RESTRICCIONES: Videos posiblemente restringidos: {', '.join(codes)}")
    if r.get("shadowban_risk") == "high":
        parts.append("ALERTA SHADOWBAN: Riesgo alto detectado. Variar hashtags, evitar contenido repetitivo.")

    if not parts:
        return ""
    return "\n".join(f"  - {p}" for p in parts)


def generate_scripts() -> str:
    print(f"\n[LLM] Generando guiones Sprint {SPRINT_N} con Gemini...")
    vault_state = read_vault_summary()
    strategy_context = _load_strategy_context()

    agent_file = AGENTS_DIR / "weekly-orchestrator.md"
    system = agent_file.read_text(encoding="utf-8").split("---", 2)[-1].strip() \
        if agent_file.exists() else (
        "Eres el weekly-orchestrator de CurioClip. Genera planes de sprint y 25+ guiones "
        "de curiosidades en español LATAM. Hook LITERAL (0-3s) en cada guión. "
        "Formato 5 bloques: HOOK | IDENTIFICACIÓN | PROMESA | DESARROLLO | CTA."
    )

    strategy_block = ""
    if strategy_context:
        strategy_block = (
            f"\n\nDATOS REALES DEL EVOLUTION ENGINE (usar para optimizar):\n"
            f"{strategy_context}\n"
            f"IMPORTANTE: Ajusta la distribucion de sub-nichos y tipos de hooks segun estos datos. "
            f"Los nichos con mayor peso son los que mejor performan. Prioriza hooks con las "
            f"primeras palabras que mejor funcionan. Respeta la duracion objetivo.\n"
        )

    user = (
        f"Sprint {SPRINT_N} — {TODAY}\n\n"
        f"Estado vault:\n{vault_state}\n"
        f"{strategy_block}\n"
        f"PRODUCCION: 4 videos por dia = 28 videos por semana.\n"
        f"Genera:\n"
        f"1. Briefing ejecutivo (KPIs, estado, decisiones)\n"
        f"2. 35+ guiones adaptados del nicho. Distribuye segun los pesos de nicho arriba. "
        f"Hook LITERAL en cada uno.\n"
        f"3. TOP 28 para esta semana (4 por dia) con V-Score estimado (/10)\n"
        f"4. 3 hipótesis de oportunidad basadas en los datos reales\n"
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

    # Extraer voiceover scripts via segunda llamada LLM, luego crear schedule
    scripts = extract_voiceover_scripts(content)
    schedule = extract_schedule(content, scripts)
    sched_path = VAULT / "40_Publicacion" / f"schedule_sprint{SPRINT_N}.json"
    sched_path.parent.mkdir(exist_ok=True)
    sched_path.write_text(json.dumps(schedule, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"[OK] Schedule: {sched_path.name}")
    return schedule


VIDEOS_PER_DAY = 4


def extract_voiceover_scripts(content: str) -> list[dict]:
    """Second LLM call: parse generated briefing into 28 structured voiceover scripts."""
    import re
    total = VIDEOS_PER_DAY * 7
    print(f"[LLM] Extracting {total} voiceover scripts from guiones...")

    system = (
        "You extract voiceover scripts from Spanish curiosity content. "
        "Return ONLY a valid JSON array — no markdown fences, no explanation."
    )

    all_scripts = []
    # Batch in groups of 14 to stay within token limits
    batch_size = 14
    for batch_idx in range(0, total, batch_size):
        batch_n = min(batch_size, total - batch_idx)
        user = (
            f"From the following content, extract guiones #{batch_idx+1} to #{batch_idx+batch_n} "
            f"from the TOP {total} selected for this week.\n"
            f"For each guion, generate a complete voiceover script in Spanish (30-60 seconds "
            f"when read aloud, 80-150 words).\n"
            f"Structure each script as:\n"
            f"- Hook (0-3s): the exact hook literal from the guion\n"
            f"- Body (15-40s): expand the topic with 3-4 fascinating facts\n"
            f"- CTA (3-5s): call to action (seguir, guardar, comentar)\n\n"
            f"Return a JSON array of exactly {batch_n} objects:\n"
            '[\n'
            '  {\n'
            '    "title": "guion title",\n'
            '    "voiceover_text": "full voiceover script in Spanish, 80-150 words",\n'
            '    "caption": "TikTok caption: title + 2-3 topic hashtags + #curioclip #fyp",\n'
            '    "hashtags": "#topic1 #topic2 #curioclip #datoscuriosos #fyp"\n'
            '  }\n'
            ']\n\n'
            f"Content:\n{content[:12000]}"
        )

        raw = call_llm(system, user, max_tokens=6144)

        json_match = re.search(r'\[[\s\S]*\]', raw)
        if json_match:
            try:
                batch = json.loads(json_match.group())
                if isinstance(batch, list):
                    all_scripts.extend(batch)
                    print(f"  [OK] Batch {batch_idx//batch_size + 1}: {len(batch)} scripts")
            except json.JSONDecodeError:
                print(f"  [WARN] Batch {batch_idx//batch_size + 1}: JSON parse failed")

    if len(all_scripts) >= total:
        print(f"[OK] Extracted {len(all_scripts)} voiceover scripts total")
        return all_scripts[:total]

    print(f"[WARN] Only got {len(all_scripts)}/{total} scripts — padding with available")
    return all_scripts


def extract_schedule(content: str, scripts: list[dict] | None = None) -> dict:
    """Build schedule: 4 videos/day × 7 days = 28 videos/week."""
    week_start = datetime.date.today()
    days_to_monday = (7 - week_start.weekday()) % 7 or 7
    monday = week_start + datetime.timedelta(days=days_to_monday)

    # 4 slots per day (CDMX times → UTC, CDMX is UTC-6)
    daily_slots_utc = [
        (15, 0),   # 09:00 CDMX
        (19, 0),   # 13:00 CDMX
        (23, 0),   # 17:00 CDMX
        (3, 0),    # 21:00 CDMX (next day UTC)
    ]

    days_es = ["lunes", "martes", "miercoles", "jueves", "viernes", "sabado", "domingo"]
    videos = []
    vid_idx = 0

    for day_offset in range(7):
        pub_date = monday + datetime.timedelta(days=day_offset)
        for slot_idx, (hour, minute) in enumerate(daily_slots_utc):
            pub_dt_utc = datetime.datetime(
                pub_date.year, pub_date.month, pub_date.day, hour, minute, 0
            )
            if hour < 6:
                pub_dt_utc += datetime.timedelta(days=1)

            script = scripts[vid_idx] if scripts and vid_idx < len(scripts) else {}
            default_hashtags = "#datoscuriosos #sabiasque #curioclip #curiosidades"

            videos.append({
                "day": days_es[day_offset],
                "slot": slot_idx + 1,
                "date": pub_date.isoformat(),
                "guion_id": f"S{SPRINT_N}_V{vid_idx+1}",
                "video_url": "",
                "voiceover_text": script.get("voiceover_text", ""),
                "caption": script.get("caption", ""),
                "hashtags": script.get("hashtags", default_hashtags),
                "published": False,
                "publish_at_utc": pub_dt_utc.strftime("%Y-%m-%dT%H:%M:%SZ"),
                "v_score": 0.0,
            })
            vid_idx += 1

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
