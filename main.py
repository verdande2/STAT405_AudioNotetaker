#!/usr/bin/env python3
"""
Audio to Text Transcription and Note Taking Software
Main application entry point
"""

import sys
from PySide6.QtWidgets import QApplication
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont, QFontDatabase

from app.main_window import MainWindow
from app.styles import load_stylesheet


def main():
    # Enable high DPI scaling
    QApplication.setHighDpiScaleFactorRoundingPolicy(
        Qt.HighDpiScaleFactorRoundingPolicy.PassThrough
    )
    
    app = QApplication(sys.argv)
    app.setApplicationName("TranscribeNotes")
    app.setOrganizationName("MentalHealthTools")
    app.setApplicationVersion("1.0.0")
    
    # Load and apply stylesheet
    stylesheet = load_stylesheet()
    app.setStyleSheet(stylesheet)
    
    # Create and show main window
    window = MainWindow()
    window.show()
    
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
