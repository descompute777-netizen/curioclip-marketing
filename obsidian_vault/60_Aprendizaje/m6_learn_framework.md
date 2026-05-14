---
agente: A7_Supervision + A8_Prediccion
fecha: 2026-05-14
tags: [m6, learn, calibracion, framework, metricas, predictor, sprint1]
estado: activo
version: 1.0
video_calibracion_inicial: curioclip_sprint1_V5_plomo
---

# M6 LEARN — Framework de Calibracion del Predictor V-Score

**CurioClip | Sprint 1 | Iniciado:** 2026-05-14
**Agentes responsables:** A7 (Supervision) + A8 (Prediccion)
**Disparador:** V5 (Plomo Fundido) publicado — primer dato real disponible en 24h

> PROPOSITO: Este framework convierte cada publicacion en datos de calibracion. El predictor V-Score empieza con margen de error ±15%. Cuando el error medio de los ultimos 5 videos sea consistentemente <15%, el predictor estara calibrado. Meta: calibracion completa en 20 publicaciones.

---

## ESTADO ACTUAL DEL PREDICTOR

| Parametro | Valor actual |
|-----------|-------------|
| Publicaciones con datos reales | 0 de 5 necesarias para primera calibracion parcial |
| Publicaciones para calibracion completa | 0 de 20 |
| Error medio (ultimos 5 videos) | N/A — sin datos reales aun |
| Estado del predictor | PRE-CALIBRACION — margen ±15% |
| Modo de calculo | Heuristico (MiroFish no disponible) |
| VisualEyes web | No consultado — heuristico local |

---

## CHECKLIST 24 HORAS POST-PUBLICACION (V5 — Plomo Fundido)

Ejecutar exactamente a las 24h de la publicacion. Registrar en: `50_Analitica/v5_24h_[fecha].md`

### Metricas de Retencion (comparar vs prediccion A8)

- [ ] Hook rate real (retencion >3s): __% (prediccion: 75%)
- [ ] Completion rate (retencion completa): __% (benchmark esperado: 35-45% para 25s)
- [ ] Average watch time: __s (de 25s totales)
- [ ] Curva de retencion: descargar grafico de TikTok Studio — anotar segundo exacto del primer drop significativo (>5%)

### Metricas de Propagacion

- [ ] Reproducciones totales: __
- [ ] Likes: __ (engagement rate = likes/views × 100: ___ %)
- [ ] Comentarios: __
- [ ] Shares: __
- [ ] Guardados (saves): __ (METRICA PRIORITARIA para cuentas <100K)
- [ ] Save rate (saves/views × 100): __% (benchmark deseable: >3%)
- [ ] Nuevos seguidores atribuibles al video: __
- [ ] Alcance no-followers (% de views de no-seguidores): __%

### Metricas de Distribucion Algoritmica

- [ ] Fuente de trafico principal (For You Page / Seguidores / Busqueda / Hashtags): __
- [ ] % For You Page: __% (deseable: >60% para cuentas nuevas)
- [ ] Regiones geograficas top-3: __, __, __
- [ ] Demografica principal (rango de edad): __

### Observaciones Cualitativas

- [ ] Top 3 comentarios por likes (copiar texto literal):
  1. "___"
  2. "___"
  3. "___"
- [ ] Sentiment predominante en comentarios: positivo / negativo / neutro / mixto
- [ ] Comentarios coinciden con prediccion A8? (Si / Parcialmente / No)
- [ ] Algo inesperado ocurrio en las primeras 24h? (anotar)

---

## CHECKLIST 72 HORAS POST-PUBLICACION (V5 — Plomo Fundido)

Ejecutar exactamente a las 72h de la publicacion. Registrar en: `50_Analitica/v5_72h_[fecha].md`

### Metricas Acumuladas 72h

- [ ] Reproducciones totales 72h: __
- [ ] Likes totales: __
- [ ] Shares totales: __
- [ ] Guardados totales: __
- [ ] Comentarios totales: __
- [ ] Seguidores ganados en 72h: __
- [ ] Engagement rate 72h: __% (likes+comments+shares+saves / views × 100)

### Evaluacion de Curva de Crecimiento

- [ ] Velocidad de crecimiento (views por hora):
  - Hora 0-6: __ views/hora
  - Hora 6-24: __ views/hora
  - Hora 24-48: __ views/hora
  - Hora 48-72: __ views/hora
- [ ] Se produjo un tipping point (aceleracion subita)? Si / No. Si SI: a las __h
- [ ] El tipping point ocurrio dentro de la ventana predicha (hora 6-12)? Si / No

### Comparacion Prediccion vs Realidad (72h)

| Metrica | Prediccion A8 | Real 24h | Real 72h | Error absoluto |
|---------|--------------|----------|----------|----------------|
| Hook rate (>3s) | 75% | __% | __% | __% |
| Completion rate | ~40% | __% | __% | __% |
| Tono comentarios | Asombro/Educativo | __ | __ | — |
| Tipping point | Hora 6-12 | Hora __ | — | — |

- [ ] Error hook rate: |75% - real%| = __%
- [ ] Error completion rate: |40% - real%| = __%
- [ ] Error medio primer video: (__%  + __%) / 2 = __%

### Estado del Video a 72h

- [ ] El video esta en crecimiento / estabilizado / en declive
- [ ] Recomendacion: dejar correr / hacer dueto/stitch / responder comentario para relanzar
- [ ] Requiere accion de A3 (ajuste de hashtags, republish)? Si / No

---

## TEMPLATE DE COMPARACION PREDICCION vs REALIDAD

Usar este template para cada video publicado. Guardar en: `60_Aprendizaje/calibracion/calibracion_[video_id]_[fecha].md`

```
---
agente: A8_Prediccion
video_id: [id]
fecha_publicacion: [fecha]
fecha_medicion_24h: [fecha]
fecha_medicion_72h: [fecha]
tags: [calibracion, m6, learn]
---

# Calibracion V-Score — [Video ID]

## Prediccion Pre-Publicacion (A8)

| Componente | Peso | Score predicho | Aporte |
|-----------|------|---------------|--------|
| VisualEyes Atencion | 0.35 | X.X/10 | X.XXX |
| MiroFish Propagacion | 0.30 | X.X/10 | X.XXX |
| MiroFish Sentimiento | 0.20 | X.X/10 | X.XXX |
| Hook Rate predicho | 0.15 | X.X/10 | X.XXX |
| V-SCORE TOTAL | 1.0 | — | X.XX |

Hook rate predicho: X%
Completion rate predicho: X%
Tipping point predicho: Hora X-Y

## Datos Reales 24h

Hook rate real: X%
Completion rate real: X%
Views 24h: X
Likes 24h: X
Shares 24h: X
Saves 24h: X
Tipping point real: Hora X (si aplica)

## Datos Reales 72h

Hook rate real: X%
Completion rate real: X%
Views 72h: X
Likes 72h: X
Shares 72h: X
Saves 72h: X

## Calculo de Error

ERROR_HOOK = |hook_predicho% - hook_real%| = X%
ERROR_COMPLETION = |completion_predicho% - completion_real%| = X%
ERROR_MEDIO_VIDEO = (ERROR_HOOK + ERROR_COMPLETION) / 2 = X%

## Diagnostico del Error

- El error fue mayor de lo esperado: Si / No
- Componente que mas contribuyo al error: [VE / MiroFish Spread / Sentimiento / Hook]
- Causa probable del error: [descripcion]
- Ajuste sugerido para siguiente prediccion: [accion concreta]

## Lecciones Aprendidas

1. [leccion concreta]
2. [leccion concreta]
3. [leccion concreta]
```

---

## CRITERIOS DE CALIBRACION DEL PREDICTOR

### Calibracion Parcial (5 videos)

- **Condicion:** 5 publicaciones con datos reales de 72h registrados
- **Evaluacion:** Calcular ERROR_MEDIO_ULTIMOS_5_VIDEOS
- **Si error medio < 15%:** Predictor en rango aceptable — continuar sin ajuste de pesos
- **Si error medio >= 15%:** Diagnosticar que componente esta fallando mas (ver tabla de ajuste abajo)

### Calibracion Completa (20 videos)

- **Condicion:** 20 publicaciones con datos reales de 72h registrados
- **Meta:** ERROR_MEDIO_ULTIMOS_5_VIDEOS < 15% de forma consistente (3 ciclos de 5 seguidos)
- **Declarar calibracion completa:** Cuando se cumpla la condicion por 3 sprints consecutivos

### Tabla de Ajuste de Pesos (Gradient Descent Simple)

Aplicar solo cuando ERROR_MEDIO > 15% en los ultimos 5 videos:

| Patron de error | Diagnostico | Ajuste de peso |
|----------------|-------------|----------------|
| VisualEyes consistentemente sobre-predice | El heatmap heuristico es demasiado optimista | Reducir peso VE: 0.35 → 0.30. Aumentar Hook Rate: 0.15 → 0.20 |
| VisualEyes consistentemente sub-predice | El heatmap heuristico es muy conservador | Aumentar peso VE: 0.35 → 0.40. Reducir MiroFish Spread: 0.30 → 0.25 |
| MiroFish Spread consistentemente sobre-predice | El sub-nicho es menos viral de lo esperado en LATAM | Reducir peso MF Spread: 0.30 → 0.25. Aumentar Hook Rate: 0.15 → 0.20 |
| MiroFish Spread consistentemente sub-predice | El sub-nicho performa mejor de lo predicho | Aumentar peso MF Spread: 0.30 → 0.35. Reducir VE: 0.35 → 0.30 |
| Hook Rate consistentemente sub-predice | Los hooks de CurioClip son mas efectivos de lo que el modelo asume | Aumentar peso Hook Rate: 0.15 → 0.20. Reducir MF Sentimiento: 0.20 → 0.15 |
| Error alto solo en videos de misterio | El sub-nicho misterio tiene comportamiento diferenciado | Crear coeficiente de sub-nicho: misterio × 1.1 en MF Spread |
| Error alto solo en videos de ciencia WTF | El sub-nicho ciencia WTF sobre-performa sistematicamente | Crear coeficiente de sub-nicho: ciencia WTF × 1.15 en MF Spread |

### Reglas de Ajuste

1. Nunca ajustar mas de un componente a la vez — un cambio por ciclo de calibracion.
2. Documentar cada ajuste en este archivo con fecha y justificacion.
3. Aplicar el ajuste al siguiente sprint completo (7 videos) antes de evaluar de nuevo.
4. Si un ajuste empeora el error, revertir al peso anterior.
5. Los pesos siempre deben sumar 1.0. Verificar despues de cada ajuste.

---

## HISTORIAL DE AJUSTES DE PESOS

| Fecha | Componente ajustado | Peso anterior | Peso nuevo | Justificacion | Error antes | Error despues |
|-------|---------------------|---------------|------------|---------------|-------------|---------------|
| (sin ajustes aun — predictor en fase pre-calibracion) | | | | | | |

---

## CALENDARIO DE MEDICIONES SPRINT 1

| Video | Fecha publicacion | Medicion 24h | Medicion 72h | Estado |
|-------|------------------|--------------|--------------|--------|
| V5 — Plomo Fundido | Por confirmar | +24h | +72h | Pendiente publicacion |
| V2 — Bacterias vs Galaxia | Por confirmar | +24h | +72h | Pendiente publicacion |
| V3 — Radio UVB-76 | Por confirmar | +24h | +72h | Pendiente publicacion |
| V1 — Medusa Inmortal | Por confirmar | +24h | +72h | Pendiente publicacion |
| V4 — Leyes Absurdas | Por confirmar | +24h | +72h | Pendiente publicacion |

---

## METRICAS PRIORITARIAS POR FASE DE CUENTA

**CurioClip actual: cuenta <100K (fase de arranque)**

En esta fase, las metricas con mayor poder predictivo de crecimiento sostenido son:

1. **Save rate (guardados / views × 100):** Metrica #1. Una tasa de guardado >3% indica que el contenido tiene valor percibido de referencia futura — el algoritmo de TikTok lo trata como señal de calidad superior al like. Peso en decisiones de M6: ALTO.

2. **Share rate (shares / views × 100):** Metrica #2. La propagacion organica fuera de la plataforma (WhatsApp, Telegram, Twitter) es el mecanismo principal de tipping point en cuentas nuevas.

3. **Hook rate (retencion >3s):** Metrica #3. Es la puerta de entrada al algoritmo. Sin hook rate >65%, el video no entra en distribucion expandida.

4. **Completion rate:** Metrica #4. Correlaciona con sentimiento y calidad narrativa. En videos de 18-28s, un completion rate >40% es señal de contenido de calidad.

5. **Likes y comentarios:** Metricas de superficie. Importantes para social proof pero menos predictivas de crecimiento algoritmico que save rate y share rate.

> Nota A8: El engagement rate calculado solo con likes es una metrica engaanosa en cuentas nuevas. Usar siempre (likes + comentarios + shares + saves) / views como denominador del engagement rate real.

---

## PROXIMOS PASOS M6 LEARN

1. Publicar V5 (Plomo Fundido) → registrar fecha y hora exacta
2. A las 24h: ejecutar Checklist 24h y registrar en `50_Analitica/`
3. A las 72h: ejecutar Checklist 72h y completar template de calibracion
4. Repetir para cada video del sprint en orden de publicacion
5. Al completar los 5 videos del sprint: calcular ERROR_MEDIO_SPRINT_1 y determinar si hay ajuste de pesos necesario
6. Registrar lecciones en `60_Aprendizaje/retros/retro_sprint1_[fecha].md`
7. Alimentar a A1 con los patrones aprendidos para M1 del Sprint 2

---

**Enlace:** [[MOC_Analitica]] | [[MOC_Aprendizaje]] | [[V5_plomo_vscore]] | [[sprint1_guiones]]
