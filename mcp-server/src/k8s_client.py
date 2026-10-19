"""Clientes de Kubernetes compartidos por las tools del servidor MCP."""

from kubernetes import client, config

_loaded = False


def _ensure_config_loaded() -> None:
    global _loaded
    if not _loaded:
        config.load_kube_config()
        _loaded = True


def get_core_v1_client() -> client.CoreV1Api:
    """Cliente para pods, logs y eventos (misma config que usa kubectl)."""
    _ensure_config_loaded()
    return client.CoreV1Api()


def get_custom_objects_client() -> client.CustomObjectsApi:
    """Cliente para CRDs, usado para leer `Application` de ArgoCD."""
    _ensure_config_loaded()
    return client.CustomObjectsApi()
