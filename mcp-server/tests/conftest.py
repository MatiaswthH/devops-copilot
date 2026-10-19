import sys
from pathlib import Path

import pytest
from kubernetes import config
from kubernetes.config.config_exception import ConfigException

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.k8s_client import get_core_v1_client, get_custom_objects_client  # noqa: E402


def _cluster_reachable() -> bool:
    try:
        core_v1 = get_core_v1_client()
        core_v1.list_namespace(limit=1, _request_timeout=5)
        return True
    except (ConfigException, Exception):
        return False


requires_cluster = pytest.mark.skipif(
    not _cluster_reachable(),
    reason="no se pudo conectar al cluster kind (¿está levantado el contenedor?)",
)


@pytest.fixture(scope="session")
def core_v1():
    return get_core_v1_client()


@pytest.fixture(scope="session")
def custom_objects():
    return get_custom_objects_client()
