"""
Agente Autónomo — Outlier Cloning Dominical
============================================
GitHub Actions: cada domingo 20:03 UTC.
Motor: Gemini 2.5-Flash GRATIS.
"""
import os, sys, json, datetime
from pathlib import Path

ROOT = Path(__file__).parent.parent.parent
VAULT = ROOT / "obsidian_vault"
AGENTS_DIR = ROOT / ".claude" / "agents"
SPRINT_N = ((datetime.date.today() - datetime.date(2026, 5, 6)).days // 7) + 2  # próximo sprint
TODAY = datetime.date.today().isoformat()


def call_llm(system: str, user: str, max_tokens: int = 8192) -> str:
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
                messages=[{"role": "system", "content": system}, {"role": "user", "content": user}]
            )
            return resp.choices[0].message.content
        except Exception as e:
            print(f"[GEMINI] Falló: {e} → Anthropic fallback...")

    anthropic_key = os.environ.get("ANTHROPIC_API_KEY")
    if anthropic_key:
        import anthropic
        client = anthropic.Anthropic(api_key=anthropic_key)
        resp = client.messages.create(
            model="claude-haiku-4-5-20251001",
            max_tokens=max_tokens,
            system=system,
            messages=[{"role": "user", "content": user}]
        )
        return resp.content[0].text

    sys.exit("[ERROR] Sin LLM disponible.")


def read_research_context() -> str:
    parts = []
    comp = VAULT / "20_Investigacion" / "competidores.md"
    if comp.exists():
        parts.append(comp.read_text(encoding="utf-8")[:2000])

    outliers = sorted((VAULT / "20_Investigacion").glob("outliers_sprint*.md"))
    if outliers:
        parts.append(f"Outliers previos:\n{outliers[-1].read_text(encoding='utf-8')[:1500]}")

    trends = sorted((VAULT / "20_Investigacion" / "trend_reports").glob("trend_*.md"))
    if trends:
        parts.append(f"Tendencias:\n{trends[-1].read_text(encoding='utf-8')[:1000]}")

    cola = VAULT / "30_Contenido" / "cola"
    if cola.exists():
        cola_files = sorted(cola.glob("*.md"), reverse=True)[:3]
        for f in cola_files:
            parts.append(f"Cola existente ({f.name}):\n{f.read_text(encoding='utf-8')[:500]}")

    return "\n\n".join(parts)[:8000]


def main():
    print(f"\n{'='*60}")
    print(f"OUTLIER HUNT — Preparando Sprint {SPRINT_N} — {TODAY}")
    print(f"Motor: Gemini 2.5-Flash (gratis)")
    print(f"{'='*60}")

    context = read_research_context()
    agent_file = AGENTS_DIR / "outlier-hunter.md"
    system = agent_file.read_text(encoding="utf-8").split("---", 2)[-1].strip() \
        if agent_file.exists() else (
        "Eres el outlier-hunter de CurioClip. Ejecutas Outlier Cloning 5 fases. "
        "Buscas en TikTok/YouTube los referentes top del nicho curiosidades en español, "
        "extraes outliers virales y adaptas 25+ guiones al formato CurioClip. "
        "Hook LITERAL en cada guión. Sub-nichos: Ciencia WTF, Misterio, Historia WTF, "
        "Psicología, Comparaciones imposibles."
    )

    user = (
        f"Outlier Cloning Sprint {SPRINT_N} — {TODAY}\n\n"
        f"Contexto previo:\n{context}\n\n"
        f"FASE 1: Identifica 5 cuentas referentes (>50K seg, ER>5%, activas últimos 14 días)\n"
        f"FASE 2: Extrae 25+ outliers (≥3x promedio de vistas)\n"
        f"FASE 3: Analiza estructura: hook literal, problema, CTA, formato\n"
        f"FASE 4: Adapta 25 guiones CurioClip (5 bloques, hook literal obligatorio)\n"
        f"FASE 5: Top 7 con V-Score estimado y horario sugerido\n\n"
        f"Canal: CurioClip | Español LATAM | 13-35 años | TikTok + Facebook"
    )

    content = call_llm(system, user)

    research_dir = VAULT / "20_Investigacion"
    research_dir.mkdir(exist_ok=True)

    ref_path = research_dir / f"referentes_sprint_{SPRINT_N}.md"
    ref_path.write_text(
        f"---\nsprint: {SPRINT_N}\nfecha: {TODAY}\nagente: outlier-hunter-cloud\n"
        f"motor: gemini-2.5-flash\n---\n\n{content}",
        encoding="utf-8"
    )

    out_path = research_dir / f"outliers_sprint_{SPRINT_N}.md"
    out_path.write_text(
        f"---\nsprint: {SPRINT_N}\nfecha: {TODAY}\nagente: outlier-hunter-cloud\n"
        f"motor: gemini-2.5-flash\n---\n\n{content}",
        encoding="utf-8"
    )

    cola_dir = VAULT / "30_Contenido" / "cola"
    cola_dir.mkdir(exist_ok=True)
    cola_path = cola_dir / f"sprint{SPRINT_N}_{TODAY}_outlier_guiones.md"
    cola_path.write_text(
        f"---\nsprint: {SPRINT_N}\nfecha: {TODAY}\nfuente: outlier-cloning-cloud\n"
        f"motor: gemini-2.5-flash\nestado: pendiente\n---\n\n{content}",
        encoding="utf-8"
    )

    print(f"[OK] Referentes: {ref_path.name}")
    print(f"[OK] Outliers: {out_path.name}")
    print(f"[OK] Guiones: {cola_path.name}")
    print(f"[DONE] Outlier Cloning Sprint {SPRINT_N} completado.")


if __name__ == "__main__":
    main()
