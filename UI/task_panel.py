from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
    QPushButton, QScrollArea, QFrame, QGraphicsDropShadowEffect
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QColor, QFont
from UI.task_item import TaskWidget
from UI.task_input import TaskInputWidget
import json
import os


class TaskPanel(QWidget):
    """Right panel for managing tasks"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.tasks_file = "tasks.json"
        self.tasks = []
        self.task_widgets = []
        
        self.load_tasks()
        self.setup_ui()
    
    def setup_ui(self):
        # Container with white background and shadow
        self.setStyleSheet("""
            QWidget {
                background-color: #FFFFFF;
                border-radius: 8px;
            }
        """)
        
        # Add shadow effect
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(20)
        shadow.setColor(QColor(0, 0, 0, 30))
        shadow.setOffset(0, 2)
        self.setGraphicsEffect(shadow)
        
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        
        # Header
        header_widget = QWidget()
        header_widget.setStyleSheet("background-color: transparent; border-radius: 0px;")
        header_layout = QHBoxLayout()
        header_layout.setContentsMargins(20, 20, 20, 16)
        
        title_label = QLabel("Tasks")
        title_font = QFont('Segoe UI', 16, QFont.Weight.Bold)
        title_label.setFont(title_font)
        title_label.setStyleSheet("color: #1F1F1F;")
        
        self.add_task_button = QPushButton("+")
        self.add_task_button.setFixedSize(32, 32)
        self.add_task_button.setCursor(Qt.CursorShape.PointingHandCursor)
        self.add_task_button.setStyleSheet("""
            QPushButton {
                background-color: transparent;
                color: #0067C0;
                font-size: 20px;
                font-weight: bold;
            }
            QPushButton:hover {
                color: grey;
            }
        """)
        self.add_task_button.clicked.connect(self.show_task_input)
        
        header_layout.addWidget(title_label)
        header_layout.addStretch()
        header_layout.addWidget(self.add_task_button)
        header_widget.setLayout(header_layout)
        
        # Divider
        divider = QFrame()
        divider.setFrameShape(QFrame.Shape.HLine)
        divider.setStyleSheet("background-color: #E5E5E5; max-height: 1px;")
        
        # Task input widget (hidden by default)
        self.task_input = TaskInputWidget()
        self.task_input.task_added.connect(self.add_task)
        
        # Scroll area for tasks
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setStyleSheet("""
            QScrollArea {
                border: none;
                background-color: transparent;
            }
            QScrollBar:vertical {
                background-color: #F3F3F3;
                width: 10px;
                border-radius: 5px;
            }
            QScrollBar::handle:vertical {
                background-color: #A8A8A8;
                border-radius: 5px;
                min-height: 20px;
            }
            QScrollBar::handle:vertical:hover {
                background-color: #808080;
            }
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
                height: 0px;
            }
        """)
        
        self.task_container = QWidget()
        self.task_container.setStyleSheet("background-color: transparent;")
        self.task_layout = QVBoxLayout()
        self.task_layout.setSpacing(2)
        self.task_layout.setContentsMargins(8, 8, 8, 8)
        self.task_layout.addStretch()
        self.task_container.setLayout(self.task_layout)
        scroll_area.setWidget(self.task_container)
        
        # Add widgets to main layout
        main_layout.addWidget(header_widget)
        main_layout.addWidget(divider)
        main_layout.addWidget(self.task_input)
        main_layout.addWidget(scroll_area, 1)
        
        self.setLayout(main_layout)
        
        # Load existing tasks
        self.refresh_tasks()
    
    def show_task_input(self):
        """Show the task input widget"""
        self.task_input.show()
        self.task_input.label_input.setFocus()
    
    def add_task(self, task_data):
        """Add a new task"""
        self.tasks.append(task_data)
        self.save_tasks()
        self.refresh_tasks()
    
    def delete_task(self, task_widget):
        """Delete a task"""
        if task_widget.task_data in self.tasks:
            self.tasks.remove(task_widget.task_data)
            self.save_tasks()
            self.refresh_tasks()
    
    def on_task_changed(self):
        """Save tasks when any task is modified"""
        self.save_tasks()
    
    def refresh_tasks(self):
        """Refresh the task list display"""
        # Clear existing task widgets
        for widget in self.task_widgets:
            widget.deleteLater()
        self.task_widgets.clear()
        
        # Remove stretch
        if self.task_layout.count() > 0:
            item = self.task_layout.takeAt(self.task_layout.count() - 1)
            if item:
                item.invalidate()
        
        # Add task widgets
        for task_data in self.tasks:
            task_widget = TaskWidget(task_data)
            task_widget.task_changed.connect(self.on_task_changed)
            task_widget.task_deleted.connect(self.delete_task)
            
            # Add separator
            if self.task_widgets:
                separator = QFrame()
                separator.setFrameShape(QFrame.Shape.HLine)
                separator.setStyleSheet("background-color: #F3F3F3; max-height: 1px;")
                self.task_layout.addWidget(separator)
            
            self.task_layout.addWidget(task_widget)
            self.task_widgets.append(task_widget)
        
        # Add stretch at the end
        self.task_layout.addStretch()
    
    def load_tasks(self):
        """Load tasks from JSON file"""
        if os.path.exists(self.tasks_file):
            try:
                with open(self.tasks_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self.tasks = data.get('tasks', [])
            except Exception as e:
                print(f"Error loading tasks: {e}")
                self.tasks = []
        else:
            self.tasks = []
    
    def save_tasks(self):
        """Save tasks to JSON file"""
        try:
            with open(self.tasks_file, 'w', encoding='utf-8') as f:
                json.dump({'tasks': self.tasks}, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"Error saving tasks: {e}")
