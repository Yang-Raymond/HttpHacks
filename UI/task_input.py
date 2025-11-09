# TaskInput module
# Provides an input field for adding new tasks to the panel.

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QLineEdit, QTextEdit
)
from PyQt6.QtCore import pyqtSignal


class TaskInputWidget(QWidget):
    """Widget for adding new tasks"""
    task_added = pyqtSignal(dict)  # Signal to notify parent when task is added

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout()
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(8)

        # Task label input
        self.label_input = QLineEdit()
        self.label_input.setPlaceholderText("Task name")
        self.label_input.setStyleSheet("""
            QLineEdit {
                border: 1px solid #E5E5E5;
                border-radius: 4px;
                padding: 8px;
                font-size: 11px;
                font-family: 'Segoe UI';
                background-color: white;
                color: black;
            }
            QLineEdit:focus {
                border: 2px solid #0067C0;
            }
        """)

        # Task description input
        self.description_input = QTextEdit()
        self.description_input.setPlaceholderText("Description (optional)")
        self.description_input.setMaximumHeight(60)
        self.description_input.setStyleSheet("""
            QTextEdit {
                border: 1px solid #E5E5E5;
                border-radius: 4px;
                padding: 8px;
                font-size: 10px;
                font-family: 'Segoe UI';
                background-color: white;
                color: black;
            }
            QTextEdit:focus {
                border: 2px solid #0067C0;
            }
        """)

        # Buttons
        button_layout = QHBoxLayout()
        button_layout.setSpacing(8)

        self.add_button = QPushButton("Add")
        self.add_button.setStyleSheet("""
            QPushButton {
                background-color: #0067C0;
                color: white;
                border: none;
                border-radius: 4px;
                padding: 8px 16px;
                font-size: 11px;
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
        self.add_button.clicked.connect(self.add_task)

        self.cancel_button = QPushButton("Cancel")
        self.cancel_button.setStyleSheet("""
            QPushButton {
                background-color: #F3F3F3;
                color: #1F1F1F;
                border: 1px solid #E5E5E5;
                border-radius: 4px;
                padding: 8px 16px;
                font-size: 11px;
                font-weight: 600;
                font-family: 'Segoe UI';
            }
            QPushButton:hover {
                background-color: #E5E5E5;
            }
            QPushButton:pressed {
                background-color: #D0D0D0;
            }
        """)
        self.cancel_button.clicked.connect(self.clear_inputs)

        button_layout.addWidget(self.add_button)
        button_layout.addWidget(self.cancel_button)
        button_layout.addStretch()

        layout.addWidget(self.label_input)
        layout.addWidget(self.description_input)
        layout.addLayout(button_layout)

        self.setLayout(layout)
        self.hide()  # Hidden by default

    def add_task(self):
        label = self.label_input.text().strip()
        description = self.description_input.toPlainText().strip()

        if label:
            task_data = {
                'label': label,
                'description': description,
                'completed': False
            }
            self.task_added.emit(task_data)
            self.clear_inputs()
            self.hide()

    def clear_inputs(self):
        self.label_input.clear()
        self.description_input.clear()
        self.hide()
