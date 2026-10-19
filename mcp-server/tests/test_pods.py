"""Pruebas unitarias de parseo, sin depender del cluster real."""

from types import SimpleNamespace

import pytest

from src.tools.pods import get_pod_logs, get_pods


def _fake_pod(name, waiting_reason=None, terminated_reason=None, restarts=0, ready=True):
    state = SimpleNamespace(
        waiting=SimpleNamespace(reason=waiting_reason) if waiting_reason else None,
    )
    last_state = SimpleNamespace(
        terminated=SimpleNamespace(reason=terminated_reason) if terminated_reason else None
    )
    container_status = SimpleNamespace(
        ready=ready, restart_count=restarts, state=state, last_state=last_state
    )
    return SimpleNamespace(
        metadata=SimpleNamespace(name=name, namespace="demo"),
        status=SimpleNamespace(phase="Running", container_statuses=[container_status]),
    )


class _FakeCoreV1:
    def __init__(self, pods):
        self._pods = pods

    def list_namespaced_pod(self, namespace):
        return SimpleNamespace(items=self._pods)


def test_get_pods_reports_waiting_reason_when_crashing():
    fake = _FakeCoreV1([_fake_pod("payments-api-abc", waiting_reason="CrashLoopBackOff", restarts=5, ready=False)])

    result = get_pods(fake, namespace="demo")

    assert result == [
        {
            "name": "payments-api-abc",
            "namespace": "demo",
            "status": "CrashLoopBackOff",
            "ready": "0/1",
            "restarts": 5,
            "last_terminated_reason": None,
        }
    ]


def test_get_pods_reports_last_terminated_reason_when_not_waiting():
    fake = _FakeCoreV1([_fake_pod("worker-abc", terminated_reason="OOMKilled", restarts=3, ready=False)])

    result = get_pods(fake, namespace="demo")

    assert result[0]["status"] == "Running"
    assert result[0]["last_terminated_reason"] == "OOMKilled"


def test_get_pods_healthy_pod():
    fake = _FakeCoreV1([_fake_pod("healthy-app-xyz", ready=True)])

    result = get_pods(fake, namespace="demo")

    assert result[0]["ready"] == "1/1"
    assert result[0]["restarts"] == 0


class _FakeCoreV1Logs:
    def __init__(self, raw_logs: bytes):
        self._raw_logs = raw_logs

    def read_namespaced_pod_log(self, name, namespace, tail_lines, _preload_content):
        return SimpleNamespace(data=self._raw_logs)


def test_get_pod_logs_decodes_bytes_and_echoes_params():
    fake = _FakeCoreV1Logs(b"FATAL: DB_HOST is not defined. Cannot connect to database.\n")

    result = get_pod_logs(fake, pod_name="payments-api-abc", namespace="demo", tail_lines=50)

    assert result == {
        "pod_name": "payments-api-abc",
        "namespace": "demo",
        "tail_lines": 50,
        "logs": "FATAL: DB_HOST is not defined. Cannot connect to database.\n",
    }


@pytest.mark.parametrize("tail_lines", [0, 501, -1])
def test_get_pod_logs_rejects_tail_lines_out_of_range(tail_lines):
    fake = _FakeCoreV1Logs(b"")

    with pytest.raises(ValueError):
        get_pod_logs(fake, pod_name="any-pod", tail_lines=tail_lines)
