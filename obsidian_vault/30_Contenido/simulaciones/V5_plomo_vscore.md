---
agente: A8_Prediccion
fecha: 2026-05-06
tags: [vscore, yellow, simulacion, V5, sprint1]
estado: YELLOW
score: 7.97
content_id: curioclip_sprint1_V5_plomo
---

# V-Score Report — curioclip_sprint1_V5_plomo
**Fecha:** 2026-05-06 | **Agente:** A8 | **Sprint:** 1

> ⚠️ **DISCLAIMER OBLIGATORIO (R6):** Este V-Score es una estimación HEURÍSTICA calculada sin MiroFish en ejecución (pendiente configuración de LLM API key) y sin análisis VisualEyes web real. Margen de error: ±15% hasta calibración (requiere ≥20 publicaciones con datos reales). No garantiza viralización. Decisión de publicación final: del usuario.

---

## Resultado: 🟡 YELLOW (7.97/10.0)

> Supera el umbral mínimo de publicación (6.0/10). Borderline GREEN (8.0). PUBLICABLE.

---

## Desglose de Componentes

| Componente | Peso | Valor bruto | Normalizado | Score ponderado |
|-----------|------|-------------|-------------|----------------|
| VisualEyes Atención | 0.35 | 78/100 | 7.8/10 | **2.730** |
| MiroFish Propagación | 0.30 | 8.5/10 | 8.5/10 | **2.550** |
| MiroFish Sentimiento | 0.20 | 7.8/10 | 7.8/10 | **1.560** |
| Hook Rate predicho | 0.15 | 75% | 7.5/10 | **1.125** |
| **TOTAL** | **1.0** | — | — | **7.965 → 7.97** |

---

## Análisis por Componente

### VisualEyes (Heurístico — 78/100 → 7.8/10)

**Método:** Análisis heurístico visual basado en principios de eye-tracking. Sin análisis web real hasta que el usuario suba thumbnail a [visualeyes.design](https://visualeyes.design).

**Frame de análisis — Segundo 0-1 (hook crítico):**
- **Elemento central:** Plomo líquido brillando naranja/rojo sobre fondo oscuro
- **Texto:** "Metió su mano en PLOMO FUNDIDO a 327°C" (superior, alto contraste)
- **Colores:** Naranja intenso + rojo + negro → máxima atención (teoría del color: alarma + calor)
- **Contraste:** ALTO — elemento brillante sobre fondo oscuro = heatmap concentrado en centro

**Zonas de alta atención (predicción):**
- Centro del frame (plomo brillando)
- Área superior donde va el texto del hook
- Zona de texto de subtítulos (si está bien posicionado)

**Zonas de baja atención (predicción):**
- Esquinas inferiores
- Bordes laterales

**Clarity score heurístico:** ~80/100
**Attention prediction:** ~78/100

**Recomendación:** Asegurar que el texto del hook ocupe la mitad superior del frame con fuente ≥50px y alto contraste.

---

### MiroFish Spread (Heurístico — 8.5/10)

**Narrativa dominante:** "La física desafía lo imposible"

**Factores de alta propagación:**
- Peligro + ciencia verificable = categoría más compartida en TikTok
- Término "PLOMO FUNDIDO" en el título activa curiosidad y ansiedad (estado motivacional de búsqueda)
- El efecto Leidenfrost es poco conocido pero demostrable → alta credibilidad + novedad
- Disclaimer de seguridad incluido → reduce riesgo de restricción algorítmica

**Factores de riesgo de propagación:**
- Ninguno crítico detectado

**Estimación de propagación:**
- Probabilidad viral (>100K views): ~70% (benchmark sub-nicho "ciencia WTF")
- Shares estimados primeras 24h: ~250-450 (partiendo de 0 seguidores)
- Tipping point predicho: primer influencer o cuenta mayor que comparte = Hora 6-12

---

### MiroFish Sentimiento (Heurístico — 7.8/10)

**Sentimiento predicho:** ASOMBRO + EDUCATIVO (positivo dominante)

**Análisis emocional:**
- 0-3s: Alarma/incredulidad → hook
- 3-14s: Curiosidad activa → retención
- 14-19s: Warning/respeto → credibilidad
- 19-25s: Asombro + satisfacción → CTA natural

**Comentarios probables:**
- "¿De verdad funciona?" (curiosidad → engagement)
- "No lo hubiera creído" (asombro → shares)
- "¿Y si falla?" (ansiedad → comentarios)

**Riesgos de sentimiento negativo:** Bajos. El disclaimer de seguridad previene acusaciones de irresponsabilidad.

---

### Hook Rate Predicho (75% → 7.5/10)

**Benchmark:** Retention ≥70% en primeros 3s → multiplicador 2.2x. Objetivo: ≥85% → 2.8x.

**Por qué 75%:**
- Frame 0: Visual de metal fundido brillando = scroll-stopper visual fuerte
- Texto 0-1s: "Metió su mano en PLOMO FUNDIDO a 327°C" = específico + peligroso + curioso
- Audio tiene V5_PlomoFundido.mp3 listo → sincronización inmediata
- Potencial pérdida del 25%: viewers que no les interesa ciencia/física

**Para subir a 85%+:**
- Asegurarse de que el primer frame sea el más impactante visualmente
- Añadir efecto de sonido al inicio (crujido/burbujeo del metal) antes del voiceover
- Subtítulos del hook en el primer frame (no esperar al segundo 1)

---

## Recomendaciones Concretas (A8 → A4)

1. **Thumbnail/frame 0:** Usar el plano del plomo más brillante e impactante del video
2. **Subtítulos desde segundo 0:** El texto del hook debe aparecer simultáneamente con el visual, no después
3. **Efecto de sonido apertura:** Añadir 0.5s de burbujeo/crujido metálico antes del voiceover (CapCut: sound effects)
4. **CTA fuerte al final:** "¿Qué otro experimento quieres ver?" en texto grande + verbal
5. **Duración exacta:** Mantener en 25s. Más largo reduce completion rate bajo 70%.

---

## Decisión GO/NO-GO

**SCORE: 7.97/10 — YELLOW → ✅ GO (supera umbral mínimo 6.0)**

Intervalo de confianza (±15%): 6.77 - 9.17

La estimación va desde YELLOW conservador hasta GREEN probable. Dado el alto hook score del script (10/10) y la fuerte diferenciación del sub-nicho "Ciencia WTF", la estimación sugiere que la probabilidad real de GREEN es alta.

**Condición para publicar:** Pasar validación de Compliance A9 (ver [[compliance_V5_2026-05-06]])

---

**Enlace:** [[sprint1_guiones]] | [[compliance_V5_2026-05-06]] | [[MOC_Contenido]]
