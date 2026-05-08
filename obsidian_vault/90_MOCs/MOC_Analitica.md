---
tipo: MOC
agente: A6_Operaciones + A8_Prediccion
fecha: 2026-05-06
tags: [moc, analitica, metricas, vscore, kpis]
---

# 📊 MOC Analítica — Métricas y KPIs

## Snapshots Diarios

- Ver `50_Analitica/YYYY-MM-DD.md` — un archivo por día
- A6 registra métricas en tiempo real después de cada publicación

## KPIs Globales — Estado Actual

| KPI | Valor Actual | Meta Sprint 1 | Meta 90d | Delta |
|-----|-------------|--------------|---------|-------|
| Seguidores TikTok | 0 | 200 | 7,000 | -7,000 |
| Seguidores Facebook | 0 | 100 | 3,000 | -3,000 |
| Reproducciones totales | 0 | 15,000 | 100,000 | -100,000 |
| Engagement Rate | — | ≥4% | ≥6% | — |
| Hook Rate (>3s) | — | ≥60% | ≥65% | — |
| V-Score promedio | — | ≥7.5 | ≥8.0 | — |
| Videos publicados | 0 | 5 | 60+ | — |

## Calibración V-Score

- [[MOC_Simulacion]] — Arquitectura del motor de viralización
- Precisión objetivo de A8: error medio <15% vs. retención real post-publicación

## Precisión Predictiva por Sprint

| Sprint | Precisión VisualEyes | Precisión MiroFish | V-Score Medio |
|--------|--------------------|--------------------|--------------|
| 0 (setup) | — | — | — |
| 1 | — | — | — |

## Herramientas de Medición

| Herramienta | Qué mide | Costo |
|------------|---------|-------|
| TikTok Analytics (Pro) | Retención segundo-a-segundo, alcance, ER | Gratis |
| Facebook Insights | Alcance, reproducciones, ER | Gratis |
| Microsoft Clarity | Heatmaps post-publicación en landing | Gratis |
| VisualEyes | Predicción pre-publicación (heatmap) | Gratis |
| MiroFish | Simulación social propagación | Gratis (self-hosted) |
