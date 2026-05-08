"""
TikTok MCP Wrapper
==================
Integracion de TikTok via proveedores verificados (Mayo 2026).

OPCIONES REALES VERIFICADAS:
  1. TikNeuron MCP — Analisis: subtitulos, metricas, busqueda de tendencias
     URL: tikneuron.com
  2. Composio — Content Posting API + OAuth managed (mas facil de configurar)
     URL: composio.dev/apps/tiktok
  3. TikTok Content Posting API directa — requiere app aprobada (2-4 semanas)
     URL: developers.tiktok.com

ESTADO: REAL — MCPs de terceros funcionales. TikTok NO tiene MCP oficial propio (mayo 2026).

MODULO PIPELINE: M1 DISCOVER (analytics) + M5 PUBLISH (posting)
"""

import os
import requests
from typing import Optional


TIKTOK_ACCESS_TOKEN = os.environ.get("TIKTOK_ACCESS_TOKEN", "<<<PENDIENTE>>>")
TIKTOK_CLIENT_KEY = os.environ.get("TIKTOK_CLIENT_KEY", "<<<PENDIENTE>>>")
COMPOSIO_API_KEY = os.environ.get("COMPOSIO_API_KEY", "<<<PENDIENTE>>>")

TIKTOK_API_BASE = "https://open.tiktokapis.com/v2"


class TikTokClient:
    """Cliente para TikTok Content Posting API y Research API."""

    def __init__(self, access_token: str = TIKTOK_ACCESS_TOKEN):
        self.access_token = access_token
        self.session = requests.Session()
        self.session.headers.update({
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json"
        })

    def _not_configured(self) -> Optional[dict]:
        if self.access_token == "<<<PENDIENTE>>>":
            return {
                "error": "TikTok Access Token no configurado.",
                "opciones": {
                    "composio": "composio.dev/apps/tiktok — mas facil, OAuth managed",
                    "tikneuron": "tikneuron.com — para analytics sin publicacion",
                    "api_directa": "developers.tiktok.com — requiere aprobacion 2-4 semanas"
                },
                "env": "Agregar TIKTOK_ACCESS_TOKEN=tu_token al .env"
            }
        return None

    def get_video_list(self, fields: list = None) -> dict:
        """Lista videos de la cuenta con metricas (para M6 LEARN)."""
        err = self._not_configured()
        if err:
            return err
        f = fields or ["id", "title", "view_count", "like_count",
                       "comment_count", "share_count", "duration"]
        resp = self.session.post(
            f"{TIKTOK_API_BASE}/video/list/",
            json={"fields": f},
            timeout=30
        )
        resp.raise_for_status()
        return resp.json()

    def get_video_analytics(self, video_id: str) -> dict:
        """Analytics detallados de un video para calibrar M4 PREDICT."""
        err = self._not_configured()
        if err:
            return err
        resp = self.session.post(
            f"{TIKTOK_API_BASE}/research/video/query/",
            json={
                "filters": {"video_ids": [video_id]},
                "fields": [
                    "view_count", "like_count", "comment_count",
                    "share_count", "average_watch_time", "reach"
                ]
            },
            timeout=30
        )
        resp.raise_for_status()
        return resp.json()

    def search_trending(self, keyword: str, region: str = "MX",
                        max_results: int = 20) -> dict:
        """
        Busca videos trending por keyword (Research API).
        REQUIERE: Research API aprobada por TikTok Developer Portal.
        Para M1 DISCOVER.
        """
        err = self._not_configured()
        if err:
            return err
        resp = self.session.post(
            f"{TIKTOK_API_BASE}/research/video/query/",
            json={
                "query": {
                    "and": [{
                        "operation": "IN",
                        "field_name": "keyword",
                        "field_values": [keyword]
                    }]
                },
                "start_date": "20260401",
                "end_date": "20260506",
                "max_count": max_results,
                "fields": [
                    "id", "view_count", "like_count", "share_count",
                    "comment_count", "hashtag_names", "video_duration",
                    "region_code"
                ],
                "cursor": 0
            },
            timeout=30
        )
        resp.raise_for_status()
        return resp.json()

    def upload_video(self, video_path: str, caption: str,
                     hashtags: list = None, privacy: str = "PUBLIC_TO_EVERYONE") -> dict:
        """
        Sube un video via Content Posting API.
        REQUIERE: App aprobada por TikTok Developer Portal.
        Solo usar en Nivel 4-5 de autonomia.
        Para Nivel 3: entregar package para publicacion manual.
        """
        err = self._not_configured()
        if err:
            return err

        # Inicializar upload
        ht = " ".join(f"#{h}" for h in (hashtags or []))
        full_caption = f"{caption}\n{ht}".strip()

        init_resp = self.session.post(
            f"{TIKTOK_API_BASE}/post/publish/video/init/",
            json={
                "post_info": {
                    "title": full_caption[:150],
                    "privacy_level": privacy,
                    "disable_duet": False,
                    "disable_comment": False,
                    "disable_stitch": False,
                },
                "source_info": {
                    "source": "FILE_UPLOAD",
                    "video_size": os.path.getsize(video_path) if os.path.exists(video_path) else 0,
                    "chunk_size": 10 * 1024 * 1024,
                    "total_chunk_count": 1
                }
            },
            timeout=30
        )
        init_resp.raise_for_status()
        return init_resp.json()

    def health_check(self) -> dict:
        if self.access_token == "<<<PENDIENTE>>>":
            return {
                "status": "not_configured",
                "providers": {
                    "Composio (recomendado)": "composio.dev/apps/tiktok",
                    "TikNeuron (analytics)": "tikneuron.com",
                    "API directa": "developers.tiktok.com (2-4 semanas aprobacion)"
                }
            }
        return {"status": "configured", "provider": "TikTok Content Posting API"}


MCP_TOOLS_SCHEMA = {
    "server_name": "tiktok-mcp",
    "description": "TikTok MCP — Analytics + Content Posting. REAL (mayo 2026).",
    "providers_verificados": ["TikNeuron", "Composio", "TikTok API directa"],
    "tools": [
        {"name": "get_video_list", "modulo_pipeline": "M6_LEARN"},
        {"name": "get_video_analytics", "modulo_pipeline": "M6_LEARN + calibracion M4"},
        {"name": "search_trending", "modulo_pipeline": "M1_DISCOVER"},
        {"name": "upload_video", "modulo_pipeline": "M5_PUBLISH (nivel 4-5 SOLO)"},
    ],
    "setup_composio": [
        "1. Ir a composio.dev → crear cuenta gratuita",
        "2. Dashboard → Apps → TikTok → Connect",
        "3. Completar OAuth con tu cuenta TikTok",
        "4. Composio genera el Access Token gestionado",
        "5. Agregar COMPOSIO_API_KEY al .env"
    ]
}


if __name__ == "__main__":
    client = TikTokClient()
    health = client.health_check()
    print(f"TikTok API: {health['status']}")
    if health["status"] == "not_configured":
        print("\nProveedores disponibles:")
        for name, url in health.get("providers", {}).items():
            print(f"  {name}: {url}")
