import json
import subprocess
from pathlib import Path
from typing import Optional

from enums import ServiceStatus
from loguru import logger as log


def _run_compose(compose_file: Path, *args, **kwargs):
    """Encapsulate all subprocess.run calls for docker compose."""
    base_cmd = [
        "docker",
        "compose",
        "-f",
        compose_file,
    ]
    cmd = base_cmd + list(args)
    try:
        return subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            check=True,
            **kwargs,
        )
    except Exception as e:
        print(f"Error running docker compose command: {cmd}\n{e}")
        return None


def get_status(
    compose_file: Path, services: Optional[list[str]] = None
) -> ServiceStatus:
    """Returns 'running', 'stopped', or 'error' if not found or on exception.
    If multiple services: returns 'running' if all running, 'stopped' if all stopped, 'partial' if mixed, 'error' on error.
    """
    try:
        if not services:
            return ServiceStatus.ERROR

        statuses = []
        for service_name in services:
            result = _run_compose(
                compose_file, "ps", "-a", "--format=json", service_name
            )
            if result is None:
                statuses.append(ServiceStatus.ERROR)
                continue
            found = False
            for line in result.stdout.strip().splitlines():
                if not line.strip():
                    continue
                svc = json.loads(line)
                if svc.get("Service") == service_name:
                    found = True
                    state = svc.get("State", "").lower()
                    if state == "running":
                        statuses.append(ServiceStatus.RUNNING)
                    elif state in ("exited", "stopped", "dead"):
                        statuses.append(ServiceStatus.STOPPED)
                    elif state in ("starting", "created"):
                        statuses.append(ServiceStatus.STARTING)
                    elif state in ("removing", "paused", "restarting"):
                        statuses.append(ServiceStatus.STOPPING)
                    else:
                        statuses.append(ServiceStatus.ERROR)
            if not found:
                statuses.append(ServiceStatus.STOPPED)
        # Aggregate status
        unique_statuses = set(statuses)
        if len(unique_statuses) == 1:
            return unique_statuses.pop()
        elif ServiceStatus.ERROR in unique_statuses:
            return ServiceStatus.ERROR
        else:
            # Mixed state
            return ServiceStatus.PARTIAL
    except Exception as e:
        print(f"Error checking service status: {e}")
        return ServiceStatus.ERROR


def get_services(compose_file: Path) -> list[str]:
    """Returns a list of services in the compose file."""
    try:
        result = _run_compose(compose_file, "config", "--services")
        if result is None:
            return []
        return [line.strip() for line in result.stdout.splitlines() if line.strip()]
    except Exception as e:
        print(f"Error retrieving services: {e}")
        return []


def start(compose_file: Path, services: Optional[list[str]]) -> bool:
    log.info(f"Starting {services}...")
    try:
        result = _run_compose(compose_file, "up", "-d", *services)
        return result is not None and result.returncode == 0
    except Exception as e:
        print(f"Error starting services: {e}")
        return False


def stop(compose_file: Path, services: Optional[list[str]]) -> bool:
    log.info(f"Stopping {services}...")

    try:
        result = _run_compose(compose_file, "stop", *services)
        return result is not None and result.returncode == 0
    except Exception as e:
        print(f"Error stopping services: {e}")
        return False
