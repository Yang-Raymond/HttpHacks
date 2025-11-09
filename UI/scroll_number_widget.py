from PyQt6.QtWidgets import QWidget
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QPainter, QColor, QFont, QKeyEvent, QWheelEvent


class ScrollNumberWidget(QWidget):
    def __init__(self, min_value=0, max_value=59, initial_value=0, parent=None):
        super().__init__(parent)
        self.min_value = min_value
        self.max_value = max_value
        self.value = initial_value
        self.is_focused = False
        self.input_buffer = ""

        self.setFixedSize(80, 90)
        self.setStyleSheet("""
            background-color: #F9F9F9;
            border: 2px solid #E1E1E1;
            border-radius: 8px;
        """)
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
        self.setStyleSheet("""
            background-color: #FFFFFF;
            border: 2px solid #0067C0;
            border-radius: 8px;
        """)
        self.update()

    def focusOutEvent(self, event):
        self.is_focused = False
        if self.input_buffer:
            new_value = int(self.input_buffer)
            self.value = max(self.min_value, min(new_value, self.max_value))
        self.input_buffer = ""
        self.setStyleSheet("""
            background-color: #F9F9F9;
            border: 2px solid #E1E1E1;
            border-radius: 8px;
        """)
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
        font = QFont("Segoe UI", 36, QFont.Weight.Bold)
        painter.setFont(font)

        if self.is_focused:
            painter.setPen(QColor("#0067C0"))
        else:
            painter.setPen(QColor("#1F1F1F"))

        text_rect = self.rect()
        painter.drawText(
            text_rect, Qt.AlignmentFlag.AlignCenter, f"{self.value:02d}")

    def get_value(self):
        return self.value

    def set_value(self, value):
        self.value = max(self.min_value, min(value, self.max_value))
        self.update()
