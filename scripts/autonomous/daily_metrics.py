"""
Agente Autónomo — Métricas Diarias
====================================
GitHub Actions: cada 2h (mejorado de analytics.yml).
Motor: Gemini 2.5-Flash GRATIS.
"""
import os, sys, datetime
from pathlib import Path

ROOT = Path(__file__).parent.parent.parent
VAULT = ROOT / "obsidian_vault"
AGENTS_DIR = ROOT / ".claude" / "agents"
TODAY = datetime.date.today().isoformat()
NOW = datetime.datetime.now().strftime("%Y-%m-%d %H:%M UTC")


def call_llm(system: str, user: str, max_tokens: int = 4096) -> str:
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

    return f"[SIN LLM] Snapshot vacío — {NOW}"


def read_analytics_state() -> str:
    parts = []
    analitica = VAULT / "50_Analitica"
    if analitica.exists():
        snapshots = sorted(analitica.glob("*.md"), reverse=True)[:3]
        for s in snapshots:
            parts.append(f"=== {s.name} ===\n{s.read_text(encoding='utf-8')[:800]}")

    vscore_dir = VAULT / "30_Contenido" / "simulaciones"
    if vscore_dir.exists():
        for v in sorted(vscore_dir.glob("*vscore*.md"), reverse=True)[:4]:
            parts.append(f"=== {v.name} ===\n{v.read_text(encoding='utf-8')[:400]}")

    pub_dir = VAULT / "40_Publicacion" / "logs"
    if pub_dir.exists():
        for p in sorted(pub_dir.glob("*.md"), reverse=True)[:2]:
            parts.append(f"=== {p.name} ===\n{p.read_text(encoding='utf-8')[:400]}")

    return "\n\n".join(parts)[:5000]


def main():
    print(f"[START] Daily Metrics — {NOW}")

    state = read_analytics_state()
    agent_file = AGENTS_DIR / "analytics-scientist.md"
    system = agent_file.read_text(encoding="utf-8").split("---", 2)[-1].strip() \
        if agent_file.exists() else (
        "Eres el analytics-scientist de CurioClip. Analizas métricas de TikTok/Facebook, "
        "calculas V-Score, calibras el predictor y generas insights accionables. "
        "DISCLAIMER: margen de error ±15% hasta calibración (≥20 publicaciones)."
    )

    user = (
        f"Análisis diario — {NOW}\n\n"
        f"Estado vault:\n{state}\n\n"
        f"Genera:\n"
        f"1. Snapshot del día (datos disponibles, indica si son estimados)\n"
        f"2. Estado calibración V-Score\n"
        f"3. M6 LEARN si hay videos publicados hace 24h/72h\n"
        f"4. 3 insights accionables para el próximo contenido\n"
        f"5. Alertas si KPIs por debajo de target\n\n"
        f"Si no hay datos TikTok API: basar en predicciones V-Score y notar claramente."
    )

    content = call_llm(system, user)

    snapshot_path = VAULT / "50_Analitica" / f"{TODAY}_auto.md"
    snapshot_path.write_text(
        f"---\nfecha: {TODAY}\nhora: {NOW}\nagente: analytics-scientist-cloud\n"
        f"motor: gemini-2.5-flash\nestado: auto\n---\n\n{content}",
        encoding="utf-8"
    )
    print(f"[OK] Snapshot: {snapshot_path.name}")
    print("[DONE] Daily metrics completado.")


if __name__ == "__main__":
    main()
