"""
Patients Page for TranscribeNotes Application
Patient profile management and listing
"""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
    QPushButton, QFrame, QScrollArea, QLineEdit,
    QTableWidget, QTableWidgetItem, QHeaderView,
    QDialog, QFormLayout, QTextEdit,
    QAbstractItemView
)
from PySide6.QtCore import Qt, Signal
from app.components.no_scroll_combo import NoScrollComboBox
from datetime import datetime

# from app.src.models.Patient import Patient # TODO make me!


class CreateNewPatientDialog(QDialog):
    """Dialog for creating a new patient profile."""
    
    patient_created = Signal(dict)  # Patient data
    _patient_data = dict() # func scope patient data dict to create and store in db later
    
    def __init__(self, parent=None):
        
        super().__init__(parent)
        self.setWindowTitle("Create New Patient Profile")
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
        create_btn.clicked.connect(self._handle_create_patient)
        buttons_layout.addWidget(create_btn)
        
        layout.addLayout(buttons_layout)
    
    def _handle_create_patient(self):
        """Validate new patient creation and emit patient creation event."""
        
        # TODO move validation and all sanitization etc to model, make it PHat with a capital PH
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
        
        # TODO rest of validation, sanity checks, xss prevention, etc
        
        self.patient_created.emit(data) # emit event
        
        # TODO insert record into database
        # new_patient = Patient(self._patient_data)
        # new_patient.save_to_db() or what not
        
        # TODO pass confirmation or error to dialog
        self.accept()


class CreateEditPatientDialog(QDialog):
    """Dialog for editing an existing patient profile."""
    
    patient_edited = Signal(dict)  # Patient edited event
    
    _local_patient_data = dict() # patient data dict to edit
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        self._ensure_local_patient_data()
        
        # ui setup
        self.setMinimumWidth(500)
        self._setup_ui()
        
        # now that the ui is setup, populate the form fields with the current patient data
        self._load_patient_data_into_edit_dialog()
        
        self.setWindowTitle(f"Edit Patient Profile: {self._local_patient_data["first_name"]} {self._local_patient_data['last_name']}") # TODO make a class model for patients, do validation and all that in fat models, leave our controllers skinny and just doing the handoffs and referrals and whatnot
        
        
    def _load_patient_data_into_edit_dialog(self):
        """Load patient data from dict and populate the inputs' text/plaintext as needed."""
        
        # set the text/plaintext fields of all the related form inputs
        self.mrn_input.setText(self._patient_data['mrn'])
        self.first_name_input.setText(self._patient_data['first_name'])
        self.last_name_input.setText(self._patient_data['last_name'])
        self.dob_input.setText(self._patient_data['dob'])
        self.notes_input.setPlainText(self._patient_data['notes'])
        
        # that should populate the existing form inputs with current data for patient
        # TODO add more fields as needed
    
    def _setup_ui(self):
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(32, 32, 32, 32)
        layout.setSpacing(24)
        
        # Title
        title = QLabel(f"Edit Patient Profile: {self._patient_data["first_name"]} {self._patient_data['last_name']}")
        title.setObjectName("dialogTitle") # TODO what is this object specifically named for? are we accessing by "dialogTitle" somewhere?
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
        
        cancel_btn = QPushButton("✖ Cancel")
        cancel_btn.setObjectName("secondaryButton")
        cancel_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        cancel_btn.clicked.connect(self.reject) # abort mission
        buttons_layout.addWidget(cancel_btn)
        
        edit_btn = QPushButton("✓ Save Changes")
        edit_btn.setObjectName("primaryButton")
        edit_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        edit_btn.clicked.connect(
            lambda checked, pid=self._local_patient_data['id']: self._handle_edit_patient() # view single patient page (passed id)
        )
        buttons_layout.addWidget(edit_btn)
        
        layout.addLayout(buttons_layout)
    
    def _handle_edit_patient(self):
        """Validate, create and emit patient."""
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
        
        # TODO rest of validation, sanity checks, xss prevention, etc
        
        # self.patient_update(idx, patient_data) # update patient in db something like this
        self.patient_edited.emit(data) # emit event
        self.accept()
        
    def _ensure_local_patient_data(self):
        """Ensure local patient data is available to the Edit Patient Dialog class."""
        
        if not self._patient_data:
            print(f"Edit Patient Dialog Class: No local patient data found to edit!") if DEBUG else None
            raise ValueError("Edit Patient Dialog Class: No local patient data found to edit!")


class PatientsPage(QWidget):
    """Patient management page with list and search."""
    
    view_patient_requested = Signal(int)  # patient_id
    edit_patient_requested = Signal(int)  # patient_id
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        self._setup_ui()
        
        main_win = self.window()
            
        patient_dataset = getattr(self.window(), "_patient_dataset")
        if not patient_dataset:
            print(f"Patients Page: No patient dataset found to load! Can't init patients page! Loading sample dataset for now!") if DEBUG else None
            
            # Load sample data for now # TODO swap to /real/ data from db query
            self._load_sample_patient_dataset()
            
        else:
            try:
                self._load_patient_dataset_from_db()
                print(f"Patients Page: Patient dataset loaded from db successfully!")
                
            except Exception as e:
                print(f"Patients Page: Error loading patient dataset from db! {e}")
                raise e # pass it on down
        
        
        main_win._ensure_patient_dataset() # make sure we populated the patient dataset in the main window object
        
        # populate dat table
        self._populate_table(getattr(main_win, "_patient_dataset")) # populate table with patient data    
            
    
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
        self.search_input.setPlaceholderText("Search patients by name or MRN...")
        self.search_input.setMinimumWidth(300)
        self.search_input.textChanged.connect(self._filter_patients)
        filter_layout.addWidget(self.search_input)
        
        filter_layout.addStretch()
        
        self.sort_combo = NoScrollComboBox()
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
        
        content_layout.addWidget(self.table)
        
        # Pagination
        pagination_layout = QHBoxLayout()
        pagination_layout.addStretch()
        
        self.page_label = QLabel("Showing 1-10 of 42 patients") # TODO update this to show dynamic numbers!
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
    
    def _load_sample_patient_dataset(self):
        """Load sample patient dataset for skeleton."""
        
        # TODO implement me, connect to db for retrieval!
        _sample_patient_dataset = [
            {"id": 1, "mrn": "12345", "name": "John Doe", "sessions": 12, "last_session": "Jan 28, 2026"},
            {"id": 2, "mrn": "12346", "name": "Maria Santos", "sessions": 8, "last_session": "Jan 27, 2026"},
            {"id": 3, "mrn": "12347", "name": "Alex Rodriguez", "sessions": 15, "last_session": "Jan 26, 2026"},
            {"id": 4, "mrn": "12348", "name": "Kim Thompson", "sessions": 6, "last_session": "Jan 25, 2026"},
            {"id": 5, "mrn": "12349", "name": "James Wilson", "sessions": 22, "last_session": "Jan 24, 2026"},
            {"id": 6, "mrn": "12350", "name": "Sarah Chen", "sessions": 4, "last_session": "Jan 23, 2026"},
            {"id": 7, "mrn": "12351", "name": "Michael Brown", "sessions": 9, "last_session": "Jan 22, 2026"},
            {"id": 8, "mrn": "12352", "name": "Emily Davis", "sessions": 11, "last_session": "Jan 21, 2026"},
        ]
        
        main_win = self.window()
        setattr(main_win, "_patient_dataset", _sample_patient_dataset)
    
    def _populate_table(self, patients: dict):
        """Populate table with patient data."""
        self.table.setRowCount(len(patients)) # preallocate rows
        
        for row, patient in enumerate(patients): # enumerate => 0-based index remember to add 1 as needed!
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
            view_btn.setObjectName("tableButton")
            view_btn.setCursor(Qt.CursorShape.PointingHandCursor)
            view_btn.clicked.connect(
                lambda checked, pid=patient['id']: self.view_patient_requested.emit(pid) # view single patient page (passed id)
            )
            actions_layout.addWidget(view_btn)

            edit_btn = QPushButton("Edit")
            edit_btn.setObjectName("tableButton")
            edit_btn.setCursor(Qt.CursorShape.PointingHandCursor)
            edit_btn.clicked.connect(
                lambda checked, pid=patient['id']: self.edit_patient_requested.emit(pid) # edit single patient page (passed id)
            )
            actions_layout.addWidget(edit_btn)
            
            self.table.setCellWidget(row, 4, actions_widget)
            self.table.setRowHeight(row, 56)
    
    def _show_create_dialog(self):
        """Show create patient dialog."""
        dialog = CreateNewPatientDialog(self)
        dialog.patient_created.connect(self._on_patient_created)
        dialog.exec()
        
    def _show_edit_dialog(self):
        """Show edit patient dialog on patients page."""

        patient_data = getattr(self.window(), "_patient_data")
        if not patient_data:
            print(f"Show Edit Dialog: No patient data found in `window._patient_data` var to edit.") if DEBUG else None
            raise ValueError("No patient data found in `window._patient_data` var to edit.")
        
        dialog = CreatePatientEditDialog(self, patient_data)
        dialog.patient_edited.connect(self._on_patient_edited)
        dialog.exec()
    
    def _on_patient_created(self, patient: dict):
        """Handle new patient creation."""
        # TODO: Hook up to backend endpoint
        # For now, just add to table
        row = self.table.rowCount() # current, pre-adding of new patient, row count of table
        self.table.insertRow(row) # insert at last index to append to list
        # TODO should probably recall whatever search param or sorts/filters/etc are active and return to that state, pyside should handle this automatically I think, as this is just a dialog/modal
        
        name = f"{patient['first_name']} {patient['last_name']}" # TODO may need to adjust this for non-US/English cultural name conventions, depending on how far we go for internationalization support ...
        
        mrn_item = QTableWidgetItem(patient['mrn'])
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
        view_btn.setObjectName("tableButton")
        view_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        view_btn.clicked.connect(
            lambda checked, pid=patient['id']: self.view_patient_requested.emit(pid) # view single patient page (passed id)
        )
        actions_layout.addWidget(view_btn)

        edit_btn = QPushButton("Edit")
        edit_btn.setObjectName("tableButton")
        edit_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        edit_btn.clicked.connect(
            lambda checked, pid=patient['id']: self.edit_patient_requested.emit(pid) # view single patient page (passed id)
        )
        actions_layout.addWidget(edit_btn)
        
        self.table.setCellWidget(row, 4, actions_widget)
        self.table.setRowHeight(row, 56)
        
    def _on_patient_edited(self, data: dict):
        """Handle edit patient."""
        # TODO: Hook up to backend endpoint
        # For now, just update table
        row_idx_to_update = 0 # self.table.get_the_damn_index_from_the_widget(widget) # TODO figure this out

        # this chunk converts the data dict passed in to a QTableWidgetItem, then should /replace/ the existing row for this record. TODO need to find index of said record.
        # TODO some DRY issues here, duplicating the dialog code, need to combine and then depending on new/edit, populate existing values, or default to blanks for new
        name = f"{data['first_name']} {data['last_name']}"
        
        mrn_item = QTableWidgetItem(data['mrn'])
        mrn_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
        self.table.setItem(row_idx_to_update, 0, mrn_item)
        
        name_item = QTableWidgetItem(name)
        self.table.setItem(row_idx_to_update, 1, name_item)
        
        sessions_item = QTableWidgetItem("0")
        sessions_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
        self.table.setItem(row_idx_to_update, 2, sessions_item)
        
        today = datetime.now().strftime("%b %d, %Y")
        last_item = QTableWidgetItem(today)
        self.table.setItem(row_idx_to_update, 3, last_item)
        
        # Add action buttons
        actions_widget = QWidget()
        actions_layout = QHBoxLayout(actions_widget)
        actions_layout.setContentsMargins(4, 4, 4, 4)
        actions_layout.setSpacing(4)
        
        view_btn = QPushButton("View")
        view_btn.setObjectName("tableButton")
        view_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        actions_layout.addWidget(view_btn)

        edit_btn = QPushButton("Edit")
        edit_btn.setObjectName("tableButton")
        edit_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        actions_layout.addWidget(edit_btn)
        
        # TODO update cell widget with appropriate widget above and proper index of existing row
        self.table.setCellWidget(row_idx_to_update, 0, actions_widget)
        self.table.setCellWidget(row_idx_to_update, 1, actions_widget)
        self.table.setCellWidget(row_idx_to_update, 2, actions_widget)
        self.table.setCellWidget(row_idx_to_update, 3, actions_widget)
        self.table.setCellWidget(row_idx_to_update, 4, actions_widget)
        self.table.setRowHeight(row_idx_to_update, 56) # TODO why are we setting rowheight here?

    
    def _filter_patients(self, text: str):
        """Filter table by search text."""
        for row in range(self.table.rowCount()):
            mrn = self.table.item(row, 0).text().lower()
            name = self.table.item(row, 1).text().lower()
            
            match = text.lower() in mrn or text.lower() in name
            self.table.setRowHidden(row, not match)
    
    def _load_patient_data_into_table(self):
        """Load patients from backend."""
        
        main_win = self.window()
        main_win._ensure_patient_dataset()
        
        # TODO: Hook up to backend endpoint, basically a SELECT * FROM patients WHERE owner_id = current_user_id ORDER BY date DESC kinda query
        self._populate_table(getattr(main_win, "_patient_data")) # populate table with patient data


    def _ensure_local_patient_data(self):
        """Ensure local patient data (singular!) is available for use for edit and others."""
        
        if not self._patient_data:
            print(f"Patients Page Class: No local patient data found to edit!") if DEBUG else None
            raise ValueError("Patients Page Class: No local patient data found to edit!")