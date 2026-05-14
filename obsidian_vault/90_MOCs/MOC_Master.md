---
tipo: MOC
agente: Sistema
fecha: 2026-05-06
tags: [moc, indice, master]
---

# 🗺️ MOC Master — Agencia de Marketing IA

## Índices por Área

- [[MOC_Estrategia]] — Plan global, sistema visual, calendario
- [[MOC_Investigacion]] — Competencia, audiencia, tendencias
- [[MOC_Contenido]] — Piezas de contenido y simulaciones
- [[MOC_Publicacion]] — Campañas, compliance y APIs
- [[MOC_Analitica]] — Métricas diarias y semanales
- [[MOC_Aprendizaje]] — Auditorías, retros, calibración

## Pipeline Ultra Máquina

- [[MOC_Pipeline]] — 6 módulos, autonomía Nivel 3, MCPs conectados

## Motores y Simulación

- [[MOC_Simulacion]] — V-Score: VisualEyes + MiroFish
- Motor_TRIBE_v2 → REEMPLAZADO por VisualEyes (gratis, sin licencia NC)

## Agentes

| ID | Agente | Responsabilidad |
|----|--------|----------------|
| A0 | Director | Orquestación y arbitraje |
| A1 | Investigación | Análisis competitivo |
| A2 | Psicología | Hooks y neuromarketing |
| A3 | Algorítmico | Timing y hashtags |
| A4 | Editor | Producción de video |
| A5 | Campañas | Media buying |
| A6 | Operaciones | Publicación en plataformas |
| A7 | Supervisión | QA y mejora continua |
| A8 | Predicción | Motor dual TRIBE+MiroFish |
| A9 | Compliance | Verificación legal |

## Estado del Proyecto

- **Meta:** 0 → 10K seguidores + 100K reproducciones
- **Plazo:** 90 días (inicio: 2026-05-06, fin: 2026-08-03)
- **Sprint actual:** 2 (semana 2026-05-13/19) — Pipeline cloud autónomo ACTIVO
- **V-Score promedio:** Pendiente calibración (≥20 publicaciones reales)
- **Videos producidos:** V5 ✅ publicado | V1-V4 en producción automatizada
- **Sistema cloud:** GitHub Actions activo (weekly-sprint + outlier-hunt + analytics)
- **CronJobs activos:** 3 (métricas diarias 10:07 | sprint lunes 09:03 | outlier domingo 20:03)

## Automatización Cloud (2026-05-14)

| Workflow | Trigger | Función |
|---------|---------|--------|
| `weekly-sprint.yml` | Lunes 09:07 UTC | weekly-orchestrator genera plan + 25 guiones |
| `outlier-hunt.yml` | Domingo 20:03 UTC | outlier-hunter Fases 1-5 + cola de guiones |
| `analytics.yml` | Cada 2h (07min) | calibración predictor + métricas diarias |

## Metodología Core

- [[outlier_cloning]] — Protocolo Outlier Cloning 5 fases — Modo A (contenido original)
- [[clip_mining]] — Pipeline Clip Mining multi-plataforma — Modo B (clips virales reales)
- [[calendario_editorial]] — Horarios 2026 + regla "publicar 10-30 min antes del pico"
- [[SEMANAS/SEMANA_01_2026-05-06_a_2026-05-12/BRIEFING_SEMANAL]] — Briefing Sprint 1
- [[SEMANAS/SEMANA_02_2026-05-13_a_2026-05-19/BRIEFING_SEMANAL]] — Briefing Sprint 2 ← ACTIVO

## Pipeline de Producción Automática

- `src/pipeline/auto_editor_generic.py` — Editor genérico (generaliza V5)
- `src/pipeline/produce_all.py` — Produce V1-V4 en secuencia
- `configs/v{1-4}_*.py` — Configuraciones por video
- `scripts/autonomous/weekly_sprint.py` — Agente cloud lunes
- `scripts/autonomous/outlier_hunt.py` — Agente cloud domingo
- `scripts/autonomous/daily_metrics.py` — Agente cloud cada 2h

## Documentos Clave Sprint 1 → Sprint 2

- [[brief_V5]] — Brief V5 (plomo fundido) — PRODUCIDO ✅
- [[V5_plomo_vscore]] — V-Score 7.88/10 YELLOW → GO ✅ PUBLICADO
- [[compliance_V5_2026-05-07_AUTO]] — Compliance APROBADO FULL ✅
- [[sprint1_estado_completo]] — Pipeline 95% automatizado ✅
- [[competidores]] — Matriz 10 competidores del nicho
- Agentes Sprint 2 corriendo: outlier-hunter + analytics-scientist + viral-strategist + audience-psychologist
