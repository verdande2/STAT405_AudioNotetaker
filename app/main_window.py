"""
Main Window for TranscribeNotes Application
"""

from PySide6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QPushButton, QStackedWidget, QFrame, QSizePolicy
)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QIcon

from app.pages.dashboard import DashboardPage
from app.pages.upload import UploadPage
from app.pages.patients import PatientsPage
from app.pages.patient_detail import PatientDetailPage
from app.pages.transcripts import TranscriptsPage
from app.pages.accounts import AccountsPage
from app.pages.settings import SettingsPage
from app.pages.login import LoginPage


class NavigationButton(QPushButton):
    """Custom navigation button for sidebar."""
    
    def __init__(self, text: str, icon_text: str = "", parent=None):
        super().__init__(parent)
        self.setText(f"  {icon_text}  {text}" if icon_text else text)
        self.setObjectName("navButton")
        self.setCheckable(True)
        self.setCursor(Qt.CursorShape.PointingHandCursor)


class Sidebar(QWidget):
    """Sidebar navigation component."""
    
    navigation_changed = Signal(int)
    logout_requested = Signal()
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("sidebar")
        self.buttons = []
        self._setup_ui()
    
    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        # Header
        header = QWidget()
        header.setObjectName("sidebarHeader")
        header_layout = QVBoxLayout(header)
        header_layout.setContentsMargins(20, 24, 20, 20)
        
        title = QLabel("TranscribeNotes")
        title.setObjectName("appTitle")
        
        subtitle = QLabel("Clinical Documentation")
        subtitle.setObjectName("appSubtitle")
        
        header_layout.addWidget(title)
        header_layout.addWidget(subtitle)
        layout.addWidget(header)
        
        # Navigation buttons
        nav_items = [
            ("Dashboard", 0),
            ("Upload Audio", 1),
            ("Patients", 2),
            ("Transcripts", 3),
            ("Accounts", 4),
            ("Settings", 5),
        ]
        
        nav_container = QWidget()
        nav_layout = QVBoxLayout(nav_container)
        nav_layout.setContentsMargins(0, 16, 0, 16)
        nav_layout.setSpacing(4)
        
        for text, index in nav_items:
            btn = NavigationButton(text)
            btn.clicked.connect(lambda checked, idx=index: self._on_nav_clicked(idx))
            self.buttons.append(btn)
            nav_layout.addWidget(btn)
        
        # Set first button as checked
        if self.buttons:
            self.buttons[0].setChecked(True)
        
        layout.addWidget(nav_container)
        layout.addStretch()
        
        # User section at bottom
        user_section = QWidget()
        user_section.setObjectName("userSection")
        user_layout = QVBoxLayout(user_section)
        user_layout.setContentsMargins(16, 16, 16, 16)
        user_layout.setSpacing(4)
        
        self.user_name = QLabel("Dr. Jane Smith")
        self.user_name.setObjectName("userName")
        
        self.user_role = QLabel("Psychologist")
        self.user_role.setObjectName("userRole")
        
        logout_btn = QPushButton("Logout")
        logout_btn.setObjectName("navButton")
        logout_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        logout_btn.clicked.connect(self.logout_requested.emit)
        
        user_layout.addWidget(self.user_name)
        user_layout.addWidget(self.user_role)
        user_layout.addSpacing(12)
        user_layout.addWidget(logout_btn)
        
        layout.addWidget(user_section)
    
    def _on_nav_clicked(self, index: int):
        for i, btn in enumerate(self.buttons):
            btn.setChecked(i == index)
        self.navigation_changed.emit(index)
    
    def set_user(self, name: str, role: str):
        """Update displayed user information."""
        self.user_name.setText(name)
        self.user_role.setText(role)
    
    def set_active_page(self, index: int):
        """Programmatically set the active navigation item."""
        for i, btn in enumerate(self.buttons):
            btn.setChecked(i == index)


class MainWindow(QMainWindow):
    """Main application window."""
    
    def __init__(self):
        super().__init__()
        self.setWindowTitle("TranscribeNotes - Clinical Documentation System")
        self.setMinimumSize(1200, 800)

        # application-wide settings and helper objects
        self.settings = {}
        self.summarizer = None

        self._setup_ui()
        self._connect_signals()

        # load defaults so that there is always at least a summarizer path
        self._load_default_settings()

        # Start with login page
        self._show_login()
        self.showMaximized()
    
    def _setup_ui(self):
        # Central widget
        central = QWidget()
        central.setObjectName("centralWidget")
        self.setCentralWidget(central)
        
        # Main layout
        main_layout = QHBoxLayout(central)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        
        # Sidebar
        self.sidebar = Sidebar()
        self.sidebar.setVisible(False)  # Hidden until login
        main_layout.addWidget(self.sidebar)
        
        # Content area
        content_widget = QWidget()
        content_widget.setObjectName("contentArea")
        content_layout = QVBoxLayout(content_widget)
        content_layout.setContentsMargins(0, 0, 0, 0)
        content_layout.setSpacing(0)
        
        # Stacked widget for pages
        self.pages = QStackedWidget()
        content_layout.addWidget(self.pages)
        
        main_layout.addWidget(content_widget)
        
        # Create pages
        self.login_page = LoginPage()
        self.dashboard_page = DashboardPage()
        self.upload_page = UploadPage()
        self.patients_page = PatientsPage()
        self.patient_detail_page = PatientDetailPage()
        self.transcripts_page = TranscriptsPage()
        self.accounts_page = AccountsPage()
        self.settings_page = SettingsPage()
        
        # Add pages to stack
        self.pages.addWidget(self.login_page)      # 0
        self.pages.addWidget(self.dashboard_page)  # 1
        self.pages.addWidget(self.upload_page)     # 2
        self.pages.addWidget(self.patients_page)   # 3
        self.pages.addWidget(self.transcripts_page) # 4
        self.pages.addWidget(self.accounts_page)   # 5
        self.pages.addWidget(self.settings_page)   # 6
        self.pages.addWidget(self.patient_detail_page) # 7
    
    def _connect_signals(self):
        # Sidebar navigation
        self.sidebar.navigation_changed.connect(self._on_navigation_changed)
        self.sidebar.logout_requested.connect(self._on_logout)
        
        # Login page
        self.login_page.login_successful.connect(self._on_login_success)
        
        # Patients page - view patient detail
        self.patients_page.view_patient_requested.connect(self._on_view_patient)
        
        # Patient detail - back to list
        self.patient_detail_page.back_requested.connect(self._on_back_to_patients)
        
        # Upload page - link to patients
        self.upload_page.patient_selection_requested.connect(
            lambda: self._on_navigation_changed(2)  # Go to patients page
        )

        # Settings page - when the user saves settings, update our state
        self.settings_page.settings_changed.connect(self._on_settings_changed)
    
    def _on_navigation_changed(self, index: int):
        """Handle sidebar navigation changes."""
        # Map sidebar index to page index (offset by 1 for login page)
        self.pages.setCurrentIndex(index + 1)
    
    def _on_login_success(self, username: str, role: str):
        """Handle successful login."""
        self.sidebar.set_user(username, role)
        self.sidebar.setVisible(True)
        self.pages.setCurrentIndex(1)  # Dashboard
    
    def _on_logout(self):
        """Handle logout request."""
        self._show_login()
    
    def _show_login(self):
        """Show login page and hide sidebar."""
        self.sidebar.setVisible(False)
        self.pages.setCurrentIndex(0)
    
    def _on_view_patient(self, patient_id: int):
        """Handle request to view patient details."""
        self.patient_detail_page.load_patient(patient_id)
        self.pages.setCurrentIndex(7)  # Patient detail page
    
    def _on_back_to_patients(self):
        """Return to patients list."""
        self.pages.setCurrentIndex(3)  # Patients page
        self.sidebar.set_active_page(2)  # Update sidebar selection

    def _load_default_settings(self):
        """Populate ``self.settings`` with every key the settings page uses.

        This is called during initialization so that other parts of the
        application can safely read ``self.settings['model_path']`` etc without
        having to check for missing keys.  In a real app these values would come
        from a file or database.
        """
        # copy the defaults from SettingsPage._reset_defaults manually
        self.settings = {
            'default_language': 'auto',
            'output_language': 'en',
            'word_timestamps': True,
            'speaker_diarization': False,
            'model_path': 'models/Qwen3-4B-Q5_0.gguf',
            'summary_length': 'standard',
            'include_quotes': True,
            'behavioral_themes': True,
            'treatment_suggestions': False,
            'storage_path': '/var/lib/transcribenotes/data',
            'auto_backup': True,
            'backup_retention': 30,
            'processing_device': 'auto',
            'max_threads': 4,
            'batch_processing': True,
            'theme': 'dark',
            'session_timeout': 30,
            'confirm_delete': True,
            'show_notifications': True,
        }
        # ensure summarizer object exists for the default
        self._ensure_summarizer()

    def _on_settings_changed(self, new_settings: dict):
        """Callback from settings page when the user presses "Save".

        We merge the dictionary, persist it if necessary, and recreate any
        heavy objects that depend on the values (currently just the
        summarizer model)."""
        self.settings.update(new_settings)
        # if summarizer model path changed we need a new instance
        self._ensure_summarizer(force_reload=True)

    def _ensure_summarizer(self, force_reload: bool = False):
        """Create or reload the :class:`Summary` object if needed.

        The upload page will grab ``self.summarizer`` when it needs to perform
        a summary.  We lazily create it so that startup doesn't blow up when
        the model file is missing; it will raise as soon as someone hits the
        button.
        """
        if self.summarizer is None or force_reload:
            try:
                from app.lm.Summarizer import Summary
            except ImportError:
                self.summarizer = None
                return

            model_path = self.settings.get('model_path')
            # if path is somehow empty, let Summary figure out default
            self.summarizer = Summary(path=model_path if model_path else None)

    def get_summarizer(self):
        """Return the current summarizer instance (may be ``None``)."""
        return self.summarizer
