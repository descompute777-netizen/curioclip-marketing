---
agente: A1_Investigacion + A4_Editor + A9_Compliance
fecha: 2026-05-07
tags: [clip-mining, pipeline, produccion, viral, investigacion, PhD]
estado: activo
fuente: WhatsApp Video 2026-05-06 at 7.22.19 PM — análisis visual del workflow
---

# 🎬 Clip Mining Pipeline — CurioClip
## Sistema de Producción por Inteligencia de Contenido Viral

> **Definición:** Clip Mining es el proceso de identificar videos virales reales en múltiples plataformas, extraer el momento de mayor retención/engagement ("Golden Clip"), y transformarlo en contenido CurioClip original con subtítulos, overlay de marca, miniatura y metadata optimizada.

---

## Arquitectura del Pipeline

```
PLATAFORMAS                    ANÁLISIS                   PRODUCCIÓN               PUBLICACIÓN
─────────────────────────────────────────────────────────────────────────────────────────────
TikTok ──┐                  ┌─ Métricas virales          ┌─ yt-dlp download
YouTube ─┼── A1 BUSCA ─────►│  Retention analysis   ──►  │  ffmpeg cut           ──► A6 PUBLICA
Facebook─┘  (agent-browser  └─ Golden Moment ID          │  Whisper subtítulos       + A9 CHECK
Instagram    + web_search)     [timestamp inicio-fin]     │  Canva thumbnail
                                                          └─ Caption + hashtags
```

---

## MODO A — Contenido Original (Outlier Cloning)
*Ya integrado en outlier_cloning.md — estructura + mensaje propio*

## MODO B — Clip Mining Directo
*Este documento — clips reales transformados con valor añadido*

> **Regla maestra:** Siempre hay TRANSFORMACIÓN. CurioClip no es un canal de reposteo.
> Cada clip extraído recibe: subtítulos nuevos + hook overlay + contexto explicativo + branding.
> Sin transformación = violación R2. Ver sección de Compliance abajo.

---

## FASE 1 — BÚSQUEDA MULTI-PLATAFORMA (A1)

### Plataformas y Métricas por Peso

| Plataforma | Señal #1 | Señal #2 | Señal #3 | Señal #4 | Herramienta |
|-----------|---------|---------|---------|---------|------------|
| **TikTok** | Completion rate (35%) | Share rate (30%) | Save rate (20%) | Comment rate (15%) | TikTok Creative Center + agent-browser |
| **YouTube** | Retention % en timestamps (35%) | CTR (25%) | Share rate (25%) | Like ratio (15%) | YouTube Trending + YouTube Studio |
| **Facebook** | Share rate (40%) | Reaction rate (30%) | Comment rate (20%) | View duration (10%) | agent-browser |
| **Instagram** | Save rate (35%) | Share rate (35%) | Comment rate (20%) | View rate (10%) | agent-browser |

### Criterios de Selección (Video debe cumplir ≥3 de 4):
- ✅ Vistas: ≥500K en TikTok/YouTube, ≥200K en Facebook/Instagram
- ✅ ER: ≥3x el promedio del canal/cuenta que lo publicó
- ✅ Trending: publicado hace ≤14 días (señal fresca)
- ✅ Nicho: curiosidades, ciencia, datos, misterio, cultura general (español o adaptable)
- ✅ Duración: ≤3 minutos (hay un "Golden Clip" extraíble de ≤60 segundos)

### Proceso de Búsqueda Semanal (A1 ejecuta cada Lunes)

```
PASO 1 — TikTok Creative Center
  URL: ads.tiktok.com/business/creativecenter/inspiration/popular/hashtag
  Búsquedas: #datoscuriosos #sabiasque #curiosidades #cienciaentiktok
  Filtros: Región LATAM/España | Periodo: 7 días | Ordenar por: Engagement rate

PASO 2 — YouTube Trending España/México
  URL: youtube.com/feed/trending → filtrar Ciencia y Tecnología
  Búsquedas: "sabías que" "datos curiosos" "no lo sabías" — Filtro: Esta semana
  agent-browser: scroll FYP de TikTok durante 10 min registrando URLs

PASO 3 — Facebook Video Search
  Grupos: "Curiosidades del mundo", "Datos curiosos", "Ciencia increíble"
  agent-browser: navegar y capturar URLs de videos con >1K shares

PASO 4 — Instagram Reels
  Hashtags: #datoscuriosos #curiosidades #sabiasque
  agent-browser: identificar reels con >100K plays recientes
```

### Output A1: `20_Investigacion/viral_clips_sprint_[N].md`

```markdown
| # | URL | Plataforma | Vistas | ER% | Trending Score | Golden Clip (timestamp) | Licencia | Prioridad |
|---|-----|-----------|--------|-----|---------------|------------------------|---------|----------|
| 1 | [url] | TikTok | 2.3M | 8% | Alto | 0:05-0:23 | Verificar | ⭐⭐⭐ |
| 2 | [url] | YouTube | 890K | 5% | Medio | 1:15-1:45 | CC-BY | ⭐⭐⭐ |
```

---

## FASE 2 — IDENTIFICACIÓN DEL GOLDEN CLIP (A1 + A4)

### ¿Qué es el Golden Clip?
El segmento de ≤60 segundos donde se concentra el mayor valor viral del video.

### Cómo identificarlo por plataforma:

**YouTube (método datos):**
1. Abrir YouTube Studio del video (si es propio) o ver comentarios públicos
2. Buscar en comentarios: timestamps mencionados ("el momento del segundo X")
3. Ver el gráfico de retención: el segmento con el "plateau" más largo y "re-watches" (bumps)
4. El Golden Clip = el plateau más largo + el momento de mayor densidad de datos

**TikTok (método observación):**
1. Ver el video completo y marcar el momento más sorprendente/WTF
2. Revisar comentarios: ¿qué momento comenta la gente?
3. En general: segundos 3-20 de videos de 30-60s son el Golden Clip
4. En videos largos (>1min): el dato/momento más impactante (normalmente en la mitad)

**Facebook/Instagram (método engagement):**
1. El Golden Clip = el momento que hace que la gente pare el scroll y comparta
2. Buscar en comentarios el dato que más se menciona o cita

### Ficha Golden Clip (A1 entrega a A4):
```
VIDEO SOURCE: [URL]
PLATAFORMA: [TikTok/YouTube/FB/IG]
VISTAS: [X] | TRENDING: [Alta/Media]
GOLDEN CLIP: [timestamp inicio] → [timestamp fin] (duración: [X]s)
POR QUÉ ES GOLDEN: [1 frase — qué hace que ese momento sea lo más viral]
LICENCIA: [CC-BY / Fair Use / Pendiente A9] 
HOOK SUGERIDO: "[texto literal para el overlay 0-3s]"
```

---

## FASE 3 — PRODUCCIÓN DEL CLIP (A4)

### Herramientas del Stack

| Herramienta | Función | Estado |
|------------|---------|--------|
| `yt-dlp` | Descargar video fuente | ✅ Instalar |
| `ffmpeg` | Cortar el Golden Clip exacto | ✅ Instalar |
| `openai-whisper` | Generar subtítulos automáticos | ✅ Instalar |
| Canva MCP | Thumbnail 9:16 | ✅ Disponible |
| CapCut | Post-producción visual | ✅ Disponible |

### Workflow de Producción Paso a Paso

```bash
# PASO 1: Descargar video fuente (solo después de A9 APPROVE)
yt-dlp -f "bestvideo[height<=1080]+bestaudio/best" -o "source_%(id)s.%(ext)s" [URL]

# PASO 2: Cortar el Golden Clip
ffmpeg -i source_video.mp4 -ss [timestamp_inicio] -to [timestamp_fin] \
  -c:v libx264 -c:a aac -y golden_clip_raw.mp4

# PASO 3: Generar subtítulos automáticos
whisper golden_clip_raw.mp4 --language es --output_format srt --output_dir ./subs/

# PASO 4: Verificar y corregir subtítulos en CapCut
# (abrir golden_clip_raw.mp4 + importar .srt → ajustar timing + ortografía)

# PASO 5: Añadir en CapCut:
#   - Hook text overlay (0-3s): texto grande, colores marca
#   - Subtítulos estilo CurioClip (blanco/amarillo, bottom center)
#   - Música de fondo royalty-free (Pixabay Music, baja en primeros 3s)
#   - Logo CurioClip + CTA final
#   - Exportar: 9:16, 1080x1920, MP4

# PASO 6: Thumbnail vía Canva MCP
# Especificaciones: 1080x1920, fondo oscuro, hook text grande, color acento rojo/naranja
```

### Scripts de automatización: `src/pipeline/clip_mining.py`
```python
# Funciones disponibles:
# download_clip(url, output_path)
# cut_golden_clip(input_path, start_ts, end_ts, output_path)  
# generate_subtitles(video_path, language='es')
# batch_process(clips_list)
```

---

## FASE 4 — POST-PRODUCCIÓN CHECKLIST (A4)

Cada clip entregado DEBE incluir:

- [ ] `golden_clip_final.mp4` — 9:16, 1080x1920, ≤60s, con subtítulos y overlay
- [ ] `thumbnail.png` — 1080x1920, generado vía Canva MCP (**OBLIGATORIO**)
- [ ] `caption_tiktok.txt` — Hook + contexto + CTA + 5-7 hashtags
- [ ] `caption_facebook.txt` — Versión expandida con más storytelling
- [ ] `hashtags_tiktok.txt` — 5-7 hashtags optimizados
- [ ] `hashtags_facebook.txt` — 3-5 hashtags Facebook
- [ ] `source_credit.txt` — Crédito al creador original (formato: "Vía @[usuario]")
- [ ] `vscore.md` — V-Score calculado por A8

---

## FASE 5 — COMPLIANCE (A9) — GATE OBLIGATORIO

> ⚠️ **SIN APPROVAL DE A9 NO SE DESCARGA NI SE PUBLICA. R1 + R2 activos.**

### Niveles de Licencia de Contenido Fuente

| Nivel | Tipo | ¿Usar? | Condiciones |
|-------|------|--------|-------------|
| 🟢 VERDE | Creative Commons (CC-BY, CC-BY-SA) | SÍ — siempre | Crédito obligatorio. Adaptar para CurioClip. |
| 🟢 VERDE | Dominio público | SÍ — siempre | Sin restricciones. |
| 🟡 AMARILLO | Fair Use / Fair Dealing | SÍ — con transformación | Clip ≤30s + overlay significativo + comentario/contexto + crédito. No reemplaza al original. |
| 🟡 AMARILLO | TikTok Stitch/Duet oficial | SÍ — vía función nativa | Usar la función Stitch o Duet de TikTok. No descargar. |
| 🔴 ROJO | Copyright estándar sin licencia | NO | Rechazar. Buscar alternativa CC o crear contenido original. |
| 🔴 ROJO | Descarga directa de TikTok/YouTube sin permiso | NO | Violación ToS. Rechazar. |

### Criterios Fair Use para un Clip CurioClip:
- ✅ Duración: ≤30 segundos del original
- ✅ Transformación: añade subtítulos, contexto educativo, overlay con datos adicionales
- ✅ Propósito: educativo/informativo (no entretenimiento puro)
- ✅ No sustituye: el clip no reemplaza el valor del video original
- ✅ Crédito: siempre mencionar al creador original en caption

### Si A9 RECHAZA:
1. Buscar el mismo tema en YouTube con filtro Creative Commons
2. Crear contenido original con el mismo dato (Modo A — Outlier Cloning)
3. Buscar B-roll en Pexels/Coverr que cubra el mismo concepto

---

## Estructura de Entregable Semanal (Clip Mining)

```
SEMANA_XX/[DIA]/
├── SOURCE/
│   ├── source_url.txt            ← URL del video fuente
│   ├── golden_clip_raw.mp4       ← Clip descargado sin editar
│   ├── golden_clip_timestamps.txt← [inicio] → [fin] y por qué
│   └── compliance_check.md       ← Aprobación A9
├── OUTPUT/
│   ├── golden_clip_final.mp4     ← Clip editado listo para publicar
│   ├── thumbnail.png             ← OBLIGATORIO — Canva MCP
│   ├── caption_tiktok.txt
│   ├── caption_facebook.txt
│   ├── hashtags_tiktok.txt
│   ├── hashtags_facebook.txt
│   └── vscore.md
└── brief_visual.md               ← Instrucciones de edición CapCut
```

---

## Tabla de Métricas: Viral Score por Plataforma

### TikTok Viral Score (0-100)
```
VS_tiktok = (completion_rate × 35) + (share_rate × 30) + (save_rate × 20) + (comment_rate × 15)

Umbrales:
  ≥80: Video viral confirmado — usar en esta semana
  60-79: Alto potencial — usar si no hay algo mejor
  40-59: Promedio — solo si el nicho es muy específico
  <40: Descartar
```

### YouTube Viral Score (0-100)
```
VS_youtube = (avg_retention% × 35) + (CTR% × 25) + (share_rate × 25) + (like_ratio × 15)
```

### Facebook/Instagram Viral Score (0-100)
```
VS_fb_ig = (share_rate × 40) + (reaction_rate × 30) + (comment_rate × 20) + (view_duration% × 10)
```

---

## Integración con Pipeline Existente

```
M1 DISCOVER (A1) ──────────────────────────────────────────────────────────┐
  MODO A: Outlier Cloning (ver outlier_cloning.md)                         │
  MODO B: Clip Mining — buscar viral_clips + identificar Golden Clip       │
                                                                            ▼
M1.5 COMPLIANCE PRE-CHECK (A9) ────────────────────────────────────────────┤
  Verificar licencia de cada clip ANTES de descargar.                      │
  VERDE/AMARILLO → avanzar. ROJO → buscar alternativa.                     │
                                                                            ▼
M2 ANALYZE (A3 + A9) ──────────────────────────────────────────────────────┤
  Brief de producción: Golden Clip timestamps + hook sugerido + hashtags   │
                                                                            ▼
M3 PRODUCE (A4) ────────────────────────────────────────────────────────────┤
  yt-dlp download → ffmpeg cut → Whisper subtítulos → CapCut post-prod     │
  + Canva MCP thumbnail (OBLIGATORIO)                                       │
                                                                            ▼
M4 PREDICT (A8) → M5 PUBLISH (A6) → M6 LEARN (A7+A1)
```

---

**Enlace:** [[outlier_cloning]] | [[calendario_editorial]] | [[MOC_Pipeline]] | [[MOC_Estrategia]]
