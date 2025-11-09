from PyQt6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, 
    QSpacerItem, QSizePolicy, QMainWindow, QDialog, QFrame, QLineEdit, 
    QMessageBox, QScrollArea, QCheckBox
)
from PyQt6.QtCore import Qt, QTimer, QRect, pyqtSignal, QPropertyAnimation, QEasingCurve, pyqtProperty
from PyQt6.QtGui import QFont, QPainter, QColor, QPen, QKeyEvent, QWheelEvent
from blocklist_manager import BlocklistManager
import subprocess, sys, threading
import json


# ============================================================================
# ToggleSwitch Widget
# ============================================================================

class ToggleSwitch(QWidget):
    """Custom toggle switch widget"""
    toggled = pyqtSignal(bool)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self._checked = False
        self._circle_position = 0
        
        self.setFixedSize(50, 24)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        
        self.animation = QPropertyAnimation(self, b"circle_position", self)
        self.animation.setEasingCurve(QEasingCurve.Type.InOutCubic)
        self.animation.setDuration(200)
        
    @pyqtProperty(int)
    def circle_position(self):
        return self._circle_position
    
    @circle_position.setter
    def circle_position(self, pos):
        self._circle_position = pos
        self.update()
    
    def isChecked(self):
        return self._checked
    
    def setChecked(self, checked):
        if self._checked != checked:
            self._checked = checked
            self.animation.setStartValue(self._circle_position)
            self.animation.setEndValue(26 if checked else 0)
            self.animation.start()
            self.toggled.emit(checked)
    
    def mousePressEvent(self, event):
        self.setChecked(not self._checked)
    
    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        # Draw background track
        if self._checked:
            painter.setBrush(QColor("#4CAF50"))
        else:
            painter.setBrush(QColor("#CCCCCC"))
        
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawRoundedRect(0, 0, 50, 24, 12, 12)
        
        # Draw circle
        painter.setBrush(QColor("#FFFFFF"))
        painter.drawEllipse(2 + self._circle_position, 2, 20, 20)


# ============================================================================
# WebsiteToggleWidget (from website_toggle.py)
# ============================================================================

class WebsiteToggleWidget(QWidget):
    """Widget for toggling website blocking status"""
    def __init__(self, website_name: str):
        super().__init__()
        self.website_name = website_name
        layout = QHBoxLayout()
        self.label = QLabel(website_name)
        self.toggle = ToggleSwitch()
        layout.addWidget(self.label)
        layout.addStretch()
        layout.addWidget(self.toggle)
        self.setLayout(layout)

    def is_blocked(self) -> bool:
        return self.toggle.isChecked()

    def get_website(self) -> str:
        return self.website_name


# ============================================================================
# Combined MainWindow with Website Blocker + Timer
# ============================================================================

class MainWindow(QMainWindow):
    def __init__(self, blocklist_path="HttpHacks/blocklist.json"):
        super().__init__()
        self.setWindowTitle('Focus Timer App')
        self.setGeometry(100, 100, 1000, 600)

        self.manager = BlocklistManager(blocklist_path)
        self.website_widgets = {}

        self._setup_ui()

    def _setup_ui(self):
        main_widget = QWidget()
        main_layout = QHBoxLayout()
        main_widget.setLayout(main_layout)
        self.setCentralWidget(main_widget)

        # ===== LEFT PANEL: Website Blocker =====
        left_container = QWidget()
        left_container.setMaximumWidth(300)
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
        self.add_button = QPushButton("Add app")
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


class ScrollNumberWidget(QWidget):
    def __init__(self, min_value=0, max_value=59, initial_value=0, parent=None):
        super().__init__(parent)
        self.min_value = min_value
        self.max_value = max_value
        self.value = initial_value
        self.is_focused = False
        self.input_buffer = ""
        
        self.setFixedSize(70, 80)
        self.setStyleSheet("background-color: #F5F5F5; border: 2px solid #CCCCCC; border-radius: 5px;")
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        
    def wheelEvent(self, event: QWheelEvent):
        delta = event.angleDelta().y()
        if delta > 0:
            self.value = min(self.value + 1, self.max_value)
        else:
            self.value = max(self.value - 1, self.min_value)
        self.update()
    
    def mousePressEvent(self, event):
        self.setFocus()
        self.is_focused = True
        self.input_buffer = ""
        self.update()
    
    def focusInEvent(self, event):
        self.is_focused = True
        self.input_buffer = ""
        self.setStyleSheet("background-color: #4A90E2; border: 2px solid #2E5C8A; border-radius: 5px;")
        self.update()
    
    def focusOutEvent(self, event):
        self.is_focused = False
        if self.input_buffer:
            new_value = int(self.input_buffer)
            self.value = max(self.min_value, min(new_value, self.max_value))
        self.input_buffer = ""
        self.setStyleSheet("background-color: #F5F5F5; border: 2px solid #CCCCCC; border-radius: 5px;")
        self.update()
    
    def keyPressEvent(self, event: QKeyEvent):
        key = event.key()
        
        if Qt.Key.Key_0 <= key <= Qt.Key.Key_9:
            digit = key - Qt.Key.Key_0
            self.input_buffer += str(digit)
            
            # Limit to 2 digits
            if len(self.input_buffer) > 2:
                self.input_buffer = self.input_buffer[-2:]
            
            # Update value if valid
            temp_value = int(self.input_buffer)
            if temp_value <= self.max_value:
                self.value = temp_value
            else:
                # If exceeds max, start fresh with this digit
                self.input_buffer = str(digit)
                self.value = digit
            
            self.update()
            
        elif key == Qt.Key.Key_Backspace:
            if self.input_buffer:
                self.input_buffer = self.input_buffer[:-1]
                if self.input_buffer:
                    self.value = int(self.input_buffer)
                else:
                    self.value = 0
                self.update()
                
        elif key == Qt.Key.Key_Delete:
            self.input_buffer = ""
            self.value = 0
            self.update()
            
        elif key in (Qt.Key.Key_Return, Qt.Key.Key_Enter, Qt.Key.Key_Tab):
            self.clearFocus()
        
    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        # Draw value
        font = QFont("Arial", 32, QFont.Weight.Bold)
        painter.setFont(font)
        
        if self.is_focused:
            painter.setPen(QColor("#FFFFFF"))
        else:
            painter.setPen(QColor("#000000"))
        
        text_rect = self.rect()
        painter.drawText(text_rect, Qt.AlignmentFlag.AlignCenter, f"{self.value:02d}")
        
    def get_value(self):
        return self.value
    
    def set_value(self, value):
        self.value = max(self.min_value, min(value, self.max_value))
        self.update()


class TimeEditDialog(QDialog):
    def __init__(self, hours=0, minutes=0, seconds=0, parent=None):
        super().__init__(parent)
        self.setWindowTitle('Set Time')
        self.setModal(True)
        self.setFixedSize(350, 250)
        
        self.hours = hours
        self.minutes = minutes
        self.seconds = seconds
        
        self.setup_ui()
        
    def setup_ui(self):
        layout = QVBoxLayout()
        layout.setSpacing(20)
        
        # Title
        title = QLabel("Set Timer Duration")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title.setStyleSheet("font-size: 18px; font-weight: bold;")
        layout.addWidget(title)
        
        # Instruction
        instruction = QLabel("Use scroll wheel to adjust")
        instruction.setAlignment(Qt.AlignmentFlag.AlignCenter)
        instruction.setStyleSheet("font-size: 12px; color: #666666;")
        layout.addWidget(instruction)
        
        # Time input section
        input_layout = QHBoxLayout()
        input_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        input_layout.setSpacing(15)
        
        # Hours input
        hours_layout = QVBoxLayout()
        hours_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        hours_label = QLabel("Hours")
        hours_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        hours_label.setStyleSheet("font-size: 14px; color: #666666;")
        self.hours_widget = ScrollNumberWidget(0, 23, self.hours)
        hours_layout.addWidget(self.hours_widget)
        hours_layout.addWidget(hours_label)
        input_layout.addLayout(hours_layout)
        
        # Colon separator
        colon1 = QLabel(":")
        colon1.setStyleSheet("font-size: 32px; font-weight: bold;")
        input_layout.addWidget(colon1)
        
        # Minutes input
        minutes_layout = QVBoxLayout()
        minutes_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        minutes_label = QLabel("Minutes")
        minutes_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        minutes_label.setStyleSheet("font-size: 14px; color: #666666;")
        self.minutes_widget = ScrollNumberWidget(0, 59, self.minutes)
        minutes_layout.addWidget(self.minutes_widget)
        minutes_layout.addWidget(minutes_label)
        input_layout.addLayout(minutes_layout)
        
        # Colon separator
        colon2 = QLabel(":")
        colon2.setStyleSheet("font-size: 32px; font-weight: bold;")
        input_layout.addWidget(colon2)
        
        # Seconds input
        seconds_layout = QVBoxLayout()
        seconds_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        seconds_label = QLabel("Seconds")
        seconds_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        seconds_label.setStyleSheet("font-size: 14px; color: #666666;")
        self.seconds_widget = ScrollNumberWidget(0, 59, self.seconds)
        seconds_layout.addWidget(self.seconds_widget)
        seconds_layout.addWidget(seconds_label)
        input_layout.addLayout(seconds_layout)
        
        layout.addLayout(input_layout)
        
        # Buttons
        button_layout = QHBoxLayout()
        button_layout.setSpacing(10)
        
        cancel_button = QPushButton("Cancel")
        cancel_button.setMinimumSize(100, 40)
        cancel_button.setStyleSheet("""
            QPushButton {
                background-color: #E0E0E0;
                border-radius: 5px;
                font-size: 14px;
            }
            QPushButton:hover {
                background-color: #D0D0D0;
            }
        """)
        cancel_button.clicked.connect(self.reject)
        
        ok_button = QPushButton("OK")
        ok_button.setMinimumSize(100, 40)
        ok_button.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50;
                color: white;
                border-radius: 5px;
                font-size: 14px;
            }
            QPushButton:hover {
                background-color: #45A049;
            }
        """)
        ok_button.clicked.connect(self.accept)
        
        button_layout.addWidget(cancel_button)
        button_layout.addWidget(ok_button)
        
        layout.addLayout(button_layout)
        
        self.setLayout(layout)
        
    def get_time(self):
        return (self.hours_widget.get_value(), self.minutes_widget.get_value(), self.seconds_widget.get_value())


class ClockWidget(QWidget):
    def __init__(self, manager=None):
        super().__init__()
        self.setWindowTitle('Clock Widget')
        
        # Reference to blocklist manager
        self.manager = manager
        
        # Timer variables
        self.total_seconds = 0
        self.remaining_seconds = 0
        self.is_running = False
        
        # Time values
        self.time_digits = [0, 0, 0, 0, 0, 0]  # Hours, Hours, Minutes, Minutes, Seconds, Seconds
        
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
        layout.addSpacerItem(QSpacerItem(20, 40, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding))
        
        # Spacer
        layout.addSpacerItem(QSpacerItem(20, 40, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding))
        
        # Start/Stop button
        self.start_button = QPushButton("Start")
        self.start_button.setMinimumSize(120, 80)
        self.start_button.setStyleSheet("""
            QPushButton {
                background-color: #D3D3D3;
                border-radius: 10px;
                font-size: 18px;
                color: #333333;
            }
            QPushButton:hover {
                background-color: #C0C0C0;
            }
        """)
        self.start_button.clicked.connect(self.toggle_timer)
        
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
            subprocess.run([sys.executable, "mvp_blocker.py", "--blocklist", temp_file, "--enable-pac"])

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
        radius = 150
        
        # Draw outer circle (background)
        pen = QPen(QColor("#3C3C3C"))
        pen.setWidth(30)
        painter.setPen(pen)
        painter.setBrush(Qt.BrushStyle.NoBrush)
        painter.drawEllipse(center_x - radius, center_y - radius, radius * 2, radius * 2)
        
        # Draw progress arc if timer is set
        if self.total_seconds > 0:
            progress = self.remaining_seconds / self.total_seconds
            span_angle = int(360 * 16 * progress)  # Qt uses 1/16th of a degree
            
            pen.setColor(QColor("#5C5C5C"))
            painter.setPen(pen)
            painter.drawArc(center_x - radius, center_y - radius, radius * 2, radius * 2, 90 * 16, -span_angle)
        
        # Draw time text
        if self.is_running or self.total_seconds > 0:
            hours = self.remaining_seconds // 3600
            minutes = (self.remaining_seconds % 3600) // 60
            seconds = self.remaining_seconds % 60
            time_text = f"{hours:02d}:{minutes:02d}:{seconds:02d}"
        else:
            # Show editable time from digits
            time_text = f"{self.time_digits[0]}{self.time_digits[1]}:{self.time_digits[2]}{self.time_digits[3]}:{self.time_digits[4]}{self.time_digits[5]}"
        
        font = QFont("Arial", 36, QFont.Weight.Bold)
        painter.setFont(font)
        painter.setPen(QColor("#000000"))
        
        text_rect = QRect(center_x - radius, center_y - 20, radius * 2, 40)
        painter.drawText(text_rect, Qt.AlignmentFlag.AlignCenter, time_text)


app = QApplication([])
window = MainWindow()
window.show()
app.exec()
