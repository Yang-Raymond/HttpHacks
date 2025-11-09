from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QScrollArea, QFrame, QMessageBox, QDialog, QGraphicsDropShadowEffect
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QColor
from blocklist_manager import BlocklistManager
from UI.website_toggle_widget import WebsiteToggleWidget
from UI.clock_widget import ClockWidget
from UI.add_website_dialog import AddWebsiteDialog
from UI.add_app_dialog import AddAppDialog


class MainWindow(QMainWindow):
    def __init__(self, blocklist_path="HttpHacks/blocklist.json"):
        super().__init__()
        self.setWindowTitle('Focus Timer App')
        self.setGeometry(100, 100, 1100, 700)

        # Windows 11 styling
        self.setStyleSheet("""
            QMainWindow {
                background-color: #F3F3F3;
            }
        """)

        self.manager = BlocklistManager(blocklist_path)
        self.website_widgets = {}

        self._setup_ui()

    def _setup_ui(self):
        main_widget = QWidget()
        main_widget.setStyleSheet("background-color: #F3F3F3;")
        main_layout = QHBoxLayout()
        main_layout.setSpacing(20)
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_widget.setLayout(main_layout)
        self.setCentralWidget(main_widget)

        # ===== LEFT PANEL: Website Blocker =====
        left_container = QWidget()
        left_container.setMaximumWidth(320)
        left_container.setStyleSheet("""
            QWidget {
                background-color: #FFFFFF;
                border-radius: 8px;
            }
        """)

        # Add shadow effect
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(20)
        shadow.setColor(QColor(0, 0, 0, 30))
        shadow.setOffset(0, 2)
        left_container.setGraphicsEffect(shadow)

        left_container_layout = QVBoxLayout()
        left_container_layout.setContentsMargins(0, 0, 0, 0)
        left_container_layout.setSpacing(0)
        left_container.setLayout(left_container_layout)

        # Header labels
        header_widget = QWidget()
        header_widget.setStyleSheet(
            "background-color: transparent; border-radius: 0px;")
        header_layout = QHBoxLayout()
        header_layout.setContentsMargins(20, 20, 20, 16)
        header_widget.setLayout(header_layout)

        app_name_label = QLabel("App Name")
        app_name_label.setStyleSheet(
            "font-weight: 600; font-size: 12px; color: #616161; font-family: 'Segoe UI';")
        block_label = QLabel("Blocked")
        block_label.setStyleSheet(
            "font-weight: 600; font-size: 12px; color: #616161; font-family: 'Segoe UI';")

        header_layout.addWidget(app_name_label)
        header_layout.addStretch()
        header_layout.addWidget(block_label)

        left_container_layout.addWidget(header_widget)

        # Divider line
        divider = QFrame()
        divider.setFrameShape(QFrame.Shape.HLine)
        divider.setStyleSheet("background-color: #E5E5E5; max-height: 1px;")
        left_container_layout.addWidget(divider)

        # Scroll area for website toggles
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setStyleSheet("""
            QScrollArea {
                border: none;
                background-color: transparent;
            }
            QScrollBar:vertical {
                background-color: #F3F3F3;
                width: 10px;
                border-radius: 5px;
            }
            QScrollBar::handle:vertical {
                background-color: #a8a8a8;
                border-radius: 5px;
                min-height: 20px;
            }
            QScrollBar::handle:vertical:hover {
                background-color: #A8A8A8;
            }
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
                height: 0px;
            }
        """)

        self.left_panel = QWidget()
        self.left_panel.setStyleSheet("background-color: transparent;")
        self.left_layout = QVBoxLayout()
        self.left_layout.setSpacing(4)
        self.left_layout.setContentsMargins(12, 8, 12, 8)
        self.left_panel.setLayout(self.left_layout)
        scroll_area.setWidget(self.left_panel)

        left_container_layout.addWidget(scroll_area)

        # Footer for add website
        footer_widget = QWidget()
        footer_widget.setStyleSheet(
            "background-color: transparent; border-radius: 0px;")
        footer_layout = QVBoxLayout()
        footer_layout.setContentsMargins(16, 12, 16, 16)
        footer_layout.setSpacing(8)
        footer_widget.setLayout(footer_layout)

        self.add_website_button = QPushButton("Add website")
        self.add_website_button.setStyleSheet("""
            QPushButton {
                background-color: #0067C0;
                color: white;
                border: none;
                border-radius: 5px;
                padding: 10px;
                font-size: 13px;
                font-weight: 600;
                font-family: 'Segoe UI';
            }
            QPushButton:hover {
                background-color: #005A9E;
            }
            QPushButton:pressed {
                background-color: #004578;
            }
        """)
        self.add_website_button.clicked.connect(lambda: self.handle_add_item("website"))

        self.add_app_button = QPushButton("Add app")
        self.add_app_button.setStyleSheet("""
            QPushButton {
                background-color: #0067C0;
                color: white;
                border: none;
                border-radius: 5px;
                padding: 10px;
                font-size: 13px;
                font-weight: 600;
                font-family: 'Segoe UI';
            }
            QPushButton:hover {
                background-color: #005A9E;
            }
            QPushButton:pressed {
                background-color: #004578;
            }
        """)
        self.add_app_button.clicked.connect(lambda: self.handle_add_item("app"))

        footer_layout.addWidget(self.add_website_button)
        footer_layout.addWidget(self.add_app_button)
        left_container_layout.addWidget(footer_widget)

        # Populate website toggles from blocked and unblocked
        all_sites = set()
        for site_list in self.manager.blocked.values():
            all_sites.update(site_list)
        for site_list in self.manager.unblocked.values():
            all_sites.update(site_list)

        for site in all_sites:
            self.add_website_widget(site)

        # ===== RIGHT PANEL: Timer/Clock Widget =====
        self.clock_widget = ClockWidget(self.manager)

        # Add both panels to main layout
        main_layout.addWidget(left_container, 1)
        main_layout.addWidget(self.clock_widget, 3)

    def add_website_widget(self, site_name):
        if site_name in self.website_widgets:
            return
        widget = WebsiteToggleWidget(site_name)
        widget.toggle.toggled.connect(
            lambda checked: self.update_block_status(site_name, checked)
        )
        self.left_layout.addWidget(widget)
        self.website_widgets[site_name] = widget

    def handle_add_item(self, item_type):
        """Open dialog to add website or app"""
        if item_type == "website":
            dialog = AddWebsiteDialog(self)
            if dialog.exec() == QDialog.DialogCode.Accepted:
                name, url = dialog.get_values()
                
                if name and url:
                    if name in self.website_widgets:
                        QMessageBox.warning(self, "Exists", f"{name} already exists.")
                        return
                    
                    self.manager.all_sites[name] = [url]
                    self.manager.unblocked[name] = [url]
                    self.manager.blocked[name] = []
                    self.add_website_widget(name)
                else:
                    QMessageBox.warning(self, "Input Error", "Please enter both website name and URL.")
        
        elif item_type == "app":
            dialog = AddAppDialog(self)
            if dialog.exec() == QDialog.DialogCode.Accepted:
                name, exe = dialog.get_values()
                
                if name and exe:
                    if name in self.website_widgets:
                        QMessageBox.warning(self, "Exists", f"{name} already exists.")
                        return
                    
                    self.manager.all_sites[name] = [exe]
                    self.manager.unblocked[name] = [exe]
                    self.manager.blocked[name] = []
                    self.add_website_widget(name)
                else:
                    QMessageBox.warning(self, "Input Error", "Please enter both app name and executable.")

    def update_block_status(self, site_name, blocked: bool):
        self.manager.set_blocked(site_name, blocked)
