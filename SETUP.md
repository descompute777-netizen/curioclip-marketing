# CurioClip — Setup Guide (Sistema Autónomo)

## Estado del Sistema
- **GitHub Actions:** 3 workflows activos (weekly-sprint, outlier-hunt, daily-publish)
- **Motor LLM:** Gemini 2.5-Flash GRATIS (primario) | Anthropic Claude Haiku (fallback)
- **TTS:** edge-tts GRATIS (Microsoft Edge Neural)
- **TikTok:** Composio OAuth pendiente
- **Costo estimado:** $0/mes

---

## PASO 1 — Configurar GitHub Secrets (5 min)

### Opción A: Script automático (recomendado)

1. Crea un PAT en GitHub: https://github.com/settings/tokens/new
   - Nombre: "CurioClip Secrets"
   - Expiration: 90 days
   - Scopes: solo `repo`

2. Ejecuta:
   ```
   python scripts/setup_github_secrets.py --token TU_PAT_TOKEN
   ```

### Opción B: Manual en GitHub UI (2 min)

Ve a: https://github.com/descompute777-netizen/curioclip-marketing/settings/secrets/actions

Agrega estos secrets:

| Secret | Valor |
|--------|-------|
| `ANTHROPIC_API_KEY` | `***REMOVED***...` (en .env) |
| `GEMINI_API_KEY` | `***REMOVED***` (en .env) |
| `COMPOSIO_API_KEY` | `ck_NcIb61zkczdt9WOrGTYQ` (en .env) |
| `PEXELS_API_KEY` | Obtener GRATIS en pexels.com/api |

---

## PASO 2 — Conectar TikTok a Composio (3 min, solo 1 vez)

Este paso es el que habilita la publicación automática en TikTok.

1. Ve a: https://app.composio.dev
2. Login / Registro (GRATIS)
3. Ve a **Connected Accounts** → **Add Connection**
4. Busca **TikTok** → Click **Connect**
5. Se abre la ventana de OAuth de TikTok
6. Inicia sesión con tu cuenta TikTok de CurioClip
7. Autoriza el acceso
8. **Listo.** Composio guarda los tokens de forma segura

> **Nota sobre privacidad:** Al conectar, TikTok puede limitar la visibilidad a `SELF_ONLY`
> si la aplicación de Composio no está auditada por TikTok. Si pasa esto:
> - Los videos se publican pero son visibles solo para ti
> - Puedes hacerlos públicos manualmente desde TikTok Studio (10 segundos)
> - Alternativa: solicitar auditoria en developers.tiktok.com

---

## PASO 3 — Obtener Pexels API Key (2 min, gratis)

1. Ve a: https://www.pexels.com/api/
2. Registro gratuito
3. Dashboard → API Key
4. Agrega como GitHub Secret: `PEXELS_API_KEY`

---

## PASO 4 — Aplicar TikTok Content API (opcional, acelera aprobación)

Para publicación 100% pública sin restricciones:

1. Ve a: https://developers.tiktok.com/products/content-posting-api/
2. Click "Apply for Access"
3. Rellena el formulario:
   - App Name: CurioClip
   - Use case: Content creation automation
   - Category: Education / Entertainment
   - Expected users: Solo la cuenta CurioClip
4. Submit → respuesta en 1-4 semanas

---

## Cómo funciona el sistema autónomo

```
LUNES 09:07 UTC — weekly-sprint.yml corre automáticamente:
  ↓
  Gemini 2.5-Flash genera 25 guiones + plan semanal
  ↓
  edge-tts genera voiceover MP3 para top-7 guiones
  ↓
  Pexels API descarga B-roll CC0
  ↓
  ffmpeg compone 7 videos 9:16 1080x1920
  ↓
  GitHub Release sube los 7 videos (URLs públicas)
  ↓
  schedule.json se actualiza con URLs y horarios

CADA HORARIO DE PUBLICACIÓN — daily-publish.yml corre:
  Lun 12:00 | Mar 19:00 | Mié 20:00 | Jue 12:00
  Vie 20:00 | Sáb 12:00 | Dom 20:00 (todos en CDMX)
  ↓
  Lee schedule.json → encuentra el video de hoy
  ↓
  Composio: TIKTOK_PUBLISH_VIDEO(url, caption)
  ↓
  Monitor de status con backoff exponencial
  ↓
  Marca como published=true → commit → push

DOMINGO 20:03 UTC — outlier-hunt.yml corre:
  ↓
  Gemini analiza competidores + extrae 25 outliers
  ↓
  Genera 25 guiones para el sprint siguiente
  ↓
  Commit a vault

CADA 2h — analytics.yml corre:
  ↓
  Gemini analiza métricas disponibles
  ↓
  Actualiza snapshot en 50_Analitica/
```

---

## Verificar que todo funciona

```powershell
# Test Gemini (gratis)
$env:GEMINI_API_KEY = "***REMOVED***"
python scripts/autonomous/daily_metrics.py

# Test voiceover (gratis, sin API key)
python scripts/autonomous/generate_voiceover.py --text "Hola mundo desde CurioClip"

# Test Composio TikTok (requiere OAuth completado)
$env:COMPOSIO_API_KEY = "ck_NcIb61zkczdt9WOrGTYQ"
python -c "from composio_openai import ComposioToolSet; ts = ComposioToolSet(api_key='ck_NcIb61zkczdt9WOrGTYQ'); print('Composio OK')"

# Verificar workflows en GitHub
# https://github.com/descompute777-netizen/curioclip-marketing/actions
```

---

## Costo real del sistema

| Componente | Costo | Límite gratis |
|-----------|-------|---------------|
| Gemini 2.5-Flash | **$0** | 1M tokens/día |
| edge-tts | **$0** | Ilimitado |
| Pexels API | **$0** | 25K requests/mes |
| GitHub Actions | **$0** | 2,000 min/mes |
| GitHub Releases | **$0** | Storage del repo |
| Composio | **$0** | Plan gratuito disponible |
| Anthropic API | **$0** | Solo como fallback |
| **TOTAL** | **$0/mes** | — |

---

## Troubleshooting

**El video se publica como SELF_ONLY (solo visible para mí):**
→ Composio aún no está auditado por TikTok. Publicación funciona pero con privacidad limitada.
→ Solución inmediata: desde TikTok Studio, cambiar manualmente a "Público" (10 seg)
→ Solución permanente: solicitar auditoria en developers.tiktok.com

**GitHub Actions falla con "sin LLM disponible":**
→ Verifica que GEMINI_API_KEY esté en GitHub Secrets (Settings → Secrets → Actions)

**ffmpeg falla en GitHub Actions:**
→ El step `Install system dependencies` instala ffmpeg automáticamente. Verificar logs.

**El video no se produce (sin B-roll):**
→ Agregar PEXELS_API_KEY en GitHub Secrets
→ O configurar Pexels API gratis en pexels.com/api
