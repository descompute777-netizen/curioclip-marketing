"""
Audience Simulator — CurioClip
================================
Reemplazo ligero de MiroFish usando Gemini directamente.

Genera N agentes simulados (perfiles TikTok LATAM/España), cada uno
evalúa el video V5 y decide acciones (ver, like, share, save, comentar, ignorar).
La red de propagación se construye como grafo dirigido y se visualiza en HTML.

Output:
  - obsidian_vault/30_Contenido/simulaciones/V5_audience_graph.json
  - obsidian_vault/30_Contenido/simulaciones/V5_audience_graph.html
  - obsidian_vault/30_Contenido/simulaciones/V5_simulation_report.md
"""
import sys
sys.stdout.reconfigure(encoding='utf-8')
import os
import json
import random
import urllib.request
from pathlib import Path
from datetime import datetime, timezone

# Cargar API key
ENV_FILE = Path(__file__).parent.parent.parent / ".env"
GEMINI_KEY = None
if ENV_FILE.exists():
    for line in ENV_FILE.read_text().splitlines():
        if line.startswith("GEMINI_API_KEY="):
            GEMINI_KEY = line.split("=", 1)[1].strip()
            break

GEMINI_URL = "https://generativelanguage.googleapis.com/v1beta/openai/chat/completions"
N_AGENTS = 100  # 100 agentes (10 batches) — Gemini free tier ~10 RPM
BATCH_SLEEP = 7  # segundos entre llamadas a Gemini para no exceder rate limit

# Perfiles demográficos basados en avatar CurioClip
DEMOGRAPHICS = {
    "edad": [(13,17,0.10),(18,24,0.45),(25,34,0.30),(35,44,0.10),(45,60,0.05)],
    "genero": [("M",0.45),("F",0.55)],
    "pais": [("Mexico",0.30),("Argentina",0.18),("Colombia",0.15),("Spain",0.12),
             ("Chile",0.08),("Peru",0.07),("Venezuela",0.05),("Otros",0.05)],
    "interes": [("ciencia",0.20),("entretenimiento",0.30),("educacion",0.15),
                ("misterio",0.12),("tecnologia",0.10),("humor",0.08),("otros",0.05)],
    "scroll_intent": [("aburrido",0.40),("buscando_aprender",0.20),("entretenimiento",0.30),("compartir",0.10)],
}


def weighted_pick(weighted_list):
    if isinstance(weighted_list[0], tuple) and len(weighted_list[0]) == 3:
        # Range tuples (min,max,weight)
        choice = random.choices(weighted_list, weights=[w for *_, w in weighted_list])[0]
        return random.randint(choice[0], choice[1])
    items = [it for it, _ in weighted_list]
    weights = [w for _, w in weighted_list]
    return random.choices(items, weights=weights)[0]


def generate_agents(n):
    agents = []
    for i in range(n):
        agents.append({
            "id": f"agent_{i:04d}",
            "edad": weighted_pick(DEMOGRAPHICS["edad"]),
            "genero": weighted_pick(DEMOGRAPHICS["genero"]),
            "pais": weighted_pick(DEMOGRAPHICS["pais"]),
            "interes": weighted_pick(DEMOGRAPHICS["interes"]),
            "scroll_intent": weighted_pick(DEMOGRAPHICS["scroll_intent"]),
            "followers": random.choices([5,50,500,5000,50000],[0.5,0.3,0.15,0.04,0.01])[0],
        })
    return agents


VIDEO_BRIEF = """
HOOK (0-3s): "Metió su mano en plomo fundido a 327 grados Celsius"
DESARROLLO: Explicación del efecto Leidenfrost — barrera de vapor protege milisegundos
WARNING: "Solo funciona milisegundos. No intentar en casa"
CTA: "¿Qué experimento quieres que explique?"
FORMATO: 9:16, 34s, voiceover IA + B-roll molten metal + subtitulos en español
NICHO: Curiosidades / Ciencia WTF
"""


def gemini_batch_evaluate(agents_batch):
    """Evaluar un batch de 10 agentes con una sola llamada a Gemini para eficiencia."""
    prompt = f"""Eres un simulador de comportamiento TikTok. Para cada agente abajo,
predice su acción al ver este video:

VIDEO:
{VIDEO_BRIEF}

AGENTES (responde JSON array, una entrada por agente):
{json.dumps(agents_batch, ensure_ascii=False)}

Devuelve un objeto JSON con un array "responses" donde cada entrada tiene:
- id (string)
- scroll_past_3s (bool)
- completed (bool)
- liked (bool)
- saved (bool)
- shared (bool)
- commented (bool)
- comment_sentiment ("positivo"|"neutro"|"negativo")
- razon (string corta, max 80 caracteres)

Formato exacto: {{"responses": [...]}}
"""
    body = json.dumps({
        "model": "gemini-2.5-flash",
        "messages": [{"role": "user", "content": prompt}],
        "max_tokens": 16000,
        "temperature": 0.7,
        "response_format": {"type": "json_object"},
    }).encode()
    req = urllib.request.Request(GEMINI_URL, data=body, headers={
        "Authorization": f"Bearer {GEMINI_KEY}",
        "Content-Type": "application/json",
    })
    try:
        with urllib.request.urlopen(req, timeout=60) as r:
            data = json.loads(r.read())
            text = data["choices"][0]["message"]["content"].strip()
            if text.startswith("```"):
                text = text.split("```")[1]
                if text.startswith("json"):
                    text = text[4:]
            parsed = json.loads(text)
            # Soportar tanto array directo como {"responses": [...]}
            if isinstance(parsed, dict) and "responses" in parsed:
                return parsed["responses"]
            return parsed
    except Exception as e:
        print(f"[BATCH FAIL] {e}")
        return []


def simulate(agents, batch_size=10):
    """Simula respuestas en batches con sleep para respetar rate limit Gemini."""
    import time as _t
    results = []
    total_batches = (len(agents)+batch_size-1)//batch_size
    for i in range(0, len(agents), batch_size):
        batch = agents[i:i+batch_size]
        bn = i//batch_size+1
        print(f"[SIM] Batch {bn}/{total_batches}: {len(batch)} agentes")
        responses = gemini_batch_evaluate(batch)
        by_id = {r["id"]: r for r in responses if isinstance(r, dict) and "id" in r}
        # Match positionally if id-based match failed
        if not by_id and isinstance(responses, list) and len(responses) == len(batch):
            for ag, resp in zip(batch, responses):
                if isinstance(resp, dict):
                    resp["id"] = ag["id"]
                    by_id[ag["id"]] = resp
        for agent in batch:
            r = by_id.get(agent["id"])
            if r:
                results.append({**agent, **r, "_simulated": True})
            else:
                results.append({**agent, "scroll_past_3s": False, "completed": False,
                                "liked": False, "saved": False, "shared": False,
                                "commented": False, "comment_sentiment": "neutro",
                                "razon": "no respuesta", "_simulated": False})
        if bn < total_batches:
            print(f"     [sleep {BATCH_SLEEP}s para rate limit]")
            _t.sleep(BATCH_SLEEP)
    return results


def build_propagation_graph(results):
    """Construye grafo: agentes que comparten → seguidores potenciales que verán."""
    nodes, edges = [], []
    for a in results:
        node_color = ("#22c55e" if a.get("saved") else
                      "#3b82f6" if a.get("liked") else
                      "#94a3b8" if a.get("scroll_past_3s") else
                      "#475569")
        nodes.append({
            "id": a["id"],
            "label": f"{a['edad']}/{a['genero']}/{a['pais'][:3]}",
            "title": f"{a['interes']} | {a['scroll_intent']} | {a.get('razon','')[:60]}",
            "color": node_color,
            "size": 6 + min(20, a["followers"]/500),
            "saved": a.get("saved", False),
            "liked": a.get("liked", False),
            "shared": a.get("shared", False),
            "completed": a.get("completed", False),
        })

    # Edges: cada agent que SHARE → 5-50 nuevos viewers (conexiones simuladas)
    sharers = [a for a in results if a.get("shared")]
    for sharer in sharers:
        n_reach = min(20, max(2, sharer["followers"]//100))
        random_targets = random.sample([a["id"] for a in results if a["id"] != sharer["id"]],
                                       min(n_reach, len(results)-1))
        for target in random_targets:
            edges.append({"from": sharer["id"], "to": target, "color": "#fb923c"})

    return {"nodes": nodes, "edges": edges}


def write_html(graph_data, output_path):
    """Genera HTML interactivo con vis-network."""
    html = f"""<!DOCTYPE html>
<html lang="es"><head>
<meta charset="UTF-8">
<title>CurioClip — V5 Audience Simulation Graph</title>
<script src="https://unpkg.com/vis-network/standalone/umd/vis-network.min.js"></script>
<style>
  body{{margin:0;background:#0a0a0a;color:#fff;font-family:Inter,sans-serif}}
  #header{{padding:18px;background:#1a1a1a;border-bottom:1px solid #333}}
  h1{{margin:0;font-size:20px;color:#FFD700}}
  .stats{{display:flex;gap:24px;margin-top:8px;font-size:13px}}
  .stat strong{{color:#FFD700}}
  #network{{height:calc(100vh - 100px);background:#0f1117}}
  .legend{{position:absolute;top:90px;right:20px;background:#1a1a1a;padding:12px;border-radius:6px;font-size:12px}}
  .dot{{display:inline-block;width:10px;height:10px;border-radius:50%;margin-right:6px;vertical-align:middle}}
</style></head>
<body>
<div id="header">
  <h1>🧠 CurioClip — Simulación de Audiencia V5 (Plomo Fundido)</h1>
  <div class="stats">
    <div class="stat">Agentes: <strong>{len(graph_data['nodes'])}</strong></div>
    <div class="stat">Save rate: <strong>{sum(1 for n in graph_data['nodes'] if n['saved'])/len(graph_data['nodes'])*100:.1f}%</strong></div>
    <div class="stat">Like rate: <strong>{sum(1 for n in graph_data['nodes'] if n['liked'])/len(graph_data['nodes'])*100:.1f}%</strong></div>
    <div class="stat">Share rate: <strong>{sum(1 for n in graph_data['nodes'] if n['shared'])/len(graph_data['nodes'])*100:.1f}%</strong></div>
    <div class="stat">Completion: <strong>{sum(1 for n in graph_data['nodes'] if n['completed'])/len(graph_data['nodes'])*100:.1f}%</strong></div>
    <div class="stat">Aristas propagación: <strong>{len(graph_data['edges'])}</strong></div>
  </div>
</div>
<div class="legend">
  <div><span class="dot" style="background:#22c55e"></span>Saved (alto valor)</div>
  <div><span class="dot" style="background:#3b82f6"></span>Liked</div>
  <div><span class="dot" style="background:#94a3b8"></span>Hook pasado, no engagement</div>
  <div><span class="dot" style="background:#475569"></span>Scrolled past</div>
  <div><span class="dot" style="background:#fb923c"></span>Edge = share propagation</div>
</div>
<div id="network"></div>
<script>
  const nodes = new vis.DataSet({json.dumps(graph_data['nodes'])});
  const edges = new vis.DataSet({json.dumps(graph_data['edges'])});
  new vis.Network(document.getElementById('network'),
    {{nodes, edges}},
    {{nodes:{{font:{{color:'#fff',size:11}},borderWidth:0}},
      edges:{{arrows:'to',width:0.5,smooth:{{type:'continuous'}}}},
      physics:{{forceAtlas2Based:{{gravitationalConstant:-50,springLength:100}},
               solver:'forceAtlas2Based',stabilization:{{iterations:200}}}},
      interaction:{{hover:true,tooltipDelay:100}}}});
</script></body></html>"""
    output_path.write_text(html, encoding="utf-8")
    return output_path


def write_report(results, graph_data, output_path):
    saved = sum(1 for r in results if r.get("saved"))
    liked = sum(1 for r in results if r.get("liked"))
    shared = sum(1 for r in results if r.get("shared"))
    commented = sum(1 for r in results if r.get("commented"))
    completed = sum(1 for r in results if r.get("completed"))
    hooked = sum(1 for r in results if r.get("scroll_past_3s"))
    n = len(results)
    pos = sum(1 for r in results if r.get("comment_sentiment")=="positivo")
    neu = sum(1 for r in results if r.get("comment_sentiment")=="neutro")
    neg = sum(1 for r in results if r.get("comment_sentiment")=="negativo")

    spread_score = min(10, (shared/n)*100*0.4 + (saved/n)*100*0.35 + (liked/n)*100*0.25)
    sent_score = (pos*1.0 + neu*0.5 - neg*0.3) / max(n, 1) * 10
    sent_score = max(0, min(10, sent_score + 5))  # baseline 5
    hook_rate = (hooked / n) * 100

    md = f"""---
agente: A8_Prediccion (audience simulator)
fecha: {datetime.now(timezone.utc).isoformat()}
tags: [simulacion, V5, audience, gemini]
n_agentes: {n}
---

# Simulacion de Audiencia V5 (Plomo Fundido)
**Modelo:** Gemini 2.5-flash | **Agentes:** {n}

## Metricas agregadas

| Metrica | Valor | %  |
|---------|-------|-----|
| Hook rate (>3s) | {hooked}/{n} | **{hook_rate:.1f}%** |
| Completion rate | {completed}/{n} | {completed/n*100:.1f}% |
| Like rate | {liked}/{n} | {liked/n*100:.1f}% |
| Save rate | {saved}/{n} | {saved/n*100:.1f}% |
| Share rate | {shared}/{n} | {shared/n*100:.1f}% |
| Comment rate | {commented}/{n} | {commented/n*100:.1f}% |

## Sentimiento (de los que comentarian)
- Positivo: {pos} ({pos/max(commented,1)*100:.0f}%)
- Neutro:   {neu}
- Negativo: {neg}

## V-Score components

- **MiroFish_spread (0-10):** {spread_score:.2f}
- **MiroFish_sentiment (0-10):** {sent_score:.2f}
- **Hook_rate (0-100%):** {hook_rate:.1f}%

## Grafo de propagación
- Nodos: {len(graph_data['nodes'])}
- Edges (shares simulados): {len(graph_data['edges'])}
- Ver visualización: `V5_audience_graph.html`

## Top 10 razones (sample)

"""
    sample = random.sample([r for r in results if r.get("razon")], min(10, n))
    for r in sample:
        md += f"- **{r['id']}** ({r['edad']}/{r['genero']}/{r['pais']}, {r['interes']}): {r.get('razon','')}\n"

    output_path.write_text(md, encoding="utf-8")
    return spread_score, sent_score, hook_rate


def main():
    if not GEMINI_KEY:
        print("[FAIL] GEMINI_API_KEY no encontrada en .env")
        return
    print(f"[OK] Gemini key cargada")

    out_dir = Path("obsidian_vault/30_Contenido/simulaciones")
    out_dir.mkdir(parents=True, exist_ok=True)

    print(f"[GEN] Generando {N_AGENTS} agentes...")
    agents = generate_agents(N_AGENTS)

    print(f"[SIM] Simulando con Gemini 2.5-flash (batches de 20)...")
    results = simulate(agents)

    print(f"[BUILD] Construyendo grafo de propagacion...")
    graph_data = build_propagation_graph(results)

    json_path = out_dir / "V5_audience_graph.json"
    html_path = out_dir / "V5_audience_graph.html"
    md_path = out_dir / "V5_simulation_report.md"

    json_path.write_text(json.dumps(graph_data, indent=2, ensure_ascii=False), encoding="utf-8")
    write_html(graph_data, html_path)
    spread, sent, hook = write_report(results, graph_data, md_path)

    print(f"\n[OK] graph.json:  {json_path}")
    print(f"[OK] graph.html:  {html_path}")
    print(f"[OK] report.md:   {md_path}")
    print(f"\n=== V-SCORE COMPONENTS (de simulacion) ===")
    print(f"MiroFish_spread:    {spread:.2f}/10")
    print(f"MiroFish_sentiment: {sent:.2f}/10")
    print(f"Hook_rate:          {hook:.1f}%")


if __name__ == "__main__":
    main()
