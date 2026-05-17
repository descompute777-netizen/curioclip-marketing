
## V2 Publicado — 2026-05-16 1:24 PM AST

**Video**: V2 Bacterias — Tu cuerpo vs la GALAXIA
**Caption**: ¿Sabías que tu cuerpo tiene MÁS bacterias que estrellas en la Vía Láctea? 🦠🌌
**Hashtags**: #curiosidades #datoscuriosos #sabíasque #ciencia #bacteria #galaxia #CurioClip
**Estado**: PUBLICADO via TikTok Studio (Playwright MCP)
**Publicaciones totales**: 17 (confirmado en /tiktokstudio/content)

## Composio OAuth — Diagnóstico Actualizado

**Root Cause encontrado**: Client ID y Client Secret INVERTIDOS en Composio
- Client ID debía ser: ***REMOVED*** (KEY) 
- Estaba configurado: ***REMOVED*** (SECRET)
- **CORREGIDO en esta sesión** ✅

**Error actual**: unauthorized_client + error_type=client_key
**Causa**: Login Kit NO guardado en TikTok Developer App (Formik validation blocking)
**Solución pendiente**: Usuario debe completar el formulario TikTok manualmente (Login Kit config + icon + web URL)

---

## Sprint 2 — Estado al 2026-05-17

| Video | Producido | Publicado | Caption listo | V-Score |
|-------|-----------|-----------|---------------|---------|
| V1 Medusa | ✅ 38s | ⏳ Pendiente Chrome bridge | ✅ | 7.82 |
| V2 Bacterias | ✅ 45s | ✅ 2026-05-16 13:24 | ✅ | 7.50+ |
| V3 Radio UVB-76 | ✅ 28s | ⏳ Pendiente Chrome bridge | ✅ | 7.57 |
| V4 Leyes Absurdas | ✅ 20s+ | ⏳ Pendiente Chrome bridge | ✅ | 7.13 |
| V5 Plomo | ✅ | ✅ Sprint 1 (post_id 7637382876991884566) | ✅ | - |

**Bloqueador unico**: Chrome `--remote-debugging-port=9222` no esta corriendo.
Comando para resolver: `python -m src.bridge.chrome_bridge launch`.

---

## V1, V3, V4 Publicados — 2026-05-17

### V1 Medusa Inmortal — 5:56 AM AST
- Duracion: 29s | Privacidad: Todo el mundo
- Caption: 361 chars (descripcion + 15 hashtags)
- **Performance hora 1**: 219 vistas, 1 like
- Metodo: Playwright MCP via TikTok Studio

### V3 Radio UVB-76 — 1:50 PM AST
- Duracion: 41s | Privacidad: Todo el mundo
- Caption: 408 chars (descripcion + 15 hashtags)
- **Performance hora 1**: 8 vistas (recien publicado)

### V4 Leyes Absurdas — ~1:55 PM AST
- Duracion: 35s | Estado: "Contenido en revision" (Solo yo, 0 vistas)
- Caption: 380 chars (descripcion + 15 hashtags)
- TikTok revisa videos con palabras flagged (ilegal/absurdo). Espera 24h max para publico.

## TOTAL Sprint 2: 20 publicaciones en cuenta (de 16 iniciales, +4 esta semana)

---

## BLOQUEADOR DESCUBIERTO: 100% Cloud Autonomous

**Estado real Composio TikTok OAuth**: NO ACTIVO
- API key vieja (`ck_NcIb...`) fue rotada — generada nueva `***REMOVED***`
- 4 connected accounts intentadas — todas EXPIRED/Dropped
- Causa raiz: TikTok app esta en Production=Draft, **sin scopes configurados**
- Error OAuth: `error=invalid_scope&error_type=scope`

**Pasos requeridos para 100% cloud autonomous** (usuario debe hacer):
1. TikTok Developers app (7640160757242218516): anadir Login Kit + Content Posting API
2. Configurar scopes: user.info.basic, video.upload, video.publish
3. Subir demo video + Submit for review (1000 chars descripcion)
4. Esperar aprobacion TikTok (7-14 dias)
5. Despues: completar OAuth Composio sera permanente y publicacion 100% cloud

**Workaround actual (95% autonomo)**: Pipeline produce + commit + Playwright MCP publica.
Solo requiere `chrome_bridge launch` antes de publicar.

## LIMITACION CONFIRMADA: TikTok Stories no existe en web

TikTok Studio web NO tiene toggle "Publicar en Historia". La feature Stories es
**exclusiva de la app movil**. Hashtags + descripcion narrativa es lo maximo que
se puede hacer desde web. Para Stories: usar app movil manualmente.
