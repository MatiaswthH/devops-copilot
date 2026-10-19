"""Tool de diagnóstico sobre el estado de deploy en ArgoCD.

Lee el CRD `Application` directamente vía la API de Kubernetes en vez de
hablar con la API REST de ArgoCD, para reutilizar la misma autenticación
que ya usan las tools de pods/eventos (el kubeconfig local).
"""

from kubernetes import client
from kubernetes.client.exceptions import ApiException

ARGOCD_GROUP = "argoproj.io"
ARGOCD_VERSION = "v1alpha1"
ARGOCD_PLURAL = "applications"


class ArgoCDAppNotFound(Exception):
    """La Application pedida no existe en el namespace de ArgoCD."""


def get_argocd_app_status(
    custom_objects: client.CustomObjectsApi,
    app_name: str,
    argocd_namespace: str = "argocd",
) -> dict:
    """Devuelve el estado de sync y health de una Application de ArgoCD.

    Es el primer paso recomendado de diagnóstico: antes de bajar a pods o
    logs, esto dice si el deploy está `Synced`/`Healthy` o si ArgoCD ya
    detectó un problema (`OutOfSync`, `Degraded`, `Progressing`).
    """
    try:
        app = custom_objects.get_namespaced_custom_object(
            group=ARGOCD_GROUP,
            version=ARGOCD_VERSION,
            namespace=argocd_namespace,
            plural=ARGOCD_PLURAL,
            name=app_name,
        )
    except ApiException as exc:
        if exc.status == 404:
            raise ArgoCDAppNotFound(
                f"No existe la Application '{app_name}' en el namespace '{argocd_namespace}'"
            ) from exc
        raise

    spec = app.get("spec", {})
    status = app.get("status", {})
    source = spec.get("source", {})
    sync = status.get("sync", {})
    health = status.get("health", {})

    return {
        "name": app_name,
        "project": spec.get("project"),
        "repo_url": source.get("repoURL"),
        "path": source.get("path"),
        "target_revision": source.get("targetRevision"),
        "destination_namespace": spec.get("destination", {}).get("namespace"),
        "sync_status": sync.get("status"),
        "health_status": health.get("status"),
        "revision": sync.get("revision"),
        "operation_phase": status.get("operationState", {}).get("phase"),
    }
