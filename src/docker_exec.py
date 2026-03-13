import logging
import docker

logger = logging.getLogger(__name__)

_client = None


def _get_client() -> docker.DockerClient:
    global _client
    if _client is None:
        _client = docker.DockerClient(base_url="unix:///var/run/docker.sock")
    return _client


def exec_in_container(container_name: str, command: str) -> str:
    """Execute a command in a running Docker container and return stdout."""
    client = _get_client()
    container = client.containers.get(container_name)
    result = container.exec_run(command, demux=True)
    stdout = result.output[0].decode().strip() if result.output[0] else ""
    stderr = result.output[1].decode().strip() if result.output[1] else ""
    if stderr:
        logger.warning("stderr from %s: %s", container_name, stderr)
    logger.info("exec in %s: %s -> %s", container_name, command, stdout)
    return stdout
