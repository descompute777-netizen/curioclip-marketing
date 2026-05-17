
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
