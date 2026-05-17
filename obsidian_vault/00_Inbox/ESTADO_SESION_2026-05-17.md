---
agente: A0_Director
fecha: 2026-05-17
hora: ~2:35 AM AST
tags: [estado-sesion, continuacion, sprint2, produccion-completa, publicacion-pendiente]
prioridad: ALTA
---

# ESTADO SESION — 2026-05-17

## RESUMEN EJECUTIVO

Continuacion de la sesion 2026-05-16. El pipeline `produce_all` cerro 4 videos
(V1, V2, V3, V4) en 686s y dejo los `*_final.mp4` listos en sus carpetas semanales.
V2 ya esta publicado en TikTok desde el 16-05. **V1, V3 y V4 quedan listos para
publicar con 1 clic** cuando el usuario relance Chrome con `chrome_bridge launch`.
Esta sesion cierra el ciclo de produccion y consolida cambios pendientes en git.

---

## ESTADO REAL DE CADA VIDEO

| Video    | Final MP4         | Thumb | Subs | V-Score | Estado          |
|----------|-------------------|-------|------|---------|-----------------|
| V1 Medusa     | 20.4 MB / 38s | OK    | OK   | 7.82 GO | LISTO PARA PUBLICAR |
| V2 Bacterias  | 13.5 MB / 45s | OK    | OK   | 7.5+ GO | PUBLICADO 16-05 ✅ |
| V3 Radio UVB-76 | 32.2 MB / 28s | OK    | OK   | 7.57 GO | LISTO PARA PUBLICAR |
| V4 Leyes Absurdas | 38.0 MB / 20s+ | OK | OK | 7.13 GO | LISTO PARA PUBLICAR |
| V5 Plomo      | publicado     | -     | -    | -       | PUBLICADO (sesion anterior) ✅ |

Todos los V-Scores superan el umbral 60/100 (6.0/10). Margen de error +/-15%
hasta calibracion (20 publicaciones reales, actualmente 2 = V2 + V5).

---

## CAMBIOS CONSOLIDADOS ESTA SESION (commit pendiente)

### 1. Configs extendidos a duracion final
- `configs/v1_medusa.py`: 22s -> 38s con 8 segmentos b-roll + caption_tiktok
- `configs/v2_bacterias.py`: 18s -> 45s, 10 segmentos + caption_tiktok
- `configs/v3_radio.py`: ajustado a la duracion real del voiceover
- `configs/v4_leyes.py`: ajustado a la duracion real del voiceover

### 2. Subs `.ass` generados por whisper
- `V1_subs.ass`, `V2_subs.ass`, `V3_subs.ass`, `V4_subs.ass` en sus OUTPUT/

### 3. SRT files de transcripcion
- `30_Contenido/audios_generados/V[1-4]_*.srt`

### 4. Thumbnails actualizados
- V1, V2, V4 regenerados con cobertura final del hook

### 5. Carpeta MIERCOLES/ creada (V3 productivo)
- V3_subs.ass + V3_thumbnail.png (V3_final.mp4 esta gitignored por tamano)

### 6. Bridge de publicacion
- `src/bridge/publish_with_caption.py` con templates de caption para V1-V5
- Helper para Playwright CDP: extrae tab TikTok Studio + step plan

### 7. Scripts CDP sandbox TikTok
- `scripts/cdp_sandbox_final.py`: setter React-compatible para Description
- `scripts/cdp_sandbox_fix_errors.py`: fix Formik errors en TikTok dev app

### 8. .gitignore
- Excluidos `sandbox_*.jpg`, `produce_*_output.txt` (artefactos diagnostico)

---

## QUE FALTA PARA PUBLICAR V1/V3/V4

Chrome no esta corriendo con `--remote-debugging-port=9222`. Pasos:

```
python -m src.bridge.chrome_bridge launch
# Esperar que se abra y usuario haya navegado a TikTok Studio
# (sesion ya esta logueada desde sesiones previas)
```

Una vez Chrome listo, publicar cada video:

```
# V1 Medusa
python -m src.bridge.publish_with_caption V1
# El script imprime el caption; el usuario o Playwright MCP sube el .mp4

# V3 Radio
python -m src.bridge.publish_with_caption V3

# V4 Leyes
python -m src.bridge.publish_with_caption V4
```

**Calendario recomendado (A3)**: V1 martes 12:00 CDMX, V3 miercoles 12:00,
V4 jueves 12:00. Si se publican hoy mismo (sabado), espaciar +6h entre videos
para no saturar al algoritmo.

---

## COMPOSIO OAUTH — SIN AVANCES

El flujo OAuth TikTok via Composio sigue bloqueado por el campo Redirect URI
en la app TikTok Dev (Formik anti-automation). El usuario debe configurarlo
manualmente cuando tenga 5 min (ver instrucciones detalladas en
[[ESTADO_SESION_2026-05-16]] seccion "Instrucciones manuales").

**Workaround actual**: publicar via Playwright CDP en TikTok Studio
(ya validado en V2 y V5).

---

## KPIs SPRINT 2 (al cierre)

| KPI | Actual | Meta Sprint 2 |
|-----|--------|--------------|
| Videos producidos | 4/4 | 4 ✅ |
| Videos publicados | 1/4 (V2) | 4 |
| V-Score promedio | 7.51/10 | >=7.5 ✅ |
| Cobertura semana | 4 dias | 5 dias |
| Pipeline produce_all funcional | ✅ | ✅ |
| Composio OAuth activo | ❌ | ✅ (manual user) |

---

## SIGUIENTE SESION — INSTRUCCION PARA CLAUDE

1. Leer este archivo + [[ESTADO_SESION_2026-05-16]].
2. Verificar si usuario relanzo Chrome (`curl localhost:9222/json`).
3. Si SI: publicar V1, V3, V4 secuencialmente con Playwright MCP.
4. Tras cada publicacion: actualizar [[PUBLICACIONES_LOG]] y abrir M6 LEARN
   a 24h y 72h.
5. Si NO: pedir al usuario que ejecute `chrome_bridge launch`.
6. Despues: arrancar M1 DISCOVER para SEMANA_03.

**Links rapidos**:
- [[MOC_Master]] | [[SEMANA_02_2026-05-13_a_2026-05-19]] | [[PUBLICACIONES_LOG]]
- TikTok Studio: `https://www.tiktok.com/tiktokstudio/upload`
