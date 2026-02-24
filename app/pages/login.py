"""
Login Page for TranscribeNotes Application
"""

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QFrame,
    QLabel,
    QLineEdit,
    QPushButton,
    QScrollArea,
    QSizePolicy,
    QStackedWidget,
    QVBoxLayout,
    QWidget,
)

from app.db import (
    AccountExistsError,
    AuthenticationError,
    AuthorizationError,
    DatabaseInitializationError,
    InvalidDatabaseKeyError,
    MissingDatabaseKeyError,
    authenticate_account,
    create_psychologist_account,
    initialize_database,
    is_psychologist_authorized,
)


class LoginPage(QWidget):
    """Login and local sign-up page for user authentication."""

    login_successful = Signal(str, str)  # display_name, role

    def __init__(self, parent=None):
        super().__init__(parent)
        self._is_signup_mode = False
        self.current_account = None
        self._setup_ui()
        self._set_mode(False)

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        layout.addWidget(scroll)

        scroll_content = QWidget()
        scroll.setWidget(scroll_content)

        content_layout = QVBoxLayout(scroll_content)
        content_layout.setContentsMargins(24, 24, 24, 24)
        content_layout.setSpacing(0)
        content_layout.setAlignment(
            Qt.AlignmentFlag.AlignHCenter | Qt.AlignmentFlag.AlignTop
        )

        card = QFrame()
        card.setObjectName("card")
        card.setFixedWidth(420)
        card.setSizePolicy(
            QSizePolicy.Policy.Fixed,
            QSizePolicy.Policy.Maximum,
        )
        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(40, 48, 40, 40)
        card_layout.setSpacing(20)

        header_layout = QVBoxLayout()
        header_layout.setSpacing(8)

        title = QLabel("TranscribeNotes")
        title.setObjectName("pageTitle")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.subtitle_label = QLabel("")
        self.subtitle_label.setObjectName("cardSubtitle")
        self.subtitle_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.subtitle_label.setWordWrap(True)

        header_layout.addWidget(title)
        header_layout.addWidget(self.subtitle_label)
        card_layout.addLayout(header_layout)

        card_layout.addSpacing(8)

        self.form_stack = QStackedWidget()
        self.form_stack.setObjectName("authFormStack")
        self.form_stack.setSizePolicy(
            QSizePolicy.Policy.Preferred,
            QSizePolicy.Policy.Fixed,
        )
        self.login_form = self._build_login_form()
        self.signup_form = self._build_signup_form()
        self.form_stack.addWidget(self.login_form)
        self.form_stack.addWidget(self.signup_form)
        self.form_stack.currentChanged.connect(self._refresh_form_stack_height)
        card_layout.addWidget(self.form_stack)

        self.mode_note_label = QLabel("")
        self.mode_note_label.setObjectName("cardSubtitle")
        self.mode_note_label.setWordWrap(True)
        self.mode_note_label.setVisible(False)
        card_layout.addWidget(self.mode_note_label)

        self.error_label = QLabel("")
        self.error_label.setObjectName("errorLabel")
        self.error_label.setVisible(False)
        self.error_label.setWordWrap(True)
        card_layout.addWidget(self.error_label)

        self.info_label = QLabel("")
        self.info_label.setObjectName("cardSubtitle")
        self.info_label.setVisible(False)
        self.info_label.setWordWrap(True)
        self.info_label.setStyleSheet("color: #93c5fd;")
        card_layout.addWidget(self.info_label)

        self.primary_btn = QPushButton()
        self.primary_btn.setObjectName("primaryButton")
        self.primary_btn.setMinimumHeight(48)
        self.primary_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.primary_btn.clicked.connect(self._submit_primary)
        card_layout.addWidget(self.primary_btn)

        self.secondary_btn = QPushButton()
        self.secondary_btn.setObjectName("secondaryButton")
        self.secondary_btn.setMinimumHeight(44)
        self.secondary_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.secondary_btn.clicked.connect(self._toggle_mode)
        card_layout.addWidget(self.secondary_btn)

        footer = QLabel("Secure local authentication - No internet required")
        footer.setObjectName("cardSubtitle")
        footer.setAlignment(Qt.AlignmentFlag.AlignCenter)
        footer.setStyleSheet("font-size: 11px; margin-top: 8px;")
        card_layout.addWidget(footer)

        content_layout.addWidget(card)

        self.login_username_input.returnPressed.connect(self._submit_primary)
        self.login_password_input.returnPressed.connect(self._submit_primary)

        self.signup_name_input.returnPressed.connect(self._submit_primary)
        self.signup_username_input.returnPressed.connect(self._submit_primary)
        self.signup_password_input.returnPressed.connect(self._submit_primary)
        self.signup_confirm_input.returnPressed.connect(self._submit_primary)
        self.signup_admin_password_input.returnPressed.connect(self._submit_primary)

        self._refresh_form_stack_height()

    def _build_login_form(self) -> QWidget:
        container = QWidget()
        layout = QVBoxLayout(container)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(16)

        self.login_username_input = QLineEdit()
        self.login_username_input.setPlaceholderText("Enter your username")
        self.login_username_input.setMinimumHeight(48)
        self._add_labeled_field(layout, "Username", self.login_username_input)

        self.login_password_input = QLineEdit()
        self.login_password_input.setPlaceholderText("Enter your password")
        self.login_password_input.setEchoMode(QLineEdit.EchoMode.Password)
        self.login_password_input.setMinimumHeight(48)
        self._add_labeled_field(layout, "Password", self.login_password_input)

        return container

    def _build_signup_form(self) -> QWidget:
        container = QWidget()
        layout = QVBoxLayout(container)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(10)

        self.signup_name_input = QLineEdit()
        self.signup_name_input.setPlaceholderText("Dr. Jane Smith")
        self.signup_name_input.setMinimumHeight(44)
        self._add_labeled_field(layout, "Full Name", self.signup_name_input)

        self.signup_username_input = QLineEdit()
        self.signup_username_input.setPlaceholderText("Choose a username")
        self.signup_username_input.setMinimumHeight(44)
        self._add_labeled_field(layout, "Username", self.signup_username_input)

        self.signup_password_input = QLineEdit()
        self.signup_password_input.setPlaceholderText("Create a password")
        self.signup_password_input.setEchoMode(QLineEdit.EchoMode.Password)
        self.signup_password_input.setMinimumHeight(44)
        self._add_labeled_field(layout, "Password", self.signup_password_input)

        self.signup_confirm_input = QLineEdit()
        self.signup_confirm_input.setPlaceholderText("Confirm your password")
        self.signup_confirm_input.setEchoMode(QLineEdit.EchoMode.Password)
        self.signup_confirm_input.setMinimumHeight(44)
        self._add_labeled_field(layout, "Confirm Password", self.signup_confirm_input)

        self.signup_admin_password_input = QLineEdit()
        self.signup_admin_password_input.setPlaceholderText(
            "Entered in person by an administrator"
        )
        self.signup_admin_password_input.setEchoMode(QLineEdit.EchoMode.Password)
        self.signup_admin_password_input.setMinimumHeight(44)
        self._add_labeled_field(
            layout,
            "Admin Authorization Password",
            self.signup_admin_password_input,
        )

        return container

    def _add_labeled_field(
        self,
        parent_layout: QVBoxLayout,
        label_text: str,
        input_widget: QLineEdit,
    ):
        field = QWidget()
        field_layout = QVBoxLayout(field)
        field_layout.setContentsMargins(0, 0, 0, 0)
        field_layout.setSpacing(8)

        label = QLabel(label_text)
        label.setObjectName("inputLabel")
        field_layout.addWidget(label)
        field_layout.addWidget(input_widget)

        parent_layout.addWidget(field)

    def _set_mode(self, is_signup: bool):
        self._is_signup_mode = is_signup
        self.form_stack.setCurrentIndex(1 if is_signup else 0)
        self._refresh_form_stack_height()
        self._clear_messages()

        if is_signup:
            self.subtitle_label.setText(
                "Create a local psychologist account (admin authorization required)"
            )
            self.mode_note_label.setText(
                "A physical administrator must enter the local authorization "
                "password to create a psychologist account on this device."
            )
            self.mode_note_label.setVisible(True)
            self.primary_btn.setText("Create Account")
            self.secondary_btn.setText("Back to Sign In")
            self.signup_name_input.setFocus()
        else:
            self.subtitle_label.setText("Clinical Documentation System")
            self.mode_note_label.setVisible(False)
            self.primary_btn.setText("Sign In")
            self.secondary_btn.setText("Create Psychologist Account")
            self.login_username_input.setFocus()

    def _toggle_mode(self):
        self._set_mode(not self._is_signup_mode)

    def _refresh_form_stack_height(self, *_args):
        """Resize stacked form to fit the current page and avoid field overlap."""
        current = self.form_stack.currentWidget()
        if current is None:
            return
        current.adjustSize()
        current.layout().activate()
        target_height = current.sizeHint().height()
        if self.form_stack.currentIndex() == 1:
            # Sign-up form has more controls and should never collapse labels.
            target_height = max(target_height, 620)
        else:
            target_height = max(target_height, 170)
        self.form_stack.setFixedHeight(target_height)
        self.form_stack.updateGeometry()

    def _submit_primary(self):
        if self._is_signup_mode:
            self._handle_signup()
            return
        self._handle_login()

    def _handle_login(self):
        """Handle login attempt."""
        username = self.login_username_input.text().strip()
        password = self.login_password_input.text()

        if not username or not password:
            self._show_error("Please enter both username and password")
            return

        try:
            initialize_database()
            account = authenticate_account(username, password)

            if account.role == "psychologist" and not is_psychologist_authorized(
                account.id
            ):
                self.login_password_input.clear()
                self._show_error("This psychologist account is not authorized.")
                return
        except AuthenticationError as exc:
            self.login_password_input.clear()
            self._show_error(str(exc))
            return
        except MissingDatabaseKeyError:
            self.login_password_input.clear()
            self._show_error("No database key is available on this machine.")
            return
        except InvalidDatabaseKeyError:
            self.login_password_input.clear()
            self._show_error("The local database key could not unlock the database.")
            return
        except DatabaseInitializationError as exc:
            self.login_password_input.clear()
            self._show_error(f"Database setup failed: {exc}")
            return
        except Exception as exc:
            self.login_password_input.clear()
            self._show_error(f"Unexpected login error: {exc}")
            return

        role = "Administrator" if account.role == "admin" else "Psychologist"
        self.current_account = account
        self.login_password_input.clear()
        self._clear_messages()
        self.login_successful.emit(account.display_name, role)

    def _handle_signup(self):
        """Handle local psychologist account creation."""
        display_name = self.signup_name_input.text().strip()
        username = self.signup_username_input.text().strip()
        password = self.signup_password_input.text()
        confirm = self.signup_confirm_input.text()
        admin_password = self.signup_admin_password_input.text()

        if not display_name or not username or not password or not admin_password:
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
            create_psychologist_account(
                psychologist_username=username,
                psychologist_password=password,
                psychologist_display_name=display_name,
                admin_master_password=admin_password,
                authorization_note="Created from login screen",
            )
        except AccountExistsError as exc:
            self._show_error(str(exc))
            return
        except AuthenticationError:
            self.signup_admin_password_input.clear()
            self._show_error("Invalid admin authorization password")
            return
        except AuthorizationError as exc:
            self._show_error(str(exc))
            return
        except MissingDatabaseKeyError:
            self._show_error("No database key is available on this machine.")
            return
        except InvalidDatabaseKeyError:
            self._show_error("The local database key could not unlock the database.")
            return
        except DatabaseInitializationError as exc:
            self._show_error(f"Database setup failed: {exc}")
            return
        except Exception as exc:
            self._show_error(f"Unexpected account creation error: {exc}")
            return

        self.login_username_input.setText(username)
        self.login_password_input.clear()
        self.signup_password_input.clear()
        self.signup_confirm_input.clear()
        self.signup_admin_password_input.clear()

        self._set_mode(False)
        self._show_info("Account created. You can now sign in.")
        self.login_password_input.setFocus()

    def _clear_messages(self):
        self.error_label.clear()
        self.error_label.setVisible(False)
        self.info_label.clear()
        self.info_label.setVisible(False)

    def _show_error(self, message: str):
        """Display error message."""
        self.info_label.clear()
        self.info_label.setVisible(False)
        self.error_label.setText(message)
        self.error_label.setVisible(True)

    def _show_info(self, message: str):
        """Display informational success message."""
        self.error_label.clear()
        self.error_label.setVisible(False)
        self.info_label.setText(message)
        self.info_label.setVisible(True)
