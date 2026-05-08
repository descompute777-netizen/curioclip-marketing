---
agente: A0_Director
fecha: 2026-05-06
tags: [setup, herramientas, gratuitas, guia]
estado: activo
---

# 🔧 Guía de Setup — Herramientas Gratuitas CurioClip

## 1. VisualEyes (Reemplaza TRIBE v2)

**URL:** https://visualeyes.design
**Costo:** GRATIS
**Qué hace:** Simula eye-tracking con IA (93% precisión vs estudios reales)

### Pasos de configuración:
1. Ir a https://visualeyes.design
2. Crear cuenta gratuita
3. Para cada thumbnail/frame de video:
   - Subir imagen (captura del frame clave del video)
   - Obtener heatmap de atención + clarity score
4. Interpretar resultados:
   - **Rojo** = zona de máxima atención (tu hook debe estar aquí)
   - **Azul** = zona ignorada (no pongas info importante aquí)
   - **Clarity score >70** = buen diseño visual

### Integración con V-Score:
- El clarity score se normaliza a 0-10
- Se usa como componente `visualeyes_attention` (peso: 0.35)

---

## 2. Microsoft Clarity (Post-publicación)

**URL:** https://clarity.microsoft.com
**Costo:** GRATIS (ilimitado)
**Qué hace:** Heatmaps y grabaciones de sesión en tu landing/web

### Pasos de configuración:
1. Ir a https://clarity.microsoft.com
2. Crear proyecto con cuenta Microsoft
3. Crear landing page gratuita (Carrd.co) con tus videos embebidos
4. Instalar snippet de Clarity en la landing
5. Analizar: dónde hace click la gente, cuánto scroll, qué videos reproducen

### Uso para CurioClip:
- Crear una landing simple con tus 5 mejores videos
- Clarity te muestra cuáles retienen más atención
- Usar esos datos para calibrar el V-Score

---

## 3. TikTok Analytics (Calibración)

**Costo:** GRATIS (cuenta Pro)
**Qué hace:** Métricas reales segundo-a-segundo

### Activar cuenta Pro:
1. Perfil → Configuración → Cuenta → Cambiar a Cuenta de Empresa/Creador
2. Seleccionar categoría: Educación / Entretenimiento
3. Esperar 7 días para que se acumulen datos

### Métricas clave a monitorear:
- **Retention graph:** ¿en qué segundo pierdes gente?
- **Traffic sources:** ¿vienes del FYP o de búsqueda?
- **Audience:** ¿edad, género, país coincide con target?

---

## 4. CapCut (Editor de Video)

**URL:** https://www.capcut.com
**Costo:** GRATIS
**Qué hace:** Editor completo (es de ByteDance, la empresa de TikTok)

### Features gratis relevantes:
- Auto-subtítulos (español)
- Text-to-speech (voiceover IA)
- Plantillas de TikTok
- Efectos y transiciones
- Exportar en 9:16 1080p

---

## 5. Fuentes de Contenido Royalty-Free

| Tipo | Fuente | URL |
|------|--------|-----|
| Imágenes | Pexels | https://pexels.com |
| Imágenes | Unsplash | https://unsplash.com |
| Videos | Pexels Videos | https://pexels.com/videos |
| Videos | Coverr | https://coverr.co |
| Música | Pixabay Music | https://pixabay.com/music |
| Iconos | Flaticon | https://flaticon.com |

> **⚠️ REGLA COMPLIANCE (A9):** Siempre verificar licencia antes de usar.
> Pexels/Unsplash/Pixabay = uso libre sin atribución.
> Otros = leer términos específicos.
