from PyQt6.QtWidgets import QWidget, QHBoxLayout, QLabel
from UI.toggle_switch import ToggleSwitch


class WebsiteToggleWidget(QWidget):
    """Widget for toggling website blocking status"""

    def __init__(self, website_name: str):
        super().__init__()
        self.website_name = website_name

        # Add card-like styling
        self.setStyleSheet("""
            WebsiteToggleWidget {
                background-color: #F9F9F9;
                border-radius: 6px;
                padding: 8px;
            }
            WebsiteToggleWidget:hover {
                background-color: #F3F3F3;
            }
        """)

        layout = QHBoxLayout()
        layout.setContentsMargins(12, 10, 12, 10)

        self.label = QLabel(website_name)
        self.label.setStyleSheet(
            "font-size: 13px; color: #1F1F1F; font-family: 'Segoe UI';")

        self.toggle = ToggleSwitch()
        layout.addWidget(self.label)
        layout.addStretch()
        layout.addWidget(self.toggle)
        self.setLayout(layout)

    def is_blocked(self) -> bool:
        return self.toggle.isChecked()

    def get_website(self) -> str:
        return self.website_name
