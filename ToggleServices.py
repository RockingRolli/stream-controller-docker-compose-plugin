import os
import sys
from pathlib import Path

sys.path.append(os.path.dirname(__file__))

from enums import ServiceStatus
from ui.ServicesSelection import ServicesSelection
import docker_compose as dc
from src.backend.DeckManagement.DeckController import DeckController
from src.backend.DeckManagement.InputIdentifier import InputIdentifier
from src.backend.PageManagement.Page import Page
from src.backend.PluginManager.ActionBase import ActionBase
from src.backend.PluginManager.PluginBase import PluginBase

# Import gtk modules - used for the config rows
import gi

gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")
from gi.repository import Adw, Gtk

STATUS_TEXTS = {
    ServiceStatus.STARTING: "Starting",
    ServiceStatus.RUNNING: "Running",
    ServiceStatus.STOPPING: "Stopping",
    ServiceStatus.STOPPED: "Stopped",
    ServiceStatus.ERROR: "Error",
}


class ToggleServices(ActionBase):
    def __init__(
        self,
        action_id: str,
        action_name: str,
        deck_controller: "DeckController",
        page: "Page",
        plugin_base: "PluginBase",
        state: int,
        input_ident: "InputIdentifier",
    ):
        super().__init__(
            action_id=action_id,
            action_name=action_name,
            deck_controller=deck_controller,
            page=page,
            plugin_base=plugin_base,
            state=state,
            input_ident=input_ident,
        )

    def set_image(self, image_name: str):
        asset_path = Path(self.plugin_base.PATH) / "assets" / image_name
        self.set_media(media_path=asset_path, size=0.75)

    @property
    def compose_status(self) -> ServiceStatus:
        """Get the status of the compose file."""
        return dc.get_status(self.compose_file_name, self.selected_services)

    @property
    def compose_file_name(self) -> Path | None:
        """Get the compose file name."""
        settings = self.get_settings()

        compose_file = settings.get("compose_file", None)
        if not compose_file:
            return None

        path = Path(compose_file)
        return path

    @compose_file_name.setter
    def compose_file_name(self, compose_file_name: str):
        """Set the compose file name."""
        settings = self.get_settings()
        settings["compose_file"] = compose_file_name
        self.set_settings(settings)
        self.compose_file_button.set_label(os.path.basename(compose_file_name))

        self.service_selection_row.set_service_names(
            dc.get_services(Path(compose_file_name))
        )

    @property
    def selected_services(self) -> list:
        """Get the selected service names."""
        settings = self.get_settings()
        service_names = settings.get("service_names", [])
        return service_names

    @selected_services.setter
    def selected_services(self, services: list):
        """Set the selected service names."""
        settings = self.get_settings()
        settings["service_names"] = services
        self.set_settings(settings)

    def on_file_selected(self, dialog, result):
        file = dialog.open_finish(result)
        if file:
            self.compose_file_name = file.get_path()

    def get_config_rows(self) -> list:
        def on_button_clicked(button):
            dialog = Gtk.FileDialog()
            dialog.set_title("Select Compose File")
            dialog.open(
                self.compose_file_button.get_root(), None, self.on_file_selected
            )

        label = "(None)"
        if self.compose_file_name:
            label = os.path.basename(self.compose_file_name)

        self.compose_file_button = Gtk.Button(label=label)
        self.compose_file_button.connect("clicked", on_button_clicked)
        # self.compose_file_button.set_label(self.compose_file_name.name)
        self.compose_file_row = Adw.ActionRow(title="Compose File")
        self.compose_file_row.add_suffix(self.compose_file_button)

        # --- Service selection as dropdown with multi-select ---
        services = []
        try:
            services = dc.get_services(self.compose_file_name)
        except Exception as e:
            print(f"Error getting services: {e}")

        def services_selection_changed(service_names: list[str]):
            """Callback to update the selected services when the selection changes."""
            self.selected_services = service_names
            self.update_label_and_icon()

        self.service_selection_row = ServicesSelection(services_selection_changed)
        self.service_selection_row.set_service_names(services, self.selected_services)

        return [
            self.compose_file_row,
            self.service_selection_row,
        ]

    def update_label_and_icon(self):
        if not self.compose_file_name:
            self.set_label("No File")
            self.set_image("file-unknown.svg")
            return

        if not self.selected_services:
            self.set_label("No SVCs")
            self.set_image("file-unknown.svg")
            return

        compose_status = self.compose_status

        if compose_status == ServiceStatus.STOPPED:
            self.set_image("server-off.svg")
        elif compose_status == ServiceStatus.RUNNING:
            self.set_image("server.svg")
        elif compose_status in (
            ServiceStatus.STARTING,
            ServiceStatus.STOPPING,
            ServiceStatus.PARTIAL,
        ):
            self.set_image("server-bolt.svg")
        elif compose_status.ERROR:
            self.set_image("plug-x.svg")

        self.set_label(STATUS_TEXTS.get(self.compose_status, "N/A"))

    def on_ready(self) -> None:
        self.update_label_and_icon()

    def on_key_down(self) -> None:
        if self.compose_status == ServiceStatus.RUNNING:
            self.set_label("Stopping...")
            self.set_image("server-bolt.svg")
            if not dc.stop(self.compose_file_name, self.selected_services):
                self.set_label("Error stopping")
                return
        else:
            self.set_label("Starting...")
            self.set_image("server-bolt.svg")
            if not dc.start(self.compose_file_name, self.selected_services):
                self.set_label("Error starting")
                return

        self.update_label_and_icon()

    def on_key_up(self) -> None:
        pass
