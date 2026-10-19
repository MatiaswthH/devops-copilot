"""Pruebas unitarias del parseo de la Application, sin depender del cluster."""

import pytest
from kubernetes.client.exceptions import ApiException

from src.tools.argocd import ArgoCDAppNotFound, get_argocd_app_status


class _FakeCustomObjects:
    def __init__(self, obj=None, not_found=False):
        self._obj = obj
        self._not_found = not_found

    def get_namespaced_custom_object(self, **kwargs):
        if self._not_found:
            raise ApiException(status=404, reason="Not Found")
        return self._obj


def test_parses_sync_and_health_from_application():
    fake_app = {
        "spec": {
            "project": "default",
            "source": {
                "repoURL": "https://github.com/MatiaswthH/devops-copilot",
                "path": "Platform/apps/healthy-app",
                "targetRevision": "main",
            },
            "destination": {"namespace": "demo"},
        },
        "status": {
            "sync": {"status": "Synced", "revision": "abc123"},
            "health": {"status": "Healthy"},
            "operationState": {"phase": "Succeeded"},
        },
    }

    status = get_argocd_app_status(_FakeCustomObjects(fake_app), "healthy-app")

    assert status["sync_status"] == "Synced"
    assert status["health_status"] == "Healthy"
    assert status["revision"] == "abc123"
    assert status["destination_namespace"] == "demo"


def test_raises_not_found_for_missing_application():
    with pytest.raises(ArgoCDAppNotFound):
        get_argocd_app_status(_FakeCustomObjects(not_found=True), "no-existe")
