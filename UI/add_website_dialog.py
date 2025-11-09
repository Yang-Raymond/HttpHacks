from PyQt6.QtWidgets import QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QLineEdit
from PyQt6.QtCore import Qt


class AddWebsiteDialog(QDialog):
    """Dialog for adding websites"""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle('Add Website')
        self.setModal(True)
        self.setFixedSize(480, 360)
        
        # Windows 11 styling - clean white background
        self.setStyleSheet("""
            QDialog {
                background-color: #FFFFFF;
            }
        """)
        
        self.setup_ui()
        
    def setup_ui(self):
        layout = QVBoxLayout()
        layout.setContentsMargins(32, 32, 32, 32)
        layout.setSpacing(20)
        
        # Title
        title_label = QLabel("Add Website")
        title_label.setStyleSheet("""
            font-size: 20px;
            color: #1F1F1F;
            font-family: 'Segoe UI';
            font-weight: 600;
        """)
        layout.addWidget(title_label)
        
        layout.addSpacing(8)
        
        # Website name label and input
        name_label = QLabel("Website name")
        name_label.setStyleSheet("""
            font-size: 13px;
            color: #616161;
            font-family: 'Segoe UI';
            font-weight: 600;
        """)
        layout.addWidget(name_label)
        
        self.name_input = QLineEdit()
        self.name_input.setPlaceholderText("e.g., Facebook")
        self.name_input.setStyleSheet("""
            QLineEdit {
                background-color: #F9F9F9;
                border: 2px solid #E1E1E1;
                border-radius: 6px;
                padding: 6px 7px;
                font-size: 14px;
                font-family: 'Segoe UI';
                color: #1F1F1F;
            }
            QLineEdit:focus {
                background-color: #FFFFFF;
                border: 2px solid #0067C0;
            }
        """)
        layout.addWidget(self.name_input)
        
        layout.addSpacing(12)
        
        # URL label and input
        url_label = QLabel("Website URL")
        url_label.setStyleSheet("""
            font-size: 13px;
            color: #616161;
            font-family: 'Segoe UI';
            font-weight: 600;
        """)
        layout.addWidget(url_label)
        
        self.url_input = QLineEdit()
        self.url_input.setPlaceholderText("e.g., facebook.com, *.facebook.com, fb.com")
        self.url_input.setStyleSheet("""
            QLineEdit {
                background-color: #F9F9F9;
                border: 2px solid #E1E1E1;
                border-radius: 6px;
                padding: 6px 7px;
                font-size: 14px;
                font-family: 'Segoe UI';
                color: #1F1F1F;
            }
            QLineEdit:focus {
                background-color: #FFFFFF;
                border: 2px solid #0067C0;
            }
        """)
        layout.addWidget(self.url_input)
        
        # Spacer
        layout.addStretch()
        
        # Buttons
        button_layout = QHBoxLayout()
        button_layout.setSpacing(12)
        
        cancel_button = QPushButton("Cancel")
        cancel_button.setMinimumSize(100, 40)
        cancel_button.setCursor(Qt.CursorShape.PointingHandCursor)
        cancel_button.setStyleSheet("""
            QPushButton {
                background-color: #F3F3F3;
                border: 1px solid #E1E1E1;
                border-radius: 6px;
                font-size: 14px;
                font-family: 'Segoe UI';
                color: #1F1F1F;
            }
            QPushButton:hover {
                background-color: #E8E8E8;
                border: 1px solid #D1D1D1;
            }
            QPushButton:pressed {
                background-color: #D8D8D8;
            }
        """)
        cancel_button.clicked.connect(self.reject)
        
        add_button = QPushButton("Add")
        add_button.setMinimumSize(100, 40)
        add_button.setCursor(Qt.CursorShape.PointingHandCursor)
        add_button.setStyleSheet("""
            QPushButton {
                background-color: #0067C0;
                color: white;
                border: none;
                border-radius: 6px;
                font-size: 14px;
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
        add_button.clicked.connect(self.accept)
        
        button_layout.addStretch()
        button_layout.addWidget(cancel_button)
        button_layout.addWidget(add_button)
        
        layout.addLayout(button_layout)
        
        self.setLayout(layout)
        
    def get_values(self):
        """Return the website name and URL entered by user"""
        return (self.name_input.text().strip(), self.url_input.text().strip())
