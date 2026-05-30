"""
audience_sim.py — Simulación de audiencia con Gemini (función de MiroFish para V-Score)
================================================================================
Cumple la MISMA función que MiroFish_spread + MiroFish_sentiment del V-Score:
predecir cómo reaccionaría la audiencia objetivo (13-35, LATAM, curiosidades) a
un video, SIN la dependencia dura de Zep/OASIS. Usa Gemini para simular un panel
de espectadores y devuelve métricas REALES (no aleatorias) por video.

Cuando haya ZEP_API_KEY, MiroFish puede reemplazar a este módulo (mismo contrato).

  from scripts.autonomous.audience_sim import simulate_audience
  r = simulate_audience(hook, caption, niche, voiceover_text)
  # r = {"hook_hold":0.0-1, "spread":0.0-1, "sentiment":0.0-1, "n":int, "verdict":str}
"""
from __future__ import annotations
import os, json, urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
for line in (ROOT / ".env").read_text(encoding="utf-8").splitlines():
    if line and not line.startswith("#") and "=" in line:
        k, v = line.split("=", 1)
        os.environ.setdefault(k, v.strip().strip('"').strip("'"))

_KEY = os.environ.get("GEMINI_API_KEY", "")
_MODEL = "gemini-2.5-flash"

_PROMPT = """Eres un panel de {n} espectadores reales de TikTok del público objetivo de
CurioClip: 13-35 años, LATAM y España, consumidores ávidos de curiosidades y datos
asombrosos, scroll rápido. Reacciona HONESTAMENTE a este video corto (no seas
complaciente; la mayoría del público es exigente y hace scroll si no engancha).

NICHO: {niche}
HOOK (primeros 3s, literal): "{hook}"
CAPTION: "{caption}"
GUION COMPLETO: "{script}"

Estima, como agregado del panel, devolviendo SOLO JSON:
{{
  "hook_hold": <0..1 fracción que NO hace scroll en los primeros 3s>,
  "spread": <0..1 fracción que compartiría o guardaría el video>,
  "sentiment": <0..1 sentimiento positivo promedio>,
  "verdict": "<una frase: por qué funciona o falla>"
}}"""


def _gemini_json(prompt: str) -> dict | None:
    if not _KEY or _KEY.startswith("<<<"):
        return None
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{_MODEL}:generateContent?key={_KEY}"
    body = {
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {"responseMimeType": "application/json", "temperature": 0.7},
    }
    try:
        req = urllib.request.Request(url, data=json.dumps(body).encode("utf-8"),
                                     headers={"Content-Type": "application/json"})
        with urllib.request.urlopen(req, timeout=60) as r:
            data = json.loads(r.read())
        txt = data["candidates"][0]["content"]["parts"][0]["text"]
        return json.loads(txt)
    except Exception as e:
        print(f"[audience_sim] Gemini falló: {str(e)[:120]}")
        return None


def _load_calib() -> dict:
    """Offsets aprendidos por el consejo (council.py) para acercar la simulación
    a la realidad. Si no existen, identidad (sin corrección)."""
    p = ROOT / "config" / "sim_calibration.json"
    if p.exists():
        try:
            c = json.loads(p.read_text(encoding="utf-8"))
            return {"so": c.get("spread_offset", 0.0), "ss": c.get("spread_scale", 1.0),
                    "eo": c.get("sentiment_offset", 0.0), "es": c.get("sentiment_scale", 1.0)}
        except Exception:
            pass
    return {"so": 0.0, "ss": 1.0, "eo": 0.0, "es": 1.0}


def simulate_audience(hook: str, caption: str, niche: str, script: str,
                      n: int = 200) -> dict:
    """Devuelve métricas de reacción de audiencia (0-1), corregidas por la
    calibración aprendida (simulación vs realidad). Fallback neutro si falla."""
    prompt = _PROMPT.format(n=n, niche=niche or "curiosidades", hook=hook or "",
                            caption=caption or "", script=(script or "")[:1200])
    r = _gemini_json(prompt)
    if not r:
        return {"hook_hold": None, "spread": None, "sentiment": None, "n": 0,
                "verdict": "simulación no disponible (sin LLM)", "source": "unavailable"}
    clamp = lambda x: max(0.0, min(1.0, float(x)))
    c = _load_calib()
    spread = clamp(clamp(r.get("spread", 0.3)) * c["ss"] + c["so"])
    sentiment = clamp(clamp(r.get("sentiment", 0.6)) * c["es"] + c["eo"])
    return {
        "hook_hold": clamp(r.get("hook_hold", 0.5)),
        "spread": spread,
        "sentiment": sentiment,
        "n": n,
        "verdict": str(r.get("verdict", ""))[:200],
        "source": "gemini_audience_panel_calibrated",
    }


if __name__ == "__main__":
    demo = simulate_audience(
        "¿Por qué cuando tú aguantas la respiración, sientes que te asfixias?",
        "Tu cuerpo te miente cuando aguantas la respiración",
        "salud",
        "No es por falta de oxígeno, es el CO2 acumulándose en tu sangre...",
        n=200)
    print(json.dumps(demo, ensure_ascii=False, indent=2))
