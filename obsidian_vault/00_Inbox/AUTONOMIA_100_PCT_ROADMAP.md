---
agente: A0_Director + A6_Operaciones + A9_Compliance
fecha: 2026-05-17
tags: [autonomia, roadmap, composio, tiktok-api, bloqueadores]
prioridad: CRITICA
---

# Roadmap a 100% Cloud Autonomous — Diagnostico Real

## ESTADO ACTUAL: 95% AUTONOMO

| Modulo | Estado | Lo que funciona | Lo que falta |
|--------|--------|-----------------|--------------|
| M1 DISCOVER | ✅ 100% | outlier-hunter agent, web search | - |
| M2 ANALYZE | ✅ 100% | V-Score engine, compliance checks | - |
| M3 PRODUCE | ✅ 100% local | FFmpeg + Whisper + Pexels + Canva | Higgsfield API key (opcional) |
| M4 PREDICT | ✅ 100% heuristico | VisualEyes local, MiroFish opcional | Calibracion (20+ pubs) |
| M5 PUBLISH | 🟡 95% | Playwright MCP TikTok Studio web | Composio TikTok OAuth real |
| M6 LEARN | 🟡 70% | TikTok Studio scraping | analytics auto-comparado a predict |

## EL BLOQUEADOR REAL DE M5

**No es codigo, no es Claude — es TikTok**: la app dev no esta aprobada.

### Estado verificado 2026-05-17 ~2:00 AM AST via Playwright MCP

1. **API key Composio**: Vieja key `ck_NcIb61zkczdt9WOrGTYQ` ya no existe.
   Nueva key generada: `***REMOVED***` (en `.env`)

2. **Composio Auth Config TikTok** (`ac_zehMCGYPXa3C`):
   - Status: Enabled ✅
   - Client ID: `sbawcx9ct1jw64945j` (cambio reciente)
   - Scopes: user.info.basic, user.info.profile, user.info.stats, video.list, video.upload, video.publish

3. **Connected Accounts** (todas EXPIRED):
   - ca_EMxJzIeti70H — curioclip-sandbox — 8h ago
   - ca_Le4vghSSWI93 — pg-test — 14h ago
   - ca_l9ug_upOQA3p — curioclip — 14h ago
   - ca_er2t7i6Oq57T — curioclip — 1d ago

4. **TikTok App** (`7640160757242218516`):
   - Production: **Draft** (no aprobada)
   - **"No scopes yet"** — la app no tiene productos ni scopes configurados
   - Result: OAuth retorna `error=invalid_scope` siempre

## CAMINO A 100%

### Fase 1 — Configurar TikTok App (1-2 horas usuario)

URL: https://developers.tiktok.com/app/7640160757242218516/pending

1. **Productos**: anadir "Login Kit" + "Content Posting API"
2. **Scopes**: marcar todos los 6 que Composio espera
3. **Basic info**:
   - App icon 1024x1024 (ya generado: `curioclip_icon.png` en raiz)
   - Descripcion >100 chars (ya escrita en config)
   - Terms of Service URL: ya configurada
   - Privacy Policy URL: ya configurada
4. **App Review**:
   - Demo video ~30s mostrando como CurioClip usa OAuth + publica
   - Descripcion del flujo (1000 chars)
5. **Submit for review**

### Fase 2 — Esperar TikTok (7-14 dias, no podemos acelerar)

### Fase 3 — Activar OAuth permanente (5 minutos)

```python
# Despues de aprobacion TikTok, ejecutar:
from composio import Composio
c = Composio(api_key='***REMOVED***')
result = c.connected_accounts.initiate(
    user_id="curioclip",
    auth_config_id="ac_zehMCGYPXa3C",
)
# Abrir result.redirect_url en Chrome → autorizar
# Connection queda ACTIVE permanente (no EXPIRED)
```

### Fase 4 — Cron daily-publish.yml usa Composio (sin Chrome)

```yaml
# .github/workflows/daily-publish.yml ya existe.
# Llama a scripts/autonomous/publish_tiktok.py que usa Composio.
# 100% cloud — corre en GitHub Actions runners.
```

## QUE FUNCIONA HOY (95% autonomo)

1. GitHub Actions corre semanalmente — produce videos
2. Pipeline `produce_all.py` genera MP4 + thumbnail + subs
3. Usuario: 1 comando `python -m src.bridge.chrome_bridge launch`
4. Claude usa Playwright MCP → publica en TikTok Studio web
5. Captions optimizados + hashtags + V-Score validado

## QUE NO FUNCIONA HOY

1. **TikTok Stories desde web**: NO existe la opcion en TikTok Studio web.
   Stories es exclusivo de la app movil — no se puede automatizar.
2. **Publicacion 100% cloud sin Chrome**: requiere OAuth Composio activo
   → bloqueado por TikTok app review.

## REFERENCIAS

- [[ESTADO_SESION_2026-05-17]]
- [[PUBLICACIONES_LOG]]
- [[MOC_Master]]
- TikTok App: https://developers.tiktok.com/app/7640160757242218516/pending
- Composio Auth: https://dashboard.composio.dev/.../auth-configs/ac_zehMCGYPXa3C
- Nueva API key (NO commitear): `***REMOVED***`
