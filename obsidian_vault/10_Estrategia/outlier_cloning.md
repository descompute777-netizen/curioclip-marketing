---
agente: A1_Investigacion + A0_Director
fecha: 2026-05-07
tags: [estrategia, outlier-cloning, metodologia, pipeline, sprint-semanal]
estado: activo
fuente: CurioClip_ULTRAPROMPT.docx (analisis video @mate.jimenez — 84.6% guardados/likes)
---

# 🎯 Metodología Outlier Cloning — CurioClip

## ¿Por qué Outlier Cloning?

El video de @mate.jimenez (reposteado por @mago_jp_oficial) obtuvo:
- 2,340 likes | 59 shares | **1,979 guardados**
- **Ratio guardados/likes: 84.6%** — extremadamente alto (benchmark normal: 5-15%)

Este ratio confirma que el contenido tipo "sistema paso a paso" tiene altísimo valor percibido. El video describe exactamente el método que CurioClip usa internamente — y también como formato de contenido.

**Insight clave (R9):** No se copia el contenido del outlier. Se copia su **estructura**. El mensaje se adapta al nicho/voz de CurioClip.

---

## Las 5 Fases — Protocolo Operativo de A1

### FASE 1 — Identificar Referentes

**Objetivo:** 5 cuentas top del nicho por ciclo semanal.

**Criterios de selección:**
- ≥50K seguidores (masa crítica que garantiza señal real)
- ER ≥5% (engagement real, no inflado)
- Posting activo: mínimo 3 posts en los últimos 14 días
- Nicho afín: curiosidades, ciencia, datos curiosos, misterio, cultura general (español)

**Output:** `20_Investigacion/referentes_sprint_[N].md`

| # | Cuenta | Plataforma | Seguidores | ER% | Posts/sem | Por qué como referente |
|---|--------|-----------|------------|-----|-----------|----------------------|
| 1 | | | | | | |
| 2 | | | | | | |
| 3 | | | | | | |
| 4 | | | | | | |
| 5 | | | | | | |

---

### FASE 2 — Extraer Outliers

**Definición de outlier:** Video con ≥3x el promedio de vistas de la cuenta.
- Si la cuenta promedia 50K vistas → outlier = cualquier video ≥150K

**Para cada referente, identificar 5-10 outliers.**
**Total esperado: 25-50 outliers por ciclo.**

**Output:** `20_Investigacion/outliers_sprint_[N].md`

| # | Referente | URL | Vistas | Likes | Shares | Guardados | Duración | Formato | Multiplicador |
|---|-----------|-----|--------|-------|--------|-----------|----------|---------|--------------|
| 1 | | | | | | | | | x |
| ... | | | | | | | | | |

---

### FASE 3 — Analizar Estructura Ganadora

**Para cada outlier, completar esta ficha:**

```
OUTLIER #[N] — @[cuenta]
URL: [link]
Vistas: [X] | Multiplicador: [X]x promedio

a) PROBLEMA QUE RESUELVE: [en 1 frase]
b) HOOK LITERAL (0-3s): "[palabras exactas del inicio]"
c) ESTRUCTURA: [ej: problema → datos shock → explicación → CTA]
d) CTA: [explícito o implícito]
e) FORMATO: [talking head / screen recording / montaje / texto animado / etc.]
f) POR QUÉ FUNCIONA: [hipótesis en 1 frase]
```

---

### FASE 4 — Adaptar al Mensaje CurioClip

**Por cada outlier analizado → generar 1 guión CurioClip.**

**Estructura de 5 bloques obligatoria (R8 en vigor):**

| Bloque | Segundos | Qué debe hacer |
|--------|---------|---------------|
| **HOOK** | 0-3s | Frase LITERAL que detiene el scroll. Escrita palabra por palabra. Sin hook genérico. |
| **IDENTIFICACIÓN** | 3-8s | El dolor o curiosidad específica de la audiencia |
| **PROMESA** | 8-12s | Qué van a obtener si se quedan mirando |
| **DESARROLLO** | 12-Xs | La sustancia del contenido (dato, ciencia, misterio) |
| **CTA** | últimos 5s | Acción específica (seguir, guardar, comentar, "parte 2 si llego a X likes") |

**R9 en vigor:** Se cambia el contenido, se preserva la estructura.
**R8 en vigor:** El HOOK debe estar escrito palabra por palabra. Ejemplo:
- ❌ Genérico: "dato sorprendente sobre el espacio"
- ✅ Literal: "Existe una estrella que llueve hierro líquido a 5,400 kilómetros por hora"

**Target:** 25+ guiones por ciclo. Los no seleccionados van a `30_Contenido/cola/`.

---

### FASE 5 — Seleccionar y Distribuir

1. A8 puntúa cada guión con V-Score (0-10)
2. Seleccionar los top 7 para la semana (1 por día)
3. A3 asigna día/hora según calendario editorial
4. Los no seleccionados van a cola (`30_Contenido/cola/`) para sprints futuros

---

## Entregable Semanal — Estructura de Carpetas

```
obsidian_vault/SEMANAS/SEMANA_[N]_[fecha_inicio]_a_[fecha_fin]/
│
├── BRIEFING_SEMANAL.md          ← KPIs, decisiones, calendario de la semana
├── RETRO_SEMANA_[N].md          ← Qué funcionó, qué no, ajustes
│
├── LUNES/
│   ├── guion_lunes.md           ← 5 bloques (R8: hook literal)
│   ├── brief_visual.md          ← Paleta, tipografía, cortes, estilo
│   ├── hashtags_tiktok.txt      ← 5-8 hashtags optimizados
│   ├── hashtags_facebook.txt    ← 3-5 hashtags para FB
│   ├── caption_tiktok.txt       ← Copy descripción + CTA
│   ├── caption_facebook.txt     ← Copy adaptado a FB (más storytelling)
│   ├── thumbnail.png            ← Generado vía Canva MCP
│   └── vscore_lunes.md          ← Scorecard predictivo V-Score + recomendaciones
│
├── MARTES/ [misma estructura]
├── MIERCOLES/ [misma estructura]
├── JUEVES/ [misma estructura]
├── VIERNES/ [misma estructura]
├── SABADO/ [misma estructura]
├── DOMINGO/ [misma estructura]
│
├── RESEARCH/
│   ├── outliers_semana_[N].md   ← 25-50 outliers analizados
│   ├── referentes.md            ← Los 5 referentes del ciclo
│   └── tendencias.md            ← Sounds, hashtags, formatos trending
│
└── ASSETS/
    ├── thumbnails/
    ├── b-roll/
    └── templates/
```

---

## Lo que NO se integra (por qué — compliance R2-R3)

| Afirmación del video fuente | Motivo de rechazo | Alternativa en sistema |
|-----------------------------|-------------------|----------------------|
| "Está asegurado que al menos uno se hará viral" | Viola R3 + G6 (nunca garantizar viralidad) | V-Score predice probabilidad con ±15% |
| "Simplemente copia y pega los guiones" | Viola R2 (plagio potencial) | Adaptar estructura, cambiar contenido (R9) |
| Depender de 1 solo creador como fuente | Fragilidad sistémica | 5 referentes por ciclo, rotados |

---

**Enlace:** [[MOC_Estrategia]] | [[MOC_Pipeline]] | [[competidores]] | [[calendario_editorial]]
