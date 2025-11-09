# TimeEditDialog module
# Provides a dialog for editing time values in the application.

from PyQt6.QtWidgets import QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont
from UI.scroll_number_widget import ScrollNumberWidget


class TimeEditDialog(QDialog):
    def __init__(self, hours=0, minutes=0, seconds=0, parent=None):
        super().__init__(parent)
        self.setWindowTitle('Set Time')
        self.setModal(True)
        self.setFixedSize(420, 300)

        # Windows 11 styling
        self.setStyleSheet("""
            QDialog {
                background-color: #F9F9F9;
            }
        """)

        self.hours = hours
        self.minutes = minutes
        self.seconds = seconds

        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout()
        layout.setSpacing(24)
        layout.setContentsMargins(30, 30, 30, 30)

        # Title
        title = QLabel("Set Timer Duration")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title.setStyleSheet(
            "font-size: 20px; font-weight: 600; color: #1F1F1F; font-family: 'Segoe UI';")
        layout.addWidget(title)

        # Instruction
        instruction = QLabel("Scroll or click to adjust values")
        instruction.setAlignment(Qt.AlignmentFlag.AlignCenter)
        instruction.setStyleSheet(
            "font-size: 13px; color: #616161; font-family: 'Segoe UI';")
        layout.addWidget(instruction)

        # Time input section
        input_layout = QHBoxLayout()
        input_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        input_layout.setSpacing(20)

        # Hours input
        hours_layout = QVBoxLayout()
        hours_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        hours_layout.setSpacing(8)
        self.hours_widget = ScrollNumberWidget(0, 23, self.hours)
        hours_label = QLabel("Hours")
        hours_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        hours_label.setStyleSheet(
            "font-size: 12px; color: #616161; font-family: 'Segoe UI';")
        hours_layout.addWidget(self.hours_widget)
        hours_layout.addWidget(hours_label)
        input_layout.addLayout(hours_layout)

        # Colon separator
        colon1 = QLabel(":")
        colon1.setStyleSheet(
            "font-size: 36px; font-weight: 300; color: #8E8E8E; font-family: 'Segoe UI';")
        input_layout.addWidget(colon1)

        # Minutes input
        minutes_layout = QVBoxLayout()
        minutes_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        minutes_layout.setSpacing(8)
        self.minutes_widget = ScrollNumberWidget(0, 59, self.minutes)
        minutes_label = QLabel("Minutes")
        minutes_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        minutes_label.setStyleSheet(
            "font-size: 12px; color: #616161; font-family: 'Segoe UI';")
        minutes_layout.addWidget(self.minutes_widget)
        minutes_layout.addWidget(minutes_label)
        input_layout.addLayout(minutes_layout)

        # Colon separator
        colon2 = QLabel(":")
        colon2.setStyleSheet(
            "font-size: 36px; font-weight: 300; color: #8E8E8E; font-family: 'Segoe UI';")
        input_layout.addWidget(colon2)

        # Seconds input
        seconds_layout = QVBoxLayout()
        seconds_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        seconds_layout.setSpacing(8)
        self.seconds_widget = ScrollNumberWidget(0, 59, self.seconds)
        seconds_label = QLabel("Seconds")
        seconds_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        seconds_label.setStyleSheet(
            "font-size: 12px; color: #616161; font-family: 'Segoe UI';")
        seconds_layout.addWidget(self.seconds_widget)
        seconds_layout.addWidget(seconds_label)
        input_layout.addLayout(seconds_layout)

        layout.addLayout(input_layout)

        # Buttons
        button_layout = QHBoxLayout()
        button_layout.setSpacing(12)

        cancel_button = QPushButton("Cancel")
        cancel_button.setMinimumSize(120, 44)
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

        ok_button = QPushButton("OK")
        ok_button.setMinimumSize(120, 44)
        ok_button.setStyleSheet("""
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
        ok_button.clicked.connect(self.accept)

        button_layout.addWidget(cancel_button)
        button_layout.addWidget(ok_button)

        layout.addLayout(button_layout)

        self.setLayout(layout)

    def get_time(self):
        return (self.hours_widget.get_value(), self.minutes_widget.get_value(), self.seconds_widget.get_value())
