---
agente: A0_Director
fecha: 2026-05-15
hora: ~14:30 AST
tags: [estado-sesion, continuacion, playwright-mcp, tiktok-oauth, composio]
prioridad: CRITICA
---

# ESTADO COMPLETO DE SESION — 2026-05-15

> PARA CONTINUAR: Lee este archivo COMPLETO antes de hacer cualquier cosa.
> Usa `python -m src.bridge.chrome_bridge launch` para restaurar Chrome si no está corriendo.

---

## RESUMEN EJECUTIVO

Sistema CurioClip en proceso de configuración final. El 95% del sistema autónomo está operativo. Quedan 2 tareas críticas para completar el 100%:

1. **TikTok Developer App** — Añadir Login Kit + Redirect URI (para OAuth funcional)
2. **Composio TikTok OAuth** — Completar la autorización (bloqueada por error `unauthorized_client`)

---

## ARQUITECTURA DEL SISTEMA (QUÉ YA FUNCIONA)

### GitHub Actions (100% en la nube, corren solos)
| Workflow | Schedule | Estado |
|---------|---------|--------|
| `weekly-sprint.yml` | Lunes 09:07 UTC | ✅ ACTIVO |
| `outlier-hunt.yml` | Domingo 20:03 UTC | ✅ ACTIVO |
| `analytics.yml` | Cada 2h | ✅ ACTIVO |
| `daily-publish.yml` | 7 horarios CDMX/semana | ✅ ACTIVO |

### Secrets configurados en GitHub
- `ANTHROPIC_API_KEY` ✅
- `GEMINI_API_KEY` ✅
- `COMPOSIO_API_KEY` ✅
- `PEXELS_API_KEY` ✅
- `OPENAI_API_KEY` ✅

### Scripts autónomos (todos con Gemini FREE)
- `scripts/autonomous/weekly_sprint.py` ✅
- `scripts/autonomous/outlier_hunt.py` ✅
- `scripts/autonomous/daily_metrics.py` ✅
- `scripts/autonomous/publish_tiktok.py` ✅
- `scripts/autonomous/cloud_produce.py` ✅
- `scripts/autonomous/upload_release.py` ✅

### Contenido producido
- **V5 Plomo Fundido**: PUBLICADO en TikTok ✅ (post ID: `7637382876991884566`)
- **V1-V4**: MP3 listos, configs creados, falta correr `produce_all.py`
- **25 guiones Sprint 2**: En `obsidian_vault/30_Contenido/cola/`
- **V-Scores V1-V4**: Calculados y documentados

---

## ESTADO ACTUAL DE TIKTOK DEVELOPER APP

### App CurioClip creada
- **App ID**: `7640160757242218516`
- **URL**: `https://developers.tiktok.com/app/7640160757242218516`
- **Estado**: Draft (Production) / Sandbox disponible
- **Client Key**: `***REMOVED***` ← CORRECTO
- **Client Secret**: `***REMOVED***` ← CORRECTO

### Lo que falta en TikTok App
1. **Añadir Login Kit** como producto (Products → Add Login Kit)
2. **Configurar Redirect URI en Login Kit**: `https://backend.composio.dev/api/v1/auth-apps/add`
3. **Añadir Content Posting API** (para publicar videos en el futuro)
4. **Añadir scopes**: `video.upload`, `video.publish`

### Cómo hacerlo con Playwright MCP
```
[Playwright MCP] navegar a https://developers.tiktok.com/app/7640160757242218516/sandbox
[Playwright MCP] click en "Products" en el sidebar IZQUIERDO (no el header nav)
[Playwright MCP] click en "Add products" 
[Playwright MCP] seleccionar "Login Kit"
[Playwright MCP] en Login Kit, buscar campo de Redirect URI
[Playwright MCP] fill redirect_uri = "https://backend.composio.dev/api/v1/auth-apps/add"
[Playwright MCP] click Save
```

---

## ESTADO ACTUAL DE COMPOSIO TIKTOK

### Auth Config creado
- **Auth Config ID**: `ac_zehMCGYPXa3C`
- **Nombre**: `tiktok-meyelc`
- **URL en Composio**: `https://dashboard.composio.dev/descompute777_workspace/descompute777_workspace_first_project/auth-configs/ac_zehMCGYPXa3C`
- **Estado**: Enabled ✅
- **Client ID configurado**: `***REMOVED***` ← (recientemente corregido, estaba duplicado)
- **Client Secret**: `***REMOVED***` ← CORRECTO
- **Redirect URI en Composio**: `https://backend.composio.dev/api/v1/auth-apps/add` ✅

### Connected Account creada pero no activa
- **Account ID**: `ca_er2t7i60q57T`
- **Entity ID**: `curioclip`
- **Estado**: Initializing (OAuth no completado)

### Por qué falló el OAuth
- TikTok devolvió `error=unauthorized_client` + `error_type=client_key`
- El client_key en la URL era `***REMOVED***` (el SECRET, invertido)
- Estaba corregido en Composio al `***REMOVED***` (correcto)
- Pero TikTok no reconoce la app porque el Redirect URI NO está configurado en TikTok Developers

### Secuencia para completar OAuth con Playwright MCP
```
PASO 1: Configurar TikTok App (ver sección anterior)
PASO 2: En Composio → Auth Configs → tiktok-meyelc
PASO 3: Click "+ Connect Account"
PASO 4: User ID: "curioclip"
PASO 5: Click "Connect"
PASO 6: Se abre pestaña de TikTok OAuth → autenticarse con cuenta CurioClip
PASO 7: TikTok redirige a Composio → OAuth completado
```

---

## PLAYWRIGHT MCP — INSTALACIÓN Y CONFIGURACIÓN

### Ya configurado en .mcp.json
```json
{
  "playwright": {
    "command": "cmd",
    "args": ["/c", "npx", "@playwright/mcp@latest", "--cdp-endpoint", "http://localhost:9222"],
    "description": "Playwright MCP conectado al Chrome con sesiones activas"
  },
  "playwright-standalone": {
    "command": "cmd",
    "args": ["/c", "npx", "@playwright/mcp@latest", "--browser", "chrome",
             "--user-data-dir", "C:/Users/Nick/AppData/Local/chrome-curioclip"],
    "description": "Playwright MCP standalone con perfil CurioClip"
  }
}
```

### Instalar antes de usar (solo 1 vez)
```powershell
npx playwright install chromium
```

### Herramientas disponibles en Playwright MCP
| Tool | Uso |
|------|-----|
| `browser_navigate` | Navegar a URL |
| `browser_click` | Click en elemento por selector o texto |
| `browser_fill` | Llenar input |
| `browser_select_option` | Seleccionar dropdown |
| `browser_screenshot` | Tomar screenshot |
| `browser_snapshot` | Ver árbol de accesibilidad |
| `browser_type` | Tipear texto |
| `browser_press_key` | Presionar tecla |
| `browser_new_tab` | Abrir nueva pestaña |
| `browser_tab_select` | Cambiar de pestaña |
| `browser_evaluate` | Ejecutar JavaScript |

### Ventaja vs CDP manual
- **Snapshot accessibility** = 2-5KB vs 100KB screenshots
- **Sin coordenadas** — usa selectores y texto, no píxeles
- **React-compatible** — entiende componentes React nativamente
- **Iframes automáticos** — maneja iframes transparentemente

---

## CHROME BRIDGE — ESTADO ACTUAL

### Chrome corriendo en CDP port 9222
```powershell
# Verificar
python -c "import urllib.request,json; print(json.loads(urllib.request.urlopen('http://localhost:9222/json/version').read())['Browser'])"

# Si no está corriendo:
python -m src.bridge.chrome_bridge launch
```

### Chrome lanzado con flags
```
--remote-debugging-port=9222
--remote-allow-origins=*
--user-data-dir=C:\Users\Nick\AppData\Local\chrome-curioclip
```

### Pestañas importantes en Chrome ahora mismo
| URL | Estado |
|-----|--------|
| `developers.tiktok.com/app/7640160757242218516` | App CurioClip |
| `dashboard.composio.dev/.../auth-configs/ac_zehMCGYPXa3C` | Auth Config manage |
| `tiktok.com/tiktokstudio` | Studio logueado |
| `pexels.com/api/` | Joan logueada |

---

## VARIABLES DE ENTORNO (.env)

```
GEMINI_API_KEY=***REMOVED***
ANTHROPIC_API_KEY=***REMOVED***...
COMPOSIO_API_KEY=ck_NcIb61zkczdt9WOrGTYQ
PEXELS_API_KEY=k0iMZlUKh9p7jpNUKjRQQ4eCPcXQ7YW4ufpBkEoZOCbKuDOt9x3xVqjR
TIKTOK_CLIENT_KEY=***REMOVED***
TIKTOK_CLIENT_SECRET=***REMOVED***
```

---

## PLAN EXACTO PARA CONTINUAR (USAR PLAYWRIGHT MCP)

### Paso 1 — Verificar Chrome
```
Playwright MCP: browser_navigate to http://localhost:9222/json/version
```
Si falla: `python -m src.bridge.chrome_bridge launch`

### Paso 2 — Añadir Login Kit en TikTok Developers
```
Playwright MCP: browser_navigate https://developers.tiktok.com/app/7640160757242218516/sandbox
Playwright MCP: browser_snapshot (ver estado actual)
Playwright MCP: buscar "Products" en sidebar → click
Playwright MCP: click "Add Login Kit" o "Add product" → seleccionar Login Kit
Playwright MCP: en configuración de Login Kit → añadir Redirect URI:
  https://backend.composio.dev/api/v1/auth-apps/add
Playwright MCP: click Save/Confirm
```

### Paso 3 — Completar OAuth en Composio
```
Playwright MCP: browser_navigate https://dashboard.composio.dev/.../auth-configs/ac_zehMCGYPXa3C
Playwright MCP: browser_snapshot (ver botones)
Playwright MCP: click "+ Connect Account"
Playwright MCP: fill User ID = "curioclip"
Playwright MCP: click "Connect"
[Se abre pestaña de TikTok OAuth]
Playwright MCP: browser_tab_select (ir a pestaña TikTok)
Playwright MCP: browser_snapshot (ver botones de autorización)
Playwright MCP: click "Authorize" o "Allow"
[OAuth completo → Composio muestra cuenta conectada]
```

### Paso 4 — Producir videos V2-V4
```powershell
python -m src.pipeline.produce_all
```

### Paso 5 — Publicar V2 en TikTok Studio
```
Playwright MCP: browser_navigate https://www.tiktok.com/tiktokstudio/upload
Playwright MCP: upload el video V2 desde OUTPUT/
```

---

## KPIs ACTUALES vs METAS

| KPI | Actual | Meta Sprint 2 |
|-----|--------|--------------|
| Videos publicados | 1 (V5) | 6 |
| Seguidores TikTok | ~0-50 | +300 |
| Composio TikTok | Initializing | ACTIVE |
| Playwright MCP | Configurado | Operativo |
| V-Score promedio | 7.72/10 | ≥7.5 ✅ |

---

## SCRIPTS RELEVANTES PARA CONTINUAR

```
src/bridge/chrome_bridge.py        — Lanzar/verificar Chrome
src/bridge/composio_connect_account.py — Connect Account en Composio
src/pipeline/produce_all.py        — Producir V1-V4
src/bridge/publish_v5.py           — Publicar en TikTok Studio
scripts/autonomous/publish_tiktok.py — Publicar vía Composio (cuando OAuth esté listo)
```

---

## INSTRUCCION PARA CLAUDE EN NUEVA SESION

Al inicio de la próxima sesión, hacer lo siguiente:

1. **Leer este archivo completo**
2. **Usar Playwright MCP** (ya configurado en .mcp.json) — es mucho más confiable que CDP manual
3. **NO usar scripts CDP** — fueron reemplazados por Playwright MCP
4. **Prioridad 1**: Añadir Login Kit + Redirect URI en TikTok App
5. **Prioridad 2**: Completar OAuth de Composio via Playwright MCP
6. **Prioridad 3**: Correr `produce_all.py` para V2-V4
7. **NO modificar** el Auth Config de Composio — ya está correcto

**Enlace**: [[MOC_Master]] | [[sprint2_briefing]] | [[SEMANA_02_2026-05-13_a_2026-05-19/BRIEFING_SEMANAL]]
