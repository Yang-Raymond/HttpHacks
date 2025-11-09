from PyQt6.QtWidgets import QWidget, QHBoxLayout, QLabel, QCheckBox

class WebsiteToggleWidget(QWidget):
    def __init__(self, website_name: str):
        super().__init__()
        self.website_name = website_name
        self.layout = QHBoxLayout()
        self.label = QLabel(website_name)
        self.toggle = QCheckBox("Block")
        self.layout.addWidget(self.label)
        self.layout.addWidget(self.toggle)
        self.setLayout(self.layout)

    def is_blocked(self) -> bool:
        return self.toggle.isChecked()

    def get_website(self) -> str:
        return self.website_name
