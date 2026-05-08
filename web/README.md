# CurioClip Calendar

Calendario web del sistema CurioClip — vista semanal de contenido con slots clickables que muestran video, caption, hashtags, V-Score y métricas reales vs predichas.

## Local development

```bash
cd web
npm install
npm run dev
# abre http://localhost:3000
```

## Build estático

```bash
npm run build
# output en web/out/ — desplegable a cualquier hosting estático
```

## Deploy a Vercel (gratis)

```bash
npx vercel --prod
```

O via GitHub:
1. Push del proyecto a GitHub
2. Importar en vercel.com
3. Root directory: `web`
4. Framework: Next.js
5. Deploy → obtienes URL pública gratis (ej: `curioclip-calendar.vercel.app`)

## Datos

El calendario lee `web/data/schedule.json`. Para actualizarlo automáticamente desde Obsidian:

```bash
python ../src/pipeline/sync_calendar.py
```

(script pendiente — convierte SEMANAS/*/BRIEFING_SEMANAL.md a schedule.json)

## Stack

- Next.js 15 (export estático)
- React 18
- Tailwind CSS
- 0 backend → 100% gratis hostable
