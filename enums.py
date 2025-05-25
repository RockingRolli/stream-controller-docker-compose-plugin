from enum import Enum


class ServiceStatus(Enum):
    """Enum for service status."""

    STARTING = "Starting"
    RUNNING = "Running"
    STOPPING = "Stopping"
    STOPPED = "Stopped"
    ERROR = "Error"
    PARTIAL = "Partial"

    def __str__(self):
        return self.value
