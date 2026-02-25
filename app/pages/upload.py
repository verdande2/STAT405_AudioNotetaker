"""
Upload Page for TranscribeNotes Application
Handles audio file ingestion and processing initiation
"""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
    QPushButton, QFrame, QScrollArea, QComboBox,
    QProgressBar, QFileDialog, QListWidget, QListWidgetItem,
    QTextEdit, QSizePolicy, QMessageBox
)
from PySide6.QtCore import Qt, Signal, QMimeData
from PySide6.QtGui import QDragEnterEvent, QDropEvent
from pathlib import Path
from app.components.no_scroll_combo import NoScrollComboBox
from app.db import (
    AuthorizationError,
    DatabaseInitializationError,
    InvalidDatabaseKeyError,
    MissingDatabaseKeyError,
    list_client_profiles,
)


class DropZone(QFrame):
    """Drag and drop zone for audio files."""
    
    files_dropped = Signal(list)  # List of file paths
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("uploadZone")
        self.setAcceptDrops(True)
        self.setMinimumHeight(200)
        self._setup_ui()
    
    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.setSpacing(16)
        
        icon = QLabel("Drop MP4 files here")
        icon.setObjectName("uploadText")
        icon.setStyleSheet("font-size: 16px;")
        icon.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        browse_btn = QPushButton("Browse Files")
        browse_btn.setObjectName("secondaryButton")
        browse_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        browse_btn.clicked.connect(self._browse_files)
        
        layout.addWidget(icon)
        layout.addSpacing(8)
        layout.addWidget(browse_btn)
    
    def dragEnterEvent(self, event: QDragEnterEvent):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()
            self.setStyleSheet("""
                QFrame#uploadZone {
                    border-color: #2563eb;
                    background-color: #1e2738;
                }
            """)
    
    def dragLeaveEvent(self, event):
        self.setStyleSheet("")
    
    def dropEvent(self, event: QDropEvent):
        self.setStyleSheet("")
        files = []
        for url in event.mimeData().urls():
            path = url.toLocalFile()
            if path.lower().endswith('.mp4'):
                files.append(path)
        
        if files:
            self.files_dropped.emit(files)
        event.acceptProposedAction()
    
    def _browse_files(self):
        files, _ = QFileDialog.getOpenFileNames(
            self,
            "Select Audio Files",
            "",
            "MP4 Files (*.mp4);;All Files (*)"
        )
        if files:
            self.files_dropped.emit(files)


class FileQueueItem(QFrame):
    """Single item in the upload queue."""
    
    remove_requested = Signal(str)  # file path
    
    def __init__(self, file_path: str, parent=None):
        super().__init__(parent)
        self.file_path = file_path
        self.setObjectName("card")
        self._setup_ui()
    
    def _setup_ui(self):
        layout = QHBoxLayout(self)
        layout.setContentsMargins(16, 12, 16, 12)
        layout.setSpacing(16)
        
        # File icon
        icon = QLabel("MP4")
        icon.setStyleSheet("font-size: 12px; font-weight: 700; color: #38bdf8; background-color: #1e3a5f; padding: 4px 8px; border-radius: 4px;")
        layout.addWidget(icon)
        
        # File info
        info_layout = QVBoxLayout()
        info_layout.setSpacing(4)
        
        filename = Path(self.file_path).name
        name_label = QLabel(filename)
        name_label.setObjectName("cardTitle")
        name_label.setStyleSheet("font-size: 14px;")
        
        path_label = QLabel(str(Path(self.file_path).parent))
        path_label.setObjectName("cardSubtitle")
        
        info_layout.addWidget(name_label)
        info_layout.addWidget(path_label)
        layout.addLayout(info_layout)
        
        layout.addStretch()
        
        # Status and progress
        self.status_label = QLabel("Ready")
        self.status_label.setObjectName("statusPending")
        layout.addWidget(self.status_label)
        
        # Progress bar (hidden initially)
        self.progress = QProgressBar()
        self.progress.setFixedWidth(120)
        self.progress.setVisible(False)
        layout.addWidget(self.progress)
        
        # Remove button
        remove_btn = QPushButton("✕")
        remove_btn.setObjectName("iconButton")
        remove_btn.setFixedSize(32, 32)
        remove_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        remove_btn.clicked.connect(lambda: self.remove_requested.emit(self.file_path))
        layout.addWidget(remove_btn)
    
    def set_processing(self):
        """Update UI to show processing state."""
        self.status_label.setText("Processing")
        self.status_label.setObjectName("statusProcessing")
        self.progress.setVisible(True)
        self.progress.setValue(0)
    
    def set_progress(self, value: int):
        """Update progress bar."""
        self.progress.setValue(value)
    
    def set_complete(self):
        """Update UI to show complete state."""
        self.status_label.setText("Complete")
        self.status_label.setObjectName("statusComplete")
        self.progress.setVisible(False)
    
    def set_error(self, message: str = "Error"):
        """Update UI to show error state."""
        self.status_label.setText(message)
        self.status_label.setObjectName("statusError")
        self.progress.setVisible(False)


class UploadPage(QWidget):
    """Audio upload and processing page."""
    
    patient_selection_requested = Signal()
    upload_started = Signal(list, int)  # files, patient_id
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self._current_account = None
        self._is_processing = False
        self.queued_files = []
        self.file_widgets = {}
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
        
        title = QLabel("Upload Audio")
        title.setObjectName("pageTitle")
        
        description = QLabel("Import MP4 recordings for transcription and summarization")
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
        content_layout.setSpacing(24)
        
        # Drop zone
        self.drop_zone = DropZone()
        self.drop_zone.files_dropped.connect(self._on_files_dropped)
        content_layout.addWidget(self.drop_zone)
        
        # Patient selection
        patient_section = QFrame()
        patient_section.setObjectName("card")
        patient_layout = QHBoxLayout(patient_section)
        patient_layout.setContentsMargins(20, 16, 20, 16)
        patient_layout.setSpacing(16)
        
        patient_label = QLabel("Assign to Patient:")
        patient_label.setObjectName("cardTitle")
        patient_label.setStyleSheet("font-size: 14px;")
        patient_layout.addWidget(patient_label)
        
        self.patient_combo = NoScrollComboBox()
        self.patient_combo.setMinimumWidth(300)
        self.patient_combo.addItem("-- Select Patient --", None)
        self.patient_combo.addItem("+ Create New Patient", "new")
        self.patient_combo.setEnabled(False)
        self.patient_combo.currentIndexChanged.connect(self._update_queue_ui)
        patient_layout.addWidget(self.patient_combo)
        
        patient_layout.addStretch()
        content_layout.addWidget(patient_section)
        
        # Queue section
        queue_section = QVBoxLayout()
        queue_section.setSpacing(12)
        
        queue_header = QHBoxLayout()
        queue_title = QLabel("Upload Queue")
        queue_title.setObjectName("cardTitle")
        queue_title.setStyleSheet("font-size: 18px;")
        queue_header.addWidget(queue_title)
        
        self.queue_count = QLabel("0 files")
        self.queue_count.setObjectName("cardSubtitle")
        queue_header.addWidget(self.queue_count)
        
        queue_header.addStretch()
        
        clear_btn = QPushButton("Clear All")
        clear_btn.setObjectName("secondaryButton")
        clear_btn.setStyleSheet("padding: 8px 16px;")
        clear_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        clear_btn.clicked.connect(self._clear_queue)
        queue_header.addWidget(clear_btn)
        
        queue_section.addLayout(queue_header)
        
        # File list container
        self.queue_container = QVBoxLayout()
        self.queue_container.setSpacing(8)
        
        self.empty_queue_label = QLabel("No files in queue. Drop files above to begin.")
        self.empty_queue_label.setObjectName("cardSubtitle")
        self.empty_queue_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.empty_queue_label.setStyleSheet("padding: 40px;")
        self.queue_container.addWidget(self.empty_queue_label)
        
        queue_section.addLayout(self.queue_container)
        content_layout.addLayout(queue_section)
        
        # Action buttons
        actions_layout = QHBoxLayout()
        actions_layout.setSpacing(16)
        
        actions_layout.addStretch()
        
        self.process_btn = QPushButton("Start Processing")
        self.process_btn.setObjectName("accentButton")
        self.process_btn.setMinimumWidth(200)
        self.process_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.process_btn.setEnabled(False)
        self.process_btn.clicked.connect(self._start_processing)
        actions_layout.addWidget(self.process_btn)
        
        content_layout.addLayout(actions_layout)
        content_layout.addStretch()
        
        scroll.setWidget(content)
        layout.addWidget(scroll)
    
    def _on_files_dropped(self, files: list):
        """Handle dropped files."""
        for file_path in files:
            if file_path not in self.queued_files:
                self.queued_files.append(file_path)
                self._add_file_widget(file_path)
        
        self._update_queue_ui()
    
    def _add_file_widget(self, file_path: str):
        """Add a file widget to the queue."""
        widget = FileQueueItem(file_path)
        widget.remove_requested.connect(self._remove_file)
        self.file_widgets[file_path] = widget
        self.queue_container.addWidget(widget)
    
    def _remove_file(self, file_path: str):
        """Remove a file from the queue."""
        if file_path in self.queued_files:
            self.queued_files.remove(file_path)
        
        if file_path in self.file_widgets:
            widget = self.file_widgets.pop(file_path)
            widget.deleteLater()
        
        self._update_queue_ui()
    
    def _clear_queue(self):
        """Clear all files from queue."""
        for file_path in list(self.file_widgets.keys()):
            widget = self.file_widgets.pop(file_path)
            widget.deleteLater()
        
        self.queued_files.clear()
        self._update_queue_ui()
    
    def _update_queue_ui(self):
        """Update queue UI state."""
        count = len(self.queued_files)
        self.queue_count.setText(f"{count} file{'s' if count != 1 else ''}")
        self.empty_queue_label.setVisible(count == 0)
        patient_selected = self.patient_combo.currentData() not in (None, "new")
        self.process_btn.setEnabled((count > 0) and patient_selected and not self._is_processing)
    
    def _start_processing(self):
        """Start processing queued files."""
        patient_id = self.patient_combo.currentData()
        
        if patient_id == "new":
            self.patient_selection_requested.emit()
            return
        
        if patient_id is None:
            QMessageBox.information(
                self,
                "Upload Audio",
                "Select a patient before starting processing.",
            )
            return
        
        self._is_processing = True
        self.process_btn.setText("Processing...")
        self.process_btn.setEnabled(False)

        # Mark all files as processing
        for widget in self.file_widgets.values():
            widget.set_processing()
        
        self.upload_started.emit(list(self.queued_files), int(patient_id))
    
    def set_file_progress(self, file_path: str, progress: int):
        """Update progress for a specific file."""
        if file_path in self.file_widgets:
            self.file_widgets[file_path].set_progress(progress)
    
    def set_file_complete(self, file_path: str):
        """Mark a file as complete."""
        if file_path in self.file_widgets:
            self.file_widgets[file_path].set_complete()
    
    def set_file_error(self, file_path: str, message: str):
        """Mark a file as error."""
        if file_path in self.file_widgets:
            self.file_widgets[file_path].set_error(message)

    def finish_processing(self, *, clear_completed: bool = False):
        """Restore controls after a processing run."""
        self._is_processing = False
        self.process_btn.setText("Start Processing")
        if clear_completed:
            self._clear_queue()
            return
        self._update_queue_ui()

    def set_authenticated_account(self, account):
        """Set signed-in account context and refresh available patients."""
        self._current_account = account
        self.refresh_patients()

    def refresh_patients(self):
        """Load patient options for the current psychologist."""
        account = self._current_account
        self.patient_combo.blockSignals(True)
        current_selection = self.patient_combo.currentData() if self.patient_combo.count() else None
        self.patient_combo.clear()
        self.patient_combo.addItem("-- Select Patient --", None)
        self.patient_combo.addItem("+ Create New Patient", "new")
        self.patient_combo.setEnabled(False)

        if account is None or getattr(account, "role", None) != "psychologist":
            self.patient_combo.blockSignals(False)
            self._update_queue_ui()
            return

        try:
            patients = list_client_profiles(account.id)
        except (
            AuthorizationError,
            MissingDatabaseKeyError,
            InvalidDatabaseKeyError,
            DatabaseInitializationError,
        ):
            self.patient_combo.blockSignals(False)
            self._update_queue_ui()
            return
        except Exception:
            self.patient_combo.blockSignals(False)
            self._update_queue_ui()
            return

        for patient in patients:
            first = (patient.first_name or "").strip()
            last = (patient.last_name or "").strip()
            name = " ".join(part for part in [first, last] if part) or "Unnamed Patient"
            display = f"{name} (ID: {patient.id})"
            self.patient_combo.addItem(display, patient.id)

        self.patient_combo.setEnabled(self.patient_combo.count() > 2)
        if current_selection is not None:
            index = self.patient_combo.findData(current_selection)
            self.patient_combo.setCurrentIndex(index if index >= 0 else 0)
        self.patient_combo.blockSignals(False)
        self._update_queue_ui()
    
    def load_patients(self, patients: list):
        """Populate patient dropdown from backend.
        
        Args:
            patients: List of dicts with 'id', 'name', 'mrn' keys
        """
        # TODO: Hook up to backend endpoint
        self.patient_combo.clear()
        self.patient_combo.addItem("-- Select Patient --", None)
        self.patient_combo.addItem("+ Create New Patient", "new")
        
        for patient in patients:
            mrn = patient.get('mrn')
            display = f"{patient['name']} (MRN: {mrn})" if mrn else patient['name']
            self.patient_combo.addItem(display, patient['id'])
        self.patient_combo.setEnabled(self.patient_combo.count() > 2)
        self._update_queue_ui()
