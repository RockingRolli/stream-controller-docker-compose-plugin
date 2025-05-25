import json
import os
import subprocess
from pathlib import Path
from typing import Optional

from loguru import logger as log

from config import ServiceStatus


def _run_compose(compose_file: Path | None, *args, **kwargs):
    if not compose_file or not compose_file.exists():
        print(f"Compose file does not exist: {compose_file}")
        return None

    base_cmd = [
        "docker",
        "compose",
        "-f",
        str(compose_file),
    ]
    cmd = base_cmd + list(args)

    # If running in Flatpak, use flatpak-spawn --host
    if os.environ.get("FLATPAK_ID"):
        cmd = ["flatpak-spawn", "--host"] + cmd
        kwargs["cwd"] = str(compose_file.parent)

    try:
        res = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            check=False,
            **kwargs,
        )
        return res
    except Exception as e:
        print(f"Error running docker compose command: {cmd}\n{e}")
        return None


def get_status(
    compose_file: Path | None, services: Optional[list[str]] = None
) -> ServiceStatus:
    """Returns 'running', 'stopped', or 'error' if not found or on exception.
    If multiple services: returns 'running' if all running, 'stopped' if all stopped, 'partial' if mixed, 'error' on error.
    """
    try:
        if not services:
            services = get_services(compose_file)

        # Get status for all services in one go
        result = _run_compose(compose_file, "ps", "-a", "--format=json")
        if result is None:
            return ServiceStatus.ERROR

        # Map service name to status
        service_status_map = {}
        for line in result.stdout.strip().splitlines():
            if not line.strip():
                continue
            svc = json.loads(line)
            name = svc.get("Service")
            state = svc.get("State", "").lower()
            if state == "running":
                service_status_map[name] = ServiceStatus.RUNNING
            elif state in ("exited", "stopped", "dead"):
                service_status_map[name] = ServiceStatus.STOPPED
            elif state in ("starting", "created"):
                service_status_map[name] = ServiceStatus.STARTING
            elif state in ("removing", "paused", "restarting"):
                service_status_map[name] = ServiceStatus.STOPPING
            else:
                service_status_map[name] = ServiceStatus.ERROR

        statuses = []
        for service_name in services:
            status = service_status_map.get(service_name)
            if status is None:
                statuses.append(ServiceStatus.STOPPED)
            else:
                statuses.append(status)

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


def get_services(compose_file: Path | None) -> list[str]:
    """Returns a list of services in the compose file."""
    try:
        result = _run_compose(compose_file, "config", "--services")
        if result is None:
            return []
        services = [line.strip() for line in result.stdout.splitlines() if line.strip()]
        return sorted(services)
    except Exception as e:
        print(f"Error retrieving services: {e}")
        return []


def start(compose_file: Path | None, services: Optional[list[str]]) -> bool:
    log.info(f"Starting {services}...")
    try:
        result = _run_compose(compose_file, "up", "-d", *services)
        return result is not None and result.returncode == 0
    except Exception as e:
        print(f"Error starting services: {e}")
        return False


def stop(compose_file: Path | None, services: Optional[list[str]]) -> bool:
    log.info(f"Stopping {services}...")

    try:
        result = _run_compose(compose_file, "stop", *services)
        return result is not None and result.returncode == 0
    except Exception as e:
        print(f"Error stopping services: {e}")
        return False
