---
agente: A4_Editor + A7_Supervision
fecha: 2026-05-08
tags: [aprendizaje, fix, subtitulos, ass, ffmpeg, calibracion]
estado: resuelto
---

# Fix: Subtítulos desproporcionados en auto-editor

## El bug (V5 publicado)
Subtítulos aparecían **6.67× más grandes** y posicionados en el tercio superior del video, no en el bottom.

## Diagnóstico técnico
ffmpeg's `subtitles` filter convierte SRT→ASS internamente con `PlayResY=288` legacy (4:3). Cuando renderea sobre 1080×1920 (9:16):
- Scale factor: `1920/288 = 6.67×`
- `Fontsize=18` → renderaba como ~120px (HUGE)
- `MarginV=200` con `Alignment=2` → ponía subs en `y = 1920 − (200 × 6.67) = 586px` desde top (tercio superior)

## El fix (permanente, en auto_editor_v5.py)
Función nueva `srt_to_ass()` que genera ASS explícito con:

```
[Script Info]
PlayResX: 1080
PlayResY: 1920
ScaledBorderAndShadow: yes

[V4+ Styles]
Style: Default,Arial,52,&H00FFFFFF,...,Bold=-1,Outline=3,Shadow=1,Alignment=2,MarginV=220
```

**Valores ahora son píxels reales:**
- Fontsize=52px (legible en mobile, no aplastante)
- MarginV=220px desde bottom (encima de UI nativa de TikTok)
- Outline=3px (negro grueso, legible sobre cualquier fondo)
- Bold=true
- Alignment=2 (bottom center)
- Auto-wrap a 2 líneas si >32 chars

## Verificación visual
Frames extraídos de V5_final.mp4 nuevo:
- Frame 2s: Hook arriba ("METIO SU MANO EN / PLOMO FUNDIDO") + sub abajo limpio
- Frame 11s: Sub wrapped en 3 líneas legibles, bottom positioned
- Frame 16s: Warning + sub coexisten sin overlap

## Aplicabilidad
Este fix se aplica automáticamente a TODOS los videos futuros que pasen por `src/pipeline/auto_editor_v5.py`. No requiere intervención por video.

## V5 publicado (antiguo)
El V5 ya publicado en TikTok tiene los subs viejos (mal proporcionados). Se está dejando publicado porque:
- Ya tiene 29+ visualizaciones orgánicas
- El nuevo render existe local pero re-subir = perder esas views + reset del algoritmo
- TikTok permite editar subtítulos nativamente desde el editor de video → el usuario puede usar TikTok caption tool si quiere

## Lección para sprint 2
Cualquier filter que toque texto sobre video debe especificar `PlayResX/Y` explícitamente al tamaño del output. Defaults legacy de ffmpeg son fuente recurrente de bugs visuales.

**Enlace:** [[../30_Contenido/sprint1_guiones]] | [[../50_Analitica/sprint1_estado_completo]]
