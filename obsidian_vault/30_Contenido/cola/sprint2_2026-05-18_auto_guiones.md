---
sprint: 2
fecha: 2026-05-18
motor: gemini-2.5-flash
fuente: weekly-orchestrator-cloud
estado: pendiente
---

═══ SPRINT 2 ORQUESTADO — 2026-05-18 ═══

# Briefing — Sprint 2 — 2026-05-18

## 1. Estado
El Sprint 2 progresa con el sistema cloud autónomo operando eficazmente, incluyendo la reciente ejecución del `outlier-hunter-cloud` para la próxima semana de contenido. El video V5 ("Plomo Fundido") fue publicado exitosamente, y se han generado los activos para los videos V1-V4. La orquestación de esta semana se enfoca en la planificación del contenido para la semana de publicación del Sprint 3, basada en los 42 nuevos outliers identificados.

## 2. KPIs actuales
| KPI | Valor | Meta sprint | Meta 90d | Delta | Tendencia |
|-----|-------|------------|---------|-------|----------|
| Seguidores TikTok | 215 | +300 | 7000 | -85 | ↗️ (lento) |
| Seguidores Facebook | 0 | +100 | 3000 | -100 | ➡️ |
| Reproducciones | 5,430 (V5) | +20,000 | 100K | -14,570 | ↗️ (lento) |
| Engagement Rate | 4.8% (V5) | ≥4% | ≥6% | +0.8% | ✅ |
| Hook Rate >3s | 61% (V5) | ≥60% | ≥65% | +1% | ✅ |
| V-Score promedio | 7.88 (V5) | ≥7.5 | ≥8.0 | +0.38 | ✅ |
| Outliers analizados | 42 | ≥25 | — | +17 | ✅ |

## 3. Decisiones tomadas
| Decisión | Justificación | Agente responsable |
|---------|--------------|--------------------|
| Priorizar sub-nichos Ciencia WTF, Misterio y Psicología para scripts de Sprint 3 | Alta tasa de engagement y multiplicadores en outliers recientes, alineado con nuestra propuesta de valor CurioClip | A0 Director |
| Mantener el umbral V-Score ≥6.0 para publicación | Permite experimentación controlada y recolección de datos, minimizando riesgo de oportunidad | A0 Director |
| Establecer calendario de publicación para Sprint 3 de Lunes a Domingo, con foco en 5 videos de alta puntuación y 2 de V-Score "YELLOW" para prueba | Optimiza la exposición a la audiencia y prueba contenido más arriesgado | A0 Director |

## 4. Próximos pasos (priorizados)
1.  **CRÍTICO — V5 caption:** Usuario debe aplicar el caption final y hashtags a V5 en TikTok.
2.  **Producción V1-V4:** `clip-miner` debe generar los assets finales para V1-V4 (que se publicarán en Sprint 2).
3.  **Preparación Top 7 Sprint 3:** `clip-miner` generará assets para los 7 guiones seleccionados hoy (para publicación en la SEMANA_03_2026-05-20_a_2026-05-26/).
4.  **Validación visual:** `audience-psychologist` validará thumbnails y overlays para todos los videos a publicar.
5.  **Análisis métricas:** `analytics-scientist` monitoreará las métricas de V1-V4 (una vez publicados) y V5 para calibrar el predictor.

## 5. Bloqueadores y riesgos
| Bloqueador | Impacto | Mitigación |
|------------|---------|------------|
| Retraso en caption V5 | Pérdida de engagement potencial | Notificación crítica al usuario. Configurar `viral-strategist` para auto-generar caption si no hay entrada. |
| Baja performance de V1-V4 | Desacelera el crecimiento de seguidores y reproducciones | `analytics-scientist` priorizará el análisis de estos videos para identificar patrones y calibrar rápidamente el V-Score. |
| Inconsistencia en branding visual | Debilita la identidad de CurioClip | `audience-psychologist` hará una revisión final de todos los assets visuales antes de la publicación. |

---

## Tareas delegadas (registro de subagentes)

| Día | Subagente | Tarea | Estado | Entregable |
|-----|-----------|-------|--------|-----------|
| Lun (13/5) | outlier-hunter | Fases 1-2 (previo al sprint) | ✅ | referentes_sprint_3.md + outliers_sprint_3.md |
| Mar (14/5) | outlier-hunter + compliance-counsel | Fase 3 + pre-check (previo al sprint) | ✅ | brief_visual + compliance_check |
| Mié (15/5) | outlier-hunter | Fase 4: Adaptación → 25+ guiones | ✅ | 25_guiones_sprint_3.md (ver abajo) |
| Jue (16/5) | analytics-scientist | Puntuación V-Score | ✅ | scorecards_sprint_3.md |
| Jue (16/5) | outlier-hunter | Fase 5: Selección top 7 | ✅ | calendario_sprint_3.md (ver abajo) |
| Vie (17/5) | clip-miner + audience-psychologist | Generación assets finales + validación | En curso | SEMANA_03/[DIA]/ completo (por generar) |

---

## 25 Guiones Adaptados (Sprint 3 — 2026-05-20 a 2026-05-26)
*(Selección basada en outliers de @LadyScience, @historiaparatontos, @QuantumFracture, @CdeCiencia, @mentes_curiosas_ok y sub-nichos solicitados)*

**Nicho: CurioClip — Curiosidades Español LATAM**
**Sub-nichos: Ciencia WTF, Misterio, Historia WTF, Comparaciones Imposibles, Psicología**

---

**Ciencia WTF**

1.  **Título Tentativo:** ¿Por qué la saliva de mosquito NO coagula tu sangre?
    *   **Hook Literal:** "Tu sangre es un tesoro... ¡para un mosquito!"
    *   **Contexto:** Desmitifica la acción anticoagulante de la saliva de mosquito y sus componentes químicos.
2.  **Título Tentativo:** ¿Podrías vivir dentro de un agujero negro sin morir al instante?
    *   **Hook Literal:** "Cae en un agujero negro y... ¿qué pasa?"
    *   **Contexto:** Explora los efectos de la espaguetificación y la dilatación del tiempo en el horizonte de sucesos.
3.  **Título Tentativo:** La paradoja de Fermi: ¿Dónde están TODOS los aliens?
    *   **Hook Literal:** "Si el universo es tan grande... ¿por qué estamos solos?"
    *   **Contexto:** Explica la paradoja y las principales hipótesis sobre el silencio cósmico.
4.  **Título Tentativo:** ¿Por qué el agua caliente se congela más rápido que la fría? (Efecto Mpemba)
    *   **Hook Literal:** "Caliente o fría: ¿Cuál se congela primero?"
    *   **Contexto:** Desglosa las teorías detrás del sorprendente efecto Mpemba.
5.  **Título Tentativo:** Si las hormigas tuvieran el tamaño de un humano, ¿serían invencibles?
    *   **Hook Literal:** "Hormigas gigantes... ¿la peor pesadilla?"
    *   **Contexto:** Analiza las limitaciones físicas y respiratorias que impedirían su tamaño, contrastando fuerza relativa.

---

**Misterio / Enigmas**

6.  **Título Tentativo:** El caso sin resolver del vuelo MH370: ¿Qué pasó realmente?
    *   **Hook Literal:** "Un avión desaparece... ¿sin dejar rastro?"
    *   **Contexto:** Recopila las teorías más plausibles y los misterios que aún rodean su desaparición.
7.  **Título Tentativo:** ¿Existen realmente las ciudades perdidas bajo la Antártida?
    *   **Hook Literal:** "¿Hay algo oculto BAJO el hielo?"
    *   **Contexto:** Explora mitos y descubrimientos geológicos en el continente helado que inspiran estas leyendas.
8.  **Título Tentativo:** El enigma de las luces de Hessdalen: ¿Fenómeno OVNI o natural?
    *   **Hook Literal:** "Luces extrañas... ¿cada noche en Noruega?"
    *   **Contexto:** Describe el fenómeno y las investigaciones científicas que intentan explicarlo.
9.  **Título Tentativo:** La 'mancha' de sangre en la luna: ¿Un evento cósmico o una ilusión?
    *   **Hook Literal:** "¿La Luna... con una herida de bala?"
    *   **Contexto:** Explicación de la "anomalía de Aristarchus" y otras ilusiones ópticas/geológicas lunares.
10. **Título Tentativo:** ¿Quién construyó las pirámides de Bosnia? El mayor engaño arqueológico.
    *   **Hook Literal:** "Las pirámides más antiguas... ¡¿estaban ocultas en Bosnia?!"
    *   **Contexto:** Desmonta la controversia y las "evidencias" presentadas por Semir Osmanagić.

---

**Historia WTF**

11. **Título Tentativo:** ¿Por qué los romanos comían un 'Viagra' hecho de semen de toro?
    *   **Hook Literal:** "Los romanos... ¡con la receta más rara!"
    *   **Contexto:** Explora las creencias antiguas sobre afrodisíacos y remedios populares en Roma.
12. **Título Tentativo:** El día que el presidente de EE.UU. perdió un avión nuclear en España.
    *   **Hook Literal:** "¡Una bomba atómica se cayó... en España!"
    *   **Contexto:** Relata el incidente de Palomares en 1966 y sus consecuencias.
13. **Título Tentativo:** La 'Guerra del Cubo de Roble': El conflicto más ridículo de la historia.
    *   **Hook Literal:** "Una guerra... ¡por un cubo de madera!"
    *   **Contexto:** Narra la breve y absurda guerra entre Bolonia y Módena en el siglo XIV.
14. **Título Tentativo:** ¿Por qué los vikingos eran los verdaderos inventores del 'drone' (sin saberlo)?
    *   **Hook Literal:** "Los vikingos... ¡inventaron el drone!"
    *   **Contexto:** Compara sus aves entrenadas para exploración a distancia con la funcionalidad de un drone.
15. **Título Tentativo:** El emperador romano que declaró la guerra a Neptuno y sus peces.
    *   **Hook Literal:** "Un emperador loco... ¡lucha contra el mar!"
    *   **Contexto:** Detalla las excentricidades de Calígula y su supuesta guerra contra el mar.

---

**Comparaciones Imposibles / Datos Curiosos**

16. **Título Tentativo:** Si el sol fuera del tamaño de una canica, ¿qué tan grande sería la Vía Láctea?
    *   **Hook Literal:** "Imagina el Sol... ¡como una canica!"
    *   **Contexto:** Visualiza la escala del universo a través de una analogía reducida.
17. **Título Tentativo:** ¿Cuántos cerebros humanos cabrían dentro del Sol?
    *   **Hook Literal:** "¿Podrías llenar el Sol... con cerebros?"
    *   **Contexto:** Cálculo hipotético y sorprendente para ilustrar el volumen del Sol.
18. **Título Tentativo:** ¿Qué pasaría si la Tierra dejara de girar por un segundo?
    *   **Hook Literal:** "Si la Tierra se detiene... ¿qué le pasa a todo?"
    *   **Contexto:** Explica las devastadoras consecuencias físicas de una parada súbita.
19. **Título Tentativo:** ¿Quién tiene más bacterias en su cuerpo: tú o la Tierra?
    *   **Hook Literal:** "¿Eres más sucio que el planeta?"
    *   **Contexto:** Compara la biomasa microbiana del cuerpo humano con la del planeta, con un twist.
20. **Título Tentativo:** ¿Qué tan lejos tendrías que saltar para escapar de la gravedad de la Tierra?
    *   **Hook Literal:** "¿Puedes saltar tan alto... que te vas al espacio?"
    *   **Contexto:** Explica el concepto de velocidad de escape y la altura necesaria.

---

**Psicología WTF / Comportamiento Humano**

21. **Título Tentativo:** ¿Por qué siempre te sientes incómodo en ascensores (síndrome de la caja)?
    *   **Hook Literal:** "Entras al ascensor... ¡y te sientes raro!"
    *   **Contexto:** Explora la psicología detrás del comportamiento en espacios reducidos y agorafobia.
22. **Título Tentativo:** El efecto Mandela: ¿Tu cerebro te está mintiendo sobre el pasado?
    *   **Hook Literal:** "¿Recuerdas algo... que NUNCA pasó?"
    *   **Contexto:** Explica el fenómeno de los falsos recuerdos colectivos y cómo funciona la memoria.
23. **Título Tentativo:** ¿Por qué nos gusta el chisme (aunque digamos que no)?
    *   **Hook Literal:** "Odias el chisme... ¡pero lo amas!"
    *   **Contexto:** Análisis evolutivo y social del chismorreo como herramienta de cohesión y aprendizaje.
24. **Título Tentativo:** El 'síndrome del impostor': Cuando crees que no mereces tu éxito.
    *   **Hook Literal:** "Eres brillante... ¡pero crees que eres un fraude!"
    *   **Contexto:** Describe el síndrome y sus implicaciones en la autoestima y el rendimiento.
25. **Título Tentativo:** ¿Por qué es tan difícil perdonar (científicamente hablando)?
    *   **Hook Literal:** "Perdonar es de valientes... ¡pero por qué cuesta tanto!"
    *   **Contexto:** Explora los procesos neuronales y psicológicos que dificultan el acto de perdonar.

---

## TOP 7 para la SEMANA_03_2026-05-20_a_2026-05-26 (V-Score estimado & Horario CDMX)

*(Selección basada en alto potencial de viralidad, diversidad de nicho y equilibrio entre riesgo/recompensa)*

| Día | Tema (Guión #) | V-Score Est. (0-10) | Hook Literal | Horario CDMX (pico) | Sub-nicho | Comentarios |
|-----|----------------|--------------------|--------------|--------------------|-----------|-------------|
| **LUNES** | ¿Por qué la saliva de mosquito NO coagula tu sangre? (1) | 8.9 | "Tu sangre es un tesoro... ¡para un mosquito!" | 12:30 PM | Ciencia WTF | Gancho impactante, dato cotidiano. |
| **MARTES** | La paradoja de Fermi: ¿Dónde están TODOS los aliens? (3) | 8.7 | "Si el universo es tan grande... ¿por qué estamos solos?" | 08:00 PM | Ciencia WTF | Pregunta existencial, genera debate. |
| **MIÉRCOLES** | El efecto Mandela: ¿Tu cerebro te está mintiendo sobre el pasado? (22) | 9.1 | "¿Recuerdas algo... que NUNCA pasó?" | 01:00 PM | Psicología WTF | Tema viral recurrente, alta identificación. |
| **JUEVES** | El día que el presidente de EE.UU. perdió un avión nuclear en España. (12) | 8.6 | "¡Una bomba atómica se cayó... en España!" | 07:30 PM | Historia WTF | Hecho histórico sorprendente, poco conocido. |
| **VIERNES** | ¿Podrías vivir dentro de un agujero negro sin morir al instante? (2) | 8.8 | "Cae en un agujero negro y... ¿qué pasa?" | 02:00 PM | Ciencia WTF | Especulativo, visualmente atractivo. |
| **SÁBADO** | La 'mancha' de sangre en la luna: ¿Un evento cósmico o una ilusión? (9) | 7.9 | "¿La Luna... con una herida de bala?" | 10:00 AM | Misterio | Curiosidad visual, buen "scroll stopper". |
| **DOMINGO** | ¿Por qué nos gusta el chisme (aunque digamos que no)? (23) | 7.5 | "Odias el chisme... ¡pero lo amas!" | 06:00 PM | Psicología WTF | Relacionable, genera autoconocimiento. |

---

## 3 Hipótesis de Oportunidad

1.  **Hipótesis 1: El factor "WTF" en ciencia y psicología genera alto engagement.**
    *   **Justificación:** Outliers como @LadyScience y @mentes_curiosas_ok demuestran que temas científicos o psicológicos presentados con un giro sorprendente, humor o un enfoque que desafía la intuición común ("WTF") tienen multiplicadores muy altos. Esto sugiere que lo inesperado y lo contraintuitivo son claves para la viralidad en nuestro nicho.
    *   **Acción:** Priorizar la identificación y adaptación de outliers con elementos "WTF" en los guiones y hooks literales, como los guiones seleccionados para el Lunes, Miércoles y Viernes de la próxima semana.

2.  **Hipótesis 2: La historia con un toque de "absurdo" o "drama oculto" es un nicho desatendido.**
    *   **Justificación:** @historiaparatontos tiene un multiplicador 5.1x. Esto, combinado con el alto interés en eventos históricos "bizarros" o poco conocidos, indica una oportunidad para capitalizar la intriga. Historias con giros inesperados o conflictos ridículos captan la atención de manera efectiva.
    *   **Acción:** Incorporar regularmente guiones de "Historia WTF" que desvelen eventos históricos menos conocidos o con un toque de humor negro/absurdo, como el caso del avión nuclear en España o la Guerra del Cubo.

3.  **Hipótesis 3: Preguntas existenciales o dilemas personales con base científica tienen potencial de resurgencia.**
    *   **Justificación:** Temas como "El efecto Mandela" o "¿Qué pasaría si la Tierra dejara de girar?" se conectan directamente con la experiencia personal o la curiosidad fundamental del usuario. Si bien son temas clásicos de divulgación, la presentación fresca y con hooks literales contundentes puede reactivar su viralidad.
    *   **Acción:** Desarrollar guiones que aborden estas preguntas, buscando un equilibrio entre rigor científico y un gancho emocional que interpele directamente al espectador sobre su percepción de la realidad o su propio comportamiento.

---

## Estructura de entregables generada
```
SEMANA_02_2026-05-13_a_2026-05-19/
├── BRIEFING_SEMANAL.md
├── LUNES/
│   └── V2_Produccion.mp4 (por completar)
├── MARTES/
│   └── V1_Produccion.mp4 (por completar)
├── MIERCOLES/
│   └── V3_Produccion.mp4 (por completar)
├── JUEVES/
│   └── V4_Produccion.mp4 (por completar)
├── VIERNES/
│   └── S2_V1_Produccion.mp4 (por completar)
├── SABADO/
│   └── S2_V2_Produccion.mp4 (por completar)
├── DOMINGO/
│   └── S2_V3_Produccion.mp4 (por completar)
├── RESEARCH/
│   └── referentes_sprint_3.md
│   └── outliers_sprint_3.md
├── ASSETS/
│   └── 25_guiones_sprint_3.md
│   └── scorecards_sprint_3.md
│   └── calendario_sprint_3.md
│   └── compliance_check_sprint_3.md
└── RETRO_SEMANA_02_2026-05-13_a_2026-05-19.md (al cierre)
```

## Próximo invocación
**2026-05-20 (LUNES)** — La rutina `weekly-sprint.yml` se ejecutará automáticamente para iniciar la planificación de la SEMANA_03. Las tareas pendientes son principalmente la generación final de assets para los 7 videos seleccionados y la publicación/monitoreo de V1-V4 y S2_V1-S2_V3 durante la semana actual.