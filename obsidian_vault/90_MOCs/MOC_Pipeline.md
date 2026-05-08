---
tipo: MOC
agente: A0_Director
fecha: 2026-05-06
tags: [moc, pipeline, ultra-maquina, modulos, automatizacion]
---

# ⚙️ MOC Pipeline — Ultra Máquina de Contenido Viral

## Arquitectura

```
DISCOVER → ANALYZE → PRODUCE → PREDICT → PUBLISH → LEARN
   M1    →    M2   →   M3    →   M4    →    M5   →   M6
   A1    →  A3+A9  → A2+A4  →   A8    →    A6   → A7+A1
```

## Módulos en Detalle

| Módulo | Agente(s) | Qué produce | Obsidian Output | Status |
|--------|----------|------------|----------------|--------|
| M1 DISCOVER | A1 | Reporte de tendencias + Top 5 oportunidades | `20_Investigacion/trend_reports/` | ⏳ Sprint 1 |
| M2 ANALYZE | A3 + A9 | Brief de produccion + verificacion de derechos | `10_Estrategia/briefs/` | ⏳ Sprint 1 |
| M3 PRODUCE | A2 + A4 | Script + assets + thumbnail | `30_Contenido/[id].md` | ⏳ Sprint 1 |
| M4 PREDICT | A8 | V-Score + scorecard con disclaimer | `30_Contenido/[id]_vscore.md` | ⏳ Sprint 1 |
| M5 PUBLISH | A6 | Publicacion o package manual + log | `40_Publicacion/logs/` | ⏳ Sprint 1 |
| M6 LEARN | A7 + A1 | Retro + calibracion del predictor | `60_Aprendizaje/retros/` | ⏳ Sprint 1 |

## Nivel de Autonomía: 3 (Recomendado)

| Nivel | Modo | Riesgo |
|-------|------|--------|
| 1 | Claude sugiere — usuario ejecuta todo | Nulo |
| 2 | Claude investiga + briefs — usuario edita y publica | Bajo |
| **3 (actual)** | **Claude investiga + produce drafts + agenda en pausa. 1 clic del usuario.** | **Bajo** |
| 4 | Claude publica automaticamente + reporte diario. Usuario puede vetar. | Medio |
| 5 | Full-auto — NO RECOMENDADO (copyright + contenido generico) | Alto |

> R7: El nivel de autonomia es un TECHO, no un suelo. Ante duda, escalar al inferior.

## MCPs Conectados al Pipeline

| Herramienta | Estado | Módulo | Fuente Verificada |
|------------|--------|--------|------------------|
| web_search (nativo Claude) | ✅ Activo | M1 DISCOVER | Nativo — REAL |
| VisualEyes heuristico local | ✅ Activo | M4 PREDICT | `src/mcp_servers/visualeyes_server.py` |
| MiroFish (simulacion social) | ✅ Configurado | M4 PREDICT | `src/mcp_servers/mirofish_server.py` |
| Canva MCP | ✅ Conectado (nativo Claude) | M3 PRODUCE | Nativo — REAL |
| Meta Ads MCP oficial | ❓ Pendiente token | M5 + M6 | mcp.facebook.com/ads (beta 29 abril 2026) |
| TikTok MCP (Composio) | ❓ Pendiente aprobacion | M1 + M5 | composio.dev/apps/tiktok — REAL |
| Higgsfield AI Video | ❓ Pendiente API key | M3 PRODUCE | higgsfield.ai (lanzado abril 2026) — REAL |

## Calibracion del Predictor (M4 → M6 Loop)

| Estado | Valor | Meta |
|--------|-------|------|
| Publicaciones analizadas | 0 | ≥ 20 |
| Error medio hook rate | — | < 15% |
| Precision acumulada | — | ≥ 85% |
| Predictor calibrado | ❌ No | ✅ Si |

> El predictor acumula calibracion automaticamente en cada ciclo M4 → M6.

## Reglas Criticas del Pipeline

| Regla | Descripcion |
|-------|------------|
| R1 | NUNCA inventar capacidades. Si herramienta no disponible → declarar y proponer alternativa. |
| R2 | NUNCA usar contenido de terceros sin licencia verificable. Creditos ≠ licencia. |
| R3 | NUNCA publicar sin pasar por M4 PREDICT y M2 verificacion de derechos. |
| R4 | NUNCA usar la palabra "garantiza". Usar: "se estima", "el analisis sugiere", "probabilidad basada en datos". |
| R7 | Nivel de autonomia es TECHO. Ante duda, escalar al inferior (mas supervision). |

## Codigo del Pipeline

- M1 DISCOVER: `src/pipeline/discover.py`
- M2 ANALYZE: `src/pipeline/analyze.py`
- M4 PREDICT: `src/pipeline/predict.py`
- M6 LEARN: `src/pipeline/learn.py`
- V-Score engine: `src/scoring/vscore_engine.py`
- MCP servers: `src/mcp_servers/`
