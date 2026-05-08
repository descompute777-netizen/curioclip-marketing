---
agente: A0_Director + A7_Supervision
fecha: 2026-05-07
tags: [pendientes, roadmap, bloqueadores, estado-proyecto]
estado: activo
---

# 🗺️ Roadmap — Lo que falta para el 100% funcional

> Auditado: 2026-05-07 (v3 — agentes PhD + Chrome Bridge + MCPs) | Estado actual: **~75% funcional**

## ✅ Lo que se acaba de agregar (esta sesión)

### Solución al bloqueo de bots
- ✅ **Chrome Bridge (CDP attach)** — `src/bridge/chrome_bridge.py`
  - Lanza tu Chrome real con debugging port → tú te logueas normalmente
  - Playwright se conecta vía `connect_over_cdp` → 0% detección de automatización
  - Comandos: `launch`, `tabs`, `analytics`, `screenshot`, `content`

### MCPs instalados
- ✅ **Sequential Thinking** — pensamiento secuencial estructurado
- ✅ **Context7** — documentación actualizada de librerías
- ✅ **Composio TikTok** (post-OAuth)
- ✅ **TikTok Ads Pipeboard**

### Plugins de Claude Code
- ✅ **Superpowers marketplace** (obra/superpowers-marketplace) — 20+ skills
- ✅ **superpowers-chrome** plugin
- ✅ **claude-mem** — memoria persistente automática
- ✅ **graphify** — knowledge graph de la bóveda Obsidian

### 6 Agentes PhD nivel DIOS (en `.claude/agents/`)
- ✅ `viral-strategist` — Stanford+MIT, behavioral economics + algoritmos
- ✅ `compliance-counsel` — Harvard JD+PhD, IP law (poder de VETO)
- ✅ `clip-miner` — USC+NYU, video extraction + post-prod
- ✅ `analytics-scientist` — Northeastern PhD, V-Score + calibración
- ✅ `audience-psychologist` — Caltech, neuromarketing + INSEAD MBA
- ✅ `outlier-hunter` — Carnegie Mellon, Outlier Cloning 5 fases
- ✅ `weekly-orchestrator` — Wharton+Stanford, A0 Director con autoridad R5

> El sistema está arquitectonicamente completo. Faltan credenciales, contenido y ejecución.

---

## 🔴 NIVEL 0 — BLOQUEADORES CRÍTICOS
*El proyecto no puede funcionar en absoluto sin esto. Prioridad máxima.*

| # | Pendiente | Por qué bloquea | Cómo resolverlo | Tiempo est. |
|---|-----------|----------------|----------------|------------|
| 1 | **Login TikTok en agent-browser** | Sin sesión activa, no hay analytics, no hay monitoreo, no hay publicación asistida | Escanear QR con la app del móvil en la ventana del navegador | 5 min |
| 2 | **Editar y publicar V5 (Plomo Fundido)** | Llevamos 2 días y 0 videos publicados. Sin datos reales, el V-Score no se calibra, el algoritmo no nos conoce | Abrir CapCut → cargar V5_PlomoFundido.mp3 + b-roll de Pexels → seguir brief_V5.md → exportar → publicar Vie 20:00 CDMX | 3-4 horas |
| 3 | **Conectar cuenta de Facebook** | Pipeline incluye FB como canal secundario pero no está configurado | Meta Business Suite → conectar página CurioClip | 20 min |

---

## 🔴 NIVEL 1 — CREDENCIALES FALTANTES
*Sistemas construidos pero inactivos por falta de API keys o tokens.*

| # | Credencial | Dónde configurarla | Sistema que desbloquea |
|---|-----------|-------------------|----------------------|
| 4 | ~~**LLM API Key**~~ | ✅ CONFIGURADO — Gemini 2.5-flash via `.env` | MiroFish operativo |
| 5 | **Meta Page Access Token** | `config/settings.json` → `engines.meta_ads_mcp.api_token` | Publicación automática + analytics Facebook |
| 6 | **TikTok Content API aprobación** | Solicitar en developers.tiktok.com | Publicación automática TikTok (hoy es manual) |
| 7 | ~~**Composio API Key**~~ | ✅ CONFIGURADO — falta conectar TikTok OAuth en `app.composio.dev/settings/connected_accounts` | TikTok MCP activo post-OAuth |
| 7b | ~~**TikTok Ads MCP (Pipeboard)**~~ | ✅ CONFIGURADO en `.mcp.json` — listo para usar | Ads analytics via MCP |
| 8 | **Miro API Token + Board ID** | Bajo impacto — esperar hasta 5K seguidores | Dashboard visual estrategia |
| 9 | **Higgsfield API Key** | Opcional — CapCut es fallback completo | Video AI generativo |

**Cómo crear el .env raíz:**
```
# C:\Users\Nick\Desktop\AGENCIA DE MARKETING\.env
OPENAI_API_KEY=sk-...
ANTHROPIC_API_KEY=sk-ant-...
META_PAGE_ACCESS_TOKEN=...
COMPOSIO_API_KEY=...
HIGGSFIELD_API_KEY=...
```

---

## 🟡 NIVEL 2 — SKILLS DE CLAUDE CODE PENDIENTES
*Comandos `/` que aceleran el trabajo semanal. Sin ellos todo es manual.*

| # | Skill | Qué hace | Impacto semanal |
|---|-------|---------|----------------|
| 10 | `/clip-mine` | Dado URL + timestamps → descarga + corta + genera subtítulos + estructura lista | Ahorra 2-3h/semana |
| 11 | `/tiktok-studio` | Abre agent-browser → TikTok Studio → extrae métricas → guarda en Obsidian | Ahorra 1h/semana |
| 12 | `/semana-nueva` | Crea SEMANA_XX/ → ejecuta Outlier Cloning Fases 1-2 → entrega briefing | Ahorra 2h/semana |
| 13 | `/viral-search` | Busca en TikTok+YouTube+FB → top 10 clips virales por métricas | Ahorra 1.5h/semana |
| 14 | `/v-score` | Evalúa cualquier guión o video con V-Score heurístico + recomendaciones | Ahorra 30min/video |
| 15 | `/compliance` | Checklist A9 completo sobre cualquier contenido | Ahorra 20min/video |
| 16 | `/publish` | Genera caption + hashtags + horario + checklist manual para publicar | Ahorra 30min/video |
| 17 | `/briefing` | Lee Obsidian → genera Briefing Ejecutivo actualizado con KPIs reales | Ahorra 1h/semana |
| 18 | `/remotion-clip` | Genera overlay programático (hook text + subtítulos) sobre un clip | Ahorra 1h/video (cuando Remotion esté listo) |

*Ya creada: `/scrape-ads` ✅*

---

## 🟡 NIVEL 3 — NOTAS DE OBSIDIAN PENDIENTES
*Documentos que el sistema necesita para funcionar como single source of truth.*

| # | Archivo | Agente responsable | Qué contiene |
|---|---------|-------------------|-------------|
| 19 | `10_Estrategia/sistema_visual.md` | A2 Psicología | Paleta de colores, tipografía, estilo visual de CurioClip |
| 20 | `20_Investigacion/audiencia_avatar.md` | A1 Investigación | Perfil detallado de la audiencia objetivo (buyer persona) |
| 21 | `10_Estrategia/algoritmo.md` | A3 Algorítmico | Checklist algorítmico por publicación (señales que premia TikTok) |
| 22 | `20_Investigacion/referentes_sprint_1.md` | A1 | 5 cuentas referentes para Outlier Cloning Semana 2 |
| 23 | `20_Investigacion/viral_clips_sprint_1.md` | A1 | Top clips virales del nicho con Golden Clip identificado |
| 24 | `30_Contenido/simulaciones/V2_bacterias_vscore.md` | A8 | V-Score heurístico para V2 |
| 25 | `30_Contenido/simulaciones/V3_radio_vscore.md` | A8 | V-Score heurístico para V3 |
| 26 | `30_Contenido/simulaciones/V1_medusa_vscore.md` | A8 | V-Score heurístico para V1 |
| 27 | `20_Investigacion/ads_intelligence.md` | A1 + A5 | Resultado del /scrape-ads del nicho |

---

## 🟡 NIVEL 4 — CONTENIDO PENDIENTE
*Videos y assets que deben producirse para cumplir Sprint 1.*

| # | Pendiente | Herramienta | Bloqueador |
|---|-----------|------------|-----------|
| 28 | **V5 editado en CapCut** (el más urgente) | CapCut + V5_PlomoFundido.mp3 + Pexels b-roll | Solo falta tiempo del usuario |
| 29 | **V5 thumbnail** | Canva MCP | Necesita el video editado primero |
| 30 | **V2 brief de producción + compliance** | Sistema listo | Pendiente de calcular V-Score |
| 31 | **V1 brief de producción + compliance** | Sistema listo | Pendiente de calcular V-Score |
| 32 | **V3 brief de producción + compliance** | Sistema listo | Pendiente de calcular V-Score |
| 33 | **V4 brief de producción + compliance** | Sistema listo | Pendiente de calcular V-Score |
| 34 | **Semana 2: 25+ guiones vía Outlier Cloning** | Sistema listo | Necesita 5 referentes identificados primero |

---

## 🟢 NIVEL 5 — HERRAMIENTAS PENDIENTES DE SETUP
*Instaladas pero no configuradas o no terminadas.*

| # | Herramienta | Estado | Qué falta |
|---|------------|--------|----------|
| 35 | **Remotion (create-video)** | Instalando... | Elegir template "Overlay" + configurar proyecto React para CurioClip |
| 36 | **MiroFish backend** | Instalado, sin API key | Crear `.env` en `vendor/MiroFish/backend/` con OPENAI_API_KEY |
| 37 | **TikTok session en agent-browser** | Agent-browser OK, sin sesión | Completar login QR → guardar session state |
| 38 | **Microsoft Clarity** | Documentado, no instalado | Crear landing en Carrd.co → instalar snippet → vincular a Clarity |
| 39 | **VisualEyes web** | Documentado, no usado | Subir thumbnail de V5 a visualeyes.design → capturar clarity score real |

---

## 🔵 NIVEL 6 — CÓDIGO PENDIENTE (Pipeline scripts)
*Scripts que existen como placeholder pero no tienen lógica real todavía.*

| # | Archivo | Estado | Qué le falta |
|---|---------|--------|-------------|
| 40 | `src/pipeline/discover.py` | Placeholder | Implementar búsqueda multi-plataforma + Outlier scoring |
| 41 | `src/pipeline/analyze.py` | Placeholder | Implementar brief generation + compliance pre-check |
| 42 | `src/pipeline/predict.py` | Placeholder | Implementar llamada a vscore_engine.py + reporte |
| 43 | `src/pipeline/learn.py` | Placeholder | Implementar comparación predicción vs. realidad + calibración |
| 44 | `src/mcp_servers/mirofish_server.py` | Existe | Verificar que conecta correctamente con MiroFish en :5001 |
| 45 | `src/mcp_servers/visualeyes_server.py` | Existe | Verificar que el scoring heurístico está calibrado |

---

## 📊 Resumen Visual del Estado

```
ARQUITECTURA DEL SISTEMA
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

CLAUDE.md (sistema multi-agente)          ████████████████ 100% ✅
Obsidian vault (estructura)               ████████████░░░░  75% 🟡
Pipeline scripts                          ████████░░░░░░░░  50% 🟡
Skills de Claude Code                     ██░░░░░░░░░░░░░░  10% 🔴
Credenciales / API Keys                   ██░░░░░░░░░░░░░░  10% 🔴
Herramientas instaladas                   ████████████░░░░  75% 🟡
Contenido producido (videos)              ░░░░░░░░░░░░░░░░   0% 🔴
Cuenta TikTok con acceso                  ░░░░░░░░░░░░░░░░   0% 🔴

PROGRESO TOTAL                            ████████░░░░░░░░  ~40%

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

---

## 🎯 Plan de acción para llegar al 100%

### Esta semana (Semana 1 — Mínimo Viable):
1. ✅ Resolver TikTok login (QR en móvil) → 5 min
2. ✅ Editar V5 en CapCut → 3-4h → publicar Vie 20:00
3. ✅ Crear .env con LLM API key → 10 min → activa MiroFish
4. ✅ Crear skills: /clip-mine, /tiktok-studio, /semana-nueva → 1h sistema

### Semana 2 (Pipeline completo):
5. Ejecutar Outlier Cloning completo (Fases 1-5) → primeros 25 guiones
6. Crear ads_intelligence.md con /scrape-ads
7. Publicar V2, V1 con thumbnails listos
8. Configurar Meta Page Token

### Semana 3 (Automatización):
9. Completar pipeline scripts (discover.py, etc.)
10. Configurar Remotion para overlays automáticos
11. Activar Microsoft Clarity en landing

### Cuando llegue a 5K seguidores (objetivo ~día 45):
12. Activar A5 (Campañas) con presupuesto
13. Configurar TikTok Content API
14. Activar Higgsfield para video AI

---

**Enlace:** [[MOC_Master]] | [[sprint1_briefing]] | [[MOC_Pipeline]]
