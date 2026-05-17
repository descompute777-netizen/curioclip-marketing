"""
Publicar video a TikTok Studio con caption completo + Historias.
Usa Playwright MCP conectado via CDP al Chrome con sesion activa.

Uso directo (imprime caption):
    python -m src.bridge.publish_with_caption V1

Pasos Playwright MCP para publicar + Historia:
    1. browser_navigate  https://www.tiktok.com/tiktokstudio/upload
    2. browser_file_upload  <selector input[type=file]>  <ruta absoluta .mp4>
    3. Esperar spinner de procesamiento (~30-60s)
    4. browser_fill  <selector descripcion>  <caption>
    5. browser_click  "Publicar tambien en Historias" (toggle)
    6. browser_click  "Publicar" (boton azul)
    7. Confirmar: browser_snapshot → verificar "Tu video fue publicado"
"""
import sys
sys.stdout.reconfigure(encoding="utf-8")
from pathlib import Path

ROOT = Path(r"C:\Users\Nick\Desktop\AGENCIA DE MARKETING")
SEMANA = ROOT / "obsidian_vault" / "SEMANAS" / "SEMANA_02_2026-05-13_a_2026-05-19"

# Rutas absolutas de los videos producidos
VIDEO_PATHS = {
    "V1": str(SEMANA / "MARTES"    / "OUTPUT" / "V1_final.mp4"),
    "V2": str(SEMANA / "LUNES"     / "OUTPUT" / "V2_final.mp4"),
    "V3": str(SEMANA / "MIERCOLES" / "OUTPUT" / "V3_final.mp4"),
    "V4": str(SEMANA / "JUEVES"    / "OUTPUT" / "V4_final.mp4"),
    "V5": str(ROOT   / "obsidian_vault" / "SEMANAS" / "SEMANA_01_2026-05-06_a_2026-05-12"
              / "VIERNES" / "OUTPUT" / "V5_final.mp4"),
}

# Captions completos — descripcion + hashtags optimizados por video
CAPTIONS = {
    "V1": (
        "Este animal puede REJUVENECER indefinidamente y vivir para siempre. "
        "La Turritopsis dohrnii revierte su ciclo biologico completo cuando esta en peligro. "
        "Los cientificos la estudian para entender si podemos frenar el envejecimiento humano. "
        "Es el unico ser vivo biologicamente inmortal conocido por la ciencia.\n\n"
        "#curiosidades #ciencia #inmortal #medusa #biologia #naturaleza #datoscuriosos "
        "#sabiasque #viral #increible #CurioClip #aprender #sabias #mente #dato"
    ),
    "V2": (
        "Sabias que tu cuerpo tiene MAS bacterias que estrellas en la Via Lactea? "
        "38 billones de bacterias conviven contigo en este momento. "
        "Tu microbioma es unico como tu huella digital y controla tu salud, humor y hasta decisiones. "
        "Tu no eres una persona — eres un ecosistema.\n\n"
        "#curiosidades #datoscuriosos #sabiasque #ciencia #bacteria #galaxia "
        "#cuerpohumano #biologia #microbioma #mente #CurioClip #viral #increible #aprender"
    ),
    "V3": (
        "Esta senal de radio suena desde 1973 y NADIE sabe que es ni para que sirve. "
        "La UVB-76 transmite desde alguna parte de Rusia y de vez en cuando emite codigos de voz misteriosos. "
        "La CIA, ex agentes de la KGB y radioaficionados llevan mas de 50 anos sin poder explicarla.\n\n"
        "#curiosidades #misterio #datoscuriosos #sabiasque #rusia #enigma #conspiracion "
        "#historia #radiomisterio #CurioClip #viral #increible #ovni #secreto #guerrafria"
    ),
    "V4": (
        "En Pocatello, Idaho, es ILEGAL no sonreir en publico desde 1948. "
        "En Alaska no puedes despertar a un oso para tomarte una foto con el. "
        "En Ohio es ilegal pescar borracho. "
        "El mundo legal esta lleno de leyes que parecen chiste pero son completamente reales.\n\n"
        "#curiosidades #leyes #datoscuriosos #sabiasque #absurdo #usa #viral "
        "#WTF #CurioClip #increible #gracioso #cultura #ley #history #loco"
    ),
    "V5": (
        "El plomo fundido siempre cae en la misma forma? La ciencia dice que NO. "
        "La geometria del caos determina como solidifica cada vez de manera diferente. "
        "Esto se llama atractor extrano en la teoria del caos — y cambia nuestra forma de ver el universo.\n\n"
        "#ciencia #fisica #caos #plomo #curiosidades #datoscuriosos "
        "#sabiasque #viral #increible #CurioClip #experimento #matemáticas #dato"
    ),
}

# Instrucciones paso a paso para Playwright MCP
PUBLISH_STEPS = """
=== PASOS PLAYWRIGHT MCP PARA PUBLICAR {vid_id} ===

Video: {video_path}

PASO 1 — Navegar a TikTok Studio:
  browser_navigate → https://www.tiktok.com/tiktokstudio/upload

PASO 2 — Subir video:
  browser_snapshot → identificar <input type="file"> o boton "Seleccionar archivo"
  browser_file_upload → selector: input[type="file"]  |  archivo: {video_path}
  Esperar 30-60s a que TikTok procese el video (spinner desaparece)

PASO 3 — Llenar descripcion:
  browser_snapshot → localizar textarea de descripcion
  browser_fill → textarea  |  texto: <caption abajo>

PASO 4 — ACTIVAR HISTORIAS:
  browser_snapshot → buscar toggle "Publicar en Historia" o "Add to Story"
  browser_click → ese toggle (debe quedar activado/verde)
  VERIFICAR con browser_snapshot que quedo activado

PASO 5 — Publicar:
  browser_click → boton "Publicar" (azul, texto "Post" o "Publicar")
  browser_snapshot → confirmar mensaje "Tu video fue publicado" o similar

PASO 6 — Registrar:
  Copiar la URL del post publicado y actualizar PUBLICACIONES_LOG.md

=== CAPTION COMPLETO ===
{caption}
"""


def get_publish_guide(video_id: str) -> str:
    vid = video_id.upper()
    if vid not in CAPTIONS:
        return f"Video ID no reconocido. Disponibles: {list(CAPTIONS.keys())}"
    return PUBLISH_STEPS.format(
        vid_id=vid,
        video_path=VIDEO_PATHS.get(vid, "RUTA_NO_CONFIGURADA"),
        caption=CAPTIONS[vid],
    )


if __name__ == "__main__":
    if len(sys.argv) >= 2:
        vid = sys.argv[1].upper()
        print(get_publish_guide(vid))
    else:
        print("Uso: python -m src.bridge.publish_with_caption <V1|V2|V3|V4|V5>\n")
        print("Videos disponibles y rutas:")
        for vid, path in VIDEO_PATHS.items():
            exists = "✅" if Path(path).exists() else "❌ NO EXISTE"
            print(f"  {vid}: {exists}  →  {path}")
