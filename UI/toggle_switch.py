# ToggleSwitch module
# Implements a custom toggle switch widget for use in the UI.

from PyQt6.QtWidgets import QWidget
from PyQt6.QtCore import Qt, pyqtSignal, QPropertyAnimation, QEasingCurve, pyqtProperty
from PyQt6.QtGui import QPainter, QColor


class ToggleSwitch(QWidget):
    """Custom toggle switch widget"""
    toggled = pyqtSignal(bool)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._checked = False
        self._circle_position = 0

        self.setFixedSize(44, 22)
        self.setCursor(Qt.CursorShape.PointingHandCursor)

        self.animation = QPropertyAnimation(self, b"circle_position", self)
        self.animation.setEasingCurve(QEasingCurve.Type.OutCubic)
        self.animation.setDuration(150)

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
            self.animation.setEndValue(22 if checked else 0)
            self.animation.start()
            self.toggled.emit(checked)

    def mousePressEvent(self, event):
        self.setChecked(not self._checked)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        # Draw background track
        if self._checked:
            painter.setBrush(QColor("#0067C0"))
        else:
            painter.setBrush(QColor("#E1E1E1"))

        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawRoundedRect(0, 0, 44, 22, 11, 11)

        # Draw circle
        painter.setBrush(QColor("#FFFFFF"))

        # Add subtle shadow to circle
        shadow_offset = 1
        painter.setOpacity(0.2)
        painter.drawEllipse(3 + self._circle_position +
                            shadow_offset, 3 + shadow_offset, 16, 16)

        painter.setOpacity(1.0)
        painter.drawEllipse(3 + self._circle_position, 3, 16, 16)
