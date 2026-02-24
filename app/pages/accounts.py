"""
Accounts Page for TranscribeNotes Application
User account management and administration
"""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
    QPushButton, QFrame, QScrollArea, QLineEdit,
    QTableWidget, QTableWidgetItem, QHeaderView,
    QAbstractItemView, QDialog,
    QFormLayout, QCheckBox
)
from PySide6.QtCore import Qt, Signal
from app.components.no_scroll_combo import NoScrollComboBox
from app.db import (
    AccountExistsError,
    AuthenticationError,
    AuthorizationError,
    DatabaseInitializationError,
    InvalidDatabaseKeyError,
    MissingDatabaseKeyError,
    create_psychologist_account,
    initialize_database,
)


class CreateAccountDialog(QDialog):
    """Dialog for creating a new user account."""
    
    account_created = Signal(dict)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Create Account")
        self.setMinimumWidth(450)
        self._setup_ui()
    
    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(32, 32, 32, 32)
        layout.setSpacing(24)
        
        # Title
        title = QLabel("New User Account")
        title.setObjectName("dialogTitle")
        layout.addWidget(title)
        
        # Form
        form = QFormLayout()
        form.setSpacing(16)
        form.setLabelAlignment(Qt.AlignmentFlag.AlignRight)
        
        self.username_input = QLineEdit()
        self.username_input.setPlaceholderText("Enter username")
        form.addRow("Username:", self.username_input)
        
        self.email_input = QLineEdit()
        self.email_input.setPlaceholderText("user@example.com")
        form.addRow("Email:", self.email_input)
        
        self.name_input = QLineEdit()
        self.name_input.setPlaceholderText("Full name")
        form.addRow("Full Name:", self.name_input)
        
        self.role_combo = NoScrollComboBox()
        self.role_combo.addItem("Psychologist", "psychologist")
        form.addRow("Role:", self.role_combo)
        
        self.password_input = QLineEdit()
        self.password_input.setPlaceholderText("Initial password")
        self.password_input.setEchoMode(QLineEdit.EchoMode.Password)
        form.addRow("Password:", self.password_input)
        
        self.confirm_input = QLineEdit()
        self.confirm_input.setPlaceholderText("Confirm password")
        self.confirm_input.setEchoMode(QLineEdit.EchoMode.Password)
        form.addRow("Confirm:", self.confirm_input)

        self.admin_password_input = QLineEdit()
        self.admin_password_input.setPlaceholderText("In-person admin authorization password")
        self.admin_password_input.setEchoMode(QLineEdit.EchoMode.Password)
        form.addRow("Admin Auth:", self.admin_password_input)
        
        layout.addLayout(form)

        admin_note = QLabel(
            "A physical administrator must enter the local admin authorization "
            "password to create a psychologist account."
        )
        admin_note.setObjectName("cardSubtitle")
        admin_note.setWordWrap(True)
        layout.addWidget(admin_note)
        
        # Options
        self.require_change = QCheckBox("Require password change on first login")
        self.require_change.setChecked(True)
        layout.addWidget(self.require_change)
        
        # Error label
        self.error_label = QLabel("")
        self.error_label.setObjectName("errorLabel")
        self.error_label.setVisible(False)
        layout.addWidget(self.error_label)
        
        # Buttons
        buttons_layout = QHBoxLayout()
        buttons_layout.addStretch()
        
        cancel_btn = QPushButton("Cancel")
        cancel_btn.setObjectName("secondaryButton")
        cancel_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        cancel_btn.clicked.connect(self.reject)
        buttons_layout.addWidget(cancel_btn)
        
        create_btn = QPushButton("Create Account")
        create_btn.setObjectName("primaryButton")
        create_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        create_btn.clicked.connect(self._create_account)
        buttons_layout.addWidget(create_btn)
        
        layout.addLayout(buttons_layout)
    
    def _create_account(self):
        """Validate and create account."""
        username = self.username_input.text().strip()
        email = self.email_input.text().strip()
        name = self.name_input.text().strip()
        password = self.password_input.text()
        confirm = self.confirm_input.text()
        admin_password = self.admin_password_input.text()
        
        # Validation
        if not username or not name or not password or not admin_password:
            self._show_error("Please fill in all required fields")
            return
        
        if password != confirm:
            self._show_error("Passwords do not match")
            return
        
        if len(password) < 8:
            self._show_error("Password must be at least 8 characters")
            return
        
        if self.role_combo.currentData() != "psychologist":
            self._show_error("Only psychologist account creation is available right now")
            return

        try:
            initialize_database()
            account = create_psychologist_account(
                psychologist_username=username,
                psychologist_password=password,
                psychologist_display_name=name,
                admin_master_password=admin_password,
                authorization_note="Created from GUI account dialog",
            )
        except AccountExistsError as exc:
            self._show_error(str(exc))
            return
        except AuthenticationError:
            self._show_error("Invalid admin authorization password")
            return
        except AuthorizationError as exc:
            self._show_error(str(exc))
            return
        except MissingDatabaseKeyError:
            self._show_error("No database key is available on this machine")
            return
        except InvalidDatabaseKeyError:
            self._show_error("The local database key could not unlock the database")
            return
        except DatabaseInitializationError as exc:
            self._show_error(f"Database setup failed: {exc}")
            return
        except Exception as exc:
            self._show_error(f"Unexpected account creation error: {exc}")
            return

        data = {
            'id': account.id,
            'username': account.username,
            'email': email,
            'name': account.display_name,
            'role': account.role,
            'role_display': "Psychologist",
            'require_password_change': self.require_change.isChecked(),
            'active': account.is_active,
        }

        self.account_created.emit(data)
        self.accept()
    
    def _show_error(self, message: str):
        """Display error message."""
        self.error_label.setText(message)
        self.error_label.setVisible(True)


class EditAccountDialog(QDialog):
    """Dialog for editing an existing user account."""
    
    account_updated = Signal(dict)
    
    def __init__(self, account_data: dict, parent=None):
        super().__init__(parent)
        self.account_data = account_data
        self.setWindowTitle("Edit Account")
        self.setMinimumWidth(450)
        self._setup_ui()
    
    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(32, 32, 32, 32)
        layout.setSpacing(24)
        
        # Title
        title = QLabel("Edit User Account")
        title.setObjectName("dialogTitle")
        layout.addWidget(title)
        
        # Form
        form = QFormLayout()
        form.setSpacing(16)
        form.setLabelAlignment(Qt.AlignmentFlag.AlignRight)
        
        self.username_input = QLineEdit()
        self.username_input.setText(self.account_data.get('username', ''))
        self.username_input.setEnabled(False)  # Username typically not editable
        form.addRow("Username:", self.username_input)
        
        self.email_input = QLineEdit()
        self.email_input.setText(self.account_data.get('email', ''))
        form.addRow("Email:", self.email_input)
        
        self.name_input = QLineEdit()
        self.name_input.setText(self.account_data.get('name', ''))
        form.addRow("Full Name:", self.name_input)
        
        self.role_combo = NoScrollComboBox()
        self.role_combo.addItem("Psychologist", "psychologist")
        self.role_combo.addItem("Administrator", "admin")
        
        # Set current role
        current_role = self.account_data.get('role', 'psychologist')
        index = self.role_combo.findData(current_role)
        if index >= 0:
            self.role_combo.setCurrentIndex(index)
        form.addRow("Role:", self.role_combo)
        
        layout.addLayout(form)
        
        # Password reset option
        self.reset_password = QCheckBox("Reset password on next login")
        layout.addWidget(self.reset_password)
        
        # Account status
        self.active_check = QCheckBox("Account active")
        self.active_check.setChecked(self.account_data.get('active', True))
        layout.addWidget(self.active_check)
        
        # Buttons
        buttons_layout = QHBoxLayout()
        buttons_layout.addStretch()
        
        cancel_btn = QPushButton("Cancel")
        cancel_btn.setObjectName("secondaryButton")
        cancel_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        cancel_btn.clicked.connect(self.reject)
        buttons_layout.addWidget(cancel_btn)
        
        save_btn = QPushButton("Save Changes")
        save_btn.setObjectName("primaryButton")
        save_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        save_btn.clicked.connect(self._save_changes)
        buttons_layout.addWidget(save_btn)
        
        layout.addLayout(buttons_layout)
    
    def _save_changes(self):
        """Save account changes."""
        data = {
            'id': self.account_data.get('id'),
            'username': self.username_input.text().strip(),
            'email': self.email_input.text().strip(),
            'name': self.name_input.text().strip(),
            'role': self.role_combo.currentData(),
            'role_display': self.role_combo.currentText(),
            'reset_password': self.reset_password.isChecked(),
            'active': self.active_check.isChecked(),
        }
        
        self.account_updated.emit(data)
        self.accept()


class AccountsPage(QWidget):
    """Account management page for administrators."""
    
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
        
        title = QLabel("User Accounts")
        title.setObjectName("pageTitle")
        
        description = QLabel("Manage system users and access permissions")
        description.setObjectName("pageDescription")
        
        title_section.addWidget(title)
        title_section.addWidget(description)
        header_layout.addLayout(title_section)
        
        header_layout.addStretch()
        
        # Create account button
        create_btn = QPushButton("+ New Account")
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
        
        # Filter bar
        filter_layout = QHBoxLayout()
        filter_layout.setSpacing(16)
        
        self.search_input = QLineEdit()
        self.search_input.setObjectName("searchInput")
        self.search_input.setPlaceholderText("Search by username or name...")
        self.search_input.setMinimumWidth(300)
        self.search_input.textChanged.connect(self._filter_accounts)
        filter_layout.addWidget(self.search_input)
        
        filter_layout.addStretch()
        
        role_label = QLabel("Role:")
        role_label.setObjectName("cardSubtitle")
        filter_layout.addWidget(role_label)
        
        self.role_filter = NoScrollComboBox()
        self.role_filter.addItem("All Roles")
        self.role_filter.addItem("Psychologist")
        self.role_filter.addItem("Administrator")
        self.role_filter.setMinimumWidth(130)
        filter_layout.addWidget(self.role_filter)
        
        status_label = QLabel("Status:")
        status_label.setObjectName("cardSubtitle")
        filter_layout.addWidget(status_label)
        
        self.status_filter = NoScrollComboBox()
        self.status_filter.addItem("All")
        self.status_filter.addItem("Active")
        self.status_filter.addItem("Inactive")
        self.status_filter.setMinimumWidth(100)
        filter_layout.addWidget(self.status_filter)
        
        content_layout.addLayout(filter_layout)
        
        # Accounts table
        self.table = QTableWidget()
        self.table.setColumnCount(6)
        self.table.setHorizontalHeaderLabels([
            "Username", "Full Name", "Email", "Role", "Status", "Actions"
        ])
        
        # Table styling
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Fixed)
        self.table.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeMode.Fixed)
        self.table.horizontalHeader().setSectionResizeMode(4, QHeaderView.ResizeMode.Fixed)
        self.table.horizontalHeader().setSectionResizeMode(5, QHeaderView.ResizeMode.Fixed)
        
        self.table.setColumnWidth(0, 130)
        self.table.setColumnWidth(3, 120)
        self.table.setColumnWidth(4, 90)
        self.table.setColumnWidth(5, 200)
        
        self.table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.table.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.table.setAlternatingRowColors(True)
        self.table.verticalHeader().setVisible(False)
        self.table.setShowGrid(False)
        
        # Load sample data
        self._load_sample_data()
        
        content_layout.addWidget(self.table)
        
        # Info section
        info_frame = QFrame()
        info_frame.setObjectName("card")
        info_layout = QHBoxLayout(info_frame)
        info_layout.setContentsMargins(20, 16, 20, 16)
        
        info_text = QLabel(
            "Account management is restricted to administrators. All changes are "
            "logged for audit purposes. Deleted accounts are soft-deleted and can "
            "be recovered within 30 days."
        )
        info_text.setObjectName("cardSubtitle")
        info_text.setWordWrap(True)
        info_layout.addWidget(info_text)
        
        content_layout.addWidget(info_frame)
        
        layout.addWidget(content)
    
    def _load_sample_data(self):
        """Load sample account data."""
        sample_accounts = [
            {"id": 1, "username": "jsmith", "name": "Dr. Jane Smith", "email": "jsmith@clinic.local", "role": "psychologist", "role_display": "Psychologist", "active": True},
            {"id": 2, "username": "admin", "name": "System Admin", "email": "admin@clinic.local", "role": "admin", "role_display": "Administrator", "active": True},
            {"id": 3, "username": "mwilson", "name": "Dr. Michael Wilson", "email": "mwilson@clinic.local", "role": "psychologist", "role_display": "Psychologist", "active": True},
            {"id": 4, "username": "slee", "name": "Dr. Sarah Lee", "email": "slee@clinic.local", "role": "psychologist", "role_display": "Psychologist", "active": True},
            {"id": 5, "username": "rgarcia", "name": "Dr. Robert Garcia", "email": "rgarcia@clinic.local", "role": "psychologist", "role_display": "Psychologist", "active": False},
        ]
        
        self._populate_table(sample_accounts)
    
    def _populate_table(self, accounts: list):
        """Populate table with account data."""
        self.table.setRowCount(len(accounts))
        
        for row, account in enumerate(accounts):
            # Username
            username_item = QTableWidgetItem(account['username'])
            self.table.setItem(row, 0, username_item)
            
            # Name
            name_item = QTableWidgetItem(account['name'])
            self.table.setItem(row, 1, name_item)
            
            # Email
            email_item = QTableWidgetItem(account['email'])
            self.table.setItem(row, 2, email_item)
            
            # Role
            role_item = QTableWidgetItem(account['role_display'])
            role_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.table.setItem(row, 3, role_item)
            
            # Status
            status = "Active" if account['active'] else "Inactive"
            status_item = QTableWidgetItem(status)
            status_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.table.setItem(row, 4, status_item)
            
            # Actions
            actions_widget = QWidget()
            actions_layout = QHBoxLayout(actions_widget)
            actions_layout.setContentsMargins(4, 4, 4, 4)
            actions_layout.setSpacing(4)
            
            edit_btn = QPushButton("Edit")
            edit_btn.setObjectName("tableButton")
            edit_btn.setCursor(Qt.CursorShape.PointingHandCursor)
            edit_btn.clicked.connect(
                lambda checked, a=account: self._show_edit_dialog(a)
            )
            actions_layout.addWidget(edit_btn)

            delete_btn = QPushButton("Delete")
            delete_btn.setObjectName("tableDangerButton")
            delete_btn.setCursor(Qt.CursorShape.PointingHandCursor)
            actions_layout.addWidget(delete_btn)

            self.table.setCellWidget(row, 5, actions_widget)
            self.table.setRowHeight(row, 56)

    def _show_create_dialog(self):
        """Show create account dialog."""
        dialog = CreateAccountDialog(self)
        dialog.account_created.connect(self._on_account_created)
        dialog.exec()

    def _show_edit_dialog(self, account: dict):
        """Show edit account dialog."""
        dialog = EditAccountDialog(account, self)
        dialog.account_updated.connect(self._on_account_updated)
        dialog.exec()

    def _on_account_created(self, data: dict):
        """Handle new account creation."""
        # TODO: Hook up to backend endpoint
        row = self.table.rowCount()
        self.table.insertRow(row)

        self.table.setItem(row, 0, QTableWidgetItem(data['username']))
        self.table.setItem(row, 1, QTableWidgetItem(data['name']))
        self.table.setItem(row, 2, QTableWidgetItem(data.get('email', '')))

        role_item = QTableWidgetItem(data['role_display'])
        role_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
        self.table.setItem(row, 3, role_item)

        status_item = QTableWidgetItem("Active")
        status_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
        self.table.setItem(row, 4, status_item)

        # Add action buttons
        actions_widget = QWidget()
        actions_layout = QHBoxLayout(actions_widget)
        actions_layout.setContentsMargins(4, 4, 4, 4)
        actions_layout.setSpacing(4)

        edit_btn = QPushButton("Edit")
        edit_btn.setObjectName("tableButton")
        edit_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        edit_btn.clicked.connect(lambda checked, a=data: self._show_edit_dialog(a))
        actions_layout.addWidget(edit_btn)

        delete_btn = QPushButton("Delete")
        delete_btn.setObjectName("tableDangerButton")
        delete_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        actions_layout.addWidget(delete_btn)

        self.table.setCellWidget(row, 5, actions_widget)
        self.table.setRowHeight(row, 56)
    
    def _on_account_updated(self, data: dict):
        """Handle account update."""
        # TODO: Hook up to backend endpoint
        # Find and update the row in the table
        for row in range(self.table.rowCount()):
            if self.table.item(row, 0).text() == data['username']:
                self.table.item(row, 1).setText(data['name'])
                self.table.item(row, 2).setText(data.get('email', ''))
                self.table.item(row, 3).setText(data['role_display'])
                
                status = "Active" if data['active'] else "Inactive"
                self.table.item(row, 4).setText(status)
                break
    
    def _filter_accounts(self, text: str):
        """Filter table by search text."""
        for row in range(self.table.rowCount()):
            username = self.table.item(row, 0).text().lower()
            name = self.table.item(row, 1).text().lower()
            
            match = text.lower() in username or text.lower() in name
            self.table.setRowHidden(row, not match if text else False)
    
    def load_accounts(self, accounts: list):
        """Load accounts from backend.
        
        Args:
            accounts: List of account dicts from API
        """
        # TODO: Hook up to backend endpoint
        self._populate_table(accounts)
