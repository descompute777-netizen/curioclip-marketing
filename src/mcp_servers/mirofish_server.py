"""
MiroFish MCP Server Wrapper (v2 — Integración Real)
=====================================================
Wrapper que se comunica con la API REST de MiroFish (Flask backend en :5001).

Workflow de MiroFish:
  1. Crear proyecto → subir seed document
  2. Construir grafo (GraphRAG) → extrae entidades y relaciones
  3. Crear simulación → genera agentes con personalidad
  4. Preparar simulación → LLM genera perfiles y config
  5. Ejecutar simulación → agentes interactúan (Twitter/Reddit simulados)
  6. Obtener reporte → predicciones y análisis

API Base: http://localhost:5001/api
Repo: https://github.com/666ghj/MiroFish
"""

import json
import os
import time
import requests
from typing import Optional


MIROFISH_BASE_URL = os.environ.get("MIROFISH_URL", "http://localhost:5001")
API_BASE = f"{MIROFISH_BASE_URL}/api"
TIMEOUT = 600  # 10 min max para operaciones largas


class MiroFishClient:
    """Cliente para la API REST de MiroFish."""

    def __init__(self, base_url: str = API_BASE):
        self.base_url = base_url
        self.session = requests.Session()
        self.session.headers.update({"Content-Type": "application/json"})

    def _post(self, endpoint: str, data: dict = None, timeout: int = TIMEOUT) -> dict:
        url = f"{self.base_url}{endpoint}"
        resp = self.session.post(url, json=data or {}, timeout=timeout)
        resp.raise_for_status()
        return resp.json()

    def _get(self, endpoint: str, params: dict = None, timeout: int = 60) -> dict:
        url = f"{self.base_url}{endpoint}"
        resp = self.session.get(url, params=params, timeout=timeout)
        resp.raise_for_status()
        return resp.json()

    # =========================================================
    # TOOL 1: create_and_prepare — Crea proyecto + simulación
    # =========================================================

    def create_project(self, seed_text: str, project_name: str = "curioclip_sim") -> dict:
        """
        Crea un proyecto MiroFish con seed document.

        Args:
            seed_text: Texto semilla (contenido a simular).
            project_name: Nombre del proyecto.

        Returns:
            dict con project_id y graph_id.
        """
        # Paso 1: Crear proyecto y subir documento
        result = self._post("/graph/create", {
            "project_name": project_name,
            "document_text": seed_text,
            "simulation_requirement": (
                "Simulate how this content spreads on social media. "
                "Analyze virality, sentiment distribution, and identify "
                "tipping points for content propagation."
            ),
        })

        if not result.get("success"):
            return {"error": result.get("error", "Error creando proyecto")}

        data = result.get("data", {})
        return {
            "project_id": data.get("project_id"),
            "graph_id": data.get("graph_id"),
            "status": "project_created",
        }

    def build_graph(self, project_id: str) -> dict:
        """
        Construye el grafo de conocimiento (GraphRAG).

        Args:
            project_id: ID del proyecto creado.

        Returns:
            dict con task_id para monitorear progreso.
        """
        result = self._post("/graph/build", {"project_id": project_id})
        if not result.get("success"):
            return {"error": result.get("error", "Error construyendo grafo")}
        return result.get("data", {})

    # =========================================================
    # TOOL 2: simulate_content — Simulación completa
    # =========================================================

    def simulate_content(
        self,
        seed_document: str,
        audience_profile: str = "general",
        project_name: str = "curioclip_sim",
        enable_twitter: bool = True,
        enable_reddit: bool = True,
        wait_for_completion: bool = False,
        poll_interval: int = 10,
        max_wait: int = 600,
    ) -> dict:
        """
        Ejecuta simulación completa de propagación social.

        Args:
            seed_document: Texto del contenido (título + descripción + contexto).
            audience_profile: Descripción del perfil de audiencia target.
            project_name: Nombre del proyecto.
            enable_twitter: Simular Twitter.
            enable_reddit: Simular Reddit.
            wait_for_completion: Si True, espera a que termine.
            poll_interval: Segundos entre polls.
            max_wait: Máximo de segundos a esperar.

        Returns:
            Métricas de propagación, sentimiento, tipping points.
        """
        # Construir seed document enriquecido
        enriched_seed = (
            f"AUDIENCE PROFILE: {audience_profile}\n"
            f"PLATFORM: TikTok / Facebook\n"
            f"LANGUAGE: Spanish\n\n"
            f"CONTENT TO SIMULATE:\n{seed_document}"
        )

        # Paso 1: Crear proyecto
        project = self.create_project(enriched_seed, project_name)
        if "error" in project:
            return project

        project_id = project["project_id"]

        # Paso 2: Construir grafo
        graph_result = self.build_graph(project_id)
        if "error" in graph_result:
            return graph_result

        # Paso 3: Esperar a que el grafo esté listo (poll)
        task_id = graph_result.get("task_id")
        if task_id and wait_for_completion:
            self._wait_for_task(task_id, poll_interval, max_wait)

        # Paso 4: Crear simulación
        sim_result = self._post("/simulation/create", {
            "project_id": project_id,
            "enable_twitter": enable_twitter,
            "enable_reddit": enable_reddit,
        })
        if not sim_result.get("success"):
            return {"error": sim_result.get("error", "Error creando simulación")}

        simulation_id = sim_result["data"]["simulation_id"]

        # Paso 5: Preparar simulación (genera agentes + config)
        prep_result = self._post("/simulation/prepare", {
            "simulation_id": simulation_id,
            "use_llm_for_profiles": True,
            "parallel_profile_count": 5,
        })
        if not prep_result.get("success"):
            return {"error": prep_result.get("error", "Error preparando simulación")}

        prep_task_id = prep_result["data"].get("task_id")

        # Paso 6: Esperar preparación
        if prep_task_id and wait_for_completion:
            self._wait_for_task_simulation(
                prep_task_id, simulation_id, poll_interval, max_wait
            )

        # Paso 7: Ejecutar simulación
        run_result = self._post("/simulation/run", {
            "simulation_id": simulation_id,
        })

        return {
            "simulation_id": simulation_id,
            "project_id": project_id,
            "status": "running" if run_result.get("success") else "prepared",
            "run_result": run_result.get("data", {}),
        }

    def _wait_for_task(self, task_id: str, interval: int, max_wait: int):
        """Poll hasta que un task general termine."""
        elapsed = 0
        while elapsed < max_wait:
            time.sleep(interval)
            elapsed += interval
            # Task status endpoint may vary — try common pattern
            try:
                status = self._post("/graph/build/status", {"task_id": task_id})
                if status.get("data", {}).get("status") in ("completed", "ready", "failed"):
                    return status
            except Exception:
                pass

    def _wait_for_task_simulation(
        self, task_id: str, sim_id: str, interval: int, max_wait: int
    ):
        """Poll hasta que la preparación de simulación termine."""
        elapsed = 0
        while elapsed < max_wait:
            time.sleep(interval)
            elapsed += interval
            try:
                status = self._post("/simulation/prepare/status", {
                    "task_id": task_id,
                    "simulation_id": sim_id,
                })
                data = status.get("data", {})
                if data.get("status") in ("ready", "completed", "failed"):
                    return status
                if data.get("already_prepared"):
                    return status
            except Exception:
                pass

    # =========================================================
    # TOOL 3: get_simulation_results — Obtener resultados
    # =========================================================

    def get_simulation_results(self, simulation_id: str) -> dict:
        """
        Obtiene resultados de una simulación completada.

        Args:
            simulation_id: ID de la simulación.

        Returns:
            Métricas de propagación y reporte.
        """
        result = self._get(f"/simulation/{simulation_id}")
        if not result.get("success"):
            return {"error": result.get("error", "Simulación no encontrada")}
        return result.get("data", {})

    def get_report(self, simulation_id: str, question: str = "") -> dict:
        """
        Obtiene reporte generado por el ReportAgent.

        Args:
            simulation_id: ID de la simulación.
            question: Pregunta específica al ReportAgent.

        Returns:
            Reporte con predicciones y análisis.
        """
        result = self._post("/report/generate", {
            "simulation_id": simulation_id,
            "question": question or "What is the virality prediction for this content?",
        })
        if not result.get("success"):
            return {"error": result.get("error", "Error generando reporte")}
        return result.get("data", {})

    # =========================================================
    # TOOL 4: interview_agent — Hablar con un agente específico
    # =========================================================

    def interview_agent(
        self, simulation_id: str, agent_id: str, question: str
    ) -> dict:
        """
        Entrevista a un agente específico post-simulación.

        Args:
            simulation_id: ID de la simulación.
            agent_id: ID del agente a entrevistar.
            question: Pregunta para el agente.

        Returns:
            Respuesta del agente basada en su personalidad y experiencia.
        """
        result = self._post("/simulation/interview", {
            "simulation_id": simulation_id,
            "agent_id": agent_id,
            "prompt": question,
        })
        if not result.get("success"):
            return {"error": result.get("error", "Error entrevistando agente")}
        return result.get("data", {})

    # =========================================================
    # Health check
    # =========================================================

    def health_check(self) -> dict:
        """Verifica si MiroFish está corriendo."""
        try:
            resp = self.session.get(f"{self.base_url}/", timeout=5)
            return {"status": "online", "code": resp.status_code}
        except requests.ConnectionError:
            return {"status": "offline", "error": "No se puede conectar a MiroFish"}
        except Exception as e:
            return {"status": "error", "error": str(e)}


# =========================================================
# MCP TOOLS SCHEMA
# =========================================================

MCP_TOOLS_SCHEMA = {
    "server_name": "mirofish-mcp",
    "description": "MiroFish — Simulación social multi-agente para predicción de viralidad",
    "tools": [
        {
            "name": "simulate_content",
            "description": "Simula cómo se propaga un contenido en redes sociales",
            "handler": "MiroFishClient.simulate_content",
        },
        {
            "name": "get_simulation_results",
            "description": "Obtiene resultados de una simulación completada",
            "handler": "MiroFishClient.get_simulation_results",
        },
        {
            "name": "get_report",
            "description": "Genera reporte de predicción con el ReportAgent",
            "handler": "MiroFishClient.get_report",
        },
        {
            "name": "interview_agent",
            "description": "Entrevista a un agente específico post-simulación",
            "handler": "MiroFishClient.interview_agent",
        },
    ],
}


if __name__ == "__main__":
    client = MiroFishClient()
    health = client.health_check()
    print(f"MiroFish status: {health['status']}")
    if health["status"] == "offline":
        print("Para iniciar MiroFish:")
        print("  cd vendor/MiroFish && npm run dev")
