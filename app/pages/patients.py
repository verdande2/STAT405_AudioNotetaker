"""
Patients Page for TranscribeNotes Application
Patient profile management and listing
"""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
    QPushButton, QFrame, QScrollArea, QLineEdit,
    QTableWidget, QTableWidgetItem, QHeaderView,
    QDialog, QFormLayout, QTextEdit, QComboBox,
    QAbstractItemView
)
from PySide6.QtCore import Qt, Signal
from datetime import datetime


class CreatePatientDialog(QDialog):
    """Dialog for creating a new patient profile."""
    
    patient_created = Signal(dict)  # Patient data
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Create Patient Profile")
        self.setMinimumWidth(500)
        self._setup_ui()
    
    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(32, 32, 32, 32)
        layout.setSpacing(24)
        
        # Title
        title = QLabel("New Patient Profile")
        title.setObjectName("dialogTitle")
        layout.addWidget(title)
        
        # Form
        form = QFormLayout()
        form.setSpacing(16)
        form.setLabelAlignment(Qt.AlignmentFlag.AlignRight)
        
        self.mrn_input = QLineEdit()
        self.mrn_input.setPlaceholderText("Medical Record Number")
        form.addRow("MRN:", self.mrn_input)
        
        self.first_name_input = QLineEdit()
        self.first_name_input.setPlaceholderText("First name")
        form.addRow("First Name:", self.first_name_input)
        
        self.last_name_input = QLineEdit()
        self.last_name_input.setPlaceholderText("Last name")
        form.addRow("Last Name:", self.last_name_input)
        
        self.dob_input = QLineEdit()
        self.dob_input.setPlaceholderText("YYYY-MM-DD")
        form.addRow("Date of Birth:", self.dob_input)
        
        self.notes_input = QTextEdit()
        self.notes_input.setPlaceholderText("Initial notes or identifying information...")
        self.notes_input.setMaximumHeight(100)
        form.addRow("Notes:", self.notes_input)
        
        layout.addLayout(form)
        
        # Buttons
        buttons_layout = QHBoxLayout()
        buttons_layout.addStretch()
        
        cancel_btn = QPushButton("Cancel")
        cancel_btn.setObjectName("secondaryButton")
        cancel_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        cancel_btn.clicked.connect(self.reject)
        buttons_layout.addWidget(cancel_btn)
        
        create_btn = QPushButton("Create Patient")
        create_btn.setObjectName("primaryButton")
        create_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        create_btn.clicked.connect(self._create_patient)
        buttons_layout.addWidget(create_btn)
        
        layout.addLayout(buttons_layout)
    
    def _create_patient(self):
        """Validate and emit patient creation."""
        data = {
            'mrn': self.mrn_input.text().strip(),
            'first_name': self.first_name_input.text().strip(),
            'last_name': self.last_name_input.text().strip(),
            'dob': self.dob_input.text().strip(),
            'notes': self.notes_input.toPlainText().strip(),
        }
        
        # Basic validation
        if not data['mrn'] or not data['first_name'] or not data['last_name']:
            # TODO: Show error
            return
        
        self.patient_created.emit(data)
        self.accept()


class PatientsPage(QWidget):
    """Patient management page with list and search."""
    
    view_patient_requested = Signal(int)  # patient_id
    
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
        header_layout = QHBoxLayout(header)
        header_layout.setContentsMargins(40, 32, 40, 32)
        
        title_section = QVBoxLayout()
        title_section.setSpacing(4)
        
        title = QLabel("Patients")
        title.setObjectName("pageTitle")
        
        description = QLabel("Manage patient profiles and view session history")
        description.setObjectName("pageDescription")
        
        title_section.addWidget(title)
        title_section.addWidget(description)
        header_layout.addLayout(title_section)
        
        header_layout.addStretch()
        
        # Create patient button
        create_btn = QPushButton("+ New Patient")
        create_btn.setObjectName("primaryButton")
        create_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        create_btn.clicked.connect(self._show_create_dialog)
        header_layout.addWidget(create_btn)
        
        layout.addWidget(header)
        
        # Content
        content = QWidget()
        content.setObjectName("pageContent")
        content_layout = QVBoxLayout(content)
        content_layout.setContentsMargins(40, 24, 40, 32)
        content_layout.setSpacing(20)
        
        # Search and filter bar
        filter_layout = QHBoxLayout()
        filter_layout.setSpacing(16)
        
        self.search_input = QLineEdit()
        self.search_input.setObjectName("searchInput")
        self.search_input.setPlaceholderText("🔍  Search patients by name or MRN...")
        self.search_input.setMinimumWidth(300)
        self.search_input.textChanged.connect(self._filter_patients)
        filter_layout.addWidget(self.search_input)
        
        filter_layout.addStretch()
        
        self.sort_combo = QComboBox()
        self.sort_combo.addItem("Sort: Most Recent")
        self.sort_combo.addItem("Sort: Name A-Z")
        self.sort_combo.addItem("Sort: Name Z-A")
        self.sort_combo.addItem("Sort: MRN")
        filter_layout.addWidget(self.sort_combo)
        
        content_layout.addLayout(filter_layout)
        
        # Patients table
        self.table = QTableWidget()
        self.table.setColumnCount(5)
        self.table.setHorizontalHeaderLabels([
            "MRN", "Patient Name", "Sessions", "Last Session", "Actions"
        ])
        
        # Table styling
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Fixed)
        self.table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.Fixed)
        self.table.horizontalHeader().setSectionResizeMode(4, QHeaderView.ResizeMode.Fixed)
        self.table.setColumnWidth(0, 100)
        self.table.setColumnWidth(2, 80)
        self.table.setColumnWidth(4, 150)
        
        self.table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.table.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.table.setAlternatingRowColors(True)
        self.table.verticalHeader().setVisible(False)
        self.table.setShowGrid(False)
        
        # Load sample data
        self._load_sample_data()
        
        content_layout.addWidget(self.table)
        
        # Pagination
        pagination_layout = QHBoxLayout()
        pagination_layout.addStretch()
        
        self.page_label = QLabel("Showing 1-10 of 42 patients")
        self.page_label.setObjectName("cardSubtitle")
        pagination_layout.addWidget(self.page_label)
        
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
        """Load sample patient data for skeleton."""
        sample_patients = [
            {"id": 1, "mrn": "12345", "name": "John Doe", "sessions": 12, "last_session": "Jan 28, 2026"},
            {"id": 2, "mrn": "12346", "name": "Maria Santos", "sessions": 8, "last_session": "Jan 27, 2026"},
            {"id": 3, "mrn": "12347", "name": "Alex Rodriguez", "sessions": 15, "last_session": "Jan 26, 2026"},
            {"id": 4, "mrn": "12348", "name": "Kim Thompson", "sessions": 6, "last_session": "Jan 25, 2026"},
            {"id": 5, "mrn": "12349", "name": "James Wilson", "sessions": 22, "last_session": "Jan 24, 2026"},
            {"id": 6, "mrn": "12350", "name": "Sarah Chen", "sessions": 4, "last_session": "Jan 23, 2026"},
            {"id": 7, "mrn": "12351", "name": "Michael Brown", "sessions": 9, "last_session": "Jan 22, 2026"},
            {"id": 8, "mrn": "12352", "name": "Emily Davis", "sessions": 11, "last_session": "Jan 21, 2026"},
        ]
        
        self._populate_table(sample_patients)
    
    def _populate_table(self, patients: list):
        """Populate table with patient data."""
        self.table.setRowCount(len(patients))
        
        for row, patient in enumerate(patients):
            # MRN
            mrn_item = QTableWidgetItem(patient['mrn'])
            mrn_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.table.setItem(row, 0, mrn_item)
            
            # Name
            name_item = QTableWidgetItem(patient['name'])
            self.table.setItem(row, 1, name_item)
            
            # Sessions
            sessions_item = QTableWidgetItem(str(patient['sessions']))
            sessions_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.table.setItem(row, 2, sessions_item)
            
            # Last session
            last_item = QTableWidgetItem(patient['last_session'])
            self.table.setItem(row, 3, last_item)
            
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
                lambda checked, pid=patient['id']: self.view_patient_requested.emit(pid)
            )
            actions_layout.addWidget(view_btn)
            
            edit_btn = QPushButton("Edit")
            edit_btn.setObjectName("secondaryButton")
            edit_btn.setStyleSheet("padding: 6px 12px; font-size: 12px;")
            edit_btn.setCursor(Qt.CursorShape.PointingHandCursor)
            actions_layout.addWidget(edit_btn)
            
            self.table.setCellWidget(row, 4, actions_widget)
            self.table.setRowHeight(row, 56)
    
    def _show_create_dialog(self):
        """Show create patient dialog."""
        dialog = CreatePatientDialog(self)
        dialog.patient_created.connect(self._on_patient_created)
        dialog.exec()
    
    def _on_patient_created(self, data: dict):
        """Handle new patient creation."""
        # TODO: Hook up to backend endpoint
        # For now, just add to table
        row = self.table.rowCount()
        self.table.insertRow(row)
        
        name = f"{data['first_name']} {data['last_name']}"
        
        mrn_item = QTableWidgetItem(data['mrn'])
        mrn_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
        self.table.setItem(row, 0, mrn_item)
        
        name_item = QTableWidgetItem(name)
        self.table.setItem(row, 1, name_item)
        
        sessions_item = QTableWidgetItem("0")
        sessions_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
        self.table.setItem(row, 2, sessions_item)
        
        today = datetime.now().strftime("%b %d, %Y")
        last_item = QTableWidgetItem(today)
        self.table.setItem(row, 3, last_item)
        
        # Add action buttons
        actions_widget = QWidget()
        actions_layout = QHBoxLayout(actions_widget)
        actions_layout.setContentsMargins(4, 4, 4, 4)
        actions_layout.setSpacing(4)
        
        view_btn = QPushButton("View")
        view_btn.setObjectName("secondaryButton")
        view_btn.setStyleSheet("padding: 6px 12px; font-size: 12px;")
        view_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        actions_layout.addWidget(view_btn)
        
        edit_btn = QPushButton("Edit")
        edit_btn.setObjectName("secondaryButton")
        edit_btn.setStyleSheet("padding: 6px 12px; font-size: 12px;")
        edit_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        actions_layout.addWidget(edit_btn)
        
        self.table.setCellWidget(row, 4, actions_widget)
        self.table.setRowHeight(row, 56)
    
    def _filter_patients(self, text: str):
        """Filter table by search text."""
        for row in range(self.table.rowCount()):
            mrn = self.table.item(row, 0).text().lower()
            name = self.table.item(row, 1).text().lower()
            
            match = text.lower() in mrn or text.lower() in name
            self.table.setRowHidden(row, not match)
    
    def load_patients(self, patients: list):
        """Load patients from backend.
        
        Args:
            patients: List of patient dicts from API
        """
        # TODO: Hook up to backend endpoint
        self._populate_table(patients)
