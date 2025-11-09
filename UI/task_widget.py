from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
    QCheckBox, QPushButton, QLineEdit, QTextEdit
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
    
    def update_strike_through(self):
        if self.task_data.get('completed', False):
            self.label.setStyleSheet("color: #A8A8A8; text-decoration: line-through;")
            self.description.setStyleSheet("color: #D0D0D0; text-decoration: line-through;")
        else:
            self.label.setStyleSheet("color: #1F1F1F;")
            self.description.setStyleSheet("color: #707070;")


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
