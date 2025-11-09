from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QFrame,
    QLineEdit, QPushButton, QMessageBox, QScrollArea
)
from website_toggle import WebsiteToggleWidget
from blocklist_manager import BlocklistManager
import subprocess, sys, threading
import json

class MainWindow(QMainWindow):
    def __init__(self, blocklist_path="blocklist.json"):
        super().__init__()
        self.setWindowTitle("Focus App")
        self.setGeometry(100,100,800,500)

        self.manager = BlocklistManager(blocklist_path)
        self.website_widgets = {}

        self._setup_ui()

    def _setup_ui(self):
        main_widget = QWidget()
        main_layout = QHBoxLayout()
        main_widget.setLayout(main_layout)
        self.setCentralWidget(main_widget)

        # Left panel container
        left_container = QWidget()
        left_container_layout = QVBoxLayout()
        left_container.setLayout(left_container_layout)

        # Scroll area for website toggles
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        self.left_panel = QWidget()
        self.left_layout = QVBoxLayout()
        self.left_panel.setLayout(self.left_layout)
        scroll_area.setWidget(self.left_panel)

        left_container_layout.addWidget(scroll_area)

        # Footer for add website
        footer_widget = QWidget()
        footer_layout = QVBoxLayout()
        footer_widget.setLayout(footer_layout)
        self.input_field = QLineEdit()
        self.input_field.setPlaceholderText("Enter website...")
        self.add_button = QPushButton("Add Website")
        self.add_button.clicked.connect(self.handle_add_website)
        footer_layout.addWidget(self.input_field)
        footer_layout.addWidget(self.add_button)
        left_container_layout.addWidget(footer_widget)

        # Populate website toggles from blocked and unblocked
        all_sites = set()
        for site_list in self.manager.blocked.values():
            all_sites.update(site_list)
        for site_list in self.manager.unblocked.values():
            all_sites.update(site_list)

        for site in all_sites:
            self.add_website_widget(site)

        # Right panel (control)
        right_panel = QFrame()
        right_panel.setFrameShape(QFrame.Shape.StyledPanel)
        right_layout = QVBoxLayout()
        right_panel.setLayout(right_layout)

        self.start_button = QPushButton("Start Blocking")
        self.start_button.clicked.connect(self.start_blocking)
        right_layout.addWidget(self.start_button)
        right_layout.addStretch()

        main_layout.addWidget(left_container, 1)
        main_layout.addWidget(right_panel, 2)

    def add_website_widget(self, site_name):
        if site_name in self.website_widgets:
            return
        widget = WebsiteToggleWidget(site_name)
        widget.toggle.stateChanged.connect(
            lambda _: self.update_block_status(site_name, widget.is_blocked())
        )
        self.left_layout.addWidget(widget)
        self.website_widgets[site_name] = widget

    def handle_add_website(self):
        site = self.input_field.text().strip()
        if site:
            if site in self.website_widgets:
                QMessageBox.warning(self, "Exists", f"{site} already exists.")
                return
            self.manager.all_sites[site] = [site]
            self.manager.unblocked[site] = [site]
            self.manager.blocked[site] = []
            self.add_website_widget(site)
            self.input_field.clear()
        else:
            QMessageBox.warning(self, "Input Error", "Please enter a website name.")

    def update_block_status(self, site_name, blocked: bool):
        self.manager.set_blocked(site_name, blocked)

    def start_blocking(self):
        urls = self.manager.get_blocked_urls()
        if not urls:
            QMessageBox.warning(self,"No Sites","No sites selected to block.")
            return
        
        temp_file = "temp_blocklist.json"
        with open(temp_file, "w", encoding="utf-8") as f:
            json.dump({"blocked": urls}, f, indent=2)

        def run_blocker():
            subprocess.run([sys.executable, "mvp_blocker.py", "--blocklist", temp_file, "--enable-pac"])

        threading.Thread(target=run_blocker, daemon=True).start()
        QMessageBox.information(self,"Blocking Started","Blocking service is now running.")
