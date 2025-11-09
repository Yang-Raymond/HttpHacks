"""
Focus Timer App - Main Entry Point
This file launches the application by creating the main window.
All UI components are in the UI/ directory.
"""

from PyQt6.QtWidgets import QApplication
from UI import MainWindow


def main():
    """Launch the Focus Timer application"""
    app = QApplication([])
    window = MainWindow()
    window.show()
    app.exec()


if __name__ == '__main__':
    main()
