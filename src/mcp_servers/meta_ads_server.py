"""
Meta Ads MCP Wrapper
====================
MCP oficial de Meta para gestion de campanas y publicacion.
URL oficial: https://mcp.facebook.com/ads
Lanzado: 29 abril 2026 | Estado: Beta publica gratuita | 29 herramientas
VERIFICADO: Mayo 2026 — REAL, no alucinacion.

MODOS:
  1. MCP nativo: Claude Code conecta via mcp.facebook.com/ads con OAuth
  2. Graph API (fallback): con Page Access Token para publicacion organica

REQUISITOS:
  - Meta Business Suite con pagina configurada
  - Page Access Token (permisos: pages_manage_posts, pages_read_engagement)
  - Para MCP oficial: App en developers.facebook.com + OAuth
"""

import os
import requests
from typing import Optional


META_API_BASE = "https://graph.facebook.com/v19.0"
META_PAGE_TOKEN = os.environ.get("META_PAGE_ACCESS_TOKEN", "<<<PENDIENTE>>>")
META_PAGE_ID = os.environ.get("META_PAGE_ID", "<<<PENDIENTE>>>")


class MetaAdsClient:
    """Cliente para Meta Graph API — fallback cuando MCP nativo no esta configurado."""

    def __init__(self, page_token: str = META_PAGE_TOKEN):
        self.page_token = page_token
        self.session = requests.Session()

    def _not_configured(self) -> Optional[dict]:
        if self.page_token == "<<<PENDIENTE>>>":
            return {
                "error": "Meta Page Access Token no configurado.",
                "accion": "Ver pasos en obsidian_vault/40_Publicacion/compliance/checklist_template.md",
                "guia": "developers.facebook.com → Graph API Explorer → generar Page Access Token",
                "mcp_oficial": "Alternativa mas facil: mcp.facebook.com/ads con OAuth directo desde Claude"
            }
        return None

    def _get(self, endpoint: str, params: dict = None) -> dict:
        err = self._not_configured()
        if err:
            return err
        url = f"{META_API_BASE}{endpoint}"
        p = {**(params or {}), "access_token": self.page_token}
        resp = self.session.get(url, params=p, timeout=30)
        resp.raise_for_status()
        return resp.json()

    def _post(self, endpoint: str, data: dict = None) -> dict:
        err = self._not_configured()
        if err:
            return err
        url = f"{META_API_BASE}{endpoint}"
        d = {**(data or {}), "access_token": self.page_token}
        resp = self.session.post(url, data=d, timeout=30)
        resp.raise_for_status()
        return resp.json()

    def get_page_insights(self, page_id: str = META_PAGE_ID,
                          metrics: list = None, period: str = "week") -> dict:
        """Metricas de la pagina: alcance, engagement, vistas."""
        m = ",".join(metrics or [
            "page_views_total", "page_engaged_users",
            "page_reach", "page_video_views"
        ])
        return self._get(f"/{page_id}/insights", {"metric": m, "period": period})

    def get_post_insights(self, post_id: str) -> dict:
        """Metricas de un post especifico post-publicacion (para M6 LEARN)."""
        return self._get(f"/{post_id}/insights", {
            "metric": (
                "post_impressions,post_engaged_users,"
                "post_video_views,post_video_avg_time_watched,"
                "post_clicks,post_reactions_like_total"
            )
        })

    def create_post_draft(self, page_id: str, message: str,
                          link: str = None, scheduled_time: int = None) -> dict:
        """
        Crea un post en Facebook EN BORRADOR (published=False).
        Nivel de autonomia 3: siempre en borrador, el usuario aprueba con 1 clic.
        """
        data = {"message": message, "published": "false"}
        if link:
            data["link"] = link
        if scheduled_time:
            data["scheduled_publish_time"] = str(scheduled_time)
            data["published"] = "false"
        return self._post(f"/{page_id}/feed", data)

    def publish_post(self, page_id: str, message: str, link: str = None) -> dict:
        """
        Publica directamente (solo usar en Nivel 4-5 de autonomia).
        REQUIERE aprobacion explicita del usuario antes de llamar.
        """
        data = {"message": message, "published": "true"}
        if link:
            data["link"] = link
        return self._post(f"/{page_id}/feed", data)

    def health_check(self) -> dict:
        err = self._not_configured()
        if err:
            return {"status": "not_configured", **err}
        try:
            result = self._get("/me", {"fields": "id,name"})
            return {"status": "online", "account": result}
        except Exception as e:
            return {"status": "error", "error": str(e)}


MCP_TOOLS_SCHEMA = {
    "server_name": "meta-ads-mcp",
    "description": "Meta Ads MCP — Integracion oficial con Meta Business Suite",
    "mcp_oficial_url": "https://mcp.facebook.com/ads",
    "status": "REAL — Beta publica desde 29 abril 2026",
    "herramientas_disponibles": 29,
    "tools": [
        {"name": "get_page_insights", "modulo_pipeline": "M6_LEARN"},
        {"name": "get_post_insights", "modulo_pipeline": "M6_LEARN"},
        {"name": "create_post_draft", "modulo_pipeline": "M5_PUBLISH (nivel <=3)"},
        {"name": "publish_post", "modulo_pipeline": "M5_PUBLISH (nivel 4-5 SOLO)"},
    ],
    "setup": [
        "1. Ir a developers.facebook.com y crear App tipo Business",
        "2. En Graph API Explorer, seleccionar tu pagina",
        "3. Generar Page Access Token con: pages_manage_posts, pages_read_engagement",
        "4. Agregar al .env: META_PAGE_ACCESS_TOKEN=EAAx...",
        "5. ALTERNATIVA MAS FACIL: mcp.facebook.com/ads → OAuth directo desde Claude Code"
    ]
}


if __name__ == "__main__":
    client = MetaAdsClient()
    health = client.health_check()
    print(f"Meta API: {health['status']}")
    if health["status"] == "not_configured":
        print("\nPasos para configurar:")
        for step in MCP_TOOLS_SCHEMA["setup"]:
            print(f"  {step}")
