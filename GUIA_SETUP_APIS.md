# Guía de Setup — APIs y MCPs del Proyecto CurioClip
## Pasos exactos para hacer correr el sistema al 100%

**Fecha:** 2026-05-06 | **Proyecto:** CurioClip — Agencia de Marketing IA

---

## Resumen Rápido — Prioridades

| # | Herramienta | Para qué | Tiempo | Costo | Prioridad |
|---|------------|---------|--------|-------|-----------|
| 1 | LLM API Key (OpenAI o Claude) | MiroFish — simulación social | 5 min | ~$5-10/mes | CRÍTICO |
| 2 | TikTok Pro (cuenta) | Analytics de retención | 2 min | Gratis | CRÍTICO |
| 3 | VisualEyes (cuenta) | Heatmap de atención visual | 3 min | Gratis | CRÍTICO |
| 4 | Composio + TikTok | MCP de TikTok (analytics + publicar) | 15 min | Gratis / $49/mes | IMPORTANTE |
| 5 | Meta Page Access Token | Publicar en Facebook + métricas | 30 min | Gratis | IMPORTANTE |
| 6 | Meta Ads MCP Oficial | MCP nativo de Meta (alternativa más fácil al #5) | 10 min | Gratis (beta) | IMPORTANTE |
| 7 | TikTok Developer App | Content Posting API directa | 30 min + 2-4 semanas aprobación | Gratis | IMPORTANTE |
| 8 | Higgsfield AI Video | Generación de video con IA | 5 min | Consultar precio | OPCIONAL |
| 9 | Microsoft Clarity | Heatmaps post-publicación | 10 min | Gratis | OPCIONAL |
| 10 | Miro API | Dashboard visual de estrategia | 10 min | Gratis (básico) | OPCIONAL |

---

## Dónde guardar las credenciales

Crea el archivo `.env` en la raíz del proyecto:
```
C:\Users\Nick\Desktop\AGENCIA DE MARKETING\.env
```

Plantilla del archivo `.env`:
```env
# LLM para MiroFish
OPENAI_API_KEY=sk-...

# Meta
META_PAGE_ACCESS_TOKEN=EAAx...
META_PAGE_ID=tu_id_de_pagina
META_AD_ACCOUNT_ID=act_...

# TikTok
TIKTOK_ACCESS_TOKEN=...
TIKTOK_CLIENT_KEY=...
TIKTOK_CLIENT_SECRET=...

# Composio (alternativa TikTok)
COMPOSIO_API_KEY=...

# Higgsfield
HIGGSFIELD_API_KEY=hf_...

# MiroFish (URL del backend si no es localhost)
MIROFISH_URL=http://localhost:5001

# Miro (opcional)
MIRO_API_TOKEN=...
MIRO_BOARD_ID=...
```

> **IMPORTANTE:** Nunca subas el archivo `.env` a GitHub. Está en `.gitignore` por defecto.

---

## BLOQUE 1 — CRÍTICO (hacer hoy, el proyecto no corre sin esto)

---

### 1. LLM API Key para MiroFish

**Por qué:** MiroFish necesita un LLM para generar los 2000 agentes virtuales que simulan cómo se propaga tu contenido. Sin esta key, A8 no puede hacer simulaciones sociales.

**Dos opciones — elige una:**

#### Opción A: OpenAI (recomendado por compatibilidad)
1. Ir a: **platform.openai.com**
2. Crear cuenta o iniciar sesión
3. Menú izquierdo → **API Keys**
4. Clic en **"+ Create new secret key"**
5. Nombre: `curioclip-mirofish`
6. Copiar la key (empieza con `sk-`)
7. Ir al archivo: `vendor\MiroFish\backend\.env.example`
8. Copiar ese archivo y renombrarlo a `.env`
9. Pegar la key:
   ```
   OPENAI_API_KEY=sk-tu-key-aqui
   ```

**Costo:** GPT-4o-mini cuesta ~$0.15/millón de tokens. Para una simulación de 2000 agentes, estima $0.50-2.00 por simulación.

#### Opción B: Anthropic (Claude API)
1. Ir a: **console.anthropic.com**
2. Crear cuenta → **API Keys** → **Create Key**
3. Copiar la key (empieza con `sk-ant-`)
4. En `vendor\MiroFish\backend\.env`:
   ```
   ANTHROPIC_API_KEY=sk-ant-tu-key-aqui
   ```

**Tiempo total:** 5 minutos

---

### 2. TikTok Pro — Activar Analytics

**Por qué:** Sin cuenta Pro, TikTok no muestra métricas de retención segundo a segundo. A8 necesita estos datos para calibrar el V-Score.

**Pasos:**
1. Abrir TikTok en el celular
2. Ir a tu perfil → tocar el ícono de **tres líneas** (arriba a la derecha)
3. **Configuración y privacidad**
4. **Cuenta**
5. **Cambiar a cuenta de Creador** (o Empresa)
6. Elegir categoría: **Educación / Entretenimiento**
7. Seguir los pasos y confirmar

**Resultado:** En 24-48h tendrás acceso a Analytics completo (retención, fuentes de tráfico, audiencia).

**Tiempo total:** 2 minutos. Gratis.

---

### 3. VisualEyes — Predicción de Atención Visual

**Por qué:** A8 usa VisualEyes para analizar las thumbnails de los videos antes de publicar (M4 PREDICT). Predice qué zonas atraen la atención del ojo humano con 93% de precisión.

**Pasos:**
1. Ir a: **visualeyes.design**
2. Clic en **"Get Started Free"** o **"Sign Up"**
3. Crear cuenta con email
4. Para analizar un video: tomar captura del frame principal → subirla a VisualEyes → obtener heatmap
5. Anotar el **Clarity Score** (número que aparece) — este es el valor que va al V-Score

**Cómo usarlo en el proyecto:**
- Antes de cada video, capturar el thumbnail
- Subirlo a VisualEyes
- El **Clarity Score** y el porcentaje de atención en el hook se ingresan en `vscore_engine.py`

**Tiempo total:** 3 minutos. Gratis.

---

## BLOQUE 2 — IMPORTANTE (para automatización de publicación y analytics)

---

### 4. Composio + TikTok MCP (recomendado sobre opción directa)

**Por qué:** Composio es la forma más fácil de conectar TikTok a Claude. Gestiona el OAuth por ti, sin necesidad de esperar aprobación de TikTok Developer. Habilita el MCP de TikTok para M1 DISCOVER y M5 PUBLISH.

**Pasos:**
1. Ir a: **composio.dev**
2. Clic en **"Sign Up"** → crear cuenta gratuita
3. En el dashboard: **Apps** → buscar **TikTok**
4. Clic en **"Connect"**
5. Se abre ventana de OAuth de TikTok → iniciar sesión con tu cuenta TikTok → autorizar
6. Composio genera automáticamente el access token
7. En el dashboard de Composio: **Settings** → **API Keys** → copiar tu API Key
8. Pegar en el archivo `.env`:
   ```
   COMPOSIO_API_KEY=tu-composio-key
   ```

**Plan gratuito:** Suficiente para empezar (límite de requests mensual).
**Plan de pago:** $49/mes si necesitas más volumen.

**Tiempo total:** 15 minutos.

---

### 5. Meta Page Access Token (para Facebook Graph API)

**Por qué:** Permite a A6 publicar en tu página de Facebook y a A7/M6 leer las métricas post-publicación de forma programática.

**Pre-requisito:** Tener una Página de Facebook (no perfil personal). Si no tienes, crear una en facebook.com/pages/create.

**Pasos:**
1. Ir a: **developers.facebook.com**
2. Iniciar sesión con tu cuenta de Facebook
3. Clic en **"My Apps"** → **"Create App"**
4. Seleccionar tipo: **Business**
5. Nombre de la app: `CurioClip Marketing`
6. Email de contacto: el tuyo
7. Clic en **"Create App"**
8. En el dashboard de la app, ir a: **Tools** → **Graph API Explorer**
9. En el menú **"Meta App"** (arriba a la derecha): seleccionar tu app `CurioClip Marketing`
10. En **"User or Page"**: seleccionar **"Get Page Access Token"**
11. Elegir tu página de Facebook
12. Se pedirán permisos — marcar:
    - `pages_manage_posts`
    - `pages_read_engagement`
    - `pages_show_list`
    - `pages_read_user_content`
13. Clic en **"Generate Access Token"**
14. Copiar el token (empieza con `EAAx...`)
15. También copiar tu **Page ID** (aparece en la URL o en Info de la Página)
16. Pegar en el archivo `.env`:
    ```
    META_PAGE_ACCESS_TOKEN=EAAx...tu-token...
    META_PAGE_ID=123456789
    ```

> **Nota importante:** El token generado en Graph API Explorer expira en ~1-2 horas. Para un token de larga duración (60 días), sigue la documentación oficial de "Long-Lived Page Access Token".

**Tiempo total:** 30 minutos.

---

### 6. Meta Ads MCP Oficial (alternativa más fácil al #5)

**Por qué:** Meta lanzó su MCP oficial el 29 de abril de 2026. Es más fácil que configurar el Graph API porque usa OAuth directo. Tiene 29 herramientas: crear campañas, leer insights, gestionar presupuestos.

**Pre-requisito:** Tener Meta Business Suite activo.

**Pasos:**
1. Ir a: **mcp.facebook.com/ads**
2. Clic en **"Connect"**
3. Iniciar sesión con tu cuenta de Facebook/Meta Business
4. Autorizar el acceso (OAuth)
5. En Claude Code, agregar el MCP al archivo de configuración de MCPs:
   - En Claude Code: menú **Settings** → **MCP Servers** → **Add**
   - O editar `~/.claude/claude_desktop_config.json` y agregar la entrada del servidor

**Beneficio:** No necesitas gestionar tokens manualmente. OAuth lo hace todo.

**Tiempo total:** 10 minutos.

---

### 7. TikTok Developer App (Content Posting API directa)

**Por qué:** Permite publicación automática en TikTok sin intermediarios. Más control que Composio, pero requiere aprobación formal de TikTok.

**Pre-requisito:** Cuenta TikTok Pro activada (paso 2).

**Pasos:**
1. Ir a: **developers.tiktok.com**
2. Iniciar sesión con tu cuenta TikTok
3. Clic en **"Manage Apps"** → **"Create App"**
4. Nombre: `CurioClip`
5. Descripción: explicar que es para publicar contenido propio de tu marca
6. Website: puedes poner cualquier URL válida (puedes crear una landing en Carrd.co gratis)
7. En **"Add Products"**, agregar:
   - **Login Kit** (obligatorio)
   - **Content Posting API**
   - **Research API** (para buscar tendencias en M1 DISCOVER)
8. Completar el formulario de solicitud de Content Posting API:
   - Use case: "Publish original content to our brand's TikTok account"
   - Describir con detalle cómo usarás la API
9. Enviar solicitud → **esperar aprobación (2-4 semanas)**
10. Cuando aprueben, generar credenciales:
    - Client Key y Client Secret aparecen en el dashboard
    - Generar Access Token via OAuth con tu cuenta TikTok
11. Pegar en el archivo `.env`:
    ```
    TIKTOK_CLIENT_KEY=aw...
    TIKTOK_CLIENT_SECRET=...
    TIKTOK_ACCESS_TOKEN=...
    ```

> **Recomendación:** Usa Composio (#4) mientras esperas esta aprobación. Son compatibles.

**Tiempo total:** 30 minutos para solicitar + 2-4 semanas de aprobación.

---

## BLOQUE 3 — OPCIONAL (mejoras incrementales)

---

### 8. Higgsfield AI Video (video generado con IA)

**Por qué:** Permite a A4/M3 generar clips de B-roll y animaciones desde texto o imágenes, eliminando la necesidad de buscar stock footage manualmente. Lanzado en abril 2026.

**Pasos:**
1. Ir a: **higgsfield.ai**
2. Clic en **"Get Started"** o **"Sign Up"**
3. Crear cuenta
4. Ir a **Settings** o **API** → generar API Key
5. Pegar en el archivo `.env`:
   ```
   HIGGSFIELD_API_KEY=hf_...
   ```
6. En `config\settings.json`, cambiar `"enabled": false` a `"enabled": true` en la sección `higgsfield`

**Uso en el proyecto:** `src\mcp_servers\higgsfield_server.py`

> Si no quieres pagar Higgsfield, el fallback gratuito es CapCut para edición manual o el generador de scripts FFmpeg incluido en `higgsfield_server.py::generate_ffmpeg_script()`.

**Tiempo total:** 5 minutos para crear cuenta + consultar precio en higgsfield.ai/pricing.

---

### 9. Microsoft Clarity — Heatmaps Post-Publicación

**Por qué:** Permite a M6 LEARN validar las predicciones de M4 PREDICT con datos reales de dónde hace clic la gente en tu landing page. Complementa TikTok Analytics.

**Pasos:**
1. Ir a: **clarity.microsoft.com**
2. Iniciar sesión con cuenta Microsoft (Outlook, Hotmail, etc.)
3. Clic en **"Add new project"**
4. Nombre: `CurioClip Landing`
5. Ingresar URL de tu landing page (puedes crear una gratis en **carrd.co**)
6. Copiar el **snippet de código** que genera Clarity
7. Pegarlo en el `<head>` de tu landing page
8. En 24h empezarás a ver heatmaps y grabaciones de sesión

**Tiempo total:** 10 minutos. Gratis ilimitado.

---

### 10. Miro API — Dashboard Visual (baja prioridad)

**Por qué:** A0 puede usar Miro para crear un dashboard visual de la estrategia. No es crítico para el pipeline principal.

**Pasos:**
1. Ir a: **miro.com** → crear cuenta gratuita
2. Crear un nuevo Board → nombrar `CurioClip Strategy`
3. Copiar el **Board ID** de la URL: `miro.com/app/board/ESTE-ES-EL-ID/`
4. Ir a: **miro.com/app/settings/user-profile/apps**
5. Clic en **"Create new app"** → nombre: `CurioClip`
6. En la app: **"Create access token"** → copiar
7. Pegar en el archivo `.env`:
   ```
   MIRO_API_TOKEN=eyJt...
   MIRO_BOARD_ID=uXjVKxxxxxx=
   ```
8. En `config\settings.json`, actualizar `api_token` y `board_id` en la sección `miro`

**Tiempo total:** 10 minutos. Gratis (plan básico).

---

## Orden de ejecución recomendado

```
DÍA 1 (hoy — 20 minutos total):
  ✅ Paso 2: Activar TikTok Pro (2 min)
  ✅ Paso 3: Crear cuenta VisualEyes (3 min)
  ✅ Paso 1: Obtener LLM API Key para MiroFish (5 min)
  ✅ Probar: ejecutar scripts\setup.ps1 desde PowerShell
  ✅ Probar: cd vendor\MiroFish && docker-compose up

DÍA 1-2 (30-45 minutos):
  ⬜ Paso 4: Composio + TikTok (15 min) — publicación TikTok desbloqueada
  ⬜ Paso 5 o 6: Meta Token o Meta MCP (10-30 min) — publicación Facebook

SEMANA 1-2:
  ⬜ Paso 7: Solicitar TikTok Developer App — empezar hoy, aprobación en 2-4 semanas
  ⬜ Paso 9: Microsoft Clarity + landing page

CUANDO HAYA PRESUPUESTO:
  ⬜ Paso 8: Higgsfield (video IA)
  ⬜ Paso 10: Miro (dashboard)
```

---

## Cómo verificar que todo funciona

Una vez configurado el `.env`, ejecutar en PowerShell desde la carpeta del proyecto:

```powershell
# Activar el entorno virtual
.\venv\Scripts\Activate.ps1

# Test 1: V-Score engine
python src\scoring\vscore_engine.py

# Test 2: MiroFish (debe mostrar "online" si Docker está corriendo)
python src\mcp_servers\mirofish_server.py

# Test 3: Meta API
python src\mcp_servers\meta_ads_server.py

# Test 4: TikTok API
python src\mcp_servers\tiktok_mcp_server.py

# Test 5: Pipeline M1 DISCOVER (genera template en Obsidian)
python src\pipeline\discover.py
```

Cada script imprime su estado: `online`, `configured`, o `not_configured` con los pasos exactos para resolver.

---

## Arrancar MiroFish (simulación social)

```powershell
# Opción 1: Docker (recomendado)
cd "C:\Users\Nick\Desktop\AGENCIA DE MARKETING\vendor\MiroFish"
docker-compose up

# Opción 2: Manual
# Terminal 1 — Backend
cd "C:\Users\Nick\Desktop\AGENCIA DE MARKETING\vendor\MiroFish\backend"
python run.py

# Terminal 2 — Frontend (opcional, solo si quieres ver la UI)
cd "C:\Users\Nick\Desktop\AGENCIA DE MARKETING\vendor\MiroFish\frontend"
npm install
npm run dev
```

MiroFish queda disponible en: `http://localhost:5001` (backend) y `http://localhost:5173` (frontend)

---

*Documento generado automáticamente por A0_Director — CurioClip Marketing IA*
*Ver configuración completa en: `config\settings.json` y `CLAUDE.md`*
