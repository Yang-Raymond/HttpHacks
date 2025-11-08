import sys
from PyQt6.QtWidgets import QApplication, QSystemTrayIcon, QMenu, QMessageBox, QDialog, QVBoxLayout, QLabel, QLineEdit, QPushButton
from PyQt6.QtGui import QAction, QIcon

# Import your storage/config here
from UI.config import read_config, write_config


class FocusDockUI:
    """
    This class encapsulates the entire FocusDock UI:
    - System tray icon with menu
    - Start/Stop focus session
    - Settings dialog to edit blocked apps/websites/duration
    """
    def __init__(self):
        self.app = QApplication(sys.argv)
        self.tray_icon = QSystemTrayIcon(QIcon("UI/icon.png"), self.app)

        # Menu items
        self.menu = QMenu()
        self.start_action = QAction("Start Focus Session")
        self.stop_action = QAction("Stop Focus Session")
        self.settings_action = QAction("Settings")
        self.quit_action = QAction("Quit")

        # Connect menu actions
        self.start_action.triggered.connect(self.start_session)
        self.stop_action.triggered.connect(self.stop_session)
        self.settings_action.triggered.connect(self.show_settings)
        self.quit_action.triggered.connect(self.quit_app)

        # Build tray menu
        self.menu.addAction(self.start_action)
        self.menu.addAction(self.stop_action)
        self.menu.addSeparator()
        self.menu.addAction(self.settings_action)
        self.menu.addSeparator()
        self.menu.addAction(self.quit_action)

        self.tray_icon.setContextMenu(self.menu)
        self.tray_icon.show()

        # Load config
        self.config = read_config()

        # Track session state
        self.session_active = False

    # -------------------------
    # Session control functions
    # -------------------------
    def start_session(self):
        if self.session_active:
            self.show_message("Focus session is already running!")
            return
        self.session_active = True
        self.show_message("Focus session started!\nApp blocking active.")
        # Here you would start the timer + block loops

    def stop_session(self):
        if not self.session_active:
            self.show_message("No session is running.")
            return
        self.session_active = False
        self.show_message("Focus session stopped.")
        # Here you would stop timers and unblock apps/sites

    # -------------------------
    # Settings dialog
    # -------------------------
    def show_settings(self):
        dialog = QDialog()
        dialog.setWindowTitle("FocusDock Settings")
        layout = QVBoxLayout()

        # Duration field
        layout.addWidget(QLabel("Focus Duration (minutes):"))
        duration_input = QLineEdit(str(self.config.get("durations", {}).get("medium", 50)))
        layout.addWidget(duration_input)

        # Blocked apps field
        layout.addWidget(QLabel("Blocked Apps (comma-separated):"))
        apps_input = QLineEdit(",".join(self.config.get("blocked_apps", [])))
        layout.addWidget(apps_input)

        # Blocked sites field
        layout.addWidget(QLabel("Blocked Sites (comma-separated):"))
        sites_input = QLineEdit(",".join(self.config.get("blocked_sites", [])))
        layout.addWidget(sites_input)

        # Save button
        save_btn = QPushButton("Save")
        layout.addWidget(save_btn)

        def save_settings():
            self.config["durations"]["medium"] = int(duration_input.text())
            self.config["blocked_apps"] = [x.strip() for x in apps_input.text().split(",") if x.strip()]
            self.config["blocked_sites"] = [x.strip() for x in sites_input.text().split(",") if x.strip()]
            write_config(self.config)
            dialog.accept()
            self.show_message("Settings saved!")

        save_btn.clicked.connect(save_settings)

        dialog.setLayout(layout)
        dialog.exec()

    # -------------------------
    # Helper functions
    # -------------------------
    def show_message(self, text):
        """Quick message box popup."""
        QMessageBox.information(None, "FocusDock", text)

    def quit_app(self):
        """Quit app and cleanup."""
        self.tray_icon.hide()
        self.app.quit()

    # -------------------------
    # Run the UI
    # -------------------------
    def run(self):
        sys.exit(self.app.exec())
