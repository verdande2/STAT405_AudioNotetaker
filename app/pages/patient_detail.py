"""
Patient Detail Page for TranscribeNotes Application
Displays individual patient profile with session history
"""

from __future__ import annotations

from datetime import datetime
from pathlib import Path

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
    QPushButton, QFrame, QScrollArea, QTabWidget,
    QTextEdit, QListWidget, QListWidgetItem, QSplitter,
    QPlainTextEdit
)
from PySide6.QtCore import Qt, Signal

from app.db import (
    AuthorizationError,
    DatabaseInitializationError,
    InvalidDatabaseKeyError,
    MissingDatabaseKeyError,
    initialize_database,
    list_client_profiles,
    list_session_records,
)


class SessionItem(QFrame):
    """Individual session item in the history list."""
    
    clicked = Signal(int)  # session_id
    
    def __init__(self, session_data: dict, parent=None):
        super().__init__(parent)
        self.session_id = session_data.get('id', 0)
        self.setObjectName("card")
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self._setup_ui(session_data)
    
    def _setup_ui(self, data: dict):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 12, 16, 12)
        layout.setSpacing(8)
        
        # Header row
        header = QHBoxLayout()
        
        date_label = QLabel(data.get('date', 'Unknown Date'))
        date_label.setObjectName("cardTitle")
        date_label.setStyleSheet("font-size: 14px;")
        header.addWidget(date_label)
        
        header.addStretch()
        
        duration_label = QLabel(data.get('duration', ''))
        duration_label.setObjectName("cardSubtitle")
        header.addWidget(duration_label)
        
        status = data.get('status', 'Complete')
        status_map = {
            "Complete": "statusComplete",
            "Processing": "statusProcessing",
            "Pending": "statusPending",
        }
        status_label = QLabel(status)
        status_label.setObjectName(status_map.get(status, "statusPending"))
        header.addWidget(status_label)
        
        layout.addLayout(header)
        
        # Summary preview
        summary = data.get('summary_preview', '')
        if summary:
            summary_label = QLabel(summary[:150] + "..." if len(summary) > 150 else summary)
            summary_label.setObjectName("cardSubtitle")
            summary_label.setWordWrap(True)
            layout.addWidget(summary_label)
    
    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.clicked.emit(self.session_id)
        super().mousePressEvent(event)


class PatientDetailPage(QWidget):
    """Detailed patient view with session history and notes."""
    
    back_requested = Signal()
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.current_patient_id = None
        self._current_account = None
        self._session_records_by_id = {}
        self._current_patient_notes = ""
        self._setup_ui()
    
    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        # Page header
        header = QWidget()
        header.setObjectName("pageHeader")
        header_layout = QHBoxLayout(header)
        header_layout.setContentsMargins(40, 24, 40, 24)
        
        # Back button and title
        title_section = QHBoxLayout()
        title_section.setSpacing(16)
        
        back_btn = QPushButton("← Back")
        back_btn.setObjectName("secondaryButton")
        back_btn.setStyleSheet("padding: 8px 16px;")
        back_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        back_btn.clicked.connect(self.back_requested.emit)
        title_section.addWidget(back_btn)
        
        title_info = QVBoxLayout()
        title_info.setSpacing(2)
        
        self.patient_name = QLabel("Patient Name")
        self.patient_name.setObjectName("pageTitle")
        
        self.patient_mrn = QLabel("Local patient profile")
        self.patient_mrn.setObjectName("pageDescription")
        
        title_info.addWidget(self.patient_name)
        title_info.addWidget(self.patient_mrn)
        title_section.addLayout(title_info)
        
        header_layout.addLayout(title_section)
        header_layout.addStretch()
        
        # Action buttons
        edit_btn = QPushButton("Edit Profile")
        edit_btn.setObjectName("secondaryButton")
        edit_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        header_layout.addWidget(edit_btn)
        
        upload_btn = QPushButton("+ Upload Session")
        upload_btn.setObjectName("primaryButton")
        upload_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        header_layout.addWidget(upload_btn)
        
        layout.addWidget(header)
        
        # Main content with splitter
        splitter = QSplitter(Qt.Orientation.Horizontal)
        splitter.setStyleSheet("QSplitter::handle { background-color: #2d3748; }")
        
        # Left panel - Session history
        left_panel = QWidget()
        left_layout = QVBoxLayout(left_panel)
        left_layout.setContentsMargins(24, 24, 12, 24)
        left_layout.setSpacing(16)
        
        sessions_header = QHBoxLayout()
        sessions_title = QLabel("Session History")
        sessions_title.setObjectName("cardTitle")
        sessions_title.setStyleSheet("font-size: 18px;")
        sessions_header.addWidget(sessions_title)
        
        self.session_count = QLabel("0 sessions")
        self.session_count.setObjectName("cardSubtitle")
        sessions_header.addWidget(self.session_count)
        sessions_header.addStretch()
        
        left_layout.addLayout(sessions_header)
        
        # Session list scroll area
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        
        self.sessions_container = QWidget()
        self.sessions_layout = QVBoxLayout(self.sessions_container)
        self.sessions_layout.setContentsMargins(0, 0, 0, 0)
        self.sessions_layout.setSpacing(8)
        self.sessions_layout.addStretch()
        
        scroll.setWidget(self.sessions_container)
        left_layout.addWidget(scroll)
        
        splitter.addWidget(left_panel)
        
        # Right panel - Session details
        right_panel = QWidget()
        right_layout = QVBoxLayout(right_panel)
        right_layout.setContentsMargins(12, 24, 24, 24)
        right_layout.setSpacing(16)
        
        # Tabs for transcript and summary
        self.tabs = QTabWidget()
        
        # Summary tab
        summary_tab = QWidget()
        summary_layout = QVBoxLayout(summary_tab)
        summary_layout.setContentsMargins(0, 16, 0, 0)
        
        self.summary_text = QPlainTextEdit()
        self.summary_text.setPlaceholderText("Select a session to view the AI-generated summary...")
        self.summary_text.setReadOnly(True)
        summary_layout.addWidget(self.summary_text)
        
        self.tabs.addTab(summary_tab, "Summary")
        
        # Transcript tab
        transcript_tab = QWidget()
        transcript_layout = QVBoxLayout(transcript_tab)
        transcript_layout.setContentsMargins(0, 16, 0, 0)
        
        self.transcript_text = QPlainTextEdit()
        self.transcript_text.setPlaceholderText("Select a session to view the full transcript...")
        self.transcript_text.setReadOnly(True)
        transcript_layout.addWidget(self.transcript_text)
        
        self.tabs.addTab(transcript_tab, "Full Transcript")
        
        # Notes tab
        notes_tab = QWidget()
        notes_layout = QVBoxLayout(notes_tab)
        notes_layout.setContentsMargins(0, 16, 0, 0)
        
        self.notes_text = QTextEdit()
        self.notes_text.setPlaceholderText("Add clinical notes for this session...")
        notes_layout.addWidget(self.notes_text)
        
        save_notes_btn = QPushButton("Save Notes")
        save_notes_btn.setObjectName("primaryButton")
        save_notes_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        notes_layout.addWidget(save_notes_btn, alignment=Qt.AlignmentFlag.AlignRight)
        
        self.tabs.addTab(notes_tab, "Clinical Notes")
        
        right_layout.addWidget(self.tabs)
        
        # Session metadata
        metadata_frame = QFrame()
        metadata_frame.setObjectName("card")
        metadata_layout = QVBoxLayout(metadata_frame)
        metadata_layout.setContentsMargins(16, 16, 16, 16)
        metadata_layout.setSpacing(8)
        
        metadata_title = QLabel("Session Details")
        metadata_title.setObjectName("cardTitle")
        metadata_title.setStyleSheet("font-size: 14px;")
        metadata_layout.addWidget(metadata_title)
        
        self.metadata_content = QLabel("Select a session to view details")
        self.metadata_content.setObjectName("cardSubtitle")
        self.metadata_content.setWordWrap(True)
        metadata_layout.addWidget(self.metadata_content)
        
        right_layout.addWidget(metadata_frame)
        
        splitter.addWidget(right_panel)
        splitter.setSizes([350, 650])
        
        layout.addWidget(splitter)

    def set_authenticated_account(self, account):
        """Set signed-in account context used for loading patient/session data."""
        self._current_account = account
        if account is None:
            self.current_patient_id = None
            self.patient_name.setText("Patient Name")
            self.patient_mrn.setText("Local patient profile")
            self._clear_session_items()
            self._reset_detail_panels()
            self.session_count.setText("0 sessions")

    def _clear_session_items(self):
        while self.sessions_layout.count() > 1:
            item = self.sessions_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

    def _reset_detail_panels(self):
        self._session_records_by_id = {}
        self.summary_text.clear()
        self.transcript_text.clear()
        self.notes_text.clear()
        self.metadata_content.setText("Select a session to view details")

    def _format_patient_name(self, first_name: str | None, last_name: str | None) -> str:
        parts = [part for part in [first_name, last_name] if part]
        return " ".join(parts) if parts else "Unnamed Patient"

    def _format_session_date(self, created_at: str | None, *, long_format: bool = False) -> str:
        if not created_at:
            return "Unknown Date"
        for fmt in ("%Y-%m-%dT%H:%M:%S.%fZ", "%Y-%m-%dT%H:%M:%SZ"):
            try:
                dt = datetime.strptime(created_at, fmt)
                return dt.strftime("%B %d, %Y") if long_format else dt.strftime("%b %d, %Y")
            except ValueError:
                continue
        return created_at

    def _build_session_item_payload(self, session) -> dict:
        summary_preview = (session.summary_text or "").strip()
        if not summary_preview:
            transcript_preview = (session.transcript_text or "").strip()
            summary_preview = transcript_preview or "No transcript or summary stored yet."

        return {
            "id": session.id,
            "date": self._format_session_date(session.created_at, long_format=True),
            "duration": "Duration TBD",
            "status": "Status TBD",
            "summary_preview": summary_preview,
        }

    def _populate_session_history(self, sessions):
        self._clear_session_items()
        self._session_records_by_id = {session.id: session for session in sessions}
        self.session_count.setText(f"{len(sessions)} session{'s' if len(sessions) != 1 else ''}")

        if not sessions:
            empty_label = QLabel("No sessions have been added for this patient yet.")
            empty_label.setObjectName("cardSubtitle")
            empty_label.setWordWrap(True)
            self.sessions_layout.insertWidget(self.sessions_layout.count() - 1, empty_label)
            return

        for session in sessions:
            item = SessionItem(self._build_session_item_payload(session))
            item.clicked.connect(self._on_session_selected)
            self.sessions_layout.insertWidget(self.sessions_layout.count() - 1, item)

    def _show_patient_overview(self, patient):
        self.patient_name.setText(
            self._format_patient_name(patient.first_name, patient.last_name)
        )
        self.patient_mrn.setText("Local patient profile")
        self._current_patient_notes = (patient.notes or "").strip()
        self.notes_text.setPlainText(
            "Clinical session notes are not stored in the local database yet.\n\n"
            "Patient profile notes:\n"
            f"{self._current_patient_notes or 'No patient notes recorded.'}"
        )
        self.metadata_content.setText(
            "Patient Details\n"
            f"Name: {self.patient_name.text()}\n"
            "Notes:\n"
            f"{self._current_patient_notes or 'No patient notes recorded.'}"
        )

    def _show_load_error(self, message: str):
        self.patient_name.setText("Patient")
        self.patient_mrn.setText("Unable to load patient details")
        self._current_patient_notes = ""
        self._clear_session_items()
        self._reset_detail_panels()
        self.session_count.setText("0 sessions")
        self.metadata_content.setText(message)
    
    def load_patient(self, patient_id: int):
        """Load patient data from backend.
        
        Args:
            patient_id: ID of patient to load
        """
        self.current_patient_id = patient_id
        self._reset_detail_panels()

        account = self._current_account
        if account is None or getattr(account, "role", None) != "psychologist":
            self._show_load_error("Sign in as a psychologist to view patient details.")
            return

        try:
            initialize_database()
            patients = list_client_profiles(account.id)
            patient = next((p for p in patients if p.id == patient_id), None)
            if patient is None:
                self._show_load_error("This patient record was not found for the signed-in account.")
                return
            sessions = list_session_records(account.id, client_profile_id=patient_id)
        except AuthorizationError as exc:
            self._show_load_error(str(exc))
            return
        except (MissingDatabaseKeyError, InvalidDatabaseKeyError) as exc:
            self._show_load_error(f"Database error: {exc}")
            return
        except DatabaseInitializationError as exc:
            self._show_load_error(f"Database setup failed: {exc}")
            return
        except Exception as exc:
            self._show_load_error(f"Failed to load patient details: {exc}")
            return

        self._show_patient_overview(patient)
        self._populate_session_history(sessions)
    
    def _load_sample_sessions(self, patient_id: int):
        """Load sample session data."""
        # Clear existing sessions
        while self.sessions_layout.count() > 1:
            item = self.sessions_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        
        sample_sessions = [
            {
                "id": 1,
                "date": "January 28, 2026",
                "duration": "45 min",
                "status": "Complete",
                "summary_preview": "Patient discussed ongoing anxiety related to school performance. Showed improvement in coping strategies."
            },
            {
                "id": 2,
                "date": "January 21, 2026",
                "duration": "52 min",
                "status": "Complete",
                "summary_preview": "Follow-up session focused on family dynamics and communication patterns."
            },
            {
                "id": 3,
                "date": "January 14, 2026",
                "duration": "48 min",
                "status": "Complete",
                "summary_preview": "Initial discussion of behavioral goals and treatment planning."
            },
            {
                "id": 4,
                "date": "January 7, 2026",
                "duration": "1h 5min",
                "status": "Complete",
                "summary_preview": "Intake assessment session. Gathered comprehensive history and baseline measures."
            },
        ]
        
        self.session_count.setText(f"{len(sample_sessions)} sessions")
        
        for session in sample_sessions:
            item = SessionItem(session)
            item.clicked.connect(self._on_session_selected)
            self.sessions_layout.insertWidget(self.sessions_layout.count() - 1, item)
    
    def _on_session_selected(self, session_id: int):
        """Handle session selection."""
        session = self._session_records_by_id.get(session_id)
        if session is not None:
            summary_text = (session.summary_text or "").strip()
            transcript_text = (session.transcript_text or "").strip()
            language = (session.detected_language or "").strip() or "Unknown / not detected"
            source_audio = (
                Path(session.source_audio_path).name
                if session.source_audio_path
                else "Unknown source"
            )

            self.summary_text.setPlainText(
                summary_text or "No summary has been generated for this session yet."
            )
            self.transcript_text.setPlainText(
                transcript_text or "No transcript has been stored for this session yet."
            )
            self.notes_text.setPlainText(
                "Clinical session notes are not stored in the local database yet.\n\n"
                "Patient profile notes:\n"
                f"{self._current_patient_notes or 'No patient notes recorded.'}"
            )
            self.metadata_content.setText(
                f"Date: {self._format_session_date(session.created_at, long_format=True)}\n"
                "Duration: Duration TBD\n"
                f"Audio Language: {language}\n"
                f"Source Audio: {source_audio}\n"
                f"Transcript Stored: {'Yes' if transcript_text else 'No'}\n"
                f"Summary Stored: {'Yes' if summary_text else 'No'}"
            )
            return

        # TODO: Hook up to backend endpoint
        
        # For skeleton, show sample data
        self.summary_text.setPlainText(
            "AI-Generated Summary\n"
            "=" * 40 + "\n\n"
            "Patient presented with moderate anxiety symptoms, primarily related to academic "
            "performance and peer relationships. During this session, we explored cognitive "
            "restructuring techniques and practiced deep breathing exercises.\n\n"
            "Key Observations:\n"
            "• Patient showed good insight into triggers\n"
            "• Demonstrated improved use of coping strategies\n"
            "• Reported better sleep quality since last session\n\n"
            "Behavioral Themes:\n"
            "• Avoidance behaviors decreasing\n"
            "• Increased engagement in extracurricular activities\n"
            "• Parent reports improved communication at home\n\n"
            "Treatment Progress:\n"
            "Patient is responding well to CBT-based interventions. Consider maintaining "
            "current treatment frequency and introducing exposure hierarchy in upcoming sessions."
        )
        
        self.transcript_text.setPlainText(
            "Session Transcript\n"
            "=" * 40 + "\n\n"
            "[00:00:15] Therapist: Good afternoon. How have things been going since our last session?\n\n"
            "[00:00:22] Patient: Hi. Things have been okay, I guess. I had a test this week that I was really nervous about.\n\n"
            "[00:00:35] Therapist: Tell me more about that. What kind of test was it?\n\n"
            "[00:00:42] Patient: It was a math test. I usually get really anxious about those because math is hard for me.\n\n"
            "[00:00:55] Therapist: And how did you handle the anxiety this time? Did you use any of the techniques we talked about?\n\n"
            "[00:01:08] Patient: Yeah, actually. I tried the breathing thing before the test started. It helped a little.\n\n"
            "[00:01:20] Therapist: That's great progress. Can you walk me through what that was like?\n\n"
            "...\n\n"
            "[Full transcript continues - 45 minutes total]"
        )
        
        self.metadata_content.setText(
            "Date: January 28, 2026\n"
            "Duration: 45 minutes\n"
            "Audio Language: English\n"
            "Transcription Quality: High (98.5%)\n"
            "Processing Time: 42 seconds\n"
            "Therapist: Dr. Jane Smith"
        )
    
    def load_sessions(self, sessions: list):
        """Load sessions from backend.
        
        Args:
            sessions: List of session dicts from API
        """
        # TODO: Hook up to backend endpoint
        # Clear existing sessions
        while self.sessions_layout.count() > 1:
            item = self.sessions_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        
        self.session_count.setText(f"{len(sessions)} sessions")
        
        for session in sessions:
            item = SessionItem(session)
            item.clicked.connect(self._on_session_selected)
            self.sessions_layout.insertWidget(self.sessions_layout.count() - 1, item)
