from dataclasses import dataclass
from enum import Enum


COLOR_GREEN = [64, 192, 87, 255]  # RGBA
COLOR_RED = [250, 82, 82, 255]  # RGBA
COLOR_ORANGE = [253, 126, 20, 255]  # RGBA
COLOR_YELLOW = [250, 186, 5, 255]  # RGBA


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
        label="Starting", icon="server-bolt.svg", background_color=COLOR_ORANGE
    ),
    ServiceStatus.RUNNING: ServiceStatusInfo(
        label="Running", icon="server.svg", background_color=COLOR_GREEN
    ),
    ServiceStatus.STOPPING: ServiceStatusInfo(
        label="Stopping", icon="server-bolt.svg", background_color=COLOR_ORANGE
    ),
    ServiceStatus.STOPPED: ServiceStatusInfo(
        label="Stopped", icon="server-off.svg", background_color=COLOR_RED
    ),
    ServiceStatus.ERROR: ServiceStatusInfo(
        label="Error", icon="plug-x.svg", background_color=COLOR_RED
    ),
    ServiceStatus.PARTIAL: ServiceStatusInfo(
        label="Partial", icon="server-bolt.svg", background_color=COLOR_YELLOW
    ),
}
