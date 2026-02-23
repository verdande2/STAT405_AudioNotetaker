"""
QSS Stylesheet for TranscribeNotes Application
Modern, clinical aesthetic with warm accents
"""


def load_stylesheet() -> str:
    """Load and return the application stylesheet."""
    return """
/* ============================================
   CSS VARIABLES (via properties)
   Color Palette: Deep navy, soft cream, warm coral accents
   ============================================ */

/* ============================================
   GLOBAL STYLES
   ============================================ */

* {
    font-family: "Segoe UI", "SF Pro Display", "Helvetica Neue", sans-serif;
    outline: none;
}

QMainWindow {
    background-color: #b9caf0;
}

QWidget {
    background-color: transparent;
    color: #e8e6e3;
    font-size: 14px;
}

QWidget#centralWidget {
    background-color: #0f1729;
}

/* ============================================
   SIDEBAR NAVIGATION
   ============================================ */

QWidget#sidebar {
    background-color: #0a0f1a;
    border-right: 1px solid #1e293b;
    min-width: 240px;
    max-width: 240px;
}

QWidget#sidebarHeader {
    background-color: transparent;
    padding: 20px;
    border-bottom: 1px solid #1e293b;
}

QLabel#appTitle {
    font-size: 22px;
    font-weight: 700;
    color: #f8fafc;
    letter-spacing: -0.5px;
}

QLabel#appSubtitle {
    font-size: 12px;
    color: #64748b;
    letter-spacing: 1px;
    text-transform: uppercase;
}

QPushButton#navButton {
    background-color: transparent;
    color: #94a3b8;
    border: none;
    border-radius: 8px;
    padding: 14px 16px;
    text-align: left;
    font-size: 14px;
    font-weight: 500;
    margin: 2px 12px;
}

QPushButton#navButton:hover {
    background-color: #1e293b;
    color: #e2e8f0;
}

QPushButton#navButton:checked {
    background-color: #1e3a5f;
    color: #38bdf8;
    border-left: 3px solid #38bdf8;
    border-radius: 0 8px 8px 0;
    margin-left: 0;
    padding-left: 25px;
}

QWidget#userSection {
    background-color: #0d1321;
    border-top: 1px solid #1e293b;
    padding: 16px;
}

QLabel#userName {
    font-size: 14px;
    font-weight: 600;
    color: #f1f5f9;
}

QLabel#userRole {
    font-size: 12px;
    color: #64748b;
}

/* ============================================
   MAIN CONTENT AREA
   ============================================ */

QWidget#contentArea {
    background-color: #0f1729;
    padding: 0;
}

QWidget#pageHeader {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
        stop:0 #0f1729, stop:1 #131d33);
    padding: 32px 40px;
    border-bottom: 1px solid #1e293b;
}

QLabel#pageTitle {
    font-size: 28px;
    font-weight: 700;
    color: #f8fafc;
    letter-spacing: -0.5px;
}

QLabel#pageDescription {
    font-size: 14px;
    color: #94a3b8;
    margin-top: 4px;
}

QWidget#pageContent {
    background-color: #0f1729;
    padding: 32px 40px;
}

/* ============================================
   CARDS AND PANELS
   ============================================ */

QFrame#card {
    background-color: #1a2332;
    border: 1px solid #2d3748;
    border-radius: 12px;
    padding: 24px;
}

QFrame#card:hover {
    border-color: #3b4a5a;
    background-color: #1e2738;
}

QFrame#statsCard {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
        stop:0 #1e3a5f, stop:1 #1a2332);
    border: 1px solid #2d4a6f;
    border-radius: 12px;
    padding: 20px;
}

QLabel#statsValue {
    font-size: 36px;
    font-weight: 700;
    color: #38bdf8;
}

QLabel#statsLabel {
    font-size: 13px;
    color: #94a3b8;
    text-transform: uppercase;
    letter-spacing: 0.5px;
}

QLabel#cardTitle {
    font-size: 16px;
    font-weight: 600;
    color: #f1f5f9;
    margin-bottom: 8px;
}

QLabel#cardSubtitle {
    font-size: 13px;
    color: #64748b;
}

/* ============================================
   BUTTONS
   ============================================ */

QPushButton#primaryButton {
    background-color: #2563eb;
    color: #ffffff;
    border: none;
    border-radius: 8px;
    padding: 8px 20px;
    font-size: 14px;
    font-weight: 600;
    min-height: 32px;
}

QPushButton#primaryButton:hover {
    background-color: #3b82f6;
}

QPushButton#primaryButton:pressed {
    background-color: #1d4ed8;
}

QPushButton#primaryButton:disabled {
    background-color: #1e3a5f;
    color: #64748b;
}

QPushButton#secondaryButton {
    background-color: transparent;
    color: #94a3b8;
    border: 1px solid #3b4a5a;
    border-radius: 8px;
    padding: 8px 20px;
    font-size: 14px;
    font-weight: 500;
    min-height: 32px;
}

QPushButton#secondaryButton:hover {
    background-color: #1e293b;
    color: #e2e8f0;
    border-color: #4b5563;
}

QPushButton#accentButton {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
        stop:0 #f97316, stop:1 #fb923c);
    color: #ffffff;
    border: none;
    border-radius: 8px;
    padding: 8px 20px;
    font-size: 14px;
    font-weight: 600;
    min-height: 32px;
}

QPushButton#accentButton:hover {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
        stop:0 #fb923c, stop:1 #fdba74);
}

QPushButton#dangerButton {
    background-color: #dc2626;
    color: #ffffff;
    border: none;
    border-radius: 8px;
    padding: 8px 20px;
    font-size: 14px;
    font-weight: 600;
    min-height: 32px;
}

QPushButton#dangerButton:hover {
    background-color: #ef4444;
}

QPushButton#tableButton {
    background-color: #1e3a5f;
    color: #e2e8f0;
    border: none;
    border-radius: 6px;
    padding: 6px 14px;
    font-size: 12px;
    font-weight: 600;
    min-height: 0px;
}

QPushButton#tableButton:hover {
    background-color: #2563eb;
    color: #ffffff;
}

QPushButton#tableDangerButton {
    background-color: #7f1d1d;
    color: #fca5a5;
    border: none;
    border-radius: 6px;
    padding: 6px 14px;
    font-size: 12px;
    font-weight: 600;
    min-height: 0px;
}

QPushButton#tableDangerButton:hover {
    background-color: #dc2626;
    color: #ffffff;
}

QPushButton#iconButton {
    background-color: transparent;
    border: none;
    border-radius: 6px;
    padding: 8px;
    min-width: 36px;
    min-height: 36px;
}

QPushButton#iconButton:hover {
    background-color: #1e293b;
}

/* ============================================
   FORM INPUTS
   ============================================ */

QLineEdit, QTextEdit, QPlainTextEdit {
    background-color: #1a2332;
    color: #e2e8f0;
    border: 1px solid #3b4a5a;
    border-radius: 8px;
    padding: 12px 16px;
    font-size: 14px;
    selection-background-color: #2563eb;
}

QLineEdit:focus, QTextEdit:focus, QPlainTextEdit:focus {
    border-color: #2563eb;
    background-color: #1e2738;
}

QLineEdit:disabled, QTextEdit:disabled {
    background-color: #0f1729;
    color: #64748b;
    border-color: #2d3748;
}

QLineEdit#searchInput {
    background-color: #1a2332;
    border: 1px solid #2d3748;
    border-radius: 24px;
    padding: 10px 20px 10px 44px;
    font-size: 14px;
}

QLineEdit#searchInput:focus {
    border-color: #3b82f6;
}

QLabel#inputLabel {
    font-size: 13px;
    font-weight: 600;
    color: #94a3b8;
    margin-bottom: 6px;
    text-transform: uppercase;
    letter-spacing: 0.5px;
}

QLabel#errorLabel {
    font-size: 12px;
    color: #f87171;
    margin-top: 4px;
}

/* ============================================
   COMBO BOX
   ============================================ */

QComboBox {
    background-color: #1a2332;
    color: #e2e8f0;
    border: 1px solid #3b4a5a;
    border-radius: 8px;
    padding: 12px 16px;
    font-size: 14px;
    min-height: 20px;
}

QComboBox:hover {
    border-color: #4b5563;
}

QComboBox:focus {
    border-color: #2563eb;
}

QComboBox::drop-down {
    subcontrol-origin: padding;
    subcontrol-position: center right;
    border: none;
    width: 32px;
    border-left: 1px solid #3b4a5a;
    margin-right: 4px;
}

QComboBox::down-arrow {
    image: none;
    width: 0;
    height: 0;
    border-left: 5px solid transparent;
    border-right: 5px solid transparent;
    border-top: 6px solid #94a3b8;
    margin-right: 4px;
}

QComboBox::down-arrow:hover {
    border-top-color: #e2e8f0;
}

QComboBox QAbstractItemView {
    background-color: #1a2332;
    border: 1px solid #3b4a5a;
    border-radius: 8px;
    padding: 4px;
    selection-background-color: #2563eb;
}

/* ============================================
   TABLES
   ============================================ */

QTableWidget, QTableView {
    background-color: #1a2332;
    alternate-background-color: #1e2738;
    border: 1px solid #2d3748;
    border-radius: 12px;
    gridline-color: #2d3748;
    selection-background-color: #1e3a5f;
}

QTableWidget::item, QTableView::item {
    padding: 12px 16px;
    border-bottom: 1px solid #2d3748;
}

QTableWidget::item:selected, QTableView::item:selected {
    background-color: #1e3a5f;
    color: #e2e8f0;
}

QHeaderView::section {
    background-color: #0f1729;
    color: #94a3b8;
    padding: 14px 16px;
    border: none;
    border-bottom: 2px solid #2d3748;
    font-weight: 600;
    font-size: 12px;
    text-transform: uppercase;
    letter-spacing: 0.5px;
}

QHeaderView::section:hover {
    background-color: #1a2332;
    color: #e2e8f0;
}

/* ============================================
   SCROLL BARS
   ============================================ */

QScrollBar:vertical {
    background-color: #0f1729;
    width: 10px;
    margin: 0;
    border-radius: 5px;
}

QScrollBar::handle:vertical {
    background-color: #3b4a5a;
    min-height: 30px;
    border-radius: 5px;
    margin: 2px;
}

QScrollBar::handle:vertical:hover {
    background-color: #4b5563;
}

QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
    height: 0;
    background: none;
}

QScrollBar:horizontal {
    background-color: #0f1729;
    height: 10px;
    margin: 0;
    border-radius: 5px;
}

QScrollBar::handle:horizontal {
    background-color: #3b4a5a;
    min-width: 30px;
    border-radius: 5px;
    margin: 2px;
}

QScrollBar::handle:horizontal:hover {
    background-color: #4b5563;
}

QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {
    width: 0;
    background: none;
}

/* ============================================
   TABS
   ============================================ */

QTabWidget::pane {
    background-color: #1a2332;
    border: 1px solid #2d3748;
    border-radius: 0 0 12px 12px;
    padding: 20px;
}

QTabBar::tab {
    background-color: #0f1729;
    color: #94a3b8;
    padding: 12px 24px;
    margin-right: 2px;
    border: 1px solid #2d3748;
    border-bottom: none;
    border-radius: 8px 8px 0 0;
    font-weight: 500;
}

QTabBar::tab:selected {
    background-color: #1a2332;
    color: #38bdf8;
    border-color: #2d3748;
    border-bottom: 2px solid #1a2332;
}

QTabBar::tab:hover:!selected {
    background-color: #1e293b;
    color: #e2e8f0;
}

/* ============================================
   PROGRESS BAR
   ============================================ */

QProgressBar {
    background-color: #1a2332;
    border: none;
    border-radius: 6px;
    height: 8px;
    text-align: center;
}

QProgressBar::chunk {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
        stop:0 #2563eb, stop:1 #38bdf8);
    border-radius: 6px;
}

/* ============================================
   DIALOGS
   ============================================ */

QDialog {
    background-color: #1a2332;
    border: 1px solid #2d3748;
    border-radius: 16px;
}

QDialog QLabel#dialogTitle {
    font-size: 20px;
    font-weight: 700;
    color: #f8fafc;
}

/* ============================================
   MESSAGE BOX
   ============================================ */

QMessageBox {
    background-color: #1a2332;
}

QMessageBox QLabel {
    color: #e2e8f0;
    font-size: 14px;
}

/* ============================================
   TOOLTIPS
   ============================================ */

QToolTip {
    background-color: #1e293b;
    color: #e2e8f0;
    border: 1px solid #3b4a5a;
    border-radius: 6px;
    padding: 8px 12px;
    font-size: 13px;
}

/* ============================================
   FILE UPLOAD ZONE
   ============================================ */

QFrame#uploadZone {
    background-color: #1a2332;
    border: 2px dashed #3b4a5a;
    border-radius: 16px;
    padding: 40px;
}

QFrame#uploadZone:hover {
    border-color: #2563eb;
    background-color: #1e2738;
}

QLabel#uploadIcon {
    font-size: 48px;
    color: #3b82f6;
}

QLabel#uploadText {
    font-size: 16px;
    color: #94a3b8;
    margin-top: 16px;
}

QLabel#uploadHint {
    font-size: 13px;
    color: #64748b;
}

/* ============================================
   STATUS INDICATORS
   ============================================ */

QLabel#statusPending {
    background-color: #854d0e;
    color: #fef3c7;
    padding: 4px 12px;
    border-radius: 12px;
    font-size: 12px;
    font-weight: 600;
}

QLabel#statusProcessing {
    background-color: #1e3a8a;
    color: #bfdbfe;
    padding: 4px 12px;
    border-radius: 12px;
    font-size: 12px;
    font-weight: 600;
}

QLabel#statusComplete {
    background-color: #166534;
    color: #bbf7d0;
    padding: 4px 12px;
    border-radius: 12px;
    font-size: 12px;
    font-weight: 600;
}

QLabel#statusError {
    background-color: #991b1b;
    color: #fecaca;
    padding: 4px 12px;
    border-radius: 12px;
    font-size: 12px;
    font-weight: 600;
}

/* ============================================
   SPLITTER
   ============================================ */

QSplitter::handle {
    background-color: #2d3748;
}

QSplitter::handle:horizontal {
    width: 1px;
}

QSplitter::handle:vertical {
    height: 1px;
}

/* ============================================
   LIST WIDGET
   ============================================ */

QListWidget {
    background-color: #1a2332;
    border: 1px solid #2d3748;
    border-radius: 12px;
    padding: 8px;
}

QListWidget::item {
    padding: 12px 16px;
    border-radius: 8px;
    margin: 2px 0;
}

QListWidget::item:selected {
    background-color: #1e3a5f;
    color: #e2e8f0;
}

QListWidget::item:hover:!selected {
    background-color: #1e293b;
}

/* ============================================
   GROUP BOX
   ============================================ */

QGroupBox {
    background-color: #1a2332;
    border: 1px solid #2d3748;
    border-radius: 12px;
    margin-top: 20px;
    padding: 20px;
    padding-top: 36px;
    font-weight: 600;
}

QGroupBox::title {
    subcontrol-origin: margin;
    subcontrol-position: top left;
    left: 16px;
    padding: 0 8px;
    color: #94a3b8;
    font-size: 13px;
    text-transform: uppercase;
    letter-spacing: 0.5px;
}

/* ============================================
   CHECKBOX & RADIO
   ============================================ */

QCheckBox, QRadioButton {
    color: #e2e8f0;
    spacing: 8px;
}

QCheckBox::indicator, QRadioButton::indicator {
    width: 20px;
    height: 20px;
    border: 2px solid #3b4a5a;
    border-radius: 4px;
    background-color: #1a2332;
}

QRadioButton::indicator {
    border-radius: 10px;
}

QCheckBox::indicator:checked, QRadioButton::indicator:checked {
    background-color: #2563eb;
    border-color: #2563eb;
}

QCheckBox::indicator:hover, QRadioButton::indicator:hover {
    border-color: #4b5563;
}

/* ============================================
   DATE EDIT
   ============================================ */

QDateEdit {
    background-color: #1a2332;
    color: #e2e8f0;
    border: 1px solid #3b4a5a;
    border-radius: 8px;
    padding: 8px 12px;
    font-size: 13px;
}

QDateEdit:focus {
    border-color: #2563eb;
}

QDateEdit::drop-down {
    border: none;
    width: 24px;
    border-left: 1px solid #3b4a5a;
}

QDateEdit::down-arrow {
    image: none;
    width: 0;
    height: 0;
    border-left: 4px solid transparent;
    border-right: 4px solid transparent;
    border-top: 5px solid #94a3b8;
}

/* ============================================
   CALENDAR WIDGET (QDateEdit popup)
   ============================================ */

/* Calendar is styled programmatically in _style_calendar() */

/* ============================================
   SPIN BOX
   ============================================ */

QSpinBox, QDoubleSpinBox {
    background-color: #1a2332;
    color: #e2e8f0;
    border: 1px solid #3b4a5a;
    border-radius: 8px;
    padding: 10px 12px;
    font-size: 14px;
}

QSpinBox:focus, QDoubleSpinBox:focus {
    border-color: #2563eb;
}

QSpinBox::up-button, QSpinBox::down-button,
QDoubleSpinBox::up-button, QDoubleSpinBox::down-button {
    background-color: #2d3748;
    border: none;
    width: 20px;
}

QSpinBox::up-button:hover, QSpinBox::down-button:hover,
QDoubleSpinBox::up-button:hover, QDoubleSpinBox::down-button:hover {
    background-color: #3b4a5a;
}

/* ============================================
   MENU
   ============================================ */

QMenu {
    background-color: #1a2332;
    border: 1px solid #2d3748;
    border-radius: 8px;
    padding: 8px;
}

QMenu::item {
    padding: 10px 24px;
    border-radius: 4px;
}

QMenu::item:selected {
    background-color: #1e3a5f;
}

QMenu::separator {
    height: 1px;
    background-color: #2d3748;
    margin: 8px 0;
}

/* ============================================
   STACKED WIDGET
   ============================================ */

QStackedWidget {
    background-color: transparent;
}
"""
