from PyQt6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QSpacerItem, QSizePolicy, QDialog, QGraphicsDropShadowEffect
from PyQt6.QtCore import Qt, QTimer, QRect
from PyQt6.QtGui import QPainter, QColor, QPen, QFont
from UI.time_edit_dialog import TimeEditDialog
import subprocess
import sys
import threading
import json


class ClockWidget(QWidget):
    def __init__(self, manager=None):
        super().__init__()
        self.setWindowTitle('Clock Widget')

        # Windows 11 background
        self.setStyleSheet("background-color: transparent;")

        # Reference to blocklist manager
        self.manager = manager

        # Timer variables
        self.total_seconds = 0
        self.remaining_seconds = 0
        self.is_running = False

        # Time values
        self.time_digits = [0, 0, 0, 0, 0, 0]

        # Setup UI
        self.setup_ui()

        # Timer for countdown
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_countdown)

        # Enable focus to receive keyboard events
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)

    def setup_ui(self):
        layout = QVBoxLayout()
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        # Spacer
        layout.addSpacerItem(QSpacerItem(
            20, 40, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding))

        # Spacer
        layout.addSpacerItem(QSpacerItem(
            20, 40, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding))

        # Start/Stop button
        self.start_button = QPushButton("Start")
        self.start_button.setMinimumSize(140, 52)
        self.start_button.setCursor(Qt.CursorShape.PointingHandCursor)
        self.start_button.setStyleSheet("""
            QPushButton {
                background-color: #0067C0;
                color: white;
                border: none;
                border-radius: 26px;
                font-size: 16px;
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
        self.start_button.clicked.connect(self.toggle_timer)

        # Add shadow to button
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(15)
        shadow.setColor(QColor(0, 103, 192, 80))
        shadow.setOffset(0, 4)
        self.start_button.setGraphicsEffect(shadow)

        button_layout = QHBoxLayout()
        button_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        button_layout.addWidget(self.start_button)
        layout.addLayout(button_layout)

        layout.addSpacing(40)

        self.setLayout(layout)

    def toggle_timer(self):
        if not self.is_running:
            # Calculate total seconds from digits
            hours = self.time_digits[0] * 10 + self.time_digits[1]
            minutes = self.time_digits[2] * 10 + self.time_digits[3]
            seconds = self.time_digits[4] * 10 + self.time_digits[5]

            self.total_seconds = hours * 3600 + minutes * 60 + seconds

            if self.total_seconds > 0:
                self.remaining_seconds = self.total_seconds
                self.is_running = True
                self.start_button.setText("Stop")
                self.timer.start(1000)  # Update every second

                # Start blocking websites when timer starts
                if self.manager:
                    self.start_blocking()
        else:
            # Stop the timer
            self.is_running = False
            self.start_button.setText("Start")
            self.timer.stop()

            # Reset to the remaining time for editing
            hours = self.remaining_seconds // 3600
            minutes = (self.remaining_seconds % 3600) // 60
            seconds = self.remaining_seconds % 60

            self.time_digits[0] = hours // 10
            self.time_digits[1] = hours % 10
            self.time_digits[2] = minutes // 10
            self.time_digits[3] = minutes % 10
            self.time_digits[4] = seconds // 10
            self.time_digits[5] = seconds % 10

            # Reset total_seconds so the progress arc clears
            self.total_seconds = 0

        self.update()

    def start_blocking(self):
        """Start blocking selected websites"""
        urls = self.manager.get_blocked_urls()
        if not urls:
            return

        temp_file = "temp_blocklist.json"
        with open(temp_file, "w", encoding="utf-8") as f:
            json.dump({"blocked": urls}, f, indent=2)

        def run_blocker():
            subprocess.run([sys.executable, "mvp_blocker.py",
                           "--blocklist", temp_file, "--enable-pac"])

        threading.Thread(target=run_blocker, daemon=True).start()

    def update_countdown(self):
        if self.remaining_seconds > 0:
            self.remaining_seconds -= 1
            self.update()
        else:
            # Timer finished
            self.is_running = False
            self.start_button.setText("Start")
            self.timer.stop()
            self.update()

    def mousePressEvent(self, event):
        if not self.is_running:
            # Calculate time display area
            width = self.width()
            height = self.height()
            center_x = width // 2
            center_y = height // 3
            radius = 150

            # Check if click is within the time display area
            time_rect = QRect(center_x - radius, center_y - 40, radius * 2, 80)
            if time_rect.contains(event.pos()):
                self.open_time_edit_dialog()

    def open_time_edit_dialog(self):
        # Get current time from digits
        hours = self.time_digits[0] * 10 + self.time_digits[1]
        minutes = self.time_digits[2] * 10 + self.time_digits[3]
        seconds = self.time_digits[4] * 10 + self.time_digits[5]

        # Open dialog
        dialog = TimeEditDialog(hours, minutes, seconds, self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            # Update time from dialog
            hours, minutes, seconds = dialog.get_time()

            self.time_digits[0] = hours // 10
            self.time_digits[1] = hours % 10
            self.time_digits[2] = minutes // 10
            self.time_digits[3] = minutes % 10
            self.time_digits[4] = seconds // 10
            self.time_digits[5] = seconds % 10

            self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        # Calculate center and radius
        width = self.width()
        height = self.height()
        center_x = width // 2
        center_y = height // 3
        radius = 180

        # Draw outer circle (background) with gradient
        pen = QPen(QColor("#E8E8E8"))
        pen.setWidth(24)
        pen.setCapStyle(Qt.PenCapStyle.RoundCap)
        painter.setPen(pen)
        painter.setBrush(Qt.BrushStyle.NoBrush)
        painter.drawEllipse(center_x - radius, center_y -
                            radius, radius * 2, radius * 2)

        # Draw progress arc if timer is set with gradient effect
        if self.total_seconds > 0:
            progress = self.remaining_seconds / self.total_seconds
            span_angle = int(360 * 16 * progress)

            # Create gradient effect
            pen = QPen(QColor("#0067C0"))
            pen.setWidth(24)
            pen.setCapStyle(Qt.PenCapStyle.RoundCap)
            painter.setPen(pen)
            painter.drawArc(center_x - radius, center_y - radius,
                            radius * 2, radius * 2, 90 * 16, -span_angle)

        # Draw time text
        if self.is_running or self.total_seconds > 0:
            hours = self.remaining_seconds // 3600
            minutes = (self.remaining_seconds % 3600) // 60
            seconds = self.remaining_seconds % 60
            time_text = f"{hours:02d}:{minutes:02d}:{seconds:02d}"
        else:
            time_text = f"{self.time_digits[0]}{self.time_digits[1]}:{self.time_digits[2]}{self.time_digits[3]}:{self.time_digits[4]}{self.time_digits[5]}"

        font = QFont("Segoe UI", 48, QFont.Weight.Bold)
        painter.setFont(font)
        painter.setPen(QColor("#1F1F1F"))

        text_rect = QRect(center_x - radius, center_y - 30, radius * 2, 60)
        painter.drawText(text_rect, Qt.AlignmentFlag.AlignCenter, time_text)
