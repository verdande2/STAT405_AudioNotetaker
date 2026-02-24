"""
Accounts Page for TranscribeNotes Application
User account management and administration
"""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
    QPushButton, QFrame, QScrollArea, QLineEdit,
    QTableWidget, QTableWidgetItem, QHeaderView,
    QAbstractItemView, QDialog,
    QFormLayout, QCheckBox, QMessageBox
)
from PySide6.QtCore import Qt, Signal
from app.components.no_scroll_combo import NoScrollComboBox
from app.db import (
    Account,
    AccountExistsError,
    AuthenticationError,
    AuthorizationError,
    DatabaseInitializationError,
    InvalidDatabaseKeyError,
    MissingDatabaseKeyError,
    create_psychologist_account,
    delete_account,
    initialize_database,
    list_accounts,
    update_account,
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
        
        self.name_input = QLineEdit()
        self.name_input.setPlaceholderText("Full name")
        form.addRow("Full Name:", self.name_input)
        
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

    def __init__(self, account_data: dict, *, is_self: bool, parent=None):
        super().__init__(parent)
        self.account_data = account_data
        self.is_self = is_self
        self._password_change_enabled = False
        self.setWindowTitle("Edit Account")
        self.setMinimumWidth(520)
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(32, 32, 32, 32)
        layout.setSpacing(24)

        title = QLabel("Edit User Account")
        title.setObjectName("dialogTitle")
        layout.addWidget(title)

        form = QFormLayout()
        form.setSpacing(16)
        form.setLabelAlignment(Qt.AlignmentFlag.AlignRight)

        self.username_input = QLineEdit()
        self.username_input.setText(self.account_data.get('username', ''))
        form.addRow("Username:", self.username_input)

        self.name_input = QLineEdit()
        self.name_input.setText(self.account_data.get('name', ''))
        form.addRow("Full Name:", self.name_input)

        role_label = QLabel(self.account_data.get("role_display", "Unknown"))
        role_label.setObjectName("cardSubtitle")
        form.addRow("Role:", role_label)

        self.change_password_btn = QPushButton("Change Password")
        self.change_password_btn.setObjectName("secondaryButton")
        self.change_password_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.change_password_btn.clicked.connect(self._enable_password_change)
        form.addRow("", self.change_password_btn)

        self.password_fields_container = QWidget()
        password_fields_layout = QVBoxLayout(self.password_fields_container)
        password_fields_layout.setContentsMargins(0, 0, 0, 0)
        password_fields_layout.setSpacing(0)

        password_form = QFormLayout()
        password_form.setSpacing(16)
        password_form.setLabelAlignment(Qt.AlignmentFlag.AlignRight)
        password_fields_layout.addLayout(password_form)

        self.current_password_input = QLineEdit()
        self.current_password_input.setEchoMode(QLineEdit.EchoMode.Password)
        self.current_password_input.setPlaceholderText("Required only to change password")
        password_form.addRow("Current Password:", self.current_password_input)

        self.new_password_input = QLineEdit()
        self.new_password_input.setEchoMode(QLineEdit.EchoMode.Password)
        self.new_password_input.setPlaceholderText("Leave blank to keep current password")
        password_form.addRow("New Password:", self.new_password_input)

        self.confirm_password_input = QLineEdit()
        self.confirm_password_input.setEchoMode(QLineEdit.EchoMode.Password)
        self.confirm_password_input.setPlaceholderText("Confirm new password")
        password_form.addRow("Confirm New:", self.confirm_password_input)
        self.admin_password_input = QLineEdit()
        self.admin_password_input.setEchoMode(QLineEdit.EchoMode.Password)
        self.admin_password_input.setPlaceholderText(
            "Required to edit an account you are not logged into"
        )
        self.admin_password_label = QLabel("Admin Auth:")
        form.addRow(self.admin_password_label, self.admin_password_input)
        self.admin_password_label.setVisible(not self.is_self)
        self.admin_password_input.setVisible(not self.is_self)
 
        self.password_fields_container.setVisible(False)
        layout.addLayout(form)
        layout.addWidget(self.password_fields_container)

        helper = QLabel(
            "You can change username and display name. Use 'Change Password' to "
            "reveal password fields. Password changes require the current password "
            "of the account being edited."
        )
        helper.setObjectName("cardSubtitle")
        helper.setWordWrap(True)
        layout.addWidget(helper)

        if not self.is_self:
            admin_note = QLabel(
                "Admin authorization password is required to edit another local account."
            )
            admin_note.setObjectName("cardSubtitle")
            admin_note.setWordWrap(True)
            layout.addWidget(admin_note)

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

        save_btn = QPushButton("Save Changes")
        save_btn.setObjectName("primaryButton")
        save_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        save_btn.clicked.connect(self._save_changes)
        buttons_layout.addWidget(save_btn)

        layout.addLayout(buttons_layout)

    def _save_changes(self):
        """Save account changes."""
        new_password = self.new_password_input.text() if self._password_change_enabled else ""
        confirm_new = (
            self.confirm_password_input.text() if self._password_change_enabled else ""
        )
        current_password = (
            self.current_password_input.text() if self._password_change_enabled else ""
        )
        if new_password and len(new_password) < 8:
            self._show_error("New password must be at least 8 characters")
            return
        if new_password != confirm_new:
            self._show_error("New password fields do not match")
            return
        if not self.is_self and not self.admin_password_input.text():
            self._show_error("Admin authorization password is required")
            return

        data = {
            'id': self.account_data.get('id'),
            'username': self.username_input.text().strip(),
            'name': self.name_input.text().strip(),
            'current_password': current_password,
            'new_password': new_password,
            'admin_password': self.admin_password_input.text().strip(),
        }
        if not data["username"] or not data["name"]:
            self._show_error("Username and full name are required")
            return

        self.account_updated.emit(data)
        self.accept()

    def _enable_password_change(self):
        self._password_change_enabled = True
        self.password_fields_container.setVisible(True)
        self.change_password_btn.setVisible(False)
        self.current_password_input.setFocus()

    def _show_error(self, message: str):
        self.error_label.setText(message)
        self.error_label.setVisible(True)


class DeleteAccountDialog(QDialog):
    """Confirm account deletion with credential checks."""

    delete_confirmed = Signal(dict)

    def __init__(self, account_data: dict, *, is_self: bool, parent=None):
        super().__init__(parent)
        self.account_data = account_data
        self.is_self = is_self
        self.setWindowTitle("Delete Account")
        self.setMinimumWidth(520)
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(32, 32, 32, 32)
        layout.setSpacing(20)

        title = QLabel("Delete Account")
        title.setObjectName("dialogTitle")
        layout.addWidget(title)

        warning = QLabel(
            f"Delete account '{self.account_data.get('username', '')}'?\n\n"
            "This will permanently remove the account and delete all data associated "
            "with that account."
        )
        warning.setObjectName("cardSubtitle")
        warning.setWordWrap(True)
        layout.addWidget(warning)

        form = QFormLayout()
        form.setSpacing(16)
        form.setLabelAlignment(Qt.AlignmentFlag.AlignRight)

        self.username_input = QLineEdit()
        self.username_input.setPlaceholderText("Enter the account username to confirm")
        form.addRow("Username:", self.username_input)

        self.password_input = QLineEdit()
        self.password_input.setEchoMode(QLineEdit.EchoMode.Password)
        self.password_input.setPlaceholderText("Enter that account's password")
        form.addRow("Password:", self.password_input)

        self.admin_password_input = QLineEdit()
        self.admin_password_input.setEchoMode(QLineEdit.EchoMode.Password)
        self.admin_password_input.setPlaceholderText(
            "Required to delete an account you are not logged into"
        )
        self.admin_password_label = QLabel("Admin Auth:")
        form.addRow(self.admin_password_label, self.admin_password_input)
        self.admin_password_label.setVisible(not self.is_self)
        self.admin_password_input.setVisible(not self.is_self)

        layout.addLayout(form)

        self.error_label = QLabel("")
        self.error_label.setObjectName("errorLabel")
        self.error_label.setVisible(False)
        self.error_label.setWordWrap(True)
        layout.addWidget(self.error_label)

        buttons = QHBoxLayout()
        buttons.addStretch()

        cancel_btn = QPushButton("Cancel")
        cancel_btn.setObjectName("secondaryButton")
        cancel_btn.clicked.connect(self.reject)
        buttons.addWidget(cancel_btn)

        delete_btn = QPushButton("Delete Account")
        delete_btn.setObjectName("dangerButton")
        delete_btn.clicked.connect(self._confirm_delete)
        buttons.addWidget(delete_btn)

        layout.addLayout(buttons)

    def _confirm_delete(self):
        if not self.username_input.text().strip() or not self.password_input.text():
            self._show_error("Username and password are required")
            return
        if not self.is_self and not self.admin_password_input.text():
            self._show_error("Admin authorization password is required")
            return
        self.delete_confirmed.emit(
            {
                "id": self.account_data.get("id"),
                "username": self.username_input.text().strip(),
                "password": self.password_input.text(),
                "admin_password": self.admin_password_input.text().strip(),
            }
        )
        self.accept()

    def _show_error(self, message: str):
        self.error_label.setText(message)
        self.error_label.setVisible(True)


class AccountsPage(QWidget):
    """Account management page for administrators."""

    authenticated_account_updated = Signal(object)
    authenticated_account_deleted = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.current_account: Account | None = None
        self._all_accounts: list[dict] = []
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
        self.role_filter.setMinimumWidth(130)
        self.role_filter.currentIndexChanged.connect(
            lambda *_: self._filter_accounts(self.search_input.text())
        )
        filter_layout.addWidget(self.role_filter)
        
        status_label = QLabel("Status:")
        status_label.setObjectName("cardSubtitle")
        filter_layout.addWidget(status_label)
        
        self.status_filter = NoScrollComboBox()
        self.status_filter.addItem("All")
        self.status_filter.addItem("Active")
        self.status_filter.addItem("Inactive")
        self.status_filter.setMinimumWidth(100)
        self.status_filter.currentIndexChanged.connect(
            lambda *_: self._filter_accounts(self.search_input.text())
        )
        filter_layout.addWidget(self.status_filter)
        
        content_layout.addLayout(filter_layout)
        
        # Accounts table
        self.table = QTableWidget()
        self.table.setColumnCount(5)
        self.table.setHorizontalHeaderLabels([
            "Username", "Full Name", "Role", "Status", "Actions"
        ])
        
        # Table styling
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Fixed)
        self.table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.Fixed)
        self.table.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeMode.Fixed)
        self.table.horizontalHeader().setSectionResizeMode(4, QHeaderView.ResizeMode.Fixed)

        self.table.setColumnWidth(0, 130)
        self.table.setColumnWidth(2, 120)
        self.table.setColumnWidth(3, 90)
        self.table.setColumnWidth(4, 200)
        
        self.table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.table.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.table.setAlternatingRowColors(True)
        self.table.verticalHeader().setVisible(False)
        self.table.setShowGrid(False)
        
        self._populate_table([])
        
        content_layout.addWidget(self.table)
        
        # Info section
        info_frame = QFrame()
        info_frame.setObjectName("card")
        info_layout = QHBoxLayout(info_frame)
        info_layout.setContentsMargins(20, 16, 20, 16)
        
        info_text = QLabel(
            "You can edit your own account. Editing or deleting a different local "
            "account requires the in-person admin authorization password. All "
            "changes are logged for audit purposes."
        )
        info_text.setObjectName("cardSubtitle")
        info_text.setWordWrap(True)
        info_layout.addWidget(info_text)
        
        content_layout.addWidget(info_frame)
        
        layout.addWidget(content)
    
    def set_authenticated_account(self, account: Account | None):
        """Set the current signed-in account context used for guarded actions."""
        self.current_account = account

    def _role_display(self, role: str) -> str:
        if role == "admin":
            return "Administrator"
        if role == "psychologist":
            return "Psychologist"
        return role.title()

    def _account_to_dict(self, account: Account) -> dict:
        return {
            "id": account.id,
            "username": account.username,
            "name": account.display_name,
            "role": account.role,
            "role_display": self._role_display(account.role),
            "active": account.is_active,
        }

    def refresh_accounts(self):
        """Load real local accounts from the encrypted database."""
        if self.current_account is None:
            self._all_accounts = []
            self._populate_table([])
            return

        try:
            initialize_database()
            accounts = list_accounts()
        except (
            MissingDatabaseKeyError,
            InvalidDatabaseKeyError,
            DatabaseInitializationError,
        ) as exc:
            self._all_accounts = []
            self._populate_table([])
            self._show_action_error("Failed to load accounts", str(exc))
            return
        except Exception as exc:
            self._all_accounts = []
            self._populate_table([])
            self._show_action_error("Failed to load accounts", f"Unexpected error: {exc}")
            return

        self._all_accounts = [
            self._account_to_dict(account)
            for account in accounts
            if account.role != "admin"
        ]
        self._apply_filters()

    def _apply_filters(self):
        """Populate the table with the currently filtered account list."""
        search_text = self.search_input.text().strip().lower()
        role_filter = self.role_filter.currentText()
        status_filter = self.status_filter.currentText()

        filtered_accounts = []
        for account in self._all_accounts:
            if search_text and (
                search_text not in account["username"].lower()
                and search_text not in account["name"].lower()
            ):
                continue
            if role_filter == "Psychologist" and account["role"] != "psychologist":
                continue
            if status_filter == "Active" and not account["active"]:
                continue
            if status_filter == "Inactive" and account["active"]:
                continue
            filtered_accounts.append(account)

        self._populate_table(filtered_accounts)

    def _show_action_error(self, title: str, message: str):
        QMessageBox.critical(self, title, message)

    def _show_action_info(self, title: str, message: str):
        QMessageBox.information(self, title, message)
    
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
            
            # Role
            role_item = QTableWidgetItem(account['role_display'])
            role_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.table.setItem(row, 2, role_item)
            
            # Status
            status = "Active" if account['active'] else "Inactive"
            status_item = QTableWidgetItem(status)
            status_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.table.setItem(row, 3, status_item)
            
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
            delete_btn.clicked.connect(
                lambda checked, a=account: self._show_delete_dialog(a)
            )
            actions_layout.addWidget(delete_btn)

            self.table.setCellWidget(row, 4, actions_widget)
            self.table.setRowHeight(row, 56)

    def _show_create_dialog(self):
        """Show create account dialog."""
        dialog = CreateAccountDialog(self)
        dialog.account_created.connect(self._on_account_created)
        dialog.exec()

    def _show_edit_dialog(self, account: dict):
        """Show edit account dialog."""
        is_self = bool(self.current_account and self.current_account.id == account.get("id"))
        dialog = EditAccountDialog(account, is_self=is_self, parent=self)
        dialog.account_updated.connect(self._on_account_updated)
        dialog.exec()

    def _show_delete_dialog(self, account: dict):
        """Show delete-account confirmation/credential dialog."""
        is_self = bool(self.current_account and self.current_account.id == account.get("id"))
        dialog = DeleteAccountDialog(account, is_self=is_self, parent=self)
        dialog.delete_confirmed.connect(self._on_account_deleted)
        dialog.exec()

    def _on_account_created(self, data: dict):
        """Handle new account creation."""
        self.refresh_accounts()
        self._show_action_info(
            "Account Created",
            f"Account '{data['username']}' was created successfully.",
        )
    
    def _on_account_updated(self, data: dict):
        """Handle account update."""
        if self.current_account is None:
            self._show_action_error("Edit Account", "You must be signed in to edit accounts.")
            return

        try:
            initialize_database()
            updated = update_account(
                actor_account_id=self.current_account.id,
                target_account_id=int(data["id"]),
                new_username=data["username"],
                new_display_name=data["name"],
                current_password=data.get("current_password") or None,
                new_password=data.get("new_password") or None,
                admin_master_password=data.get("admin_password") or None,
            )
        except (ValueError, AccountExistsError, AuthenticationError, AuthorizationError) as exc:
            self._show_action_error("Edit Account", str(exc))
            return
        except (
            MissingDatabaseKeyError,
            InvalidDatabaseKeyError,
            DatabaseInitializationError,
        ) as exc:
            self._show_action_error("Edit Account", str(exc))
            return
        except Exception as exc:
            self._show_action_error("Edit Account", f"Unexpected error: {exc}")
            return

        if self.current_account and updated.id == self.current_account.id:
            self.current_account = updated
            self.authenticated_account_updated.emit(updated)

        self.refresh_accounts()
        self._show_action_info(
            "Account Updated",
            f"Account '{updated.username}' was updated successfully.",
        )

    def _on_account_deleted(self, data: dict):
        """Handle account deletion."""
        if self.current_account is None:
            self._show_action_error("Delete Account", "You must be signed in to delete accounts.")
            return

        target_account_id = int(data["id"])
        is_self_delete = target_account_id == self.current_account.id

        try:
            initialize_database()
            deleted = delete_account(
                actor_account_id=self.current_account.id,
                target_account_id=target_account_id,
                target_username=data["username"],
                target_password=data["password"],
                admin_master_password=data.get("admin_password") or None,
            )
        except (AuthenticationError, AuthorizationError) as exc:
            self._show_action_error("Delete Account", str(exc))
            return
        except (
            MissingDatabaseKeyError,
            InvalidDatabaseKeyError,
            DatabaseInitializationError,
        ) as exc:
            self._show_action_error("Delete Account", str(exc))
            return
        except Exception as exc:
            self._show_action_error("Delete Account", f"Unexpected error: {exc}")
            return

        self.refresh_accounts()

        if is_self_delete:
            self._show_action_info(
                "Account Deleted",
                "Your account was permanently deleted. You will now be signed out.",
            )
            self.authenticated_account_deleted.emit()
            return

        self._show_action_info(
            "Account Deleted",
            f"Account '{deleted.username}' was permanently deleted.",
        )
    
    def _filter_accounts(self, text: str):
        """Filter table by search text."""
        self._apply_filters()
    
    def load_accounts(self, accounts: list):
        """Load accounts from backend.
        
        Args:
            accounts: List of account dicts from API
        """
        self._all_accounts = list(accounts)
        self._apply_filters()
