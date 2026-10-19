"""Tools de diagnóstico sobre pods de Kubernetes."""

from kubernetes import client


def get_pods(core_v1: client.CoreV1Api, namespace: str = "demo") -> list[dict]:
    """Lista los pods de un namespace y muestra su estado actual."""
    pods = core_v1.list_namespaced_pod(namespace=namespace)

    result = []

    for pod in pods.items:
        container_statuses = pod.status.container_statuses or []

        ready_containers = sum(1 for status in container_statuses if status.ready)
        restart_count = sum(status.restart_count for status in container_statuses)

        waiting_reasons = [
            status.state.waiting.reason
            for status in container_statuses
            if status.state.waiting is not None
        ]
        # Un contenedor que ya murió antes (ej. OOMKilled) no queda en
        # `waiting`, solo en `last_state` -> sin esto, el agente no ve la
        # causa real de un restart y solo ve "Running" o "Waiting".
        last_terminated_reasons = [
            status.last_state.terminated.reason
            for status in container_statuses
            if status.last_state is not None and status.last_state.terminated is not None
        ]

        status_reason = waiting_reasons[0] if waiting_reasons else pod.status.phase

        result.append(
            {
                "name": pod.metadata.name,
                "namespace": pod.metadata.namespace,
                "status": status_reason or "Unknown",
                "ready": f"{ready_containers}/{len(container_statuses)}",
                "restarts": restart_count,
                "last_terminated_reason": last_terminated_reasons[0]
                if last_terminated_reasons
                else None,
            }
        )

    return result


def get_pod_logs(
    core_v1: client.CoreV1Api,
    pod_name: str,
    namespace: str = "demo",
    tail_lines: int = 100,
) -> dict:
    """Obtiene las últimas líneas de logs de un pod de Kubernetes.

    Usa esta herramienta para investigar errores de arranque, como un
    CrashLoopBackOff. Por seguridad, devuelve como máximo 500 líneas.
    """
    if not 1 <= tail_lines <= 500:
        raise ValueError("tail_lines debe estar entre 1 y 500")

    response = core_v1.read_namespaced_pod_log(
        name=pod_name,
        namespace=namespace,
        tail_lines=tail_lines,
        _preload_content=False,
    )
    raw_logs = response.data
    logs = (
        raw_logs.decode("utf-8", errors="replace")
        if isinstance(raw_logs, bytes)
        else str(raw_logs)
    )

    return {
        "pod_name": pod_name,
        "namespace": namespace,
        "tail_lines": tail_lines,
        "logs": logs,
    }
