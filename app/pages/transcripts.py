"""
Transcripts Page for TranscribeNotes Application
Search, filter, and manage all transcripts
"""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
    QPushButton, QFrame, QScrollArea, QLineEdit,
    QTableWidget, QTableWidgetItem, QHeaderView,
    QComboBox, QAbstractItemView, QDateEdit,
    QDialog, QTextEdit, QPlainTextEdit, QSplitter
)
from PySide6.QtCore import Qt, Signal, QDate


class TranscriptDetailDialog(QDialog):
    """Dialog for viewing full transcript details."""
    
    def __init__(self, transcript_data: dict, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Transcript Details")
        self.setMinimumSize(800, 600)
        self._setup_ui(transcript_data)
    
    def _setup_ui(self, data: dict):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(32, 32, 32, 32)
        layout.setSpacing(24)
        
        # Header
        header = QHBoxLayout()
        
        title_section = QVBoxLayout()
        title = QLabel(data.get('patient_name', 'Unknown Patient'))
        title.setObjectName("dialogTitle")
        
        subtitle = QLabel(f"Session: {data.get('date', 'Unknown Date')} • {data.get('duration', '')}")
        subtitle.setObjectName("cardSubtitle")
        
        title_section.addWidget(title)
        title_section.addWidget(subtitle)
        header.addLayout(title_section)
        
        header.addStretch()
        
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
        
        # Content splitter
        splitter = QSplitter(Qt.Orientation.Vertical)
        
        # Summary section
        summary_frame = QFrame()
        summary_frame.setObjectName("card")
        summary_layout = QVBoxLayout(summary_frame)
        summary_layout.setContentsMargins(16, 16, 16, 16)
        
        summary_title = QLabel("AI Summary")
        summary_title.setObjectName("cardTitle")
        summary_layout.addWidget(summary_title)
        
        summary_text = QPlainTextEdit()
        summary_text.setPlainText(data.get('summary', 'No summary available'))
        summary_text.setReadOnly(True)
        summary_text.setMaximumHeight(150)
        summary_layout.addWidget(summary_text)
        
        splitter.addWidget(summary_frame)
        
        # Full transcript section
        transcript_frame = QFrame()
        transcript_frame.setObjectName("card")
        transcript_layout = QVBoxLayout(transcript_frame)
        transcript_layout.setContentsMargins(16, 16, 16, 16)
        
        transcript_title = QLabel("Full Transcript")
        transcript_title.setObjectName("cardTitle")
        transcript_layout.addWidget(transcript_title)
        
        transcript_text = QPlainTextEdit()
        transcript_text.setPlainText(data.get('transcript', 'No transcript available'))
        transcript_text.setReadOnly(True)
        transcript_layout.addWidget(transcript_text)
        
        splitter.addWidget(transcript_frame)
        splitter.setSizes([200, 400])
        
        layout.addWidget(splitter)
        
        # Close button
        close_btn = QPushButton("Close")
        close_btn.setObjectName("secondaryButton")
        close_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        close_btn.clicked.connect(self.accept)
        layout.addWidget(close_btn, alignment=Qt.AlignmentFlag.AlignRight)


class TranscriptsPage(QWidget):
    """Transcripts management page with search and filtering."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self._setup_ui()
    
    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        # Page header
        header = QWidget()
        header.setObjectName("pageHeader")
        header_layout = QVBoxLayout(header)
        header_layout.setContentsMargins(40, 32, 40, 32)
        header_layout.setSpacing(4)
        
        title = QLabel("Transcripts")
        title.setObjectName("pageTitle")
        
        description = QLabel("Search, filter, and review all session transcripts")
        description.setObjectName("pageDescription")
        
        header_layout.addWidget(title)
        header_layout.addWidget(description)
        layout.addWidget(header)
        
        # Content
        content = QWidget()
        content.setObjectName("pageContent")
        content_layout = QVBoxLayout(content)
        content_layout.setContentsMargins(40, 24, 40, 32)
        content_layout.setSpacing(20)
        
        # Search and filter bar
        filter_frame = QFrame()
        filter_frame.setObjectName("card")
        filter_layout = QVBoxLayout(filter_frame)
        filter_layout.setContentsMargins(20, 20, 20, 20)
        filter_layout.setSpacing(16)
        
        # Row 1: Search
        search_layout = QHBoxLayout()
        
        self.search_input = QLineEdit()
        self.search_input.setObjectName("searchInput")
        self.search_input.setPlaceholderText("🔍  Search transcripts by content, patient name, or keywords...")
        self.search_input.textChanged.connect(self._filter_transcripts)
        search_layout.addWidget(self.search_input)
        
        search_btn = QPushButton("Search")
        search_btn.setObjectName("primaryButton")
        search_btn.setStyleSheet("padding: 10px 24px;")
        search_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        search_layout.addWidget(search_btn)
        
        filter_layout.addLayout(search_layout)
        
        # Row 2: Filters
        filters_layout = QHBoxLayout()
        filters_layout.setSpacing(16)
        
        # Patient filter
        patient_label = QLabel("Patient:")
        patient_label.setObjectName("cardSubtitle")
        filters_layout.addWidget(patient_label)
        
        self.patient_filter = QComboBox()
        self.patient_filter.addItem("All Patients")
        self.patient_filter.addItem("John Doe")
        self.patient_filter.addItem("Maria Santos")
        self.patient_filter.addItem("Alex Rodriguez")
        self.patient_filter.setMinimumWidth(150)
        filters_layout.addWidget(self.patient_filter)
        
        # Status filter
        status_label = QLabel("Status:")
        status_label.setObjectName("cardSubtitle")
        filters_layout.addWidget(status_label)
        
        self.status_filter = QComboBox()
        self.status_filter.addItem("All Status")
        self.status_filter.addItem("Complete")
        self.status_filter.addItem("Processing")
        self.status_filter.addItem("Pending Review")
        self.status_filter.setMinimumWidth(130)
        filters_layout.addWidget(self.status_filter)
        
        # Date range
        date_label = QLabel("Date Range:")
        date_label.setObjectName("cardSubtitle")
        filters_layout.addWidget(date_label)
        
        self.date_from = QDateEdit()
        self.date_from.setCalendarPopup(True)
        self.date_from.setDate(QDate.currentDate().addMonths(-1))
        filters_layout.addWidget(self.date_from)
        
        to_label = QLabel("to")
        to_label.setObjectName("cardSubtitle")
        filters_layout.addWidget(to_label)
        
        self.date_to = QDateEdit()
        self.date_to.setCalendarPopup(True)
        self.date_to.setDate(QDate.currentDate())
        filters_layout.addWidget(self.date_to)
        
        filters_layout.addStretch()
        
        clear_btn = QPushButton("Clear Filters")
        clear_btn.setObjectName("secondaryButton")
        clear_btn.setStyleSheet("padding: 8px 16px;")
        clear_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        clear_btn.clicked.connect(self._clear_filters)
        filters_layout.addWidget(clear_btn)
        
        filter_layout.addLayout(filters_layout)
        
        content_layout.addWidget(filter_frame)
        
        # Results table
        self.table = QTableWidget()
        self.table.setColumnCount(6)
        self.table.setHorizontalHeaderLabels([
            "Date", "Patient", "Duration", "Language", "Status", "Actions"
        ])
        
        # Table styling
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Fixed)
        self.table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.Fixed)
        self.table.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeMode.Fixed)
        self.table.horizontalHeader().setSectionResizeMode(4, QHeaderView.ResizeMode.Fixed)
        self.table.horizontalHeader().setSectionResizeMode(5, QHeaderView.ResizeMode.Fixed)
        
        self.table.setColumnWidth(0, 130)
        self.table.setColumnWidth(2, 80)
        self.table.setColumnWidth(3, 90)
        self.table.setColumnWidth(4, 110)
        self.table.setColumnWidth(5, 180)
        
        self.table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.table.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.table.setAlternatingRowColors(True)
        self.table.verticalHeader().setVisible(False)
        self.table.setShowGrid(False)
        
        # Load sample data
        self._load_sample_data()
        
        content_layout.addWidget(self.table)
        
        # Results count and pagination
        pagination_layout = QHBoxLayout()
        
        self.results_label = QLabel("Showing 1-15 of 156 transcripts")
        self.results_label.setObjectName("cardSubtitle")
        pagination_layout.addWidget(self.results_label)
        
        pagination_layout.addStretch()
        
        prev_btn = QPushButton("← Previous")
        prev_btn.setObjectName("secondaryButton")
        prev_btn.setStyleSheet("padding: 8px 16px;")
        prev_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        pagination_layout.addWidget(prev_btn)
        
        next_btn = QPushButton("Next →")
        next_btn.setObjectName("secondaryButton")
        next_btn.setStyleSheet("padding: 8px 16px;")
        next_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        pagination_layout.addWidget(next_btn)
        
        content_layout.addLayout(pagination_layout)
        
        layout.addWidget(content)
    
    def _load_sample_data(self):
        """Load sample transcript data."""
        sample_transcripts = [
            {"id": 1, "date": "Jan 28, 2026", "patient": "John Doe", "duration": "45 min", "language": "English", "status": "Complete"},
            {"id": 2, "date": "Jan 27, 2026", "patient": "Maria Santos", "duration": "1h 12min", "language": "Spanish→EN", "status": "Processing"},
            {"id": 3, "date": "Jan 26, 2026", "patient": "Alex Rodriguez", "duration": "32 min", "language": "English", "status": "Complete"},
            {"id": 4, "date": "Jan 25, 2026", "patient": "Kim Thompson", "duration": "58 min", "language": "English", "status": "Pending"},
            {"id": 5, "date": "Jan 24, 2026", "patient": "James Wilson", "duration": "41 min", "language": "English", "status": "Complete"},
            {"id": 6, "date": "Jan 23, 2026", "patient": "Sarah Chen", "duration": "55 min", "language": "English", "status": "Complete"},
            {"id": 7, "date": "Jan 22, 2026", "patient": "Michael Brown", "duration": "38 min", "language": "Spanish→EN", "status": "Complete"},
            {"id": 8, "date": "Jan 21, 2026", "patient": "Emily Davis", "duration": "1h 5min", "language": "English", "status": "Complete"},
            {"id": 9, "date": "Jan 20, 2026", "patient": "John Doe", "duration": "48 min", "language": "English", "status": "Complete"},
            {"id": 10, "date": "Jan 19, 2026", "patient": "Maria Santos", "duration": "52 min", "language": "Spanish→EN", "status": "Complete"},
        ]
        
        self._populate_table(sample_transcripts)
    
    def _populate_table(self, transcripts: list):
        """Populate table with transcript data."""
        self.table.setRowCount(len(transcripts))
        
        for row, transcript in enumerate(transcripts):
            # Date
            date_item = QTableWidgetItem(transcript['date'])
            self.table.setItem(row, 0, date_item)
            
            # Patient
            patient_item = QTableWidgetItem(transcript['patient'])
            self.table.setItem(row, 1, patient_item)
            
            # Duration
            duration_item = QTableWidgetItem(transcript['duration'])
            duration_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.table.setItem(row, 2, duration_item)
            
            # Language
            lang_item = QTableWidgetItem(transcript['language'])
            lang_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.table.setItem(row, 3, lang_item)
            
            # Status
            status = transcript['status']
            status_item = QTableWidgetItem(status)
            status_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.table.setItem(row, 4, status_item)
            
            # Actions
            actions_widget = QWidget()
            actions_layout = QHBoxLayout(actions_widget)
            actions_layout.setContentsMargins(4, 4, 4, 4)
            actions_layout.setSpacing(4)
            
            view_btn = QPushButton("View")
            view_btn.setObjectName("secondaryButton")
            view_btn.setStyleSheet("padding: 6px 12px; font-size: 12px;")
            view_btn.setCursor(Qt.CursorShape.PointingHandCursor)
            view_btn.clicked.connect(
                lambda checked, t=transcript: self._view_transcript(t)
            )
            actions_layout.addWidget(view_btn)
            
            export_btn = QPushButton("Export")
            export_btn.setObjectName("secondaryButton")
            export_btn.setStyleSheet("padding: 6px 12px; font-size: 12px;")
            export_btn.setCursor(Qt.CursorShape.PointingHandCursor)
            actions_layout.addWidget(export_btn)
            
            self.table.setCellWidget(row, 5, actions_widget)
            self.table.setRowHeight(row, 56)
    
    def _view_transcript(self, transcript: dict):
        """Open transcript detail dialog."""
        # Enhance with full data for dialog
        full_data = {
            **transcript,
            'patient_name': transcript['patient'],
            'summary': (
                "This session focused on continued progress in anxiety management. "
                "The patient demonstrated effective use of breathing techniques during "
                "stressful situations described. Notable improvement in sleep patterns "
                "and social engagement was reported. The therapeutic alliance remains "
                "strong, with the patient actively participating in session activities.\n\n"
                "Key themes discussed:\n"
                "• Academic stress and coping mechanisms\n"
                "• Family communication improvements\n"
                "• Peer relationship dynamics\n\n"
                "Recommendations: Continue current treatment approach with gradual "
                "exposure exercises. Consider family session in coming weeks."
            ),
            'transcript': (
                "[00:00:15] Therapist: Welcome back. How has your week been?\n\n"
                "[00:00:22] Patient: It's been pretty good actually. I used that breathing "
                "technique before my presentation and it really helped.\n\n"
                "[00:00:35] Therapist: That's wonderful to hear. Tell me more about how that went.\n\n"
                "[00:00:42] Patient: Well, I was really nervous, but I remembered to do the "
                "4-7-8 breathing before I started, and I felt a lot calmer.\n\n"
                "... [transcript continues] ..."
            )
        }
        
        dialog = TranscriptDetailDialog(full_data, self)
        dialog.exec()
    
    def _filter_transcripts(self, text: str):
        """Filter table by search text."""
        for row in range(self.table.rowCount()):
            match = False
            for col in range(self.table.columnCount() - 1):  # Exclude actions column
                item = self.table.item(row, col)
                if item and text.lower() in item.text().lower():
                    match = True
                    break
            self.table.setRowHidden(row, not match if text else False)
    
    def _clear_filters(self):
        """Reset all filters."""
        self.search_input.clear()
        self.patient_filter.setCurrentIndex(0)
        self.status_filter.setCurrentIndex(0)
        self.date_from.setDate(QDate.currentDate().addMonths(-1))
        self.date_to.setDate(QDate.currentDate())
        
        # Show all rows
        for row in range(self.table.rowCount()):
            self.table.setRowHidden(row, False)
    
    def load_transcripts(self, transcripts: list):
        """Load transcripts from backend.
        
        Args:
            transcripts: List of transcript dicts from API
        """
        # TODO: Hook up to backend endpoint
        self._populate_table(transcripts)
