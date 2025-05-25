import sys
import os
import json

sys.path.insert(0, os.path.dirname(__file__))

import subprocess

from streamcontroller_plugin_tools import BackendBase
from loguru import logger as log

from config import ServiceStatus


class DockerComposeBackend(BackendBase):
    def __init__(self):
        super().__init__()
        self.compose_file = None
        self.service_names = []  # Now supports a list of service names

    def _run_compose(self, *args, **kwargs):
        """Encapsulate all subprocess.run calls for docker compose."""
        base_cmd = [
            "docker",
            "compose",
            "-f",
            self.compose_file,
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

    def set_compose_file(self, compose_file: str):
        """Sets the compose file path."""
        self.compose_file = compose_file

    def set_service_names(self, services_names):
        """Sets the service names as a list."""
        if isinstance(services_names, str):
            # Accept comma or whitespace separated string
            self.service_names = [
                s.strip() for s in services_names.replace(",", " ").split() if s.strip()
            ]
        elif isinstance(services_names, list):
            self.service_names = services_names
        else:
            self.service_names = []

    def can_run(self) -> bool:
        log.info(self)
        """Checks if the backend can run with the current compose file and service names."""
        if not self.compose_file or not os.path.isfile(self.compose_file):
            log.error("Compose file is not set or does not exist.")
            return False
        if not self.service_names:
            log.error("No service names provided.")
            return False
        return True

    def get_status(self) -> str:
        """Returns 'running', 'stopped', or 'error' if not found or on exception.
        If multiple services: returns 'running' if all running, 'stopped' if all stopped, 'partial' if mixed, 'error' on error.
        """
        if not self.can_run():
            return ServiceStatus.ERROR.value

        try:
            if not self.service_names:
                return ServiceStatus.ERROR.value

            statuses = []
            for service_name in self.service_names:
                result = self._run_compose("ps", "-a", "--format=json", service_name)
                if result is None:
                    statuses.append(ServiceStatus.ERROR.value)
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
                            statuses.append(ServiceStatus.RUNNING.value)
                        elif state in ("exited", "stopped", "dead"):
                            statuses.append(ServiceStatus.STOPPED.value)
                        elif state in ("starting", "created"):
                            statuses.append(ServiceStatus.STARTING.value)
                        elif state in ("removing", "paused", "restarting"):
                            statuses.append(ServiceStatus.STOPPING.value)
                        else:
                            statuses.append(ServiceStatus.ERROR.value)
                if not found:
                    statuses.append(ServiceStatus.STOPPED.value)
            # Aggregate status
            unique_statuses = set(statuses)
            if len(unique_statuses) == 1:
                return unique_statuses.pop()
            elif ServiceStatus.ERROR.value in unique_statuses:
                return ServiceStatus.ERROR.value
            else:
                # Mixed state
                return ServiceStatus.PARTIAL.value
        except Exception as e:
            print(f"Error checking service status: {e}")
            return ServiceStatus.ERROR.value

    def get_services(self) -> list:
        """Returns a list of services in the compose file."""
        if not self.compose_file:
            return ServiceStatus.ERROR.value

        try:
            result = self._run_compose("config", "--services")
            if result is None:
                return []
            return [line.strip() for line in result.stdout.splitlines() if line.strip()]
        except Exception as e:
            print(f"Error retrieving services: {e}")
            return []

    def start(self) -> bool:
        if not self.can_run():
            return ServiceStatus.ERROR.value

        log.info(f"Starting {self.service_names}...")
        try:
            result = self._run_compose("up", "-d", *self.service_names)
            return result is not None and result.returncode == 0
        except Exception as e:
            print(f"Error starting services: {e}")
            return False

    def stop(self) -> bool:
        if not self.can_run():
            return ServiceStatus.ERROR.value

        log.info(f"Stopping {self.service_names}...")

        try:
            result = self._run_compose("stop", *self.service_names)
            return result is not None and result.returncode == 0
        except Exception as e:
            print(f"Error stopping services: {e}")
            return False


backend = DockerComposeBackend()
