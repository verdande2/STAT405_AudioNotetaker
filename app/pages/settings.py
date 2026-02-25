"""
Settings Page for TranscribeNotes Application
Application configuration and preferences
"""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
    QPushButton, QFrame, QScrollArea, QLineEdit,
    QCheckBox, QSpinBox, QGroupBox,
    QFormLayout, QSlider, QTextEdit, QFileDialog
)
from PySide6.QtCore import Qt, Signal
from app.components.no_scroll_combo import NoScrollComboBox


class SettingsSection(QFrame):
    """Reusable settings section container."""
    
    def __init__(self, title: str, description: str = "", parent=None):
        super().__init__(parent)
        self.setObjectName("card")
        self._setup_ui(title, description)
    
    def _setup_ui(self, title: str, description: str):
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(24, 20, 24, 20)
        self.layout.setSpacing(16)
        
        # Header
        header = QVBoxLayout()
        header.setSpacing(4)
        
        title_label = QLabel(title)
        title_label.setObjectName("cardTitle")
        title_label.setStyleSheet("font-size: 16px;")
        header.addWidget(title_label)
        
        if description:
            desc_label = QLabel(description)
            desc_label.setObjectName("cardSubtitle")
            desc_label.setWordWrap(True)
            header.addWidget(desc_label)
        
        self.layout.addLayout(header)
        
        # Content container for child widgets
        self.content_layout = QVBoxLayout()
        self.content_layout.setSpacing(12)
        self.layout.addLayout(self.content_layout)
    
    def add_widget(self, widget: QWidget):
        """Add a widget to the section."""
        self.content_layout.addWidget(widget)
    
    def add_layout(self, layout):
        """Add a layout to the section."""
        self.content_layout.addLayout(layout)


class SettingsPage(QWidget):
    """Application settings and configuration page."""
    
    # private const for available languages and ISO language/locale codes
    _available_languages = [{"name": "English", "ISO_code": "en_US  "}, {"name": "Spanish", "ISO_code": "es_ES"}]
    
    settings_changed = Signal(dict)
    
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
        
        title = QLabel("Settings")
        title.setObjectName("pageTitle")
        
        description = QLabel("Configure application preferences and system options")
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
        content_layout.setContentsMargins(40, 24, 40, 32)
        content_layout.setSpacing(24)
        
        # Transcription Settings
        transcription_section = SettingsSection(
            "Transcription Settings",
            "Configure speech-to-text processing options"
        )
        
        trans_form = QFormLayout()
        trans_form.setSpacing(12)
        trans_form.setLabelAlignment(Qt.AlignmentFlag.AlignRight)
        
        
        self.default_language = NoScrollComboBox()
        self.default_language.addItem("Auto-detect", "auto")
        for language in self._available_languages:
            self.default_language.addItem(language["name"], language["ISO_code"])
        trans_form.addRow("Input Language:", self.default_language)
        
        self.output_language = NoScrollComboBox()
        for language in self._available_languages:
            self.output_language.addItem(language["name"], language["ISO_code"])
        trans_form.addRow("Output Language:", self.output_language)
        
        self.word_timestamps = QCheckBox("Include word-level timestamps")
        self.word_timestamps.setChecked(True)
        trans_form.addRow("", self.word_timestamps)
        
        self.speaker_diarization = QCheckBox("Enable speaker diarization")
        self.speaker_diarization.setChecked(False)
        trans_form.addRow("", self.speaker_diarization)
        
        transcription_section.add_layout(trans_form)
        content_layout.addWidget(transcription_section)
        
        # Summarization Settings
        summary_section = SettingsSection(
            "Summarization Settings",
            "Configure AI-powered summary generation"
        )
        
        summary_form = QFormLayout()
        summary_form.setSpacing(12)
        summary_form.setLabelAlignment(Qt.AlignmentFlag.AlignRight)
        
        # Which local gguf file to use for the summarizer.  the file is too
        # large to check in, so users are expected to download James's model
        # manually and point this field at the path.  we default to the
        # conventional ``models/Qwen3-4B-Q5_0.gguf`` location that the rest
        # of the code also uses.
        self.model_path = QLineEdit()
        self.model_path.setText("models/Qwen3-4B-Q5_0.gguf")
        self.model_path.setReadOnly(False)
        model_layout = QHBoxLayout()
        model_layout.addWidget(self.model_path)
        browse_model_btn = QPushButton("Browse")
        browse_model_btn.setObjectName("secondaryButton")
        browse_model_btn.setStyleSheet("padding: 8px 16px;")
        browse_model_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        browse_model_btn.clicked.connect(self._browse_model_file)
        model_layout.addWidget(browse_model_btn)
        summary_form.addRow("Summarizer Model:", model_layout)

        self.summary_length = NoScrollComboBox()
        self.summary_length.addItem("Brief (1-2 paragraphs)", "brief")
        self.summary_length.addItem("Standard (3-4 paragraphs)", "standard")
        self.summary_length.addItem("Detailed (comprehensive)", "detailed")
        self.summary_length.setCurrentIndex(1)
        summary_form.addRow("Summary Length:", self.summary_length)
        
        self.include_quotes = QCheckBox("Include relevant quotes from transcript")
        self.include_quotes.setChecked(True)
        summary_form.addRow("", self.include_quotes)
        
        self.behavioral_themes = QCheckBox("Extract behavioral themes")
        self.behavioral_themes.setChecked(True)
        summary_form.addRow("", self.behavioral_themes)
        
        self.treatment_suggestions = QCheckBox("Include treatment suggestions")
        self.treatment_suggestions.setChecked(False)
        summary_form.addRow("", self.treatment_suggestions)
        
        summary_section.add_layout(summary_form)
        content_layout.addWidget(summary_section)
        
        # Storage Settings
        storage_section = SettingsSection(
            "Storage & Data",
            "Manage local data storage and encryption settings"
        )
        
        storage_form = QFormLayout()
        storage_form.setSpacing(12)
        storage_form.setLabelAlignment(Qt.AlignmentFlag.AlignRight)
        
        storage_path_layout = QHBoxLayout()
        self.storage_path = QLineEdit()
        self.storage_path.setText("/var/lib/transcribenotes/data")
        self.storage_path.setReadOnly(True)
        storage_path_layout.addWidget(self.storage_path)
        
        browse_btn = QPushButton("Browse")
        browse_btn.setObjectName("secondaryButton")
        browse_btn.setStyleSheet("padding: 8px 16px;")
        browse_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        storage_path_layout.addWidget(browse_btn)
        
        storage_form.addRow("Data Location:", storage_path_layout)
        
        self.encryption_enabled = QCheckBox("Enable AES-256 encryption (required)")
        self.encryption_enabled.setChecked(True)
        self.encryption_enabled.setEnabled(False)  # Always required
        storage_form.addRow("", self.encryption_enabled)
        
        self.auto_backup = QCheckBox("Enable automatic local backups")
        self.auto_backup.setChecked(True)
        storage_form.addRow("", self.auto_backup)
        
        self.backup_retention = QSpinBox()
        self.backup_retention.setRange(7, 365)
        self.backup_retention.setValue(30)
        self.backup_retention.setSuffix(" days")
        storage_form.addRow("Backup Retention:", self.backup_retention)
        
        storage_section.add_layout(storage_form)
        content_layout.addWidget(storage_section)
        
        # Performance Settings
        perf_section = SettingsSection(
            "Performance",
            "Configure processing performance options"
        )
        
        perf_form = QFormLayout()
        perf_form.setSpacing(12)
        perf_form.setLabelAlignment(Qt.AlignmentFlag.AlignRight)
        
        self.processing_device = NoScrollComboBox()
        self.processing_device.addItem("Auto (GPU if available)", "auto")
        self.processing_device.addItem("CPU Only", "cpu")
        self.processing_device.addItem("NVIDIA GPU (CUDA)", "cuda")
        perf_form.addRow("Processing Device:", self.processing_device)
        
        self.max_threads = QSpinBox()
        self.max_threads.setRange(1, 16)
        self.max_threads.setValue(4)
        perf_form.addRow("Max CPU Threads:", self.max_threads)
        
        self.batch_processing = QCheckBox("Enable batch processing for multiple files")
        self.batch_processing.setChecked(True)
        perf_form.addRow("", self.batch_processing)
        
        perf_section.add_layout(perf_form)
        content_layout.addWidget(perf_section)
        
        # Interface Settings
        ui_section = SettingsSection(
            "Interface",
            "Customize the application appearance and behavior"
        )
        
        ui_form = QFormLayout()
        ui_form.setSpacing(12)
        ui_form.setLabelAlignment(Qt.AlignmentFlag.AlignRight)
        
        self.theme = NoScrollComboBox()
        self.theme.addItem("Dark (Default)", "dark")
        self.theme.addItem("Light", "light")
        self.theme.addItem("System", "system")
        ui_form.addRow("Theme:", self.theme)
        
        self.session_timeout = QSpinBox()
        self.session_timeout.setRange(5, 120)
        self.session_timeout.setValue(30)
        self.session_timeout.setSuffix(" minutes")
        ui_form.addRow("Session Timeout:", self.session_timeout)
        
        self.confirm_delete = QCheckBox("Require confirmation for deletions")
        self.confirm_delete.setChecked(True)
        ui_form.addRow("", self.confirm_delete)
        
        self.show_notifications = QCheckBox("Show processing notifications")
        self.show_notifications.setChecked(True)
        ui_form.addRow("", self.show_notifications)
        
        ui_section.add_layout(ui_form)
        content_layout.addWidget(ui_section)
        
        # About / System Info
        about_section = SettingsSection(
            "System Information",
            "Application and system details"
        )
        
        info_layout = QVBoxLayout()
        info_layout.setSpacing(8)
        
        info_items = [
            ("Version:", "1.0.0"),
            ("Build:", "2026.01.25-stable"),
            ("Data Format:", "SQLite + AES-256"),
            ("Models:", "Whisper Large V3, Local LLM"),
        ]
        
        for label, value in info_items:
            row = QHBoxLayout()
            label_widget = QLabel(label)
            label_widget.setObjectName("cardSubtitle")
            label_widget.setFixedWidth(120)
            row.addWidget(label_widget)
            
            value_widget = QLabel(value)
            row.addWidget(value_widget)
            
            row.addStretch()
            info_layout.addLayout(row)
        
        about_section.add_layout(info_layout)
        content_layout.addWidget(about_section)
        
        # Action buttons
        actions_layout = QHBoxLayout()
        actions_layout.setSpacing(16)
        
        reset_btn = QPushButton("Reset to Defaults")
        reset_btn.setObjectName("secondaryButton")
        reset_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        reset_btn.clicked.connect(self._reset_defaults)
        actions_layout.addWidget(reset_btn)
        
        actions_layout.addStretch()
        
        export_btn = QPushButton("Export Settings")
        export_btn.setObjectName("secondaryButton")
        export_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        actions_layout.addWidget(export_btn)
        
        save_btn = QPushButton("Save Settings")
        save_btn.setObjectName("primaryButton")
        save_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        save_btn.clicked.connect(self._save_settings)
        actions_layout.addWidget(save_btn)
        
        content_layout.addLayout(actions_layout)
        content_layout.addStretch()
        
        scroll.setWidget(content)
        layout.addWidget(scroll)
    
    def _save_settings(self):
        """Collect and save all settings."""
        settings = {
            # Transcription
            'default_language': self.default_language.currentData(),
            'output_language': self.output_language.currentData(),
            'word_timestamps': self.word_timestamps.isChecked(),
            'speaker_diarization': self.speaker_diarization.isChecked(),
            
            # Summarization
            'model_path': self.model_path.text(),
            'summary_length': self.summary_length.currentData(),
            'include_quotes': self.include_quotes.isChecked(),
            'behavioral_themes': self.behavioral_themes.isChecked(),
            'treatment_suggestions': self.treatment_suggestions.isChecked(),
            
            # Storage
            'storage_path': self.storage_path.text(),
            'auto_backup': self.auto_backup.isChecked(),
            'backup_retention': self.backup_retention.value(),
            
            # Performance
            'processing_device': self.processing_device.currentData(),
            'max_threads': self.max_threads.value(),
            'batch_processing': self.batch_processing.isChecked(),
            
            # Interface
            'theme': self.theme.currentData(),
            'session_timeout': self.session_timeout.value(),
            'confirm_delete': self.confirm_delete.isChecked(),
            'show_notifications': self.show_notifications.isChecked(),
        }
        
        # TODO sync settings dict somewhere, .env? local json? db store?
        
        
        # TODO: Hook up to backend/config file
        self.settings_changed.emit(settings)
    
    def _reset_defaults(self):
        """Reset all settings to defaults."""
        # Transcription
        self.default_language.setCurrentIndex(0)
        self.output_language.setCurrentIndex(0)
        self.word_timestamps.setChecked(True)
        self.speaker_diarization.setChecked(False)
        
        # Summarization
        self.model_path.setText("models/Qwen3-4B-Q5_0.gguf")
        self.summary_length.setCurrentIndex(1)
        self.include_quotes.setChecked(True)
        self.behavioral_themes.setChecked(True)
        self.treatment_suggestions.setChecked(False)
        
        # Storage
        self.auto_backup.setChecked(True)
        self.backup_retention.setValue(30)
        
        # Performance
        self.processing_device.setCurrentIndex(0)
        self.max_threads.setValue(4)
        self.batch_processing.setChecked(True)
        
        # Interface
        self.theme.setCurrentIndex(0)
        self.session_timeout.setValue(30)
        self.confirm_delete.setChecked(True)
        self.show_notifications.setChecked(True)
    
    def load_settings(self, settings: dict):
        """Load settings from config.
        
        Args:
            settings: Dictionary of setting key-value pairs
        """
        # TODO: Hook up to backend/config file, pull from .env? json?
        # Apply settings to UI widgets
        if 'model_path' in settings:
            self.model_path.setText(settings.get('model_path', self.model_path.text()))

    def _browse_model_file(self):
        """Open file dialog to select summarizer gguf file."""
        path, _ = QFileDialog.getOpenFileName(
            self,
            "Select Summarizer Model",
            "",
            "GGUF Files (*.gguf);;All Files (*)"
        )
        if path:
            self.model_path.setText(path)
        pass
