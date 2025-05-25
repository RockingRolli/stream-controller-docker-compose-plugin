import gi

gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")
from gi.repository import Gtk, Adw


class ServicesSelection(Adw.ActionRow):
    def __init__(self, on_selection_change, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.set_title("Select Services")
        self.set_subtitle("Choose services to manage")
        self.set_activatable(True)

        self._service_rows = []
        self.selected_services = []

        self.on_selection_change = on_selection_change

        self.services_popover = Gtk.Popover()
        self.services_popover.set_has_arrow(False)
        self.services_listbox = Gtk.ListBox()
        self.services_listbox.set_selection_mode(Gtk.SelectionMode.MULTIPLE)
        self.services_popover.set_child(self.services_listbox)

        # Set a fixed width for the MenuButton to prevent jumping
        self.services_menu_button = Gtk.MenuButton(label="Select Services")
        self.services_menu_button.set_popover(self.services_popover)
        self.services_menu_button.set_direction(Gtk.ArrowType.RIGHT)
        self.services_menu_button.set_size_request(180, -1)

        self.add_suffix(self.services_menu_button)

    def update_services_menu_button_label(self):
        selected_services = self.selected_services
        if selected_services:
            # Use linebreaks for display
            label = "\n".join(selected_services)
            self.services_menu_button.set_label(label)
        else:
            self.services_menu_button.set_label("Select Services")

    def on_check_toggled(self, *args, **kwargs):
        selected_services = [
            c.service_name for c in self._service_rows if c.get_active()
        ]
        self.selected_services = selected_services
        self.update_services_menu_button_label()
        self.on_selection_change(selected_services)

    def set_service_names(
        self, service_names: list[str], selected_services: list[str] = None
    ):
        """Sets the service names and updates the check buttons."""
        self._service_rows = []
        if selected_services is None:
            selected_services = []

        self.selected_services = set(selected_services)

        for svc in service_names:
            row = Gtk.ListBoxRow()
            box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
            check = Gtk.CheckButton(label=svc)
            check.set_active(svc in self.selected_services)
            check.service_name = svc
            box.append(check)
            row.set_child(box)
            self.services_listbox.append(row)
            self._service_rows.append(check)

        for check in self._service_rows:
            check.connect("toggled", self.on_check_toggled, None)

        self.update_services_menu_button_label()
