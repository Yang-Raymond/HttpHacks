# TaskItem module
# Represents an individual task item in the task panel.

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
    QCheckBox
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont


class TaskWidget(QWidget):
    """Individual task item widget"""
    task_deleted = pyqtSignal(object)  # Signal to notify parent when task is deleted
    task_changed = pyqtSignal()  # Signal when task is modified
    
    def __init__(self, task_data, parent=None):
        super().__init__(parent)
        self.task_data = task_data  # Dict with 'label', 'description', 'completed'
        self.setup_ui()
    
    def setup_ui(self):
        layout = QHBoxLayout()
        layout.setContentsMargins(12, 8, 12, 8)
        layout.setSpacing(8)
        
        # Checkbox
        self.checkbox = QCheckBox()
        self.checkbox.setChecked(self.task_data.get('completed', False))
        self.checkbox.setStyleSheet("""
            QCheckBox::indicator {
                width: 18px;
                height: 18px;
                border-radius: 4px;
                border: 2px solid #A8A8A8;
                background-color: white;
            }
            QCheckBox::indicator:checked {
                background-color: #0067C0;
                border-color: #0067C0;
                image: url(none);
            }
            QCheckBox::indicator:hover {
                border-color: #0067C0;
            }
        """)
        self.checkbox.stateChanged.connect(self.on_checkbox_changed)
        
        # Task content
        content_layout = QVBoxLayout()
        content_layout.setSpacing(2)
        
        self.label = QLabel(self.task_data.get('label', 'Task'))
        label_font = QFont('Segoe UI', 11)
        self.label.setFont(label_font)
        self.label.setStyleSheet("color: #1F1F1F;")
        
        self.description = QLabel(self.task_data.get('description', ''))
        desc_font = QFont('Segoe UI', 9)
        self.description.setFont(desc_font)
        self.description.setStyleSheet("color: #707070;")
        self.description.setWordWrap(True)
        
        content_layout.addWidget(self.label)
        if self.task_data.get('description'):
            content_layout.addWidget(self.description)
        
        layout.addWidget(self.checkbox)
        layout.addLayout(content_layout, 1)
        
        self.setLayout(layout)
        self.update_strike_through()
    
    def on_checkbox_changed(self, state):
        self.task_data['completed'] = (state == Qt.CheckState.Checked.value)
        self.update_strike_through()
        self.task_changed.emit()
        
        # Delete task when completed
        if self.task_data['completed']:
            self.task_deleted.emit(self)
    
    def update_strike_through(self):
        if self.task_data.get('completed', False):
            self.label.setStyleSheet("color: #A8A8A8; text-decoration: line-through;")
            self.description.setStyleSheet("color: #D0D0D0; text-decoration: line-through;")
        else:
            self.label.setStyleSheet("color: #1F1F1F;")
            self.description.setStyleSheet("color: #707070;")
