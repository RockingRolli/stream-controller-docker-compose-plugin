import os
import sys
from pathlib import Path

sys.path.insert(0, os.path.dirname(__file__))
# Import StreamController modules

# Import python modules
import os

from config import ServiceStatus
from src.backend.DeckManagement.DeckController import DeckController
from src.backend.DeckManagement.InputIdentifier import InputIdentifier
from src.backend.PageManagement.Page import Page
from src.backend.PluginManager.ActionBase import ActionBase
from src.backend.PluginManager.PluginBase import PluginBase

# compose_file = "/home/rvo/dev/customers/psysolutions/tepavi/docker-compose.yml"
service_name = "postgres"  # Make this configurable as needed

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

        backend_path = os.path.join(
            self.plugin_base.PATH, "actions", "ToggleServices", "backend.py"
        )
        self.launch_backend(backend_path=backend_path, open_in_terminal=False)

    @property
    def compose_status(self) -> ServiceStatus:
        """Get the status of the compose file."""
        if not self.backend:
            return ServiceStatus.ERROR
        status_str = self.backend.get_status()
        return ServiceStatus(status_str)

    @property
    def compose_file_name(self) -> Path:
        """Get the compose file name."""
        settings = self.get_settings()
        path = Path(settings.get("compose_file", ""))
        return path

    @compose_file_name.setter
    def compose_file_name(self, compose_file_name: str):
        """Set the compose file name."""
        settings = self.get_settings()
        settings["compose_file"] = compose_file_name
        self.backend.set_compose_file(str(compose_file_name))
        self.set_settings(settings)
        self.compose_file_button.set_label(os.path.basename(compose_file_name))
        self.set_media()

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
        self.backend.set_service_names(services)
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

        self.compose_file_button = Gtk.Button(
            label=os.path.basename(self.compose_file_name)
        )
        self.compose_file_button.connect("clicked", on_button_clicked)
        self.compose_file_button.set_label(self.compose_file_name.name)
        self.compose_file_row = Adw.ActionRow(title="Compose File")
        self.compose_file_row.add_suffix(self.compose_file_button)

        # --- Service selection as dropdown with multi-select ---
        services = []
        if self.backend:
            try:
                services = self.backend.get_services()
            except Exception as e:
                print(f"Error getting services: {e}")

        self.services_menu_button = Gtk.MenuButton(label="Select Services")
        self.services_popover = Gtk.Popover()
        self.services_listbox = Gtk.ListBox()
        self.services_listbox.set_selection_mode(Gtk.SelectionMode.MULTIPLE)
        self._service_rows = []
        selected = set(self.selected_services)
        for svc in services:
            row = Gtk.ListBoxRow()
            box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
            check = Gtk.CheckButton(label=svc)
            check.set_active(svc in selected)
            check.service_name = svc
            box.append(check)
            row.set_child(box)
            self.services_listbox.append(row)
            self._service_rows.append(check)

        def update_services_menu_button_label():
            selected_services = self.selected_services
            if selected_services:
                # Use linebreaks for display
                label = "\n".join(selected_services)
                self.services_menu_button.set_label(label)
            else:
                self.services_menu_button.set_label("Select Services")

        def on_check_toggled(check, _):
            selected_services = [
                c.service_name for c in self._service_rows if c.get_active()
            ]
            self.selected_services = selected_services
            update_services_menu_button_label()

        for check in self._service_rows:
            check.connect("toggled", on_check_toggled, None)

        self.services_popover.set_child(self.services_listbox)
        self.services_menu_button.set_popover(self.services_popover)
        update_services_menu_button_label()

        self.services_names_row = Adw.ActionRow(title="Service Names")
        self.services_names_row.add_suffix(self.services_menu_button)

        return [
            self.compose_file_row,
            self.services_names_row,
        ]

    def update_label_and_icon(self):
        self.set_label(STATUS_TEXTS.get(self.compose_status, "N/A"))

    def on_ready(self) -> None:
        self.update_label_and_icon()

        self.backend.set_compose_file(str(self.compose_file_name))
        self.backend.set_service_names(self.selected_services)

        media_path = os.path.join(self.plugin_base.PATH, "assets", "test.png")
        self.set_media(media_path=media_path, size=0.75)
        self.set_background_color([200, 100, 123])  # Dark gray background

    def on_key_down(self) -> None:
        if self.compose_status == ServiceStatus.RUNNING:
            self.set_label("Stopping...")
            if not self.backend.stop():
                self.set_label("Error stopping")
                return
        else:
            self.set_label("Starting...")
            if not self.backend.start():
                self.set_label("Error starting")
                return

        self.update_label_and_icon()

    def on_key_up(self) -> None:
        pass
