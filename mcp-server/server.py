from mcp.server.mcpserver import MCPServer

from src.k8s_client import get_core_v1_client, get_custom_objects_client
from src.tools.argocd import get_argocd_app_status as _get_argocd_app_status
from src.tools.events import get_k8s_events as _get_k8s_events
from src.tools.pods import get_pod_logs as _get_pod_logs
from src.tools.pods import get_pods as _get_pods

mcp = MCPServer("devops-copilot-kubernetes")


@mcp.tool()
def get_pods(namespace: str = "demo") -> list[dict]:
    """Lista los pods de un namespace y muestra su estado actual."""
    return _get_pods(get_core_v1_client(), namespace=namespace)


@mcp.tool()
def get_pod_logs(pod_name: str, namespace: str = "demo", tail_lines: int = 100) -> dict:
    """Obtiene las últimas líneas de logs de un pod de Kubernetes.

    Usa esta herramienta para investigar errores de arranque, como un
    CrashLoopBackOff. Por seguridad, devuelve como máximo 500 líneas.
    """
    return _get_pod_logs(
        get_core_v1_client(), pod_name=pod_name, namespace=namespace, tail_lines=tail_lines
    )


@mcp.tool()
def get_k8s_events(namespace: str = "demo", pod_name: str | None = None) -> list[dict]:
    """Lista los eventos recientes de un namespace (ej. FailedScheduling, OOMKilled).

    Si se pasa `pod_name`, filtra solo los eventos de ese pod.
    """
    return _get_k8s_events(get_core_v1_client(), namespace=namespace, pod_name=pod_name)


@mcp.tool()
def get_argocd_app_status(app_name: str, argocd_namespace: str = "argocd") -> dict:
    """Devuelve el estado de sync y health de una Application de ArgoCD.

    Primer paso recomendado de diagnóstico: dice si el deploy está
    `Synced`/`Healthy` o si ArgoCD ya detectó un problema.
    """
    return _get_argocd_app_status(
        get_custom_objects_client(), app_name=app_name, argocd_namespace=argocd_namespace
    )


if __name__ == "__main__":
    mcp.run()
