"""
council.py — CONSEJO DE AGENTES AUTÓNOMO (loop de auto-mejora cerrado)
================================================================================
El sistema que hace al motor MÁS INTELIGENTE solo, comparando lo que la
SIMULACIÓN predijo contra los RESULTADOS REALES de TikTok, y dejando que cada
agente haga consultoría (razonamiento LLM sobre datos reales) para evolucionar
la estrategia que leen los generadores.

Ciclo (todo verídico, nada hardcodeado):
  1. EVIDENCIA   — junta datos reales de la DB (videos publicados + métricas
                   reales + V-Score predicho, crecimiento, patrones, estrategia).
  2. CALIBRACIÓN (A8) — compara predicción vs realidad por componente, mide el
                   sesgo de la simulación, re-ajusta los PESOS del V-Score (con
                   guardas estadísticas), versiona en vscore_weight_history, y
                   escribe offsets en config/sim_calibration.json que audience_sim
                   aplica → la simulación se vuelve más precisa cada ciclo.
  3. CONSULTORÍA — cada agente (A1,A2,A3,A7,A9) recibe SUS datos y devuelve una
                   recomendación concreta vía Gemini. Se registra como actividad
                   real en automation_queue (visible en la oficina).
  4. SÍNTESIS (A0) — fusiona las recomendaciones en cambios concretos de
                   content_strategy.json (niche_weights, hooks, horarios, voces).
  5. REPORTE     — escribe el acta del consejo a obsidian + briefing en la DB.

Rigor: con pocos datos NO sobre-ajusta (sería overfitting); registra "datos
insuficientes" y mantiene defaults. La máquina es correcta desde n=0 y gana
poder conforme se acumulan publicaciones reales.

Uso:
  python scripts/learn/council.py                # corre el consejo completo
  python scripts/learn/council.py --calibrate    # solo calibración A8
"""
from __future__ import annotations
import os, sys, json, math, statistics, urllib.request
from pathlib import Path
from datetime import datetime, timezone

sys.stdout.reconfigure(encoding="utf-8")
ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from dashboard import db

STRATEGY = ROOT / "config" / "content_strategy.json"
SIM_CALIB = ROOT / "config" / "sim_calibration.json"
ACTA_DIR = ROOT / "obsidian_vault" / "60_Aprendizaje" / "consejo"
MIN_SAMPLES_CALIB = 8       # umbral para re-ajustar pesos sin overfitting
DEFAULT_WEIGHTS = {"ve": 0.35, "spread": 0.30, "sentiment": 0.20, "hook": 0.15}

# ── Gemini (mismo endpoint que ya validamos) ────────────────────────────────
for line in (ROOT / ".env").read_text(encoding="utf-8").splitlines():
    if line and not line.startswith("#") and "=" in line:
        k, v = line.split("=", 1)
        os.environ.setdefault(k, v.strip().strip('"').strip("'"))
_KEY = os.environ.get("GEMINI_API_KEY", "")

def gemini_json(prompt: str, temperature: float = 0.6) -> dict | None:
    if not _KEY or _KEY.startswith("<<<"):
        return None
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key={_KEY}"
    body = {"contents": [{"parts": [{"text": prompt}]}],
            "generationConfig": {"responseMimeType": "application/json", "temperature": temperature}}
    import time as _t
    for attempt in range(3):  # reintento ante 503/429 transitorios de Gemini
        try:
            req = urllib.request.Request(url, data=json.dumps(body).encode("utf-8"),
                                         headers={"Content-Type": "application/json"})
            with urllib.request.urlopen(req, timeout=70) as r:
                data = json.loads(r.read())
            return json.loads(data["candidates"][0]["content"]["parts"][0]["text"])
        except Exception as e:
            code = getattr(e, "code", 0)
            if attempt < 2 and code in (503, 429, 500):
                _t.sleep(2 + attempt * 3); continue
            print(f"  [gemini] fallo: {str(e)[:90]}")
            return None
    return None


# ════════════════════════════════════════════════════════════════════════════
# 1. EVIDENCIA — datos reales
# ════════════════════════════════════════════════════════════════════════════
def collect_evidence() -> dict:
    db.init_db()
    # videos publicados con métrica real + predicción
    rows = db.query("""
        SELECT v.id, v.video_code, v.niche, v.hook, v.vscore_predicted,
               s.visualeyes_attention ve, s.mirofish_spread spread,
               s.mirofish_sentiment sentiment, s.hook_score hook, s.source sim_source,
               m.views, m.likes, m.comments
        FROM videos v
        LEFT JOIN simulations s ON s.video_id = v.id
        LEFT JOIN (SELECT video_id, MAX(views) views, MAX(likes) likes, MAX(comments) comments
                   FROM metrics_snapshots GROUP BY video_id) m ON m.video_id = v.id
        WHERE m.views IS NOT NULL
        ORDER BY m.views DESC
    """)
    growth = db.query_one("SELECT date,total_views,posts_count,followers FROM account_metrics_daily ORDER BY date DESC LIMIT 1")
    strat = json.loads(STRATEGY.read_text(encoding="utf-8")) if STRATEGY.exists() else {}
    # baseline de la cuenta
    views = [r["views"] for r in rows if r["views"]]
    baseline = statistics.median(views) if views else 0
    return {"videos": rows, "growth": growth, "strategy": strat,
            "baseline_views": baseline, "n_with_metrics": len(rows)}


def real_outcome(r: dict, baseline: float) -> dict:
    """Convierte métricas reales en proxies 0-1 comparables a los componentes
    predichos. HONESTO: sin retención/shares del scraper, spread/hook son proxies
    de engagement (mejoran cuando se scrapee analytics profundo)."""
    v = max(r["views"] or 0, 1)
    likes = r["likes"] or 0
    comments = r["comments"] or 0
    perf = 1 - math.exp(-(v) / (baseline + 1))           # 0-1 vs baseline de la cuenta
    spread_real = min((likes + 2 * comments) / v, 1.0)   # engagement como proxy de viralidad
    sentiment_real = min(likes / v * 5, 1.0)             # ratio de likes (proxy de sentimiento +)
    return {"perf": round(perf, 4), "spread_real": round(spread_real, 4),
            "sentiment_real": round(sentiment_real, 4), "views": v}


# ════════════════════════════════════════════════════════════════════════════
# 2. CALIBRACIÓN (A8) — simulación vs realidad
# ════════════════════════════════════════════════════════════════════════════
def calibrate(evidence: dict) -> dict:
    # SOLO pares del formato de simulación ACTUAL (audience_sim 0-1). Excluye
    # registros viejos de otra escala que contaminarían el sesgo.
    rows = [r for r in evidence["videos"]
            if r.get("spread") is not None and 0 <= (r["spread"] or -1) <= 1
            and (r.get("sim_source") or "").startswith("gemini")]
    baseline = evidence["baseline_views"]
    paired = []
    for r in rows:
        ro = real_outcome(r, baseline)
        paired.append({**r, **ro})
        # registrar comparación por-componente
        db.execute("""INSERT INTO simulations_vs_reality
            (video_id, mf_spread_predicted, mf_spread_real, mf_spread_delta,
             mf_sentiment_predicted, mf_sentiment_real, mf_sentiment_delta,
             vscore_predicted_total, vscore_real_total)
            VALUES (?,?,?,?,?,?,?,?,?)""",
            (r["id"], r["spread"], ro["spread_real"], (r["spread"] or 0) - ro["spread_real"],
             r["sentiment"], ro["sentiment_real"], (r["sentiment"] or 0) - ro["sentiment_real"],
             r["vscore_predicted"], ro["perf"] * 100))
    n = len(paired)
    if n == 0:
        _save_calibration(DEFAULT_WEIGHTS, 0.0, 0.0, 0, "sin pares predicción/realidad")
        return {"status": "no_data", "n": 0,
                "message": "0 videos publicados con predicción + métrica real. Máquina lista; calibra al acumular datos."}

    # sesgo de la simulación (cuánto sobre/sub-predice)
    spread_bias = statistics.mean((p["spread"] or 0) - p["spread_real"] for p in paired)
    sent_bias = statistics.mean((p["sentiment"] or 0) - p["sentiment_real"] for p in paired)
    # error del V-Score total vs performance real
    errors = [(p["vscore_predicted"] or 0) / 100 - p["perf"] for p in paired]
    mae_before = statistics.mean(abs(e) for e in errors)

    weights = dict(DEFAULT_WEIGHTS)
    note = f"n={n}; sesgo spread={spread_bias:+.3f}, sentiment={sent_bias:+.3f}"
    if n >= MIN_SAMPLES_CALIB:
        # re-pesar por correlación de cada componente predicho con la performance real
        comps = {"ve": [(p["ve"] or 0) / 10 for p in paired],
                 "spread": [p["spread"] or 0 for p in paired],
                 "sentiment": [p["sentiment"] or 0 for p in paired],
                 "hook": [p["hook"] or 0 for p in paired]}
        perfs = [p["perf"] for p in paired]
        corrs = {k: max(_corr(v, perfs), 0.0) for k, v in comps.items()}
        tot = sum(corrs.values())
        if tot > 0:
            weights = {k: round(0.5 * DEFAULT_WEIGHTS[k] + 0.5 * (corrs[k] / tot), 3) for k in DEFAULT_WEIGHTS}
            s = sum(weights.values()); weights = {k: round(w / s, 3) for k, w in weights.items()}
        note += f"; pesos re-ajustados por correlación {corrs}"
    else:
        note += f"; <{MIN_SAMPLES_CALIB} muestras → mantengo pesos default (no overfit)"

    # offsets que audience_sim aplicará para acercarse a la realidad (amortiguados
    # y acotados a ±0.4 para nunca romper la escala 0-1 de la simulación)
    _cl = lambda x: round(max(-0.4, min(0.4, x)), 4)
    calib = {"spread_offset": _cl(-0.5 * spread_bias), "spread_scale": 1.0,
             "sentiment_offset": _cl(-0.5 * sent_bias), "sentiment_scale": 1.0,
             "weights": weights}
    _save_calibration(weights, mae_before, 0.0, n, note, calib)
    # versionar pesos
    ver = (db.query_one("SELECT MAX(version) v FROM vscore_weight_history") or {}).get("v") or 0
    db.execute("""INSERT INTO vscore_weight_history
        (version, weights_json, offsets_json, mae_before, mae_after, sample_size, justification)
        VALUES (?,?,?,?,?,?,?)""",
        (ver + 1, json.dumps(weights), json.dumps(calib), mae_before, mae_before, n, note))
    db.execute("""INSERT INTO calibration_log (sample_size, mae, rmse, bias, is_calibrated)
        VALUES (?,?,?,?,?)""",
        (n, mae_before, math.sqrt(statistics.mean(e * e for e in errors)),
         statistics.mean(errors), 1 if (n >= 20 and mae_before < 0.15) else 0))
    return {"status": "ok", "n": n, "mae": round(mae_before, 4),
            "spread_bias": round(spread_bias, 4), "sentiment_bias": round(sent_bias, 4),
            "weights": weights, "note": note}


def _corr(xs, ys):
    if len(xs) < 2: return 0.0
    try:
        return statistics.correlation(xs, ys)
    except Exception:
        return 0.0


def _save_calibration(weights, mae_before, mae_after, n, note, calib=None):
    payload = calib or {"spread_offset": 0.0, "spread_scale": 1.0,
                        "sentiment_offset": 0.0, "sentiment_scale": 1.0, "weights": weights}
    payload.update({"n_samples": n, "mae": round(mae_before, 4), "note": note,
                    "updated_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")})
    SIM_CALIB.parent.mkdir(parents=True, exist_ok=True)
    SIM_CALIB.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


# ════════════════════════════════════════════════════════════════════════════
# 3. CONSULTORÍA — cada agente razona sobre SUS datos reales
# ════════════════════════════════════════════════════════════════════════════
_AGENTS = {
    "A1": ("Investigación de Mercado (PhD análisis competitivo)",
           "Analiza qué nichos y temas tienen tracción real. ¿Qué amplificar, qué reducir?"),
    "A2": ("Psicología de Marketing (PhD neuromarketing)",
           "Analiza los hooks de los videos que funcionaron vs los que no. ¿Qué patrón de hook recomiendas?"),
    "A3": ("Estratega Algorítmico (PhD sistemas de recomendación)",
           "Analiza horarios y hashtags vs rendimiento. ¿Mejores horas UTC y enfoque de hashtags?"),
    "A7": ("Supervisión Evolutiva (QA del sistema)",
           "¿El sistema está mejorando? ¿Cuál es el cuello de botella # 1 a atacar ahora?"),
    "A9": ("Compliance Legal (abogado IP/ToS)",
           "Revisa señales de restricción o riesgo. ¿Algún patrón a evitar para no perder alcance?"),
}

def consult(agent_id: str, evidence: dict, calib: dict) -> dict:
    role, focus = _AGENTS[agent_id]
    top = [{"code": r["video_code"], "niche": r["niche"], "views": r["views"],
            "likes": r["likes"], "hook": (r["hook"] or "")[:80]} for r in evidence["videos"][:6]]
    prompt = (
        f"Eres {role}, un agente del sistema autónomo CurioClip (TikTok de curiosidades, "
        f"meta 10k seguidores en 90 días). Tu tarea: {focus}\n\n"
        f"DATOS REALES:\n- Crecimiento: {evidence['growth']}\n"
        f"- Baseline de vistas: {evidence['baseline_views']}\n"
        f"- Top videos por vistas: {json.dumps(top, ensure_ascii=False)}\n"
        f"- Estrategia actual: {json.dumps(evidence['strategy'].get('niche_weights', {}), ensure_ascii=False)}\n"
        f"- Calibración simulación: {json.dumps({k: calib.get(k) for k in ('n','mae','spread_bias','sentiment_bias')}, ensure_ascii=False)}\n\n"
        f"Si los datos son escasos, dilo honestamente y da la mejor hipótesis accionable. "
        f"Responde SOLO JSON: {{\"insight\": \"<1-2 frases basadas en los datos>\", "
        f"\"action\": \"<acción concreta para el próximo lote>\", \"confidence\": <0..1>}}"
    )
    qid = db.execute("INSERT INTO automation_queue (agent, action, status, started_at) VALUES (?,?,?,?)",
                     (agent_id, "consultoria", "in_progress", db.now_iso()))
    rec = gemini_json(prompt) or {"insight": "sin LLM disponible", "action": "—", "confidence": 0}
    db.execute("UPDATE automation_queue SET status='completed', completed_at=?, result=? WHERE id=?",
               (db.now_iso(), db.safe_json(rec), qid))
    print(f"  [{agent_id}] {rec.get('insight','')[:90]}")
    return {"agent": agent_id, "role": role, **rec}


# ════════════════════════════════════════════════════════════════════════════
# 4. SÍNTESIS (A0) — fusiona en estrategia concreta
# ════════════════════════════════════════════════════════════════════════════
def synthesize(consultations: list, evidence: dict, calib: dict) -> dict:
    strat = dict(evidence["strategy"])
    prompt = (
        "Eres A0, Director del sistema CurioClip. Fusiona las recomendaciones de tu equipo "
        "en ajustes CONCRETOS de estrategia. Recomendaciones:\n"
        + json.dumps(consultations, ensure_ascii=False) +
        f"\n\nEstrategia actual (niche_weights): {json.dumps(strat.get('niche_weights', {}), ensure_ascii=False)}\n"
        "Responde SOLO JSON: {\"niche_weights\": {<nicho>:<peso 0..1, suman ~1>}, "
        "\"hook_directive\": \"<guía de hooks para el próximo lote>\", "
        "\"optimal_posting_hours_utc\": [<horas>], \"decision\": \"<decisión ejecutiva 1 frase>\"}"
    )
    out = gemini_json(prompt, temperature=0.4) or {}
    # aplicar con guardas
    nw = out.get("niche_weights")
    if isinstance(nw, dict) and nw:
        s = sum(v for v in nw.values() if isinstance(v, (int, float))) or 1
        strat["niche_weights"] = {k: round(v / s, 3) for k, v in nw.items() if isinstance(v, (int, float))}
    if out.get("optimal_posting_hours_utc"):
        strat["optimal_posting_hours_utc"] = out["optimal_posting_hours_utc"][:4]
    strat.setdefault("hook_patterns", {})["directive"] = out.get("hook_directive", "")
    strat["vscore_weights"] = calib.get("weights", DEFAULT_WEIGHTS)
    strat["version"] = (strat.get("version", 0) or 0) + 1
    strat["updated_at"] = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    strat["updated_by"] = "agent_council"
    strat.setdefault("evolution_log", []).append({
        "version": strat["version"], "date": datetime.now(timezone.utc).strftime("%Y-%m-%d"),
        "changes": out.get("decision", "consejo autónomo"), "trigger": "agent_council"})
    STRATEGY.write_text(json.dumps(strat, ensure_ascii=False, indent=2), encoding="utf-8")
    return {"decision": out.get("decision", ""), "new_version": strat["version"],
            "niche_weights": strat.get("niche_weights")}


# ════════════════════════════════════════════════════════════════════════════
# ORQUESTADOR DEL CONSEJO
# ════════════════════════════════════════════════════════════════════════════
def run_council() -> dict:
    print(f"\n{'='*64}\nCONSEJO DE AGENTES — {datetime.now(timezone.utc):%Y-%m-%d %H:%M UTC}\n{'='*64}")
    ev = collect_evidence()
    print(f"  evidencia: {ev['n_with_metrics']} videos con métrica real · baseline={ev['baseline_views']} vistas")
    print("  [A8] calibrando simulación vs realidad...")
    calib = calibrate(ev)
    print(f"  [A8] {calib.get('status')} · {calib.get('note', calib.get('message',''))[:90]}")
    print("  consultoría de agentes:")
    consultations = [consult(aid, ev, calib) for aid in _AGENTS]
    print("  [A0] sintetizando estrategia...")
    decision = synthesize(consultations, ev, calib)
    print(f"  [A0] v{decision['new_version']}: {decision['decision'][:90]}")
    _write_acta(ev, calib, consultations, decision)
    # briefing en DB
    db.execute("""INSERT INTO briefings (sprint_number, date, status_summary, kpis_json, decisions)
        VALUES (?,?,?,?,?)""",
        (3, db.now_iso(), f"Consejo: calib n={calib.get('n')} · estrategia v{decision['new_version']}",
         db.safe_json({"calibration": calib}), decision["decision"]))
    print(f"\n[CONSEJO] completo · simulación calibrada · estrategia v{decision['new_version']} · acta guardada")
    return {"calibration": calib, "consultations": consultations, "decision": decision}


def _write_acta(ev, calib, consultations, decision):
    ACTA_DIR.mkdir(parents=True, exist_ok=True)
    ts = datetime.now(timezone.utc).strftime("%Y-%m-%d_%H%M")
    lines = [f"# Acta del Consejo — {ts}\n",
             f"**Evidencia:** {ev['n_with_metrics']} videos con métrica real · baseline {ev['baseline_views']} vistas\n",
             f"## Calibración (A8 — simulación vs realidad)\n```json\n{json.dumps(calib, ensure_ascii=False, indent=2)}\n```\n",
             "## Consultoría de agentes\n"]
    for c in consultations:
        lines.append(f"- **{c['agent']}** ({c['role'].split('(')[0].strip()}): {c.get('insight','')}\n  → _{c.get('action','')}_ (conf {c.get('confidence',0)})\n")
    lines.append(f"\n## Decisión del Director (A0)\n> {decision['decision']}\n\nEstrategia → v{decision['new_version']} · niche_weights: {decision.get('niche_weights')}\n")
    (ACTA_DIR / f"acta_{ts}.md").write_text("".join(lines), encoding="utf-8")


if __name__ == "__main__":
    if "--calibrate" in sys.argv:
        print(json.dumps(calibrate(collect_evidence()), ensure_ascii=False, indent=2))
    else:
        run_council()
