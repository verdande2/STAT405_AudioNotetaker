"""
Main Window for TranscribeNotes Application
"""

import os

from PySide6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QPushButton, QStackedWidget, QFrame, QSizePolicy, QMessageBox, QApplication
)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QIcon

from app.pages.upload import UploadPage
from app.pages.patients import PatientsPage
from app.pages.patient_detail import PatientDetailPage
from app.pages.transcripts import TranscriptsPage
from app.pages.accounts import AccountsPage
from app.pages.login import LoginPage


from app.db import (
    AuthorizationError,
    DatabaseInitializationError,
    InvalidDatabaseKeyError,
    MissingDatabaseKeyError
)

from app.services import AudioSessionProcessor


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
        
        # Navigation buttons
        nav_items = [
            ("Upload Audio", 0),
            ("Patients", 1),
            ("Transcripts", 2),
            ("Account", 3),
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
        self.current_account = None
        self.audio_processor = AudioSessionProcessor()

        # application-wide settings and helper objects
        self.settings = {} # starting with blank dict, to be populated with defaults below, and overridden by .env vars
        self.summarizer = None
        self.summarizer_init_error = None

        self._setup_ui()
        self._connect_signals() # set up event handlers

        # load defaults so that there is always at least a summarizer path
        self._load_default_settings()
        
        self._load_env_vars() # override any defaults with .env vars

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
        self.upload_page = UploadPage()
        self.patients_page = PatientsPage()
        self.patient_detail_page = PatientDetailPage()
        self.transcripts_page = TranscriptsPage()
        self.accounts_page = AccountsPage()

        # Add pages to stack
        self.pages.addWidget(self.login_page)           # 0
        self.pages.addWidget(self.upload_page)          # 1
        self.pages.addWidget(self.patients_page)        # 2
        self.pages.addWidget(self.transcripts_page)     # 3
        self.pages.addWidget(self.accounts_page)        # 4
        self.pages.addWidget(self.patient_detail_page)  # 5
    
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

        # Patient detail - upload session for this patient
        self.patient_detail_page.upload_session_requested.connect(self._on_upload_session_for_patient)

        # Accounts page - keep signed-in session in sync with edits/deletes
        self.accounts_page.authenticated_account_updated.connect(
            self._on_authenticated_account_updated
        )
        self.accounts_page.authenticated_account_deleted.connect(
            self._on_authenticated_account_deleted
        )
        
        # Upload page - link to patients
        self.upload_page.patient_selection_requested.connect(
            # TODO handle event here, when user selects "new patient" from the upload page
            # do stuff

            lambda: self._on_navigation_changed(1)  # Go to patients page
        )
        self.upload_page.upload_started.connect(self._on_upload_started)

    def _on_navigation_changed(self, index: int):
        """Handle sidebar navigation changes."""
        # Map sidebar index to page index (offset by 1 for login page)
        if index == 0:
            self.upload_page.refresh_patients()
        if index == 1:
            self.patients_page.refresh_patients()
        if index == 2:
            self.transcripts_page.refresh_transcripts()
        if index == 3:
            self.accounts_page.refresh_accounts()
        self.pages.setCurrentIndex(index + 1)
    
    def _on_login_success(self, username: str, role: str):
        """Handle successful login."""
        self.current_account = self.login_page.current_account
        self.sidebar.set_user(username, role)
        self.upload_page.set_authenticated_account(self.current_account)
        self.patients_page.set_authenticated_account(self.current_account)
        self.patient_detail_page.set_authenticated_account(self.current_account)
        self.transcripts_page.set_authenticated_account(self.current_account)
        self.accounts_page.set_authenticated_account(self.current_account)
        self.sidebar.setVisible(True)
        self.patients_page.refresh_patients()
        self.sidebar.set_active_page(1)
        self.pages.setCurrentIndex(2)  # Patients
    
    def _on_logout(self):
        """Handle logout request."""
        self.current_account = None
        self.login_page.current_account = None
        self.upload_page.set_authenticated_account(None)
        self.patients_page.set_authenticated_account(None)
        self.patient_detail_page.set_authenticated_account(None)
        self.transcripts_page.set_authenticated_account(None)
        self.accounts_page.set_authenticated_account(None)
        self._show_login()
    
    def _show_login(self):
        """Show login page and hide sidebar."""
        self.sidebar.setVisible(False)
        self.pages.setCurrentIndex(0)
    
    def _on_view_patient(self, patient_id: int):
        """Handle request to view patient details."""
        self.patient_detail_page.set_authenticated_account(self.current_account)
        self.patient_detail_page.load_patient(patient_id)
        self.pages.setCurrentIndex(5)  # Patient detail page
    
    def _on_back_to_patients(self):
        """Return to patients list."""
        self.pages.setCurrentIndex(2)  # Patients page
        self.sidebar.set_active_page(1)  # Update sidebar selection

    def _on_upload_session_for_patient(self, patient_id: int):
        """Navigate to upload page with the given patient pre-selected."""
        self.upload_page.refresh_patients()
        if patient_id:
            self.upload_page.select_patient(patient_id)
        self.sidebar.set_active_page(0)
        self.pages.setCurrentIndex(1)  # Upload page

    def _on_authenticated_account_updated(self, account):
        """Update current session after editing the signed-in account."""
        self.current_account = account
        self.login_page.current_account = account
        role = "Administrator" if getattr(account, "role", "") == "admin" else "Psychologist"
        self.sidebar.set_user(account.display_name, role)
        self.upload_page.set_authenticated_account(account)
        self.patients_page.set_authenticated_account(account)
        self.patient_detail_page.set_authenticated_account(account)
        self.transcripts_page.set_authenticated_account(account)
        self.accounts_page.set_authenticated_account(account)

    def _on_authenticated_account_deleted(self):
        """Force logout when the signed-in account is deleted."""
        self._on_logout()

    def _on_upload_started(self, files: list[str], patient_id: int):
        """Process queued uploads and persist sessions.

        Pipeline stages are delegated to `AudioSessionProcessor`.
        """
        # first, check current acc role, display dialog/modal if not a psychologist role
        account = self.current_account
        if account is None or getattr(account, "role", None) != "psychologist":
            QMessageBox.warning(
                self,
                "Upload Audio",
                "Sign in as a psychologist to process uploads.",
            )
            self.upload_page.finish_processing() # jump to end
            return # kick back to referrer

        if not files:
            self.upload_page.finish_processing() # jump to end
            return # kick back to referrer

        # counters for success/failure (failure is a list of tuples: (file_path, reason))
        successes = 0
        failures: list[tuple[str, str]] = []

        for file_path in files:
            try:
                self.upload_page.set_file_progress(file_path, 5)
                QApplication.processEvents()

                processed_result = self.audio_processor.process_audio_file(
                    psychologist_account_id=account.id,
                    client_profile_id=patient_id,
                    source_audio_path=file_path,
                    progress_callback=lambda value, fp=file_path: self._update_upload_progress(fp, value),
                )
                
                # `process_audio_file()` persists `summary_text` to the session
                # record before returning. Keeping the result here makes it easy
                # to add UI hooks that use the generated summary later.
                _ = processed_result.summary_text
                self.upload_page.set_file_complete(file_path) # set complete for this upload item
                QApplication.processEvents()
                successes += 1
            except (
                AuthorizationError,
                MissingDatabaseKeyError,
                InvalidDatabaseKeyError,
                DatabaseInitializationError,
            ) as exc:
                message = str(exc)
                self.upload_page.set_file_error(file_path, "DB/Auth Error")
                failures.append((file_path, message))
                QApplication.processEvents()
            except Exception as exc:
                message = str(exc) or exc.__class__.__name__
                self.upload_page.set_file_error(file_path, "Processing Error")
                failures.append((file_path, message))
                QApplication.processEvents()

        self._refresh_after_upload_processing(patient_id=patient_id)
        self.upload_page.finish_processing(clear_completed=(successes > 0 and not failures))

        if failures:
            error_lines = "\n".join(
                f"- {file}: {reason}" for file, reason in failures[:5]
            )
            suffix = "\n..." if len(failures) > 5 else ""
            QMessageBox.warning(
                self,
                "Upload Processing Complete",
                f"Processed {successes} file(s) successfully.\n"
                f"Failed: {len(failures)}\n\n"
                f"{error_lines}{suffix}",
            )
            return

        QMessageBox.information(
            self,
            "Upload Processing Complete",
            f"Processed and saved {successes} file(s).",
        )

    def _update_upload_progress(self, file_path: str, value: int):
        self.upload_page.set_file_progress(file_path, value)
        QApplication.processEvents()

    def _refresh_after_upload_processing(self, *, patient_id: int | None = None):
        self.patients_page.refresh_patients()
        self.transcripts_page.refresh_transcripts()
        self.upload_page.refresh_patients()
        if (
            patient_id is not None
            and getattr(self.patient_detail_page, "current_patient_id", None) == patient_id
            and self.current_account is not None
        ):
            self.patient_detail_page.load_patient(patient_id)

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
            'output_language': 'en', # English summary/transcript output by default
            'word_timestamps': False, # enable word-level timestamps (extra compute/time required)
            'speaker_diarization': True,
            "translation": True,
            'model_path': 'models/Qwen3-4B-Q5_0.gguf', # model_path is specific for the summarizer: .gguf model file
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
            # TODO add additional transcription/translation/diarization/etc settings to default dict here
        }
        
        self._sync_audio_processor_config()
        # ensure summarizer object exists for the default
        self._ensure_summarizer()

    def _on_settings_changed(self, new_settings: dict):
        """Callback from settings page when the user presses "Save".

        We merge the dictionary, persist it if necessary, and recreate any
        heavy objects that depend on the values (currently just the
        summarizer model)."""
        self.settings.update(new_settings)
        self._sync_audio_processor_config()
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
                model_path = self.settings.get('model_path')
                # if path is somehow empty, let Summary figure out default
                self.summarizer = Summary(path=model_path if model_path else None)
                self.summarizer_init_error = None
                self.audio_processor.set_summarizer(self.summarizer)
            except Exception as exc:
                self.summarizer = None
                self.summarizer_init_error = str(exc)
                self.audio_processor.set_summarizer(None)
                return

    def get_summarizer(self):
        """Return the current summarizer instance (may be ``None``)."""
        return self.summarizer

    def _sync_audio_processor_config(self) -> None:
        """Keep the upload processor aligned with current summarizer settings."""
        model_path = self.settings.get('model_path') if isinstance(self.settings, dict) else None
        self.audio_processor.set_model_path(model_path)

    def _load_env_vars(self) -> None:
        """Load environment variables for settings."""
        
        self.settings = {
            "default_language": os.getenv(
                "INPUT_DEFAULT_LANGUAGE", None
            ),  # input language, this and below both follow ISO 639-1 standard (2char lang code)
            "output_language": os.getenv(
                "OUTPUT_DEFAULT_LANGUAGE", "en"
            ),  # English summary/transcript output by default
            "word_timestamps": False,  # enable word-level timestamps (extra compute/time required)
            "translation": True,
            "speaker_diarization": True,  # id unique speakers if possible
            "cached_model_dir": os.getenv(
                "CACHED_MODEL_DIR", "./tmp"
            ),
            
            "model_path": "models/Qwen3-4B-Q5_0.gguf",  # model_path is specific for the summarizer: .gguf model file
            "summary_length": "standard",
            "include_quotes": True,
            "behavioral_themes": True,
            "treatment_suggestions": False,
            "storage_path": "/var/lib/transcribenotes/data",
            "auto_backup": True,
            "backup_retention": 30,
            "processing_device": "auto",
            "max_threads": 4,
            "batch_processing": True,
            "theme": "dark",
            "session_timeout": 30,
            "confirm_delete": True,
            "show_notifications": True,
            # TODO add additional transcription/translation/diarization/etc settings to default dict here
        }
        