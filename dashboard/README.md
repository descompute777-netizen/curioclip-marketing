# CurioClip Mission Control

Dashboard operativo multi-cuenta para la agencia.

## Quick start

```bash
python -m dashboard.run
```

Auto-instala dependencias, hace seed desde `obsidian_vault/`, abre el navegador
en `http://localhost:8000`.

Flags:
- `--port 8080` — puerto custom
- `--no-browser` — no abrir navegador
- `--no-seed` — saltar el seed inicial

## Secciones

1. **🏠 Overview** — KPIs en vivo, actividad reciente, próximas 24h
2. **👥 Cuentas** — multi-cuenta CRUD (TikTok / FB / IG / YT)
3. **📅 Calendario** — FullCalendar con eventos coloreados por status
4. **🎬 Pipeline** — Kanban M1→M6 (Draft → Published → Archived)
5. **🧠 Simulaciones** — V-Score predicho vs real + scatter plot
6. **📈 Crecimiento** — followers / views / ER por cuenta
7. **💡 Sugerencias** — inbox de URLs con auto-scoring
8. **🤖 Automatización** — cola de los 10 agentes + triggers manuales
9. **🎓 Aprendizaje** — calibración + patrones detectados
10. **📋 Briefings** — resúmenes ejecutivos semanales

## Loop autónomo de evolución

```
Publicar video → poll_metrics (15min) → metrics_snapshots
              → compare predicted vs actual → calibration_log
              → scan_patterns (hooks/niches) → learn_patterns
              → siguiente pick → automation_queue
              → trigger producción → ciclo se repite
```

## Endpoints clave

| Endpoint | Método | Función |
|----------|--------|---------|
| `/` | GET | Home (Overview) |
| `/partial/{section}` | GET | HTMX-loaded section |
| `/api/accounts` | GET/POST | CRUD cuentas |
| `/api/videos` | GET/POST/PATCH | CRUD videos |
| `/api/calendar/events` | GET | FullCalendar feed |
| `/api/suggestions` | GET/POST | Inbox sugerencias |
| `/api/automation/{id}/run` | POST | Ejecutar tarea manual |
| `/api/learn/calibrate` | POST | Recalcular MAE/RMSE |
| `/api/learn/scan_patterns` | POST | Detectar patrones |
| `/api/seed/run` | POST | Re-poblar desde vault |

## Arquitectura

```
dashboard/
├── app.py          # FastAPI con routers
├── db.py           # SQLite + schema (10 tablas)
├── models.py       # Pydantic
├── services.py     # poll_metrics, calibrate, scan_patterns
├── seed.py         # importa desde obsidian_vault
├── run.py          # launcher
├── curioclip.db    # SQLite (auto-creado)
├── templates/
│   ├── base.html
│   ├── index.html
│   └── partials/*.html
└── static/
    ├── style.css
    └── app.js
```

## Stack

- **Backend**: FastAPI + SQLite (stdlib)
- **Frontend**: Jinja2 + HTMX + Alpine.js + Tailwind (CDN)
- **Charts**: Chart.js 4.4 + FullCalendar 6.1 (CDN)
- **Sin build step**, sin Node, sin React. Todo Python.

## Integración con el pipeline existente

- `produce_all` se invoca via `/api/pipeline/produce_all`
- `chrome_bridge` polleado via `/api/pipeline/poll_metrics`
- Configs `configs/v*.py` se importan al seed
- Schedules `obsidian_vault/40_Publicacion/schedule_sprint*.json` se importan al seed
- Cola de guiones `obsidian_vault/30_Contenido/cola/` → suggestions
