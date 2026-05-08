---
tipo: MOC
agente: A8_Motor_Simulacion
fecha: 2026-05-06
tags: [moc, simulacion, vscore, tribe, mirofish]
---

# 🔬 MOC Simulación — Motor de Viralización

## Arquitectura del Engranaje

```
Video Borrador → VisualEyes (atención visual) → MiroFish (social) → V-Score → GO/NO-GO
```

## V-Score Formula (actualizada — VisualEyes reemplaza TRIBE v2)

```
V = (0.35 × VE_attention) + (0.30 × MF_spread) + (0.20 × MF_sentiment) + (0.15 × hook)
```

> TRIBE v2 reemplazado por VisualEyes (gratis, sin licencia NC).
> Engine: `src/scoring/vscore_engine.py` | Pesos en `config/settings.json`

| Umbral | Acción |
|--------|--------|
| ≥ 8.0 🟢 | PUBLICAR |
| 6.0-8.0 🟡 | ITERAR |
| < 6.0 🔴 | DESCARTAR |

## Simulaciones Realizadas

_Pendiente — se poblará con links a resultados en 30_Contenido/simulaciones/_

## Calibración

- [[calibracion/visualeyes_umbrales]] — Umbrales de VisualEyes (clarity score → 0-10)
- [[calibracion/mirofish_perfiles]] — Perfiles de agentes MiroFish

## Precisión Histórica

| Sprint | Precisión TRIBE | Precisión MiroFish | V-Score Promedio |
|--------|----------------|-------------------|-----------------|
| _pendiente_ | — | — | — |
