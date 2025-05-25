# Import StreamController modules
from src.backend.PluginManager.PluginBase import PluginBase
from src.backend.PluginManager.ActionHolder import ActionHolder

# Import actions
from .actions.ToggleServices.ToggleServices import ToggleServices


class PluginTemplate(PluginBase):
    def __init__(self):
        super().__init__()

        ## Register actions
        self.simple_action_holder = ActionHolder(
            plugin_base=self,
            action_base=ToggleServices,
            action_id="docker-compose::ToggleServices",
            action_name="Toggle Services",
        )
        self.add_action_holder(self.simple_action_holder)

        # Register plugin
        self.register(
            plugin_name="Docker Compose",
            github_repo="https://github.com/RockingRolli/stream-controller-docker-compose-plugin",
            plugin_version="0.0.1",
            app_version="1.1.1-alpha",
        )
