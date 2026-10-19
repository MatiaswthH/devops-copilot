"""Pruebas unitarias de parseo, sin depender del cluster real."""

from datetime import datetime, timezone
from types import SimpleNamespace

from src.tools.events import get_k8s_events


def _fake_event(kind, name, reason, event_type="Warning", count=1, last_timestamp=None):
    return SimpleNamespace(
        type=event_type,
        reason=reason,
        message=f"{reason} message",
        involved_object=SimpleNamespace(kind=kind, name=name),
        count=count,
        last_timestamp=last_timestamp or datetime(2026, 1, 1, tzinfo=timezone.utc),
        event_time=None,
    )


class _FakeCoreV1:
    def __init__(self, events):
        self._events = events

    def list_namespaced_event(self, namespace):
        return SimpleNamespace(items=self._events)


def test_get_k8s_events_filters_by_pod_name():
    fake = _FakeCoreV1(
        [
            _fake_event("Pod", "payments-api-abc", "BackOff"),
            _fake_event("Pod", "healthy-app-xyz", "Started", event_type="Normal"),
        ]
    )

    result = get_k8s_events(fake, namespace="demo", pod_name="payments-api-abc")

    assert len(result) == 1
    assert result[0]["reason"] == "BackOff"
    assert result[0]["involved_object"] == "Pod/payments-api-abc"


def test_get_k8s_events_without_pod_name_returns_all_sorted_by_recency():
    older = _fake_event(
        "Pod", "a", "Pulled", event_type="Normal", last_timestamp=datetime(2026, 1, 1, tzinfo=timezone.utc)
    )
    newer = _fake_event(
        "Pod", "b", "BackOff", last_timestamp=datetime(2026, 1, 2, tzinfo=timezone.utc)
    )
    fake = _FakeCoreV1([older, newer])

    result = get_k8s_events(fake, namespace="demo")

    assert [e["reason"] for e in result] == ["BackOff", "Pulled"]
