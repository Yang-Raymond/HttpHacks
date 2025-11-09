"""UI package for Focus Dock application
This package contains all user interface components, dialogs, and widgets used in the app.
Each module provides a specific part of the UI, such as main window, dialogs, and custom widgets."""

from .toggle_switch import ToggleSwitch
from .website_toggle_widget import WebsiteToggleWidget
from .scroll_number_widget import ScrollNumberWidget
from .time_edit_dialog import TimeEditDialog
from .clock_widget import ClockWidget
from .add_website_dialog import AddWebsiteDialog
from .add_app_dialog import AddAppDialog
from .main_window import MainWindow

__all__ = [
    'ToggleSwitch',
    'WebsiteToggleWidget',
    'ScrollNumberWidget',
    'TimeEditDialog',
    'ClockWidget',
    'AddWebsiteDialog',
    'AddAppDialog',
    'MainWindow',
]
