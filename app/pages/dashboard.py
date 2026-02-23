"""
Dashboard Page for TranscribeNotes Application
"""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
    QPushButton, QFrame, QGridLayout, QScrollArea,
    QSizePolicy
)
from PySide6.QtCore import Qt, Signal


class StatsCard(QFrame):
    """Statistics display card."""
    
    def __init__(self, value: str, label: str, trend: str = "", parent=None):
        super().__init__(parent)
        self.setObjectName("statsCard")
        self._setup_ui(value, label, trend)
    
    def _setup_ui(self, value: str, label: str, trend: str):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(8)
        
        value_label = QLabel(value)
        value_label.setObjectName("statsValue")
        
        text_label = QLabel(label)
        text_label.setObjectName("statsLabel")
        
        layout.addWidget(value_label)
        layout.addWidget(text_label)
        
        if trend:
            trend_label = QLabel(trend)
            trend_label.setStyleSheet("color: #22c55e; font-size: 12px;")
            layout.addWidget(trend_label)
    
    def update_value(self, value: str):
        """Update the displayed value."""
        # Find the value label and update it
        for i in range(self.layout().count()):
            widget = self.layout().itemAt(i).widget()
            if widget and widget.objectName() == "statsValue":
                widget.setText(value)
                break


class RecentActivityItem(QFrame):
    """Single item in recent activity list."""
    
    clicked = Signal(int)
    
    def __init__(self, title: str, subtitle: str, status: str, item_id: int = 0, parent=None):
        super().__init__(parent)
        self.item_id = item_id
        self.setObjectName("card")
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self._setup_ui(title, subtitle, status)
    
    def _setup_ui(self, title: str, subtitle: str, status: str):
        layout = QHBoxLayout(self)
        layout.setContentsMargins(16, 12, 16, 12)
        
        # Text info
        text_layout = QVBoxLayout()
        text_layout.setSpacing(4)
        
        title_label = QLabel(title)
        title_label.setObjectName("cardTitle")
        title_label.setStyleSheet("font-size: 14px;")
        
        subtitle_label = QLabel(subtitle)
        subtitle_label.setObjectName("cardSubtitle")
        
        text_layout.addWidget(title_label)
        text_layout.addWidget(subtitle_label)
        layout.addLayout(text_layout)
        
        layout.addStretch()
        
        # Status badge
        status_label = QLabel(status)
        status_map = {
            "Complete": "statusComplete",
            "Processing": "statusProcessing",
            "Pending": "statusPending",
            "Error": "statusError"
        }
        status_label.setObjectName(status_map.get(status, "statusPending"))
        layout.addWidget(status_label)
    
    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.clicked.emit(self.item_id)
        super().mousePressEvent(event)


class DashboardPage(QWidget):
    """Main dashboard page showing overview and statistics."""
    
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
        
        title = QLabel("Dashboard")
        title.setObjectName("pageTitle")
        
        description = QLabel("Overview of your transcription activity and patient records")
        description.setObjectName("pageDescription")
        
        header_layout.addWidget(title)
        header_layout.addWidget(description)
        layout.addWidget(header)
        
        # Scrollable content
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        
        content = QWidget()
        content.setObjectName("pageContent")
        content_layout = QVBoxLayout(content)
        content_layout.setContentsMargins(40, 32, 40, 32)
        content_layout.setSpacing(32)
        
        # Stats cards
        stats_layout = QHBoxLayout()
        stats_layout.setSpacing(20)
        
        self.total_patients = StatsCard("0", "Total Patients")
        self.total_transcripts = StatsCard("0", "Transcripts", "↑ 12 this week")
        self.pending_review = StatsCard("0", "Pending Review")
        self.processing = StatsCard("0", "Processing")
        
        stats_layout.addWidget(self.total_patients)
        stats_layout.addWidget(self.total_transcripts)
        stats_layout.addWidget(self.pending_review)
        stats_layout.addWidget(self.processing)
        
        content_layout.addLayout(stats_layout)
        
        # Quick actions
        actions_section = QVBoxLayout()
        actions_section.setSpacing(16)
        
        actions_title = QLabel("Quick Actions")
        actions_title.setObjectName("cardTitle")
        actions_title.setStyleSheet("font-size: 18px;")
        actions_section.addWidget(actions_title)
        
        actions_layout = QHBoxLayout()
        actions_layout.setSpacing(16)
        
        upload_btn = QPushButton("Upload New Audio")
        upload_btn.setObjectName("primaryButton")
        upload_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        
        new_patient_btn = QPushButton("Create Patient Profile")
        new_patient_btn.setObjectName("secondaryButton")
        new_patient_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        
        search_btn = QPushButton("Search Records")
        search_btn.setObjectName("secondaryButton")
        search_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        
        actions_layout.addWidget(upload_btn)
        actions_layout.addWidget(new_patient_btn)
        actions_layout.addWidget(search_btn)
        actions_layout.addStretch()
        
        actions_section.addLayout(actions_layout)
        content_layout.addLayout(actions_section)
        
        # Two column layout for recent activity
        columns_layout = QHBoxLayout()
        columns_layout.setSpacing(24)
        
        # Recent transcripts
        transcripts_section = QVBoxLayout()
        transcripts_section.setSpacing(12)
        
        transcripts_header = QHBoxLayout()
        transcripts_title = QLabel("Recent Transcripts")
        transcripts_title.setObjectName("cardTitle")
        transcripts_title.setStyleSheet("font-size: 18px;")
        transcripts_header.addWidget(transcripts_title)
        transcripts_header.addStretch()
        
        view_all_btn = QPushButton("View All →")
        view_all_btn.setObjectName("secondaryButton")
        view_all_btn.setStyleSheet("padding: 8px 16px;")
        view_all_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        transcripts_header.addWidget(view_all_btn)
        
        transcripts_section.addLayout(transcripts_header)
        
        # Sample transcript items
        sample_transcripts = [
            ("Session - John D.", "January 28, 2026 • 45 min", "Complete"),
            ("Initial Assessment - Maria S.", "January 27, 2026 • 1h 12min", "Processing"),
            ("Follow-up - Alex R.", "January 26, 2026 • 32 min", "Complete"),
            ("Session - Kim T.", "January 25, 2026 • 58 min", "Pending"),
        ]
        
        for title, subtitle, status in sample_transcripts:
            item = RecentActivityItem(title, subtitle, status)
            transcripts_section.addWidget(item)
        
        transcripts_container = QWidget()
        transcripts_container.setLayout(transcripts_section)
        columns_layout.addWidget(transcripts_container)
        
        # Recent patients
        patients_section = QVBoxLayout()
        patients_section.setSpacing(12)
        
        patients_header = QHBoxLayout()
        patients_title = QLabel("Recent Patients")
        patients_title.setObjectName("cardTitle")
        patients_title.setStyleSheet("font-size: 18px;")
        patients_header.addWidget(patients_title)
        patients_header.addStretch()
        
        view_patients_btn = QPushButton("View All →")
        view_patients_btn.setObjectName("secondaryButton")
        view_patients_btn.setStyleSheet("padding: 8px 16px;")
        view_patients_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        patients_header.addWidget(view_patients_btn)
        
        patients_section.addLayout(patients_header)
        
        # Sample patient items
        sample_patients = [
            ("John Doe", "MRN: 12345 • Last session: Jan 28", "Complete"),
            ("Maria Santos", "MRN: 12346 • Last session: Jan 27", "Processing"),
            ("Alex Rodriguez", "MRN: 12347 • Last session: Jan 26", "Complete"),
            ("Kim Thompson", "MRN: 12348 • Last session: Jan 25", "Complete"),
        ]
        
        for title, subtitle, status in sample_patients:
            item = RecentActivityItem(title, subtitle, status)
            patients_section.addWidget(item)
        
        patients_container = QWidget()
        patients_container.setLayout(patients_section)
        columns_layout.addWidget(patients_container)
        
        content_layout.addLayout(columns_layout)
        content_layout.addStretch()
        
        scroll.setWidget(content)
        layout.addWidget(scroll)
    
    def refresh_stats(self, stats: dict):
        """Update dashboard statistics from backend data.
        
        Args:
            stats: Dictionary with keys like 'total_patients', 'total_transcripts', etc.
        """
        # TODO: Hook up to backend endpoint
        if 'total_patients' in stats:
            self.total_patients.update_value(str(stats['total_patients']))
        if 'total_transcripts' in stats:
            self.total_transcripts.update_value(str(stats['total_transcripts']))
        if 'pending_review' in stats:
            self.pending_review.update_value(str(stats['pending_review']))
        if 'processing' in stats:
            self.processing.update_value(str(stats['processing']))
