"""Tool de diagnóstico sobre eventos de Kubernetes."""

from kubernetes import client


def get_k8s_events(
    core_v1: client.CoreV1Api,
    namespace: str = "demo",
    pod_name: str | None = None,
) -> list[dict]:
    """Lista los eventos recientes de un namespace.

    Útil para causas que no quedan en los logs del contenedor, como
    `FailedScheduling` o `OOMKilled`. Si se pasa `pod_name`, filtra solo
    los eventos de ese pod.
    """
    events = core_v1.list_namespaced_event(namespace=namespace)

    result = []
    for event in events.items:
        involved = event.involved_object
        if pod_name and not (involved and involved.name == pod_name):
            continue

        last_seen = event.last_timestamp or event.event_time
        result.append(
            {
                "type": event.type,
                "reason": event.reason,
                "message": event.message,
                "involved_object": f"{involved.kind}/{involved.name}" if involved else None,
                "count": event.count,
                "last_seen": last_seen.isoformat() if last_seen else None,
            }
        )

    result.sort(key=lambda e: e["last_seen"] or "", reverse=True)
    return result
