"""
Patients Page for TranscribeNotes Application
Patient profile management and listing
"""

from __future__ import annotations

from datetime import datetime

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QAbstractItemView,
    QDialog,
    QFormLayout,
    QFrame,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QTextEdit,
    QVBoxLayout,
    QWidget,
    QHeaderView,
)

from app.components.no_scroll_combo import NoScrollComboBox
from app.db import (
    AuthorizationError,
    DatabaseInitializationError,
    InvalidDatabaseKeyError,
    MissingDatabaseKeyError,
    create_client_profile,
    delete_client_profile,
    list_client_profiles,
    list_session_records,
)


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

        title = QLabel("New Patient Profile")
        title.setObjectName("dialogTitle")
        layout.addWidget(title)

        form = QFormLayout()
        form.setSpacing(16)
        form.setLabelAlignment(Qt.AlignmentFlag.AlignRight)

        self.first_name_input = QLineEdit()
        self.first_name_input.setPlaceholderText("First name")
        form.addRow("First Name:", self.first_name_input)

        self.last_name_input = QLineEdit()
        self.last_name_input.setPlaceholderText("Last name")
        form.addRow("Last Name:", self.last_name_input)

        self.notes_input = QTextEdit()
        self.notes_input.setPlaceholderText(
            "Initial notes or identifying information..."
        )
        self.notes_input.setMaximumHeight(100)
        form.addRow("Notes:", self.notes_input)

        layout.addLayout(form)

        self.error_label = QLabel("")
        self.error_label.setObjectName("errorLabel")
        self.error_label.setVisible(False)
        self.error_label.setWordWrap(True)
        layout.addWidget(self.error_label)

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
            "first_name": self.first_name_input.text().strip(),
            "last_name": self.last_name_input.text().strip(),
            "notes": self.notes_input.toPlainText().strip(),
        }

        if not data["first_name"] or not data["last_name"]:
            self._show_error("First name and last name are required")
            return

        self.error_label.clear()
        self.error_label.setVisible(False)
        self.patient_created.emit(data)
        self.accept()

    def _show_error(self, message: str):
        self.error_label.setText(message)
        self.error_label.setVisible(True)


class PatientsPage(QWidget):
    """Patient management page with list and search."""

    view_patient_requested = Signal(int)  # patient_id

    def __init__(self, parent=None):
        super().__init__(parent)
        self._current_account = None
        self._patients_cache: list[dict] = []
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

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

        self.create_btn = QPushButton("+ New Patient")
        self.create_btn.setObjectName("primaryButton")
        self.create_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.create_btn.setEnabled(False)
        self.create_btn.clicked.connect(self._show_create_dialog)
        header_layout.addWidget(self.create_btn)

        layout.addWidget(header)

        content = QWidget()
        content.setObjectName("pageContent")
        content_layout = QVBoxLayout(content)
        content_layout.setContentsMargins(40, 24, 40, 32)
        content_layout.setSpacing(20)

        filter_layout = QHBoxLayout()
        filter_layout.setSpacing(16)

        self.search_input = QLineEdit()
        self.search_input.setObjectName("searchInput")
        self.search_input.setPlaceholderText("Search patients by name...")
        self.search_input.setMinimumWidth(300)
        self.search_input.textChanged.connect(self._filter_patients)
        filter_layout.addWidget(self.search_input)

        filter_layout.addStretch()

        self.sort_combo = NoScrollComboBox()
        self.sort_combo.addItem("Sort: Most Recent")
        self.sort_combo.addItem("Sort: Name A-Z")
        self.sort_combo.addItem("Sort: Name Z-A")
        self.sort_combo.currentIndexChanged.connect(self._apply_sort_and_refresh)
        filter_layout.addWidget(self.sort_combo)

        content_layout.addLayout(filter_layout)

        self.table = QTableWidget()
        self.table.setColumnCount(4)
        self.table.setHorizontalHeaderLabels(
            ["Patient Name", "Sessions", "Last Session", "Actions"]
        )

        self.table.horizontalHeader().setSectionResizeMode(
            QHeaderView.ResizeMode.Stretch
        )
        self.table.horizontalHeader().setSectionResizeMode(
            1, QHeaderView.ResizeMode.Fixed
        )
        self.table.horizontalHeader().setSectionResizeMode(
            3, QHeaderView.ResizeMode.Fixed
        )
        self.table.setColumnWidth(1, 90)
        self.table.setColumnWidth(3, 170)

        self.table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.table.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.table.setAlternatingRowColors(True)
        self.table.verticalHeader().setVisible(False)
        self.table.setShowGrid(False)

        self._populate_table([])
        content_layout.addWidget(self.table)

        pagination_layout = QHBoxLayout()
        pagination_layout.addStretch()

        self.page_label = QLabel("Sign in as a psychologist to load patients")
        self.page_label.setObjectName("cardSubtitle")
        pagination_layout.addWidget(self.page_label)

        self.prev_btn = QPushButton("Previous")
        self.prev_btn.setObjectName("secondaryButton")
        self.prev_btn.setStyleSheet("padding: 8px 16px;")
        self.prev_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.prev_btn.setEnabled(False)
        pagination_layout.addWidget(self.prev_btn)

        self.next_btn = QPushButton("Next")
        self.next_btn.setObjectName("secondaryButton")
        self.next_btn.setStyleSheet("padding: 8px 16px;")
        self.next_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.next_btn.setEnabled(False)
        pagination_layout.addWidget(self.next_btn)

        content_layout.addLayout(pagination_layout)
        layout.addWidget(content)

    def set_authenticated_account(self, account):
        """Set current signed-in account and refresh patients if applicable."""
        self._current_account = account
        self.search_input.clear()

        if account is None:
            self.create_btn.setEnabled(False)
            self._patients_cache = []
            self._populate_table([])
            self.page_label.setText("Sign in as a psychologist to load patients")
            return

        if getattr(account, "role", None) != "psychologist":
            self.create_btn.setEnabled(False)
            self._patients_cache = []
            self._populate_table([])
            self.page_label.setText("Patient management is available to psychologists")
            return

        self.create_btn.setEnabled(True)
        self.refresh_patients()

    def refresh_patients(self):
        """Load patient rows from the local database for the signed-in psychologist."""
        account = self._current_account
        if account is None or getattr(account, "role", None) != "psychologist":
            self._patients_cache = []
            self._populate_table([])
            return

        try:
            clients = list_client_profiles(account.id)
            sessions = list_session_records(account.id)
        except AuthorizationError as exc:
            self._patients_cache = []
            self._populate_table([])
            self.page_label.setText(str(exc))
            return
        except (MissingDatabaseKeyError, InvalidDatabaseKeyError) as exc:
            self._patients_cache = []
            self._populate_table([])
            self.page_label.setText(f"Database error: {exc}")
            return
        except DatabaseInitializationError as exc:
            self._patients_cache = []
            self._populate_table([])
            self.page_label.setText(f"Database setup failed: {exc}")
            return
        except Exception as exc:
            self._patients_cache = []
            self._populate_table([])
            self.page_label.setText(f"Failed to load patients: {exc}")
            return

        session_counts: dict[int, int] = {}
        session_last: dict[int, str] = {}
        for session in sessions:
            pid = session.client_profile_id
            session_counts[pid] = session_counts.get(pid, 0) + 1
            prev_ts = session_last.get(pid)
            if prev_ts is None or session.created_at > prev_ts:
                session_last[pid] = session.created_at

        rows: list[dict] = []
        for client in clients:
            rows.append(
                {
                    "id": client.id,
                    "name": self._format_patient_name(client.first_name, client.last_name),
                    "sessions": session_counts.get(client.id, 0),
                    "last_session": self._format_last_session(session_last.get(client.id)),
                }
            )

        self._patients_cache = rows
        self._apply_sort_and_refresh()

    def _apply_sort_and_refresh(self):
        """Apply UI sort selection to cached patient rows and repopulate table."""
        rows = list(self._patients_cache)
        sort_text = self.sort_combo.currentText() if hasattr(self, "sort_combo") else ""

        if "Name A-Z" in sort_text:
            rows.sort(key=lambda p: (p["name"].lower(), p["id"]))
        elif "Name Z-A" in sort_text:
            rows.sort(key=lambda p: (p["name"].lower(), p["id"]), reverse=True)
        # "Most Recent" preserves DB order (created_at DESC from list_client_profiles)

        self._populate_table(rows)
        count = len(rows)
        self.page_label.setText(
            f"Showing {count} of {count} patient{'s' if count != 1 else ''}"
        )
        self._filter_patients(self.search_input.text())

    def _format_patient_name(self, first_name: str | None, last_name: str | None) -> str:
        parts = [p for p in [first_name, last_name] if p]
        return " ".join(parts) if parts else "Unnamed Patient"

    def _format_last_session(self, created_at: str | None) -> str:
        if not created_at:
            return "No sessions"
        for fmt in ("%Y-%m-%dT%H:%M:%S.%fZ", "%Y-%m-%dT%H:%M:%SZ"):
            try:
                return datetime.strptime(created_at, fmt).strftime("%b %d, %Y")
            except ValueError:
                continue
        return created_at

    def _generate_hidden_client_code(self) -> str:
        """Generate a hidden numeric identifier for the DB-only client_code field."""
        return datetime.utcnow().strftime("%Y%m%d%H%M%S%f")

    def _populate_table(self, patients: list):
        """Populate table with patient data."""
        self.table.setRowCount(len(patients))

        for row, patient in enumerate(patients):
            name_item = QTableWidgetItem(patient["name"])
            self.table.setItem(row, 0, name_item)

            sessions_item = QTableWidgetItem(str(patient["sessions"]))
            sessions_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.table.setItem(row, 1, sessions_item)

            last_item = QTableWidgetItem(patient["last_session"])
            self.table.setItem(row, 2, last_item)

            actions_widget = QWidget()
            actions_layout = QHBoxLayout(actions_widget)
            actions_layout.setContentsMargins(4, 4, 4, 4)
            actions_layout.setSpacing(4)

            view_btn = QPushButton("View")
            view_btn.setObjectName("tableButton")
            view_btn.setCursor(Qt.CursorShape.PointingHandCursor)
            view_btn.clicked.connect(
                lambda checked, pid=patient["id"]: self.view_patient_requested.emit(pid)
            )
            actions_layout.addWidget(view_btn)

            delete_btn = QPushButton("Delete")
            delete_btn.setObjectName("tableDangerButton")
            delete_btn.setCursor(Qt.CursorShape.PointingHandCursor)
            delete_btn.clicked.connect(
                lambda checked, p=patient: self._delete_patient(p)
            )
            actions_layout.addWidget(delete_btn)

            self.table.setCellWidget(row, 3, actions_widget)
            self.table.setRowHeight(row, 56)

    def _show_create_dialog(self):
        """Show create patient dialog."""
        account = self._current_account
        if account is None or getattr(account, "role", None) != "psychologist":
            QMessageBox.information(
                self,
                "Patients",
                "Sign in as a psychologist to create patient profiles.",
            )
            return

        dialog = CreatePatientDialog(self)
        dialog.patient_created.connect(self._on_patient_created)
        dialog.exec()

    def _on_patient_created(self, data: dict):
        """Create a patient in the local DB and refresh the list."""
        account = self._current_account
        if account is None or getattr(account, "role", None) != "psychologist":
            QMessageBox.warning(self, "Create Patient", "No psychologist account is active.")
            return

        try:
            create_client_profile(
                psychologist_account_id=account.id,
                client_code=self._generate_hidden_client_code(),
                first_name=data["first_name"],
                last_name=data["last_name"],
                notes=(data["notes"] or None),
            )
        except AuthorizationError as exc:
            QMessageBox.warning(self, "Create Patient", str(exc))
            return
        except Exception as exc:
            QMessageBox.warning(self, "Create Patient", str(exc))
            return

        self.refresh_patients()

    def _delete_patient(self, patient: dict):
        """Delete a patient profile for the current psychologist."""
        account = self._current_account
        if account is None or getattr(account, "role", None) != "psychologist":
            QMessageBox.warning(self, "Delete Patient", "No psychologist account is active.")
            return

        confirm = QMessageBox.question(
            self,
            "Delete Patient",
            f"Delete patient '{patient['name']}'?\n\n"
            "Any linked session records will also be deleted.",
        )
        if confirm != QMessageBox.StandardButton.Yes:
            return

        try:
            deleted = delete_client_profile(
                psychologist_account_id=account.id,
                client_profile_id=patient["id"],
            )
        except AuthorizationError as exc:
            QMessageBox.warning(self, "Delete Patient", str(exc))
            return
        except Exception as exc:
            QMessageBox.warning(self, "Delete Patient", str(exc))
            return

        if not deleted:
            QMessageBox.information(
                self,
                "Delete Patient",
                "Patient record was not found or was already deleted.",
            )
        self.refresh_patients()

    def _filter_patients(self, text: str):
        """Filter table by search text."""
        query = text.lower().strip()
        visible_count = 0

        for row in range(self.table.rowCount()):
            name_item = self.table.item(row, 0)
            name = name_item.text().lower() if name_item else ""

            match = (query in name) if query else True
            self.table.setRowHidden(row, not match)
            if match:
                visible_count += 1

        total = self.table.rowCount()
        if self._current_account is None:
            self.page_label.setText("Sign in as a psychologist to load patients")
        elif getattr(self._current_account, "role", None) != "psychologist":
            self.page_label.setText("Patient management is available to psychologists")
        else:
            self.page_label.setText(
                f"Showing {visible_count} of {total} patient{'s' if total != 1 else ''}"
            )

    def load_patients(self, patients: list):
        """Load patients from backend-like data."""
        self._patients_cache = list(patients)
        self._apply_sort_and_refresh()
