"""
Login Page for TranscribeNotes Application
"""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
    QLineEdit, QPushButton, QFrame, QSpacerItem, QSizePolicy
)
from PySide6.QtCore import Qt, Signal


class LoginPage(QWidget):
    """Login page for user authentication."""
    
    login_successful = Signal(str, str)  # username, role
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self._setup_ui()
    
    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        # Login card
        card = QFrame()
        card.setObjectName("card")
        card.setFixedWidth(420)
        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(40, 48, 40, 40)
        card_layout.setSpacing(24)
        
        # Header
        header_layout = QVBoxLayout()
        header_layout.setSpacing(8)
        
        title = QLabel("TranscribeNotes")
        title.setObjectName("pageTitle")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        subtitle = QLabel("Clinical Documentation System")
        subtitle.setObjectName("cardSubtitle")
        subtitle.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        header_layout.addWidget(title)
        header_layout.addWidget(subtitle)
        card_layout.addLayout(header_layout)
        
        card_layout.addSpacing(16)
        
        # Username field
        username_layout = QVBoxLayout()
        username_layout.setSpacing(8)
        
        username_label = QLabel("Username")
        username_label.setObjectName("inputLabel")
        
        self.username_input = QLineEdit()
        self.username_input.setPlaceholderText("Enter your username")
        self.username_input.setMinimumHeight(48)
        
        username_layout.addWidget(username_label)
        username_layout.addWidget(self.username_input)
        card_layout.addLayout(username_layout)
        
        # Password field
        password_layout = QVBoxLayout()
        password_layout.setSpacing(8)
        
        password_label = QLabel("Password")
        password_label.setObjectName("inputLabel")
        
        self.password_input = QLineEdit()
        self.password_input.setPlaceholderText("Enter your password")
        self.password_input.setEchoMode(QLineEdit.EchoMode.Password)
        self.password_input.setMinimumHeight(48)
        
        password_layout.addWidget(password_label)
        password_layout.addWidget(self.password_input)
        card_layout.addLayout(password_layout)
        
        # Error message (hidden by default)
        self.error_label = QLabel("")
        self.error_label.setObjectName("errorLabel")
        self.error_label.setVisible(False)
        card_layout.addWidget(self.error_label)
        
        card_layout.addSpacing(8)
        
        # Login button
        self.login_btn = QPushButton("Sign In")
        self.login_btn.setObjectName("primaryButton")
        self.login_btn.setMinimumHeight(48)
        self.login_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.login_btn.clicked.connect(self._handle_login)
        card_layout.addWidget(self.login_btn)
        
        # Footer note
        footer = QLabel("Secure local authentication • No internet required")
        footer.setObjectName("cardSubtitle")
        footer.setAlignment(Qt.AlignmentFlag.AlignCenter)
        footer.setStyleSheet("font-size: 11px; margin-top: 16px;")
        card_layout.addWidget(footer)
        
        layout.addWidget(card)
        
        # Connect enter key to login
        self.username_input.returnPressed.connect(self._handle_login)
        self.password_input.returnPressed.connect(self._handle_login)
    
    def _handle_login(self):
        """Handle login attempt."""
        username = self.username_input.text().strip()
        password = self.password_input.text()
        
        if not username or not password:
            self._show_error("Please enter both username and password")
            return
        
        # TODO: Replace with actual backend authentication
        # For skeleton, accept any non-empty credentials
        
        # Simulate checking credentials
        # In production, this would call the backend authentication endpoint
        
        # Determine role based on username (skeleton logic)
        role = "Administrator" if "admin" in username.lower() else "Psychologist"
        
        # Clear inputs
        self.password_input.clear()
        self.error_label.setVisible(False)
        
        # Emit success signal
        self.login_successful.emit(username, role)
    
    def _show_error(self, message: str):
        """Display error message."""
        self.error_label.setText(message)
        self.error_label.setVisible(True)
