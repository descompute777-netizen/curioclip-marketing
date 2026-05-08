"""
Persona Simulator — CurioClip
==============================
Reemplazo enriquecido de simulate_audience.py con 50 perfiles profundos.

Cada agente tiene:
- Big 5 personality (Openness, Conscientiousness, Extraversion, Agreeableness, Neuroticism)
- Profesión + nivel educativo
- Rutina diaria (cuándo scrollea, cuántas horas, en qué plataformas)
- Tastes específicos (3-5 niches favoritos, niches que aborrece)
- Trigger psicológicos personales

El agente RAZONA antes de decidir engagement (no solo decide).

Output:
- 30_Contenido/simulaciones/personas_richt_v[id].json
- 30_Contenido/simulaciones/personas_richt_v[id].html (grafo enriquecido)
- 30_Contenido/simulaciones/personas_richt_v[id]_report.md (análisis estadístico)
"""
import sys
sys.stdout.reconfigure(encoding='utf-8')
import os
import json
import random
import urllib.request
import time
from pathlib import Path
from datetime import datetime, timezone

ENV = Path(__file__).parent.parent.parent / ".env"
GEMINI_KEY = None
if ENV.exists():
    for line in ENV.read_text().splitlines():
        if line.startswith("GEMINI_API_KEY="):
            GEMINI_KEY = line.split("=", 1)[1].strip()
            break

GEMINI_URL = "https://generativelanguage.googleapis.com/v1beta/openai/chat/completions"

N_AGENTS = 50
BATCH_SIZE = 5  # Menos agentes por batch porque cada uno tiene perfil rico = más tokens
SLEEP_BETWEEN = 8

# Catálogo de profesiones reales con probabilidades para LATAM/España jóvenes
PROFESIONES = [
    ("Estudiante universitario", 0.18),
    ("Estudiante secundaria", 0.10),
    ("Trabajador/a en retail", 0.08),
    ("Empleado/a de oficina", 0.10),
    ("Freelancer creativo", 0.07),
    ("Programador/a", 0.05),
    ("Profesor/a", 0.04),
    ("Enfermero/a", 0.04),
    ("Mesero/a o cocinero/a", 0.06),
    ("Conductor de Uber/delivery", 0.05),
    ("Ama/o de casa", 0.05),
    ("Desempleado/a buscando", 0.04),
    ("Vendedor/a", 0.04),
    ("Operario industrial", 0.03),
    ("Médico/a residente", 0.02),
    ("Influencer pequeño/a", 0.02),
    ("Atleta amateur", 0.02),
    ("Otros", 0.01),
]

PASIONES_SECUNDARIAS = [
    "fútbol", "música pop latina", "kpop", "anime", "manga", "videojuegos AAA",
    "videojuegos casuales móvil", "cocina casera", "reposteria", "running",
    "gym/fitness", "yoga", "meditación", "lectura ficción", "podcasts true crime",
    "películas terror", "series Netflix", "reality shows", "skincare",
    "moda urbana", "fotografía móvil", "viajes baratos", "memes", "política nacional",
    "tecnología consumer", "ciencia divulgativa", "historia", "religión",
    "horóscopo", "tarot", "espiritualidad new age", "minimalismo", "criptomonedas",
    "trading", "bici/skate", "coleccionismo Pokemon", "drag/cultura LGBTQ+",
]

NICHES_TIKTOK = [
    "comedia/humor", "danza/coreografías", "cocina rápida", "tutoriales DIY",
    "ASMR", "storytime", "crime real", "ciencia/curiosidades", "misterio paranormal",
    "fitness", "moda haul", "skincare", "noticias", "política", "pranks",
    "reaccion videos", "anime/k-pop", "videojuegos", "memes", "lifestyle vlog",
    "food review", "viajes", "spirituality/tarot", "self-help", "psicología pop",
]

ESCOLARIDAD = [
    ("Secundaria incompleta", 0.10),
    ("Secundaria completa", 0.30),
    ("Técnico/oficio", 0.20),
    ("Universidad incompleta", 0.20),
    ("Universidad completa", 0.15),
    ("Postgrado", 0.05),
]


def weighted_pick(items_with_weights):
    items = [i for i, _ in items_with_weights]
    weights = [w for _, w in items_with_weights]
    return random.choices(items, weights=weights)[0]


def generate_persona(idx):
    edad = random.choices(
        [random.randint(13, 17), random.randint(18, 24), random.randint(25, 34),
         random.randint(35, 44), random.randint(45, 60)],
        weights=[0.10, 0.45, 0.30, 0.10, 0.05]
    )[0]
    genero = random.choices(["M", "F", "NB"], weights=[0.45, 0.50, 0.05])[0]
    pais = random.choices(
        ["México", "Argentina", "Colombia", "España", "Chile", "Perú", "Venezuela", "Ecuador", "Otros LATAM"],
        weights=[0.28, 0.16, 0.14, 0.12, 0.08, 0.07, 0.06, 0.04, 0.05]
    )[0]

    # Big 5 — cada dimensión 0-100
    big5 = {
        "openness": random.randint(20, 95),       # apertura a experiencia
        "conscientiousness": random.randint(10, 95),  # responsabilidad
        "extraversion": random.randint(10, 95),
        "agreeableness": random.randint(20, 95),
        "neuroticism": random.randint(10, 90),     # ansiedad/inestabilidad
    }

    profesion = weighted_pick(PROFESIONES)
    escolaridad = weighted_pick(ESCOLARIDAD)
    pasiones = random.sample(PASIONES_SECUNDARIAS, k=random.randint(2, 4))
    nicho_amados = random.sample(NICHES_TIKTOK, k=random.randint(3, 5))
    nicho_odiados = random.sample([n for n in NICHES_TIKTOK if n not in nicho_amados], k=random.randint(1, 3))

    # Rutina diaria
    horas_tiktok_dia = round(random.choices([0.5, 1, 2, 3, 4, 6], weights=[0.05, 0.20, 0.30, 0.25, 0.15, 0.05])[0], 1)
    momento_pico_scroll = random.choices(
        ["mañana antes de trabajar", "almuerzo", "transporte", "tarde-noche post-trabajo", "antes de dormir", "madrugada insomnio"],
        weights=[0.10, 0.15, 0.10, 0.30, 0.30, 0.05]
    )[0]
    estado_actual = random.choices(
        ["aburrido_buscando_distracción", "cansado_después_trabajo", "buscando_aprender", "matando_tiempo_corto",
         "ansioso_no_puedo_dormir", "modo_descanso_relax", "concentrado_buscando_info_específica"],
        weights=[0.30, 0.20, 0.10, 0.15, 0.08, 0.12, 0.05]
    )[0]

    followers = random.choices([5, 50, 200, 1000, 5000, 30000],
                                 weights=[0.40, 0.30, 0.15, 0.10, 0.04, 0.01])[0]

    return {
        "id": f"persona_{idx:03d}",
        "edad": edad, "genero": genero, "pais": pais,
        "profesion": profesion, "escolaridad": escolaridad,
        "big5": big5,
        "pasiones": pasiones,
        "niches_que_ama": nicho_amados,
        "niches_que_odia": nicho_odiados,
        "horas_tiktok_dia": horas_tiktok_dia,
        "momento_pico_scroll": momento_pico_scroll,
        "estado_actual": estado_actual,
        "followers": followers,
    }


VIDEO_BRIEF_V5 = """
PLATAFORMA: TikTok
DURACIÓN: 34 segundos, 9:16 vertical
SUB-NICHE: Ciencia WTF / experimentos imposibles
HOOK (0-3s): Texto en pantalla "METIO SU MANO EN PLOMO FUNDIDO" + visual de metal líquido brillando
NARRATIVA: Voiceover IA explica el efecto Leidenfrost — barrera de vapor que protege milisegundos
CTA FINAL: "¿Qué otro experimento quieres ver?"
HASHTAGS: #ciencia #fisica #datoscuriosos #sabiasque #curioclip #experimento
TIPO DE CONTENIDO: educativo + asombro + warning de seguridad incluido
"""


def gemini_evaluate_persona(persona, video_brief):
    """Pide a Gemini que ROL-PLAY como la persona y razone su engagement."""
    prompt = f"""Eres un simulador psicológico realista. Adopta COMPLETAMENTE este perfil:

PERFIL:
- Edad: {persona['edad']}, género: {persona['genero']}, país: {persona['pais']}
- Profesión: {persona['profesion']} | Escolaridad: {persona['escolaridad']}
- Big 5: Apertura {persona['big5']['openness']}, Responsabilidad {persona['big5']['conscientiousness']}, Extraversión {persona['big5']['extraversion']}, Amabilidad {persona['big5']['agreeableness']}, Neuroticismo {persona['big5']['neuroticism']}
- Pasiones: {', '.join(persona['pasiones'])}
- Niches TikTok que ADORA: {', '.join(persona['niches_que_ama'])}
- Niches que IGNORA/skip: {', '.join(persona['niches_que_odia'])}
- TikTok diario: {persona['horas_tiktok_dia']}h | Pico: {persona['momento_pico_scroll']}
- Estado actual al ver el video: {persona['estado_actual']}

VIDEO QUE VES EN TU FYP:
{video_brief}

ROL-PLAY: Estás scrolleando TikTok en tu pico de actividad. Aparece este video. Razona realísticamente:
1. ¿El hook visual + texto te hace parar de scrollear o sigues? (basado en tu Big 5 + tastes + estado)
2. Si te quedas: ¿completas? ¿das like? ¿guardas? ¿compartes? ¿comentas?
3. Si comentas: ¿qué tipo de comentario harías?

Responde SOLO con este JSON (sin markdown):
{{
  "id": "{persona['id']}",
  "decision_3s": "scroll_past" | "stayed",
  "razon_decision_3s": "frase breve",
  "completion": true | false,
  "like": true | false,
  "save": true | false,
  "share": true | false,
  "share_to": "amigos_chat" | "estado_whatsapp" | "no_share",
  "comment": true | false,
  "comment_text": "lo que comentaría literalmente, en su tono natural" | "",
  "comment_sentiment": "positivo" | "neutro" | "negativo" | "curioso" | "escéptico",
  "follow": true | false,
  "razon_general": "1-2 frases del por qué actuó así dado SU perfil"
}}
"""
    body = json.dumps({
        "model": "gemini-2.5-flash",
        "messages": [{"role": "user", "content": prompt}],
        "max_tokens": 800,
        "temperature": 0.85,
        "response_format": {"type": "json_object"},
    }).encode()
    req = urllib.request.Request(GEMINI_URL, data=body, headers={
        "Authorization": f"Bearer {GEMINI_KEY}",
        "Content-Type": "application/json",
    })
    try:
        with urllib.request.urlopen(req, timeout=45) as r:
            data = json.loads(r.read())
            text = data["choices"][0]["message"]["content"].strip()
            if text.startswith("```"):
                text = text.split("```")[1]
                if text.startswith("json"): text = text[4:]
            return json.loads(text)
    except Exception as e:
        print(f"  [FAIL persona {persona['id']}] {e}")
        return None


def simulate_personas(personas, video_brief):
    results = []
    for i, persona in enumerate(personas):
        print(f"[{i+1}/{len(personas)}] {persona['id']} — {persona['edad']}/{persona['genero']}/{persona['pais']} {persona['profesion']}")
        response = gemini_evaluate_persona(persona, video_brief)
        if response:
            results.append({**persona, **response, "_simulated": True})
        else:
            results.append({**persona, "_simulated": False, "decision_3s": "scroll_past",
                             "completion": False, "like": False, "save": False, "share": False,
                             "comment": False, "follow": False, "razon_general": "no respuesta del modelo"})
        if i < len(personas) - 1:
            time.sleep(SLEEP_BETWEEN)
    return results


def build_graph(results):
    """Grafo: agentes saved/shared → potenciales viewers (followers)"""
    nodes, edges = [], []
    color_map = {
        "saved": "#22c55e",     # verde
        "shared": "#fb923c",    # naranja
        "liked": "#3b82f6",     # azul
        "stayed": "#94a3b8",    # gris claro
        "scroll": "#475569",    # gris oscuro
    }
    for r in results:
        if not r.get("_simulated"):
            color = color_map["scroll"]
        elif r.get("save"): color = color_map["saved"]
        elif r.get("share"): color = color_map["shared"]
        elif r.get("like"): color = color_map["liked"]
        elif r.get("decision_3s") == "stayed": color = color_map["stayed"]
        else: color = color_map["scroll"]

        nodes.append({
            "id": r["id"],
            "label": f"{r['edad']}/{r['genero']}\n{r['profesion'][:18]}",
            "title": f"{r['profesion']} | {r['pais']} | {r['estado_actual']}\n{r.get('razon_general','')[:120]}\n{r.get('comment_text','')[:80]}",
            "color": color,
            "size": 8 + min(25, r["followers"] / 200),
            "shape": "dot",
        })

    sharers = [r for r in results if r.get("share")]
    for s in sharers:
        n_reach = min(15, max(2, s["followers"] // 100))
        targets = random.sample([r["id"] for r in results if r["id"] != s["id"]],
                                  min(n_reach, len(results) - 1))
        for t in targets:
            edges.append({"from": s["id"], "to": t, "color": "#fb923c", "width": 0.5})

    return {"nodes": nodes, "edges": edges}


def write_html(graph, results, out_path, video_id="V5"):
    n = len([r for r in results if r.get("_simulated")])
    saved = sum(1 for r in results if r.get("save"))
    liked = sum(1 for r in results if r.get("like"))
    shared = sum(1 for r in results if r.get("share"))
    completed = sum(1 for r in results if r.get("completion"))
    hooked = sum(1 for r in results if r.get("decision_3s") == "stayed")
    commented = sum(1 for r in results if r.get("comment"))
    followed = sum(1 for r in results if r.get("follow"))

    html = f"""<!DOCTYPE html>
<html lang="es"><head>
<meta charset="UTF-8"><title>CurioClip — Personas {video_id}</title>
<script src="https://unpkg.com/vis-network/standalone/umd/vis-network.min.js"></script>
<style>
body{{margin:0;background:#0a0a0a;color:#fff;font-family:Inter,sans-serif}}
#header{{padding:20px;background:#1a1a1a;border-bottom:1px solid #333}}
h1{{margin:0;font-size:20px;color:#FFD700}}
.stats{{display:flex;gap:20px;flex-wrap:wrap;margin-top:10px;font-size:13px}}
.stat strong{{color:#FFD700}}
#network{{height:calc(100vh - 110px);background:#0f1117}}
.legend{{position:absolute;top:120px;right:20px;background:#1a1a1a;padding:12px;border-radius:6px;font-size:12px;border:1px solid #333}}
.dot{{display:inline-block;width:10px;height:10px;border-radius:50%;margin-right:6px;vertical-align:middle}}
</style></head>
<body>
<div id="header">
<h1>🧬 CurioClip — Personas Profundas {video_id} (Plomo Fundido)</h1>
<div class="stats">
<div class="stat">Personas: <strong>{n}/{len(results)}</strong></div>
<div class="stat">Hook (>3s): <strong>{hooked/len(results)*100:.1f}%</strong></div>
<div class="stat">Completion: <strong>{completed/len(results)*100:.1f}%</strong></div>
<div class="stat">Like: <strong>{liked/len(results)*100:.1f}%</strong></div>
<div class="stat">Save: <strong>{saved/len(results)*100:.1f}%</strong></div>
<div class="stat">Share: <strong>{shared/len(results)*100:.1f}%</strong></div>
<div class="stat">Comment: <strong>{commented/len(results)*100:.1f}%</strong></div>
<div class="stat">Follow: <strong>{followed/len(results)*100:.1f}%</strong></div>
</div></div>
<div class="legend">
<div><span class="dot" style="background:#22c55e"></span>Saved (alto valor)</div>
<div><span class="dot" style="background:#fb923c"></span>Shared (viral)</div>
<div><span class="dot" style="background:#3b82f6"></span>Liked</div>
<div><span class="dot" style="background:#94a3b8"></span>Hook pasado</div>
<div><span class="dot" style="background:#475569"></span>Scrolled</div>
</div>
<div id="network"></div>
<script>
const nodes=new vis.DataSet({json.dumps(graph['nodes'], ensure_ascii=False)});
const edges=new vis.DataSet({json.dumps(graph['edges'])});
new vis.Network(document.getElementById('network'),{{nodes,edges}},
{{nodes:{{font:{{color:'#fff',size:11,multi:true}},borderWidth:0}},
edges:{{arrows:'to',width:0.5,smooth:{{type:'continuous'}}}},
physics:{{forceAtlas2Based:{{gravitationalConstant:-60,springLength:120}},
solver:'forceAtlas2Based',stabilization:{{iterations:300}}}},
interaction:{{hover:true,tooltipDelay:80}}}});
</script></body></html>"""
    out_path.write_text(html, encoding="utf-8")


def write_report(personas_results, out_path, video_id):
    n = len(personas_results)
    sim = [r for r in personas_results if r.get("_simulated")]
    n_sim = len(sim)
    if n_sim == 0:
        out_path.write_text("# Reporte vacío — sin simulaciones exitosas", encoding="utf-8")
        return

    saved = sum(1 for r in sim if r.get("save"))
    liked = sum(1 for r in sim if r.get("like"))
    shared = sum(1 for r in sim if r.get("share"))
    completed = sum(1 for r in sim if r.get("completion"))
    hooked = sum(1 for r in sim if r.get("decision_3s") == "stayed")
    commented = sum(1 for r in sim if r.get("comment"))
    followed = sum(1 for r in sim if r.get("follow"))

    # Análisis por segmento demográfico
    by_age = {}
    for r in sim:
        bucket = "13-17" if r["edad"]<18 else "18-24" if r["edad"]<25 else "25-34" if r["edad"]<35 else "35-44" if r["edad"]<45 else "45+"
        by_age.setdefault(bucket, []).append(r)

    # Razones positivas vs negativas (top 10)
    razones_save = [r for r in sim if r.get("save")][:10]
    razones_skip = [r for r in sim if not r.get("save") and r.get("decision_3s") == "scroll_past"][:5]
    comentarios_sample = [r for r in sim if r.get("comment") and r.get("comment_text")][:8]

    # Sentimiento
    sentiments = [r.get("comment_sentiment", "n/a") for r in sim if r.get("comment")]
    sent_counts = {s: sentiments.count(s) for s in set(sentiments)}

    md = f"""---
agente: A8_Prediccion (persona simulator)
fecha: {datetime.now(timezone.utc).isoformat()}
tags: [simulacion, personas-ricas, {video_id}, gemini]
n_personas_total: {n}
n_personas_simuladas: {n_sim}
---

# Reporte Personas Profundas — {video_id}

**Modelo:** Gemini 2.5-flash | **Personas:** {n_sim}/{n} simuladas con éxito

## Métricas agregadas (sobre {n_sim} simuladas)

| Métrica | N | % |
|---------|---|---|
| Hook (>3s) | {hooked} | **{hooked/n_sim*100:.1f}%** |
| Completion | {completed} | {completed/n_sim*100:.1f}% |
| Like | {liked} | {liked/n_sim*100:.1f}% |
| Save | {saved} | {saved/n_sim*100:.1f}% |
| Share | {shared} | {shared/n_sim*100:.1f}% |
| Comment | {commented} | {commented/n_sim*100:.1f}% |
| Follow new | {followed} | {followed/n_sim*100:.1f}% |

## Comportamiento por edad

| Rango | N | Hook% | Save% | Share% |
|-------|---|-------|-------|--------|
"""
    for bucket in sorted(by_age.keys()):
        people = by_age[bucket]
        if not people: continue
        n_b = len(people)
        h = sum(1 for r in people if r.get("decision_3s")=="stayed")
        s = sum(1 for r in people if r.get("save"))
        sh = sum(1 for r in people if r.get("share"))
        md += f"| {bucket} | {n_b} | {h/n_b*100:.0f}% | {s/n_b*100:.0f}% | {sh/n_b*100:.0f}% |\n"

    md += f"""

## Sentimiento de comentarios
{json.dumps(sent_counts, ensure_ascii=False, indent=2) if sent_counts else "Sin comentarios"}

## Comentarios simulados (sample real-life-like)
"""
    for r in comentarios_sample:
        md += f"- **{r['profesion']} {r['edad']}{r['genero']} {r['pais']}** ({r.get('comment_sentiment','')}): \"{r.get('comment_text','')}\"\n"

    md += "\n## Razones de SAVE (alto valor)\n"
    for r in razones_save:
        md += f"- **{r['profesion']} {r['edad']}/{r['genero']}**: {r.get('razon_general','')}\n"

    md += "\n## Razones de SKIP (no engagement)\n"
    for r in razones_skip:
        md += f"- **{r['profesion']} {r['edad']}/{r['genero']}**: {r.get('razon_decision_3s','')} | {r.get('razon_general','')}\n"

    # V-Score components
    spread_score = min(10, (shared/n_sim)*100*0.4 + (saved/n_sim)*100*0.35 + (liked/n_sim)*100*0.25)
    pos = sent_counts.get("positivo", 0) + sent_counts.get("curioso", 0)
    neg = sent_counts.get("negativo", 0) + sent_counts.get("escéptico", 0)
    sent_score = max(0, min(10, 5 + (pos - neg) / max(commented, 1) * 5))

    md += f"""

## V-Score components calculados

- **MiroFish_spread (0-10):** {spread_score:.2f}
- **MiroFish_sentiment (0-10):** {sent_score:.2f}
- **Hook_rate (0-100%):** {hooked/n_sim*100:.1f}%

## Calibración pendiente
- Comparar con métricas reales de {video_id} cuando estén disponibles
- Ajustar pesos del V-Score si error >15%
"""
    out_path.write_text(md, encoding="utf-8")


def main():
    if not GEMINI_KEY:
        print("[FAIL] No GEMINI_API_KEY"); return

    video_id = "V5"
    out_dir = Path("obsidian_vault/30_Contenido/simulaciones")
    out_dir.mkdir(parents=True, exist_ok=True)

    print(f"[GEN] Generando {N_AGENTS} personas profundas...")
    personas = [generate_persona(i) for i in range(N_AGENTS)]

    # Save personas iniciales
    (out_dir / f"personas_rich_{video_id}_profiles.json").write_text(
        json.dumps(personas, indent=2, ensure_ascii=False), encoding="utf-8"
    )

    print(f"\n[SIM] Simulando con Gemini 2.5-flash (1 persona/llamada, {SLEEP_BETWEEN}s entre)...")
    print(f"[INFO] ETA: ~{N_AGENTS * SLEEP_BETWEEN / 60:.0f} minutos\n")
    results = simulate_personas(personas, VIDEO_BRIEF_V5)

    graph = build_graph(results)

    json_path = out_dir / f"personas_rich_{video_id}.json"
    html_path = out_dir / f"personas_rich_{video_id}.html"
    md_path = out_dir / f"personas_rich_{video_id}_report.md"

    json_path.write_text(json.dumps({
        "video_id": video_id,
        "n_total": len(results),
        "n_simulated": sum(1 for r in results if r.get("_simulated")),
        "graph": graph,
        "results": results,
    }, indent=2, ensure_ascii=False), encoding="utf-8")

    write_html(graph, results, html_path, video_id)
    write_report(results, md_path, video_id)

    print(f"\n[OK] Profiles:    {out_dir / f'personas_rich_{video_id}_profiles.json'}")
    print(f"[OK] Resultados: {json_path}")
    print(f"[OK] Grafo HTML: {html_path}")
    print(f"[OK] Reporte MD: {md_path}")


if __name__ == "__main__":
    main()
