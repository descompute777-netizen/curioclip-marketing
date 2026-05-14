---
agente: A2_Psicologia
fecha: 2026-05-14
tags: [sistema-visual, paleta, tipografia, composicion, triggers, arco-emocional, sprint1]
estado: activo
version: 1.0
fuente: benchmarks neuromarketing 2026 + análisis competitivo LATAM + brief V5 Sprint 1
---

# Sistema Visual y Arco Emocional — CurioClip
**Actualizado:** 2026-05-14 | **Agente:** A2 Psicología de Marketing

> Documento constitucional del sistema visual. Su contenido es fijo salvo justificación por A/B test con datos reales.
> Todo agente (A4 Editor, A3 Algorítmico, A1 Investigación) debe leerlo antes de producir o evaluar contenido.

---

## 1. Arco Emocional Óptimo CurioClip (15-30s)

El arco emocional no es una narrativa arbitraria. Está mapeado sobre la curva de activación atencional documentada en estudios de eye-tracking en consumo de video corto (Nielsen Consumer Neuroscience 2024; MIT Media Lab Digital Attention Study 2025). El sistema nervioso tiene ventanas predecibles de apertura y cierre atencional. CurioClip diseña para esas ventanas.

### Mapa de Arco por Segundo

| Segundo | Emoción Objetivo | Mecanismo Cognitivo | Qué debe ocurrir en pantalla | Qué debe ocurrir en audio |
|---------|-----------------|--------------------|-----------------------------|--------------------------|
| 0-1 | **SHOCK / PATTERN INTERRUPT** | Activación amígdala — señal de novedad extrema | Imagen o texto que contradice expectativas. Visual más impactante del video. NO logos, NO intros. | Efecto sonoro agudo o silencio total (contraste con feed sonoro) |
| 1-3 | **INCREDULIDAD ACTIVA** | Loop cognitivo abierto — el cerebro busca resolución | Texto hook completo en pantalla. La frase que hace que el usuario deje de hacer swipe. | Primer segundo de narración: la pregunta o afirmación imposible |
| 3-8 | **TENSIÓN / QUIERO SABER MÁS** | Curiosity gap (Loewenstein, 1994) — brecha entre lo que sé y lo que quiero saber | Setup del fenómeno. Mostrar el "¿cómo es posible?" sin responderlo. Ritmo más lento para que el cerebro registre la pregunta. | Narración crea la pregunta, no la responde. Música sube ligeramente. |
| 8-15 | **SATISFACCIÓN PARCIAL / REVEAL PROGRESIVO** | Dopamina en dosis controlada — recompensa parcial que mantiene el loop | Primera respuesta visual: mostrar el mecanismo o dato clave. Infografía simple o B-roll ilustrativo. | Narración explica el mecanismo base. Tono más informativo, menos dramático. |
| 15-25 | **CLÍMAX / DATO MÁS IMPACTANTE** | Pico dopaminérgico — el payoff del loop abierto | El dato más WTF del video. Texto grande, color de acento, efecto visual de énfasis. | Cambio de tono vocal o pausa dramática antes del dato clave. |
| 25-30 | **RESOLUCIÓN + APERTURA SECUNDARIA** | Cierre del loop primario + apertura del loop secundario para parte 2 | CTA visual + texto del CTA. Dato de cierre que deja una pregunta nueva abierta. | Narración del CTA + última frase que crea anticipación ("y eso no es lo más raro...") |

### Curva de Retención Objetivo

```
Retención
100% |████████████████
     |         ███████████
 75% |                   ███████
     |                          █████
 50% |                               ████
     |                                   ██
 25% |────────────────────────────────────────
     0s   5s   10s   15s   20s   25s   30s
          ↑         ↑          ↑
        Hook      Reveal     CTA
       (≥85%)   (≥65%)    (≥45%)
```

**Umbrales de alerta A8:**
- Retención a 3s < 65% → hook fallido → devolver a A2
- Retención a 15s < 45% → setup demasiado lento → edición de ritmo
- Completion rate < 35% → CTA mal posicionado o video demasiado largo

### Arco Emocional por Sub-Nicho

| Sub-nicho | Emoción dominante 0-3s | Emoción dominante 3-15s | Emoción dominante 15-30s |
|-----------|----------------------|------------------------|-------------------------|
| Ciencia WTF | Incredulidad / adrenalina | Comprensión asombrada | Respeto + urgencia de compartir |
| Misterio sin resolver | Inquietud / ansiedad controlada | Tensión sostenida | Frustración positiva (quiero saber más) |
| Comparación absurda | Disonancia cognitiva | Recalibración mental | Asombro existencial |
| Sabías que / Dato específico | Curiosidad activada | Satisfacción de aprender | Status epistémico ("ahora lo sé") |
| Leyes / Países WTF | Humor / absurdo | Reconocimiento cultural | Impulso de compartir como chiste |

---

## 2. Paleta de Colores — Sistema Oficial CurioClip

### Paleta Principal (inmutable salvo A/B test)

| Nombre | Hex | RGB | Uso |
|--------|-----|-----|-----|
| Negro Profundo | `#0A0A0A` | 10, 10, 10 | Fondo dominante (preferido) |
| Carbón Oscuro | `#1A1A1A` | 26, 26, 26 | Fondo alternativo (más suave) |
| Blanco Puro | `#FFFFFF` | 255, 255, 255 | Texto principal, subtítulos |
| Amarillo CurioClip | `#FFD700` | 255, 215, 0 | Palabras de énfasis en hook, highlights |
| Rojo Alarma | `#FF3B3B` | 255, 59, 59 | Warnings, datos de peligro, cifras críticas |
| Naranja Energía | `#FF8C00` | 255, 140, 0 | CTAs, flechas, acentos de acción |

### Paleta Secundaria (uso contextual)

| Nombre | Hex | Cuándo usar |
|--------|-----|------------|
| Azul Ciencia | `#00B4D8` | Sub-nicho ciencia/espacio/biología — evoca laboratorio |
| Verde Naturaleza | `#2DC653` | Sub-nicho animales, biología, naturaleza |
| Púrpura Misterio | `#7B2FBE` | Sub-nicho misterio, fenómenos paranormales, señales |
| Gris Neutro | `#3D3D3D` | Fondos de texto secundario, separadores |

> REGLA CARDINAL: Los fondos saturados están PROHIBIDOS. El texto siempre domina visualmente sobre el B-roll.
> El B-roll es contexto; el texto es el contenido. Si el B-roll compite con el texto, pierde el texto y pierde la retención.

### Uso de Color por Emoción

| Emoción objetivo | Color principal | Color de apoyo | Por qué |
|-----------------|----------------|----------------|---------|
| Shock / Peligro | `#FF3B3B` rojo | `#FFD700` amarillo | Señal de alarma — activa amígdala (Elliot 2011) |
| Asombro / WTF | `#FFD700` amarillo | `#FFFFFF` blanco | Alta visibilidad + asociación con descubrimiento |
| Misterio | `#7B2FBE` púrpura | `#1A1A1A` carbón | Oscuridad + inusual = inquietud controlada |
| CTA / Acción | `#FF8C00` naranja | `#FFFFFF` blanco | Naranja es el color de mayor tasa de conversión en CTAs digitales (HubSpot 2024) |
| Dato científico | `#00B4D8` azul | `#FFFFFF` blanco | Asociación con credibilidad, laboratorio, datos |

### Contraste Obligatorio
- Relación mínima texto/fondo: **7:1** (WCAG AAA — garantiza legibilidad en pantallas de baja calidad)
- Blanco `#FFFFFF` sobre Negro `#0A0A0A` = 21:1 (máximo posible)
- Amarillo `#FFD700` sobre Negro `#0A0A0A` = 14.1:1 (óptimo para hooks)
- Verificar siempre con: webaim.org/resources/contrastchecker

---

## 3. Sistema Tipográfico

### Jerarquía de Fuentes

| Nivel | Uso | Fuente | Peso | Tamaño mínimo | Color |
|-------|-----|--------|------|--------------|-------|
| H1 — Hook | Texto gancho 0-3s | Montserrat Black o Bebas Neue | Black / 900 | 52px | `#FFD700` o `#FFFFFF` |
| H2 — Énfasis | Palabras clave en el desarrollo | Montserrat Bold o Inter Black | Bold / 800 | 38px | `#FF3B3B` o `#FFD700` |
| H3 — Subtítulo | Narración sincronizada | Montserrat SemiBold o Inter Bold | SemiBold / 600 | 28px | `#FFFFFF` con sombra negra |
| H4 — CTA | Texto de acción final | Montserrat Bold o Inter Bold | Bold / 700 | 36px | `#FF8C00` o `#FFD700` |
| Caption | Datos, fuentes, disclaimers | Inter Regular | Regular / 400 | 18px | `#AAAAAA` |

### Reglas Tipográficas

1. **Una sola familia tipográfica por video** — mezclar Montserrat y Bebas Neue en el mismo video genera disonancia visual
2. **El hook siempre en MAYÚSCULAS parciales** — las palabras clave en mayúsculas activan el escaneo visual automático (pre-attentive processing)
3. **Sombra de texto obligatoria en subtítulos** — `text-shadow: 2px 2px 4px #000000` — garantiza legibilidad sobre cualquier B-roll
4. **Kerning ajustado en hooks** — letra espaciada (+5 a +10) para facilitar lectura rápida
5. **Máximo 7 palabras por línea de texto** — legibilidad en pantalla de 6 pulgadas a distancia de brazo

### Descargas Gratuitas
- Montserrat: fonts.google.com/specimen/Montserrat
- Bebas Neue: fonts.google.com/specimen/Bebas+Neue
- Inter: fonts.google.com/specimen/Inter
- Todas las fuentes anteriores: licencia Open Font License — uso comercial permitido

---

## 4. Estilo de B-roll — Guía Visual

### Jerarquía de Tipos de B-roll por Impacto

| Tipo | Impacto visual | Sub-nicho ideal | Fuentes gratuitas |
|------|---------------|----------------|------------------|
| **Slow-motion científico** | Muy alto | Ciencia WTF, física | Pexels, Coverr — buscar "slow motion" |
| **Microscopía / macro extremo** | Muy alto | Biología, bacterias, materiales | Pexels: "microscope", "macro water drop" |
| **Astronómico / espacio** | Alto | Comparaciones de escala, cosmología | NASA Image Library (dominio público) |
| **Fenómeno natural en tiempo real** | Alto | Lava, cristales, plasma | Pexels: "lava flow", "crystal formation" |
| **Animación de datos** | Medio-alto | Comparaciones absurdas, escalas | CapCut templates, Motion Array free |
| **Documental con licencia** | Medio | Misterio, historia | Wikimedia Commons, Internet Archive |
| **Infografía animada** | Medio | Cualquier sub-nicho | Canva MCP, CapCut text animations |

### Reglas de Selección de B-roll

1. **Primeros 2 segundos: el plano más impactante disponible** — no el más informativo, el más visualmente extremo
2. **Nunca más de 2.5 segundos por plano en los primeros 10s** — el algoritmo penaliza frames estáticos prolongados
3. **Movimiento en cada plano** — si el clip no tiene movimiento inherente, agregar zoom-in/out o parallax leve en edición
4. **Coherencia cromática con la paleta** — preferir B-roll con tonos oscuros o que permitan overlay de texto sin perder legibilidad
5. **Verificar licencia SIEMPRE antes de usar** — compliance R2 — Pexels/Pixabay/Coverr son CC0 por defecto pero verificar ficha por ficha

### Búsquedas Tipo por Sub-Nicho

| Sub-nicho | Búsqueda en Pexels | Alternativa |
|-----------|-------------------|-------------|
| Plomo / Metal fundido | "molten metal", "liquid metal pour", "foundry" | NASA: no aplica — usar Pexels |
| Espacio / Cosmología | "galaxy", "nebula", "space", "star" | NASA Image Library (PD) |
| Biología / Bacterias | "microscope", "bacteria culture", "cell" | Wikimedia Commons: "microscopy" |
| Misterio / Radio | "radio tower", "antenna", "dark signal" | Coverr: "abandoned technology" |
| Animales extremos | "mantis shrimp", "tardigrade animation" | Wikimedia Commons: BBC Natural History (verificar) |
| Física / Efectos | "leidenfrost", "water drop hot pan", "levitation" | Pexels: "physics experiment" |

---

## 5. Reglas de Composición Visual

### Posicionamiento del Texto

```
┌─────────────────────────┐
│  [ZONA HOOK — TOP 40%]  │  ← Hook y palabras clave aquí
│  ████████████████████   │
│  ████████████████████   │
│─────────────────────────│
│  [ZONA B-ROLL — 60%]    │  ← Acción visual principal aquí
│  [+ subtítulos sup.]    │
│  [+ subtítulos inf.]    │
│─────────────────────────│
│  [ZONA CTA — BOTTOM 15%]│  ← CTA y hashtags aquí
└─────────────────────────┘
     ⚠️ Zona muerta: evitar texto
     en los bordes laterales (10px cada lado)
     y el centro exacto (compite con face cam)
```

**Regla del único protagonista:** Un solo elemento dominante por frame. Si hay texto grande y B-roll impactante simultáneamente, uno de los dos pierde — y nunca debe perder el texto.

### Densidad de Información

| Segundo | Elementos en pantalla (máximo) | Por qué |
|---------|-------------------------------|---------|
| 0-3 | 1 texto + 1 imagen de fondo | El cerebro procesa un solo canal visual en el hook |
| 3-10 | 1 texto principal + subtítulo + B-roll | Setup — se puede agregar información progresivamente |
| 10-20 | Texto + B-roll + subtítulo + 1 gráfico | Desarrollo — mayor densidad acceptable porque el viewer ya está comprometido |
| 20-30 | Texto CTA + Logo + subtítulo | Reducir elementos — el cerebro está en modo decisión (share / follow / swipe) |

### Movimiento y Dinamismo
- **Regla 2 segundos:** Nunca frame estático por más de 2 segundos — el algoritmo de TikTok interpreta stasis como baja calidad
- **Ken Burns effect:** Para imágenes fijas, aplicar zoom lento (1.0 a 1.08 en 3s) — simula movimiento sin distorsionar
- **Jump cuts:** Mínimo 3 cortes antes del segundo 8 — el ritmo de corte es proporcional a la retención en Perfil A
- **Transición de énfasis:** Flash blanco (2-3 frames) antes del dato más impactante — activa el sistema visual de alerta

---

## 6. Sistema de Thumbnails / Miniaturas

> En TikTok 2026, el thumbnail es el frame del video más compartido en otras plataformas y el primer elemento visible en el perfil del canal. En Facebook Reels y al compartir por WhatsApp, el thumbnail determina el CTR fuera de plataforma.

### Especificaciones Técnicas
- **Dimensión primaria (TikTok perfil + Facebook):** 1080 × 1920 px (9:16)
- **Dimensión alternativa (preview externo):** 1280 × 720 px (16:9 para WhatsApp/Telegram preview)
- **Formato:** PNG (sin compresión) o JPG calidad 95+
- **Herramienta:** Canva MCP (nativo) — template oscuro + texto grande

### Elementos Obligatorios del Thumbnail

1. **El frame más extremo del video** — el momento de mayor tensión visual, no el más informativo
2. **Texto de impacto: 3-5 palabras máximo** — debe leerse en 1.5 segundos a distancia de brazo
3. **Fondo oscuro** — `#0A0A0A` o `#1A1A1A` — garantiza que el texto en amarillo/blanco destaque siempre
4. **Un elemento de color de acento** — `#FFD700` o `#FF3B3B` — el ojo lo busca antes del texto
5. **Sin logos gigantes** — el logo CurioClip máximo al 8% del frame, esquina inferior izquierda

### Anatomía del Thumbnail que Para el Scroll en 2026

```
┌────────────────────────────┐
│ 🔴 [COLOR ACENTO]          │  ← Elemento visual de alerta — esquina o centro
│                            │
│   [IMAGEN EXTREMA          │  ← El momento más WTF del video
│    DEL VIDEO]              │
│                            │
│  ████ TEXTO EN             │  ← 3-5 palabras, fuente Black, ≥52px
│  ████ MAYÚSCULAS           │  ← Amarillo sobre negro o blanco sobre negro
│       AQUÍ                 │
│                        [○] │  ← Logo CurioClip — mínimo y esquina
└────────────────────────────┘
```

### Fórmulas de Texto de Thumbnail por Sub-Nicho

| Sub-nicho | Fórmula | Ejemplo |
|-----------|---------|---------|
| Ciencia WTF | [VERBO EXTREMO] + [DATO IMPOSIBLE] | "METIÓ SU MANO EN 327°C" |
| Misterio | [NÚMERO] + [OBJETO MISTERIOSO] | "50 AÑOS SIN RESPUESTA" |
| Comparación | [OBJETO A] vs [OBJETO B] | "TU CUERPO vs LA GALAXIA" |
| Sabías que | [NÚMERO EXACTO] + [CONTEXTO] | "38 BILLONES en tu boca AHORA" |
| Leyes WTF | [ACCIÓN] + [PAÍS] | "ILEGAL en este PAÍS" |

### Lo que NO funciona en thumbnails 2026
- Texto sobre imagen sin sombra o sin contraste suficiente (se pierde en feed oscuro)
- Más de 6 palabras (requiere más de 2 segundos para leer — el usuario ya hizo swipe)
- Caras de sorpresa genéricas sin texto (funciona para canales de 1M+, no para canales nuevos)
- Colores saturados brillantes como fondo (compiten con el texto en lugar de servirle)
- Logos grandes (el viewer no conoce la marca todavía — no es un activo sino un obstáculo)

---

## 7. Los 7 Triggers Psicológicos del Nicho Curiosidades

### Marco teórico
Los triggers que siguen están basados en la intersección de tres modelos: el Curiosity Gap de Loewenstein (1994), la teoría de Regulación Emocional en consumo de redes sociales (Gross 2015, adaptado a TikTok por investigadores de MIT 2024), y los datos de eye-tracking de VisualEyes sobre contenido de ciencia en español.

Cada trigger se documenta con: mecanismo cognitivo, cómo incorporarlo sin manipulación, y ejemplo de hook literal que lo activa.

---

### TRIGGER 1 — Curiosity Gap (Brecha de Curiosidad)

**Mecanismo:** El cerebro experimenta incomodidad ante información incompleta y está biológicamente motivado a cerrar esa brecha. Loewenstein demostró que la magnitud de la curiosidad es proporcional a la distancia entre lo que sabemos y lo que queremos saber.

**Cómo incorporarlo sin manipulación:** La información incompleta debe ser real — no clickbait. Si el video promete resolver la brecha, la debe resolver. La manipulación ocurre cuando el payoff no existe; la curiosidad legítima ocurre cuando el payoff es real pero diferido.

**En el guión:**
- Abrir el loop en segundos 1-3: plantear la pregunta o el hecho imposible
- Mantenerlo abierto hasta el segundo 15: no resolver antes
- Cerrar con payoff real en segundos 15-25

**Hook que activa este trigger:**
- "Esta señal lleva 50 años transmitiéndose y NADIE sabe de dónde viene"
- "El 99% de las personas que leen esto no saben cómo funciona su propio corazón"
- "Existe un material que NO puede existir según las leyes de la física — y lo tenemos en casa"

---

### TRIGGER 2 — Awe / Asombro (Elevación Emocional)

**Mecanismo:** El awe activa el eje parasimpático — reduce la frecuencia cardíaca y produce una sensación de ingravidez temporal. Estudios de Keltner & Haidt (2003, actualizado 2022) muestran que el asombro aumenta la probabilidad de compartir en un 34% en comparación con contenido neutral de igual información.

**Cómo incorporarlo sin manipulación:** El asombro genuino requiere datos reales y verificables. Exagerar las cifras destruye la credibilidad a largo plazo. La especificidad es el mejor vehículo del asombro real.

**En el guión:**
- El dato de asombro va siempre en el clímax (segundos 15-25)
- Usar el número exacto, nunca la aproximación ("327°C", no "muy caliente")
- El B-roll debe visualmente magnificar el dato, no solo ilustrarlo

**Hook que activa este trigger:**
- "Existe una estrella donde llueve HIERRO LÍQUIDO a 5,400 km/h"
- "Tu cuerpo tiene 37 BILLONES de células — más que estrellas en la Vía Láctea"
- "Un cucharadita de estrella de neutrones pesa más que todos los humanos juntos"

---

### TRIGGER 3 — Status Epistémico (Juego de Conocimiento)

**Mecanismo:** El conocimiento exclusivo o raro genera un activo de status social. Cialdini (1984, Influence) documentó que la información escasa aumenta su valor percibido — si "el 99% no lo sabe", saber ese dato te coloca en el 1% y tu cerebro registra esa posición como recompensa.

**Cómo incorporarlo sin manipulación:** No inventar exclusividad donde no la hay. "El 99% no sabe esto" solo debe usarse cuando el dato es genuinamente desconocido para el público general — verificable comparando con encuestas o datos de búsqueda.

**En el guión:**
- La frase de exclusividad va en el hook o en la identificación (segundos 0-8)
- El payoff debe justificar la exclusividad — si el dato es común, no usar este trigger
- Conectar el dato con el CTA: "ahora que lo sabes, comenta..." refuerza el status

**Hook que activa este trigger:**
- "El 99% no sabe por qué el cielo es azul — y la respuesta real no es la que te enseñaron"
- "Lo que nadie te explica sobre cómo funciona tu memoria"
- "La causa real de la resaca — y no tiene nada que ver con el alcohol en sí"

---

### TRIGGER 4 — Pattern Interrupt (Ruptura de Patrón)

**Mecanismo:** El sistema nervioso entra en modo de piloto automático durante el scroll. Un estímulo que contradice el patrón esperado (visual, auditivo o conceptual) fuerza la salida de ese modo. Este es el mecanismo primario del hook de 0-1 segundo — la función es interrumpir el automatismo, no informar.

**Cómo incorporarlo sin manipulación:** El pattern interrupt debe ser relevante al contenido — no un ruido aleatorio para capturar atención y luego no cumplir. El contraste debe tener relación directa con el tema del video.

**En el guión:**
- El pattern interrupt es siempre el primer elemento (frame 0 a frame 30 — menos de 1 segundo)
- Puede ser visual (imagen extrema), auditivo (sonido inusual) o textual (afirmación contradictoria)
- NO usar el mismo tipo de pattern interrupt en videos consecutivos — el cerebro aprende el patrón del canal y deja de sorprenderse

**Hooks que activan este trigger:**
- Visual: plano de plomo fundido naranja brillante sobre fondo negro
- Auditivo: el tono exacto de la señal UVB-76 como primer sonido del video
- Textual: "Lo que sabes sobre X está completamente equivocado" (contradice creencia establecida)

---

### TRIGGER 5 — Social Proof Inverso (Transgresión Positiva)

**Mecanismo:** La cognición social humana está calibrada para detectar violaciones a normas. Cuando algo es "ilegal en este país" o "prohibido por la ciencia" o "lo que el gobierno no te dice", el cerebro activa el sistema de detección de injusticia y el viewer se siente empoderado al conocer la verdad.

**Cómo incorporarlo sin manipulación:** La transgresión debe ser real — leyes absurdas reales, prohibiciones científicas reales, datos que instituciones no promueven activamente (pero no desinformación disfrazada de transgresión). La diferencia es verificabilidad.

**En el guión:**
- Este trigger funciona mejor en sub-nicho Leyes WTF y Misterio
- Conectar con CTA de share: la gente comparte transgressions porque se siente el "descubridor valiente"
- Cuidado compliance A9: verificar que la "transgresión" sea legal y verificable

**Hook que activa este trigger:**
- "En este país es ILEGAL llevar una espada si tu apellido es Smith"
- "La NASA tiene un documento clasificado sobre esto — y está en internet"
- "Lo que tu colegio te enseñó sobre X es oficialmente incorrecto"

---

### TRIGGER 6 — Identidad de Tribu (Pertenencia / Exclusión)

**Mecanismo:** El cerebro procesa la pertenencia grupal en el mismo circuito que el dolor físico (Eisenberger 2003). El contenido que activa "tú eres parte de los que saben" crea afiliación emocional con el canal. Este es el mecanismo de largo plazo que convierte viewers en seguidores.

**Cómo incorporarlo sin manipulación:** No crear exclusión negativa ("los que no saben esto son tontos"). Crear exclusión positiva por curiosidad, no por superioridad ("esto es para los que siempre quisieron entender cómo funciona todo").

**En el guión:**
- El trigger de tribu va principalmente en el CTA (segundos 25-30)
- También en el caption de la publicación — "sígueme si eres de los que..." 
- Construir identidad de marca: "En CurioClip, los curiosos se quedan" es más poderoso que "sígueme para más videos"

**Hook que activa este trigger:**
- "Este video es para los que nunca se conformaron con 'así es como funciona'"
- "Si llegas al final, eres de los que realmente quieren entender el mundo"
- CTA: "Sígueme — aquí los curiosos no se quedan con preguntas"

---

### TRIGGER 7 — Reciprocidad Cognitiva (Deuda de Aprendizaje)

**Mecanismo:** Cialdini documentó que los humanos sienten una obligación inconsciente de corresponder cuando reciben algo de valor. En contenido digital, este mecanismo se activa cuando el video entrega un dato genuinamente útil o asombroso — el viewer siente que "debe" dar algo a cambio (like, follow, share, comentario).

**Cómo incorporarlo sin manipulación:** El valor debe ser real. La reciprocidad se activa por valor genuino, no por valor inflado. Si el dato es superficial, el mecanismo no se activa — peor, genera desconfianza.

**En el guión:**
- Entregar el dato más valioso antes del CTA — no después
- El CTA explota la reciprocidad: "te di algo interesante, ahora dame un follow"
- La forma más poderosa: entregar primero, pedir después — nunca pedir antes del payoff

**Hook que activa este trigger:**
- CTA post-reveal: "Ahora que lo sabes, sígueme — mañana te enseño algo aún más raro"
- "Te expliqué el efecto Leidenfrost de forma que no lo vas a olvidar — sígueme para más"
- "Si esto te sorprendió, guarda el video — te prometo que lo vas a querer contar"

---

## 8. Tabla de Decisión Rápida — Pre-Producción

Antes de escribir el guión, el equipo debe completar esta tabla:

| Pregunta | Respuesta requerida |
|----------|-------------------|
| ¿Qué perfil de avatar es el target primario del video? | A / B / C |
| ¿Qué emoción domina los primeros 3 segundos? | Shock / Incredulidad / Awe / Transgresión |
| ¿Cuál es el trigger psicológico primario? | 1 de los 7 triggers anteriores |
| ¿Cuál es el trigger psicológico secundario? | 1 de los 7 triggers anteriores |
| ¿Qué número exacto aparece en el hook? | [dato específico — no estimado] |
| ¿El loop cognitivo se abre en los primeros 3s? | Sí / No (si No, reescribir hook) |
| ¿El loop cognitivo se cierra antes del segundo 15? | Sí (problema) / No (correcto) |
| ¿El CTA corresponde al trigger de tribu o reciprocidad? | Sí / No |
| ¿Los subtítulos son legibles sin sonido? | Sí / No (si No, revisar tipografía) |
| ¿El B-roll del frame 0 es el más impactante disponible? | Sí / No (si No, edición) |

---

## 9. Checklist Visual Pre-Exportación

- [ ] Fondo: `#0A0A0A` o `#1A1A1A` — no fondo saturado
- [ ] Hook texto: Montserrat Black o Bebas Neue — mínimo 52px
- [ ] Hook posición: mitad superior del frame (top 40%)
- [ ] Contraste texto/fondo: mínimo 7:1 (verificado)
- [ ] Subtítulos: sombra negra, 28-32px, legibles sin audio
- [ ] CTA texto: 36-40px, color de acento (`#FF8C00` o `#FFD700`)
- [ ] B-roll frame 0: el más impactante del video
- [ ] Movimiento en cada plano: no más de 2s estático
- [ ] Jump cuts antes del segundo 8: mínimo 3 cortes
- [ ] Thumbnail: frame extremo + 3-5 palabras + fondo oscuro + acento de color
- [ ] Logo CurioClip: presente, máximo 8% del frame, esquina inferior izquierda
- [ ] Duración: 18-30s (no superar 30s hasta calibrar retención con datos reales)

---

## 10. Historial de Decisiones A/B (Vacío — Pendiente Datos Reales)

> Este bloque se completa a partir de la publicación #3 con datos reales de TikTok Analytics.
> Antes de ese punto, las especificaciones de este documento son los defaults del sistema.

| Fecha | Variable testeada | Variante A | Variante B | Ganador | Métrica |
|-------|------------------|-----------|-----------|---------|---------|
| — | — | — | — | — | — |

**Próxima revisión:** Sprint 3 (2026-05-27) o cuando se tengan datos de 5+ publicaciones.

---

**Enlace MOC:** [[MOC_Estrategia]] | [[audiencia_avatar]] | [[outlier_cloning]] | [[MOC_Contenido]] | [[calendario_editorial]]
