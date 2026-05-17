"""
Publicar video a TikTok Studio con caption completo, hashtags, y opcion de historia.
Usa Playwright CDP (Chrome con sesion activa).

Uso: python -m src.bridge.publish_with_caption <video_path> <caption>
"""
import sys
sys.stdout.reconfigure(encoding='utf-8')
import asyncio
import urllib.request
import json
import time


def get_tiktok_tab_ws():
    """Obtiene el WebSocket URL de la pestaña de TikTok Studio."""
    tabs = json.loads(urllib.request.urlopen('http://localhost:9222/json').read())
    # Priorizar TikTok Studio
    for tab in tabs:
        url = tab.get('url', '')
        if 'tiktokstudio' in url and tab.get('type') == 'page':
            return tab['webSocketDebuggerUrl']
    # Fallback: cualquier tiktok.com
    for tab in tabs:
        url = tab.get('url', '')
        if 'tiktok.com' in url and tab.get('type') == 'page':
            return tab['webSocketDebuggerUrl']
    return None


async def publish_video_playwright(video_path: str, caption: str, post_to_story: bool = True):
    """
    Publica un video a TikTok Studio usando Playwright MCP via CDP.

    Args:
        video_path: Ruta absoluta al video MP4
        caption: Descripcion completa con hashtags
        post_to_story: Si True, tambien sube a Historias
    """
    # Este script genera los comandos que Playwright debe ejecutar
    # Se usa desde el context de Claude con Playwright MCP ya conectado

    print(f"[PUBLISH] Video: {video_path}")
    print(f"[PUBLISH] Caption ({len(caption)} chars): {caption[:80]}...")
    print(f"[PUBLISH] Historias: {post_to_story}")

    steps = {
        "step1_navigate": "https://www.tiktok.com/tiktokstudio/upload",
        "step2_upload_file": video_path,
        "step3_caption": caption,
        "step4_post_to_story": post_to_story,
        "step5_publish": "Click button 'Publicar'"
    }

    return steps


# Caption templates por video
CAPTIONS = {
    "V1": (
        "Este animal puede REJUVENECER indefinidamente y vivir para siempre. "
        "La Turritopsis dohrnii revierte su ciclo biologico cuando esta en peligro. "
        "Es el unico ser vivo biologicamente inmortal conocido por la ciencia. "
        "#curiosidades #ciencia #inmortal #medusa #biologia #naturaleza #datoscuriosos "
        "#sabiasque #viral #increible #CurioClip #aprender"
    ),
    "V2": (
        "Tu cuerpo tiene MAS bacterias que estrellas en la Via Lactea. "
        "38 billones de bacterias conviven contigo en este momento. "
        "Tu microbioma te supera por mucho en numero. "
        "#curiosidades #datoscuriosos #sabiasque #ciencia #bacteria #galaxia "
        "#cuerpohumano #biologia #CurioClip #viral #increible"
    ),
    "V3": (
        "Esta senal de radio suena desde 1973 y NADIE sabe que es. "
        "La UVB-76 transmite desde Rusia y da codigos misteriosos sin explicacion. "
        "La CIA lleva 50 anos sin poder explicarla. "
        "#curiosidades #misterio #datoscuriosos #rusia #enigma #conspiracion "
        "#historia #radiomisterio #CurioClip #viral #increible"
    ),
    "V4": (
        "En Pocatello, Idaho, es ILEGAL no sonreir en publico desde 1948. "
        "Hay mas leyes absurdas: en Alaska no puedes despertar un oso para foto. "
        "El mundo legal tiene leyes que parecen chiste pero son reales. "
        "#curiosidades #leyes #datoscuriosos #sabiasque #absurdo #usa #viral "
        "#WTF #CurioClip #increible #gracioso #cultura"
    ),
    "V5": (
        "El plomo fundido siempre cae en la misma forma? La ciencia dice que NO. "
        "La geometria del caos determina como solidifica cada vez diferente. "
        "Esto se llama atractor extraño en la teoria del caos. "
        "#ciencia #fisica #caos #plomo #curiosidades #datoscuriosos "
        "#sabiasque #viral #increible #CurioClip #experimento"
    ),
}


if __name__ == "__main__":
    if len(sys.argv) >= 2:
        video_id = sys.argv[1].upper()
        if video_id in CAPTIONS:
            print(f"Caption para {video_id}:")
            print(CAPTIONS[video_id])
        else:
            print(f"Video ID no reconocido. Disponibles: {list(CAPTIONS.keys())}")
    else:
        print("Captions disponibles:")
        for vid, cap in CAPTIONS.items():
            print(f"\n{vid}: {cap[:100]}...")
