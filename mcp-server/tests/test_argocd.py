"""Pruebas de integración: validan que la tool lee bien el estado real de
ArgoCD en el cluster `kind` (requieren el cluster levantado)."""

import pytest

from conftest import requires_cluster
from src.tools.argocd import ArgoCDAppNotFound, get_argocd_app_status


@requires_cluster
def test_healthy_app_is_synced_and_healthy(custom_objects):
    status = get_argocd_app_status(custom_objects, "healthy-app")

    assert status["name"] == "healthy-app"
    assert status["sync_status"] == "Synced"
    assert status["health_status"] == "Healthy"
    assert status["path"] == "Platform/apps/healthy-app"
    assert status["repo_url"].endswith("devops-copilot")
    assert status["destination_namespace"] == "demo"


@requires_cluster
def test_payments_api_reports_the_real_incident(custom_objects):
    """payments-api está desplegada a propósito sin DB_HOST (ver
    Platform/apps/broken-app). ArgoCD debe seguir reportando el deploy
    como Synced (el YAML sí se aplicó), pero con salud degradada."""
    status = get_argocd_app_status(custom_objects, "payments-api")

    assert status["sync_status"] == "Synced"
    assert status["health_status"] in {"Degraded", "Progressing"}
    assert status["path"] == "Platform/apps/broken-app"


@requires_cluster
def test_unknown_app_raises_not_found(custom_objects):
    with pytest.raises(ArgoCDAppNotFound):
        get_argocd_app_status(custom_objects, "no-existe-esta-app")


@requires_cluster
def test_root_app_manages_itself_via_git(custom_objects):
    """Valida el bootstrap de la Fase 1: el app-of-apps también es una
    Application leíble, y apunta a la carpeta de manifiestos en Git."""
    status = get_argocd_app_status(custom_objects, "root-app")

    assert status["sync_status"] == "Synced"
    assert status["path"] == "Platform/argocd/applications"
