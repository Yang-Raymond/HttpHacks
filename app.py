from PyQt6.QtWidgets import QApplication, QWidget

app = QApplication([])

window = QWidget()
window.setWindowTitle('App name')
window.show()
app.exec()
