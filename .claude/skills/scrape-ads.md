---
name: scrape-ads
description: Scrape and analyze competitor ads from Facebook Ad Library and TikTok Creative Center. Use when the user asks to research ads, find competitor creatives, analyze what ads are running in the curiosidades/datos curiosos niche, or prepare intelligence for A5 (Logística de Campañas). Triggers: "scrape ads", "qué anuncios corre X", "investiga anuncios del nicho", "busca ads de competidores", "qué está pagando X".
allowed-tools: Bash(agent-browser*), Bash(python*), Write, Read, WebSearch
---

# Skill: /scrape-ads
## Agente responsable: A1_Investigacion + A5_Logistica

Scrapes ads from Facebook Ad Library, TikTok Creative Center, and other ad platforms.
Saves structured intelligence to Obsidian for A5 (Campañas) to use when budget activates.

---

## PASO 1 — Determinar qué scrape hacer

Si el usuario no especificó plataforma ni cuenta, hacer AMBAS por defecto:
- Facebook Ad Library: ads de competidores del nicho curiosidades
- TikTok Creative Center: top creatives del nicho

Si especificó una cuenta (@usuario), buscar esa cuenta específicamente.

---

## PASO 2 — Facebook Ad Library

```bash
# Abrir Facebook Ad Library con búsqueda del nicho
agent-browser open "https://www.facebook.com/ads/library/?active_status=active&ad_type=all&country=ALL&q=datos+curiosos&search_type=keyword_unordered"
agent-browser wait "[role='main']"
agent-browser screenshot ads_fb_1.png
agent-browser snapshot
```

Para cada anuncio visible, extraer con `agent-browser get text`:
- Nombre del anunciante
- Copy del anuncio (texto principal)
- CTA (botón de acción)
- Formato (imagen/video/carrusel)
- Fecha de inicio (cuánto lleva corriendo)
- Plataformas donde aparece

Si el usuario especificó una cuenta, usar:
```bash
agent-browser open "https://www.facebook.com/ads/library/?active_status=active&ad_type=all&country=ALL&search_type=page&q=[NOMBRE_CUENTA]"
```

Hacer scroll 3 veces para cargar más anuncios:
```bash
agent-browser scroll down 800
agent-browser scroll down 800
agent-browser scroll down 800
```

---

## PASO 3 — TikTok Creative Center

```bash
agent-browser open "https://ads.tiktok.com/business/creativecenter/inspiration/topads/pc/en"
agent-browser wait "[class*='content']"
agent-browser screenshot ads_tiktok_1.png
agent-browser snapshot
```

Filtros a aplicar (buscar refs en el snapshot):
- Industry: Education / Entertainment
- Región: Latin America o Spain
- Período: 7 días
- Ordenar por: Engagement rate

Extraer para cada ad:
- Anunciante
- Duración del video
- Hook (primeras palabras visibles)
- Engagement rate
- Link al video si está disponible

---

## PASO 4 — Análisis e informe

Una vez recopilados los datos, analizar patrones:

**Preguntas clave:**
1. ¿Qué formato domina? (video 9:16 corto, carrusel, imagen)
2. ¿Qué hooks aparecen más? (preguntas, datos WTF, "¿sabías que...?")
3. ¿Qué CTAs usan? ("Saber más", "Ver ahora", "Seguir")
4. ¿Cuánto tiempo llevan corriendo? (si llevan >30 días = rentable)
5. ¿Hay algún anunciante gastando mucho en este nicho? (señal de que hay dinero)

**Regla de oro de ad intelligence:**
> Si un anuncio lleva corriendo >30 días = está siendo rentable para el anunciante.
> Eso es el formato/hook/CTA que hay que replicar cuando A5 active presupuesto.

---

## PASO 5 — Guardar en Obsidian

Crear o actualizar: `obsidian_vault/20_Investigacion/ads_intelligence.md`

Formato del entregable:

```markdown
---
agente: A1_Investigacion
fecha: [HOY]
tags: [ads, inteligencia, competencia, facebook, tiktok]
---

# Ad Intelligence — [fecha]

## Facebook Ad Library

| Anunciante | Copy Hook | Formato | CTA | Lleva corriendo | Plataformas |
|-----------|-----------|---------|-----|----------------|-------------|
| [nombre] | "[primeras palabras]" | video 9:16 | Saber más | 45 días | FB+IG |

## TikTok Creative Center — Top Ads Nicho

| Anunciante | Duración | Hook | ER% | Observaciones |
|-----------|---------|------|-----|--------------|

## Patrones detectados

### Formatos que dominan:
- ...

### Hooks más usados:
- ...

### CTAs más usados:
- ...

### Oportunidades detectadas:
- ...

## Recomendación A5 (cuando active presupuesto)
[Qué formato/hook/CTA probar primero basado en lo encontrado]
```

---

## Notas de compliance (A9)

- Facebook Ad Library es acceso público — legal sin restricciones.
- TikTok Creative Center es acceso público — legal sin restricciones.
- Los datos recopilados son de anuncios pagados públicamente visibles.
- NO descargar creatives/videos de los anuncios sin verificar licencia.
- Solo capturar metadatos (texto, formato, fechas, métricas).

---

## Cierre

Reportar al usuario:
1. Cuántos anuncios analizados por plataforma
2. Top 3 patrones detectados
3. Recomendación concreta para A5
4. Ruta del archivo guardado en Obsidian
