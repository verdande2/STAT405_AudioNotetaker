from PySide6.QtWidgets import QComboBox

class NoScrollComboBox(QComboBox):
    def wheelEvent(self, event):
        event.ignore()  # Don't handle scroll, pass it to parent