---
agente: A0_Director
fecha: 2026-05-06
tags: [briefing, sprint0, setup, completado]
estado: completado
---

# Briefing — Sprint 0 (Setup) — 2026-05-06

## 1. Estado

Sprint 0 completado. La arquitectura técnica del sistema está operativa: V-Score engine
implementado con VisualEyes + MiroFish, bóveda Obsidian inicializada con todas las carpetas
y MOCs, y 5 guiones de alto hook score (8-10/10) listos para producción en Sprint 1.
Cuenta CurioClip aún sin publicaciones — Sprint 1 arranca el 2026-05-06.

## 2. KPIs Actuales

| KPI | Valor Actual | Meta Sprint 1 | Meta 90d |
|-----|-------------|--------------|---------|
| Seguidores TikTok | 0 | 200 | 7,000 |
| Seguidores Facebook | 0 | 100 | 3,000 |
| Reproducciones totales | 0 | 15,000 | 100,000 |
| Engagement Rate | — | ≥4% | ≥6% |
| Hook Rate (>3s) | — | ≥60% | ≥65% |
| Videos publicados | 0 | 5 | 60+ |
| V-Score promedio | — | ≥7.5 | ≥8.0 |

## 3. Decisiones Tomadas

- **TRIBE v2 → VisualEyes:** Licencia Non-Commercial incompatible. Reemplazado por VisualEyes (gratis, 93% precisión) + heurísticas locales en `src/mcp_servers/visualeyes_server.py`. `[A0]`
- **Presupuesto $0:** Validar contenido orgánico antes de invertir en ads. `[A0]`
- **Sub-nicho inicial: Ciencia WTF + Misterio:** Hook scores 9-10/10 en guiones de A2+A3. `[A2, A3]`
- **Orden Sprint 1:** V5 (Plomo Fundido 10/10) → V3 (Señal Radio 9/10) → V2 (Bacterias 9/10) → V1 → V4. `[A0]`
- **Publicación manual:** TikTok Content API requiere aprobación; Meta requiere Page Token. `[A6, A9]`

## 4. Próximos Pasos (Sprint 1 — semana del 2026-05-06)

1. Producir Video V5 (Plomo Fundido) con CapCut `[A4]`
2. Analizar thumbnail V5 con VisualEyes web + `visualeyes_server.py` `[A8]`
3. Correr simulación MiroFish para V5 `[A8]`
4. Calcular V-Score: si ≥7.5 → A9 Compliance → publicar `[A8, A9]`
5. Producir V3 (Señal de Radio) y V2 (Bacterias vs Galaxia) `[A4]`
6. Análisis competitivo inicial: ≥5 cuentas del nicho `[A1]`
7. Activar perfil TikTok Pro para analytics `[A6]`
8. Solicitar TikTok Content Posting API en developers.tiktok.com `[A6]`

## 5. Bloqueadores y Riesgos

| Bloqueador | Impacto | Mitigación |
|-----------|---------|-----------|
| TikTok Content API no aprobada | Medio — no automatizar | Publicación manual, A6 entrega paquete listo |
| Meta Page Access Token pendiente | Medio — no automatizar | Publicación manual en Facebook |
| MiroFish requiere LLM API key | Alto — sin simulación social | Configurar OpenAI/Claude key en `vendor/MiroFish/backend/.env` |
| VisualEyes sin API pública | Bajo — modo manual | Usar heurístico local + checklist web |
| Miro token pendiente | Bajo — no crítico | Omitir hasta 5K seguidores |
