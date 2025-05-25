from dataclasses import dataclass
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


@dataclass
class ServiceStatusInfo:
    """Dataclass to hold service status information."""

    label: str
    icon: str
    background_color: list[int]  # RGBA as list of ints


STATUS_MAP = {
    ServiceStatus.STARTING: ServiceStatusInfo(
        label="Starting",
        icon="server-bolt.svg",
        background_color=[255, 165, 0, 255],  # Orange
    ),
    ServiceStatus.RUNNING: ServiceStatusInfo(
        label="Running",
        icon="server.svg",
        background_color=[0, 255, 0, 255],  # Green
    ),
    ServiceStatus.STOPPING: ServiceStatusInfo(
        label="Stopping",
        icon="server-bolt.svg",
        background_color=[255, 165, 0, 255],  # Orange
    ),
    ServiceStatus.STOPPED: ServiceStatusInfo(
        label="Stopped",
        icon="server-off.svg",
        background_color=[255, 0, 0, 255],  # Red
    ),
    ServiceStatus.ERROR: ServiceStatusInfo(
        label="Error",
        icon="plug-x.svg",
        background_color=[255, 0, 0, 255],  # Red
    ),
    ServiceStatus.PARTIAL: ServiceStatusInfo(
        label="Partial",
        icon="server-bolt.svg",
        background_color=[255, 255, 0, 255],  # Yellow
    ),
}
