"""Admin dashboard for the Voice-Based Attendance System."""
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QPushButton, QTabWidget,
    QMessageBox, QHBoxLayout, QGridLayout, QFrame, QDateEdit,
    QComboBox, QLineEdit, QTableWidget, QTableWidgetItem, QHeaderView,
    QSplitter, QFileDialog, QGraphicsDropShadowEffect, QApplication
)
from PyQt5.QtCore import Qt, QDate, QPropertyAnimation, QEasingCurve, QSize, QTimer
from PyQt5.QtGui import QFont, QIcon, QColor, QPixmap, QPainter, QPen, QBrush, QLinearGradient, QPalette

import sys
import os
from datetime import datetime, timedelta
import random

# Add the root directory to the path to ensure imports work correctly
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from modules.db_manager import (
    fetch_attendance_by_date, fetch_attendance_by_range, 
    fetch_attendance_by_student, calculate_attendance_percentage,
    export_to_excel, delete_student, mark_attendance
)
from modules.utils import CONFIG, logger, validate_date, validate_user_id

# Rajeev Institute of Technology Theme Colors
RIT_PRIMARY = "#1E3A8A"     # Deep blue for primary elements
RIT_SECONDARY = "#4F46E5"   # Bright blue for accent and highlights
RIT_ACCENT = "#7C3AED"      # Purple accent for special elements
RIT_LIGHT = "#F1F5F9"       # Light background
RIT_DARK = "#1E293B"        # Dark background
RIT_TEXT_LIGHT = "#F8FAFC"  # Light text
RIT_TEXT_DARK = "#334155"   # Dark text
RIT_SUCCESS = "#10B981"     # Green for success
RIT_WARNING = "#F59E0B"     # Orange for warnings
RIT_ERROR = "#EF4444"       # Red for errors
RIT_BG = "#0F172A"          # Main background
RIT_CARD_BG = "#1E293B"     # Card background

class AnimatedButton(QPushButton):
    """Custom button with hover and click animations."""
    def __init__(self, *args, **kwargs):
        color = kwargs.pop('color', RIT_SECONDARY)
        self.hover_color = kwargs.pop('hover_color', RIT_ACCENT)
        self.press_color = kwargs.pop('press_color', RIT_PRIMARY)
        super(AnimatedButton, self).__init__(*args, **kwargs)
        
        self.setStyleSheet(f"""
            QPushButton {{
                background-color: {color};
                color: {RIT_TEXT_LIGHT};
                border: none;
                border-radius: 6px;
                padding: 12px;
                font-weight: bold;
                font-size: 14px;
            }}
            QPushButton:hover {{
                background-color: {self.hover_color};
            }}
            QPushButton:pressed {{
                background-color: {self.press_color};
            }}
            QPushButton:disabled {{
                background-color: {RIT_DARK};
                color: #64748B;
            }}
        """)
        
        # Add shadow effect
        self.shadow = QGraphicsDropShadowEffect()
        self.shadow.setBlurRadius(15)
        self.shadow.setColor(QColor(0, 0, 0, 80))
        self.shadow.setOffset(3, 3)
        self.setGraphicsEffect(self.shadow)
        
    def enterEvent(self, event):
        # Animation for hover
        self.shadow.setBlurRadius(25)
        self.shadow.setOffset(5, 5)
        super().enterEvent(event)
        
    def leaveEvent(self, event):
        # Animation for leave
        self.shadow.setBlurRadius(15)
        self.shadow.setOffset(3, 3)
        super().leaveEvent(event)

class CardFrame(QFrame):
    """Custom frame with card-like appearance."""
    def __init__(self, *args, **kwargs):
        super(CardFrame, self).__init__(*args, **kwargs)
        
        self.setStyleSheet(f"""
            CardFrame {{
                background-color: {RIT_CARD_BG};
                border-radius: 10px;
                padding: 15px;
            }}
        """)
        
        # Add shadow effect
        self.shadow = QGraphicsDropShadowEffect()
        self.shadow.setBlurRadius(20)
        self.shadow.setColor(QColor(0, 0, 0, 60))
        self.shadow.setOffset(4, 4)
        self.setGraphicsEffect(self.shadow)

class AdminDashboard(QWidget):
    def __init__(self, username, stack=None):
        super().__init__()
        self.username = username
        self.stack = stack

        # Add data cleanup timer
        self.cleanup_timer = QTimer(self)
        self.cleanup_timer.timeout.connect(self.run_scheduled_cleanup)
        self.cleanup_timer.start(3600000)  # Run every hour
        
        self.init_ui()
        
        # Run initial cleanup
        QTimer.singleShot(5000, self.run_scheduled_cleanup)
        
    def init_ui(self):
        # Set global font and window properties
        self.setFont(QFont("Segoe UI", 10))
        self.setWindowTitle("RIT Voice Attendance System - Admin Dashboard")
        self.resize(1200, 800)  # Set a larger default size
        
        # Apply styling
        self.setStyleSheet(f"""
            QWidget {{
                background-color: {RIT_BG};
                color: {RIT_TEXT_LIGHT};
                font-family: 'Segoe UI';
            }}
            QTabWidget::pane {{
                background-color: {RIT_CARD_BG};
                border: none;
                border-radius: 12px;
            }}
            QTabBar::tab {{
                background-color: {RIT_DARK};
                color: {RIT_TEXT_LIGHT};
                padding: 12px 20px;
                border-top-left-radius: 8px;
                border-top-right-radius: 8px;
                margin-right: 3px;
                font-weight: bold;
            }}
            QTabBar::tab:selected {{
                background-color: {RIT_SECONDARY};
                color: white;
            }}
            QLabel {{
                font-size: 14px;
            }}
            QTableWidget {{
                background-color: {RIT_CARD_BG};
                alternate-background-color: {RIT_DARK};
                border: none;
                border-radius: 8px;
                gridline-color: #475569;
                color: {RIT_TEXT_LIGHT};
                padding: 5px;
            }}
            QTableWidget::item:selected {{
                background-color: {RIT_SECONDARY};
            }}
            QHeaderView::section {{
                background-color: {RIT_PRIMARY};
                padding: 8px;
                border: none;
                font-weight: bold;
                color: {RIT_TEXT_LIGHT};
            }}
            QLineEdit, QDateEdit, QComboBox {{
                padding: 10px;
                background-color: {RIT_DARK};
                border: 2px solid {RIT_SECONDARY};
                border-radius: 6px;
                color: {RIT_TEXT_LIGHT};
                selection-background-color: {RIT_SECONDARY};
            }}
            QLineEdit:focus, QDateEdit:focus, QComboBox:focus {{
                border: 2px solid {RIT_ACCENT};
            }}
            QComboBox QAbstractItemView {{
                background-color: {RIT_DARK};
                selection-background-color: {RIT_SECONDARY};
                color: {RIT_TEXT_LIGHT};
                border-radius: 6px;
            }}
            QScrollBar:vertical {{
                background-color: {RIT_DARK};
                width: 14px;
                margin: 15px 0 15px 0;
                border-radius: 7px;
            }}
            QScrollBar::handle:vertical {{
                background-color: {RIT_SECONDARY};
                min-height: 30px;
                border-radius: 7px;
            }}
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
                border: none;
                background: none;
            }}
            QMessageBox {{
                background-color: {RIT_CARD_BG};
                color: {RIT_TEXT_LIGHT};
            }}
        """)
        
        # Main layout
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(20)
        
        # Header
        header_frame = CardFrame()
        header_layout = QHBoxLayout(header_frame)
        header_layout.setContentsMargins(15, 15, 15, 15)
        
        logo_label = QLabel()
        logo_size = 60
        logo_path = os.path.join(os.path.dirname(__file__), '..', 'assets', 'rit_logo.png')  # Adjust path as needed

        if os.path.exists(logo_path):
            logo_pixmap = QPixmap(logo_path).scaled(logo_size, logo_size, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            logo_label.setPixmap(logo_pixmap)
        else:
            # Fallback to the programmatically generated logo if file doesn't exist
            logo_pixmap = QPixmap(logo_size, logo_size)
            logo_pixmap.fill(Qt.transparent)
            
            # Draw a stylized "RIT" logo (existing code)
            painter = QPainter(logo_pixmap)
            painter.setRenderHint(QPainter.Antialiasing)
            
            # Create gradient for logo
            gradient = QLinearGradient(0, 0, logo_size, logo_size)
            gradient.setColorAt(0, QColor(RIT_PRIMARY))
            gradient.setColorAt(1, QColor(RIT_ACCENT))
            
            # Draw circle with gradient
            painter.setBrush(QBrush(gradient))
            painter.setPen(QPen(Qt.NoPen))
            painter.drawEllipse(0, 0, logo_size, logo_size)
            
            # Draw "RIT" text
            painter.setPen(QPen(QColor(RIT_TEXT_LIGHT)))
            painter.setFont(QFont("Arial", 22, QFont.Bold))
            painter.drawText(logo_pixmap.rect(), Qt.AlignCenter, "RIT")
            painter.end()

        logo_label.setFixedSize(logo_size, logo_size)
        
        # Title with gradient
        title_label = QLabel("Rajeev Institute of Technology")
        title_label.setFont(QFont("Segoe UI", 22, QFont.Bold))
        title_label.setStyleSheet(f"""
            background: -webkit-linear-gradient({RIT_SECONDARY}, {RIT_ACCENT});
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
        """)
        
        subtitle_label = QLabel("Voice Based Attendance System")
        subtitle_label.setFont(QFont("Segoe UI", 16))
        subtitle_label.setStyleSheet(f"color: {RIT_TEXT_LIGHT};")
        
        title_layout = QVBoxLayout()
        title_layout.addWidget(title_label)
        title_layout.addWidget(subtitle_label)
        
        welcome_label = QLabel(f"Welcome, {self.username}!")
        welcome_label.setFont(QFont("Segoe UI", 14))
        welcome_label.setStyleSheet(f"color: {RIT_ACCENT};")
        
        self.logout_button = AnimatedButton("Logout", color=RIT_ERROR)
        self.logout_button.setFixedWidth(120)
        self.logout_button.clicked.connect(self.logout)
        
        header_layout.addWidget(logo_label)
        header_layout.addSpacing(15)
        header_layout.addLayout(title_layout)
        header_layout.addStretch()
        header_layout.addWidget(welcome_label)
        header_layout.addWidget(self.logout_button)
        
        # Tab widget for different admin functions
        self.tabs = QTabWidget()
        self.tabs.setStyleSheet(f"""
            QTabWidget::tab-bar {{
                alignment: center;
            }}
        """)
        
        # Create various tabs
        self.attendance_tab = self.create_attendance_tab()
        self.student_tab = self.create_student_management_tab()
        self.reports_tab = self.create_reports_tab()
        self.manual_tab = self.create_manual_attendance_tab()
        
        # Add tabs to tab widget
        self.tabs.addTab(self.attendance_tab, "Attendance Records")
        self.tabs.addTab(self.student_tab, "Student Management")
        self.tabs.addTab(self.reports_tab, "Reports & Analysis")
        self.tabs.addTab(self.manual_tab, "Manual Attendance")
        
        # Set tab icons
        self.tabs.setTabIcon(0, self.create_icon("calendar"))
        self.tabs.setTabIcon(1, self.create_icon("users"))
        self.tabs.setTabIcon(2, self.create_icon("chart"))
        self.tabs.setTabIcon(3, self.create_icon("edit"))
        
        # Add components to main layout
        main_layout.addWidget(header_frame)
        main_layout.addWidget(self.tabs)
        
        # Status bar
        status_bar = QLabel("RIT Voice Attendance System v1.0 | Last Updated: April 2025")
        status_bar.setAlignment(Qt.AlignRight)
        status_bar.setStyleSheet(f"color: #64748B; font-size: 12px;")
        main_layout.addWidget(status_bar)
        
        self.setLayout(main_layout)
        
    def create_icon(self, icon_type):
        """Creates simple icons for tabs."""
        pixmap = QPixmap(24, 24)
        pixmap.fill(Qt.transparent)
        
        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.Antialiasing)
        painter.setPen(QPen(QColor(RIT_TEXT_LIGHT), 2))
        
        if icon_type == "calendar":
            # Draw calendar icon
            painter.drawRect(4, 4, 16, 16)
            painter.drawLine(8, 4, 8, 8)
            painter.drawLine(16, 4, 16, 8)
            painter.drawLine(4, 10, 20, 10)
        elif icon_type == "users":
            # Draw users icon
            painter.drawEllipse(8, 6, 8, 8)
            painter.drawArc(5, 14, 14, 8, 0, 180 * 16)
        elif icon_type == "chart":
            # Draw chart icon
            painter.drawLine(4, 20, 4, 4)
            painter.drawLine(4, 20, 20, 20)
            painter.drawLine(8, 16, 8, 10)
            painter.drawLine(12, 16, 12, 6)
            painter.drawLine(16, 16, 16, 12)
        elif icon_type == "edit":
            # Draw edit icon
            painter.drawLine(4, 20, 20, 20)
            painter.drawLine(8, 16, 8, 10)
            painter.drawLine(12, 16, 12, 6)
            painter.drawLine(16, 16, 16, 12)
            painter.drawRect(4, 4, 16, 16)
        
        painter.end()
        return QIcon(pixmap)
        
    def create_attendance_tab(self):
        """Creates the attendance records viewing tab."""
        tab = QWidget()
        layout = QVBoxLayout()
        layout.setContentsMargins(15, 15, 15, 15)
        layout.setSpacing(15)
        
        # Title
        title_label = QLabel("Attendance Records")
        title_label.setFont(QFont("Segoe UI", 16, QFont.Bold))
        title_label.setStyleSheet(f"color: {RIT_SECONDARY};")
        title_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(title_label)
        
        # Filter section
        filter_frame = CardFrame()
        filter_layout = QGridLayout(filter_frame)
        filter_layout.setContentsMargins(15, 15, 15, 15)
        filter_layout.setSpacing(15)
        
        # Section subtitle
        filter_subtitle = QLabel("Filter Options")
        filter_subtitle.setFont(QFont("Segoe UI", 12, QFont.Bold))
        filter_subtitle.setStyleSheet(f"color: {RIT_ACCENT};")
        filter_layout.addWidget(filter_subtitle, 0, 0, 1, 4)
        
        # Date filter
        date_label = QLabel("Date:")
        date_label.setFont(QFont("Segoe UI", 10, QFont.Bold))
        self.date_picker = QDateEdit()
        self.date_picker.setDate(QDate.currentDate())
        self.date_picker.setCalendarPopup(True)
        
        # Date range filter
        range_label = QLabel("Date Range:")
        range_label.setFont(QFont("Segoe UI", 10, QFont.Bold))
        self.start_date = QDateEdit()
        self.start_date.setDate(QDate.currentDate().addDays(-7))
        self.start_date.setCalendarPopup(True)
        
        self.end_date = QDateEdit()
        self.end_date.setDate(QDate.currentDate())
        self.end_date.setCalendarPopup(True)
        
        # Student filter
        student_label = QLabel("Student ID:")
        student_label.setFont(QFont("Segoe UI", 10, QFont.Bold))
        self.student_id_input = QLineEdit()
        self.student_id_input.setPlaceholderText("Enter Student ID")
        
        # Buttons
        self.view_by_date_btn = AnimatedButton("View by Date")
        self.view_by_date_btn.clicked.connect(self.view_attendance_by_date)
        
        self.view_by_range_btn = AnimatedButton("View by Range")
        self.view_by_range_btn.clicked.connect(self.view_attendance_by_range)
        
        self.view_by_student_btn = AnimatedButton("View by Student")
        self.view_by_student_btn.clicked.connect(self.view_attendance_by_student)
        
        self.export_btn = AnimatedButton("Export to Excel", color=RIT_SUCCESS)
        self.export_btn.clicked.connect(self.export_attendance)
        
        # Add widgets to filter layout
        filter_layout.addWidget(date_label, 1, 0)
        filter_layout.addWidget(self.date_picker, 1, 1)
        filter_layout.addWidget(self.view_by_date_btn, 1, 2)
        
        filter_layout.addWidget(range_label, 2, 0)
        filter_layout.addWidget(self.start_date, 2, 1)
        filter_layout.addWidget(self.end_date, 2, 2)
        filter_layout.addWidget(self.view_by_range_btn, 2, 3)
        
        filter_layout.addWidget(student_label, 3, 0)
        filter_layout.addWidget(self.student_id_input, 3, 1)
        filter_layout.addWidget(self.view_by_student_btn, 3, 2)
        filter_layout.addWidget(self.export_btn, 3, 3)
        
        # Table for attendance records
        table_frame = CardFrame()
        table_layout = QVBoxLayout(table_frame)
        table_layout.setContentsMargins(15, 15, 15, 15)
        
        self.attendance_table = QTableWidget(0, 5)
        self.attendance_table.setHorizontalHeaderLabels(["ID", "Student ID", "Name", "Status", "Timestamp"])
        self.attendance_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.attendance_table.setAlternatingRowColors(True)
        self.attendance_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.attendance_table.setEditTriggers(QTableWidget.NoEditTriggers)
        
        # Records count label
        self.records_label = QLabel("No records to display")
        self.records_label.setAlignment(Qt.AlignCenter)
        self.records_label.setStyleSheet(f"color: {RIT_SECONDARY}; font-size: 14px; font-weight: bold;")
        
        table_layout.addWidget(self.attendance_table)
        table_layout.addWidget(self.records_label)
        
        # Add to main layout
        layout.addWidget(filter_frame)
        layout.addWidget(table_frame)
        
        tab.setLayout(layout)
        return tab
    
    def create_student_management_tab(self):
        """Creates the student management tab."""
        tab = QWidget()
        layout = QVBoxLayout()
        layout.setContentsMargins(15, 15, 15, 15)
        layout.setSpacing(15)
        
        # Title
        title_label = QLabel("Student Management")
        title_label.setFont(QFont("Segoe UI", 16, QFont.Bold))
        title_label.setStyleSheet(f"color: {RIT_SECONDARY};")
        title_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(title_label)
        
        # Student management controls
        actions_frame = CardFrame()
        actions_layout = QVBoxLayout(actions_frame)
        actions_layout.setContentsMargins(20, 20, 20, 20)
        actions_layout.setSpacing(20)
        
        # Register student section
        register_section = QVBoxLayout()
        
        register_title = QLabel("Register New Student")
        register_title.setFont(QFont("Segoe UI", 14, QFont.Bold))
        register_title.setStyleSheet(f"color: {RIT_ACCENT};")
        
        register_desc = QLabel("Add a new student to the system with voice recognition")
        register_desc.setWordWrap(True)
        
        self.register_student_btn = AnimatedButton("Register New Student", color=RIT_SUCCESS)
        self.register_student_btn.setIcon(self.create_icon("users"))
        self.register_student_btn.setIconSize(QSize(20, 20))
        self.register_student_btn.clicked.connect(self.go_to_register_page)
        
        register_section.addWidget(register_title)
        register_section.addWidget(register_desc)
        register_section.addWidget(self.register_student_btn)
        
        # Horizontal line
        divider = QFrame()
        divider.setFrameShape(QFrame.HLine)
        divider.setStyleSheet(f"background-color: #475569;")
        
        # Delete student section
        delete_section = QVBoxLayout()
        
        delete_title = QLabel("Delete Student")
        delete_title.setFont(QFont("Segoe UI", 14, QFont.Bold))
        delete_title.setStyleSheet(f"color: {RIT_ERROR};")
        
        delete_warning = QLabel("Warning: This will permanently remove all student data, including attendance records and voice samples")
        delete_warning.setWordWrap(True)
        delete_warning.setStyleSheet(f"color: {RIT_WARNING};")
        
        delete_input_layout = QHBoxLayout()
        
        self.delete_id_input = QLineEdit()
        self.delete_id_input.setPlaceholderText("Enter Student ID to delete")
        
        self.delete_student_btn = AnimatedButton("Delete Student", color=RIT_ERROR)
        self.delete_student_btn.clicked.connect(self.confirm_delete_student)
        
        delete_input_layout.addWidget(self.delete_id_input)
        delete_input_layout.addWidget(self.delete_student_btn)
        
        delete_section.addWidget(delete_title)
        delete_section.addWidget(delete_warning)
        delete_section.addLayout(delete_input_layout)
        
        # Add all sections to the actions layout
        actions_layout.addLayout(register_section)
        actions_layout.addWidget(divider)
        actions_layout.addLayout(delete_section)
        
        # Add to main layout
        layout.addWidget(actions_frame)
        layout.addStretch()
        
        tab.setLayout(layout)
        return tab
    
    def create_reports_tab(self):
        """Creates the reports and analytics tab."""
        tab = QWidget()
        layout = QVBoxLayout()
        layout.setContentsMargins(15, 15, 15, 15)
        layout.setSpacing(15)
        
        # Title
        title_label = QLabel("Reports & Analysis")
        title_label.setFont(QFont("Segoe UI", 16, QFont.Bold))
        title_label.setStyleSheet(f"color: {RIT_SECONDARY};")
        title_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(title_label)
        
        # Reports section
        reports_frame = CardFrame()
        reports_layout = QVBoxLayout(reports_frame)
        reports_layout.setContentsMargins(20, 20, 20, 20)
        reports_layout.setSpacing(15)
        
        # Section title
        reports_title = QLabel("Generate Attendance Reports")
        reports_title.setFont(QFont("Segoe UI", 14, QFont.Bold))
        reports_title.setStyleSheet(f"color: {RIT_ACCENT};")
        reports_layout.addWidget(reports_title)
        
        # Date range for reports
        date_grid = QGridLayout()
        
        reports_range_label = QLabel("Report Date Range:")
        reports_range_label.setFont(QFont("Segoe UI", 10, QFont.Bold))
        
        self.report_start_date = QDateEdit()
        self.report_start_date.setDate(QDate.currentDate().addDays(-30))
        self.report_start_date.setCalendarPopup(True)
        
        date_to_label = QLabel("to")
        date_to_label.setAlignment(Qt.AlignCenter)
        
        self.report_end_date = QDateEdit()
        self.report_end_date.setDate(QDate.currentDate())
        self.report_end_date.setCalendarPopup(True)
        
        date_grid.addWidget(reports_range_label, 0, 0)
        date_grid.addWidget(self.report_start_date, 0, 1)
        date_grid.addWidget(date_to_label, 0, 2)
        date_grid.addWidget(self.report_end_date, 0, 3)
        
        # Optional student filter
        filter_layout = QHBoxLayout()
        
        report_student_label = QLabel("Student ID (optional):")
        report_student_label.setFont(QFont("Segoe UI", 10, QFont.Bold))
        
        self.report_student_id = QLineEdit()
        self.report_student_id.setPlaceholderText("Leave blank for all students")
        
        filter_layout.addWidget(report_student_label)
        filter_layout.addWidget(self.report_student_id)
        
        # Buttons
        button_layout = QHBoxLayout()
        
        self.generate_report_btn = AnimatedButton("Generate Attendance Report")
        self.generate_report_btn.clicked.connect(self.generate_attendance_report)
        
        self.export_report_btn = AnimatedButton("Export Report", color=RIT_SUCCESS)
        self.export_report_btn.clicked.connect(self.export_report)
        
        button_layout.addWidget(self.generate_report_btn)
        button_layout.addWidget(self.export_report_btn)
        
        # Add all layouts to reports layout
        reports_layout.addLayout(date_grid)
        reports_layout.addLayout(filter_layout)
        reports_layout.addLayout(button_layout)
        
        # Table for report data
        table_frame = CardFrame()
        table_layout = QVBoxLayout(table_frame)
        table_layout.setContentsMargins(15, 15, 15, 15)
        
        table_title = QLabel("Attendance Percentage Report")
        table_title.setFont(QFont("Segoe UI", 14, QFont.Bold))
        table_title.setStyleSheet(f"color: {RIT_ACCENT};")
        table_title.setAlignment(Qt.AlignCenter)
        
        self.report_table = QTableWidget(0, 3)
        self.report_table.setHorizontalHeaderLabels(["Student ID", "Name", "Attendance Percentage"])
        self.report_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.report_table.setAlternatingRowColors(True)
        self.report_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.report_table.setEditTriggers(QTableWidget.NoEditTriggers)
        
        table_layout.addWidget(table_title)
        table_layout.addWidget(self.report_table)
        
        # Add Data Management Section
        data_frame = CardFrame()
        data_layout = QVBoxLayout(data_frame)
        data_layout.setContentsMargins(20, 20, 20, 20)
        data_layout.setSpacing(15)

        data_title = QLabel("Data Management")
        data_title.setFont(QFont("Segoe UI", 14, QFont.Bold))
        data_title.setStyleSheet(f"color: {RIT_WARNING};")

        # Info text
        info_text = QLabel(
            f"• Temporary voice samples are kept for {CONFIG['temp_samples_retention_days']} day(s)\n"
            f"• Attendance records are archived after {CONFIG['attendance_records_retention_months']} months\n"
            "• Archived records can still be accessed but are stored separately"
        )
        info_text.setWordWrap(True)

        # Cleanup buttons
        cleanup_layout = QHBoxLayout()
        
        self.cleanup_temp_btn = AnimatedButton("Clean Temp Files", color=RIT_WARNING)
        self.cleanup_temp_btn.clicked.connect(self.manual_cleanup_temp)
        
        self.archive_records_btn = AnimatedButton("Archive Old Records", color=RIT_WARNING)
        self.archive_records_btn.clicked.connect(self.manual_archive_records)

        cleanup_layout.addWidget(self.cleanup_temp_btn)
        cleanup_layout.addWidget(self.archive_records_btn)

        # Add widgets to layout
        data_layout.addWidget(data_title)
        data_layout.addWidget(info_text)
        data_layout.addLayout(cleanup_layout)

        # Add to main layout
        layout.addWidget(reports_frame)
        layout.addWidget(table_frame)
        layout.addWidget(data_frame)
        layout.addStretch()

        tab.setLayout(layout)
        return tab

    def run_scheduled_cleanup(self):
        """Run automated cleanup tasks."""
        from modules.data_cleanup import cleanup_temp_samples, archive_old_attendance_records
        
        try:
            cleanup_temp_samples(CONFIG['temp_samples_retention_days'])
            archive_old_attendance_records(CONFIG['attendance_records_retention_months'])
        except Exception as e:
            logger.error(f"Scheduled cleanup failed: {str(e)}")

    def manual_cleanup_temp(self):
        """Manually trigger temporary files cleanup."""
        from modules.data_cleanup import cleanup_temp_samples
        
        try:
            self.cleanup_temp_btn.setText("Cleaning...")
            self.cleanup_temp_btn.setEnabled(False)
            QApplication.processEvents()
            
            cleanup_temp_samples(CONFIG['temp_samples_retention_days'])
            self.show_message("Temporary files cleaned successfully.", "Cleanup Complete")
            
        except Exception as e:
            self.show_message(f"Cleanup failed: {str(e)}", "Error", QMessageBox.Critical)
        finally:
            self.cleanup_temp_btn.setText("Clean Temp Files")
            self.cleanup_temp_btn.setEnabled(True)

    def manual_archive_records(self):
        """Manually trigger attendance records archiving."""
        from modules.data_cleanup import archive_old_attendance_records
        
        try:
            self.archive_records_btn.setText("Archiving...")
            self.archive_records_btn.setEnabled(False)
            QApplication.processEvents()
            
            archive_old_attendance_records(CONFIG['attendance_records_retention_months'])
            self.show_message("Old records archived successfully.", "Archive Complete")
            
        except Exception as e:
            self.show_message(f"Archiving failed: {str(e)}", "Error", QMessageBox.Critical)
        finally:
            self.archive_records_btn.setText("Archive Old Records")
            self.archive_records_btn.setEnabled(True)

    def create_manual_attendance_tab(self):
        """Creates the manual attendance marking tab."""
        tab = QWidget()
        layout = QVBoxLayout()
        layout.setContentsMargins(15, 15, 15, 15)
        layout.setSpacing(15)
        
        # Title
        title_label = QLabel("Manual Attendance")
        title_label.setFont(QFont("Segoe UI", 16, QFont.Bold))
        title_label.setStyleSheet(f"color: {RIT_SECONDARY};")
        title_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(title_label)
        
        # Manual attendance section
        manual_frame = CardFrame()
        manual_layout = QVBoxLayout(manual_frame)
        manual_layout.setContentsMargins(20, 20, 20, 20)
        manual_layout.setSpacing(15)
        
        # Section title
        manual_title = QLabel("Mark Attendance Manually")
        manual_title.setFont(QFont("Segoe UI", 14, QFont.Bold))
        manual_title.setStyleSheet(f"color: {RIT_ACCENT};")
        
        manual_desc = QLabel("Use this feature when a student cannot be recognized by the voice system")
        manual_desc.setWordWrap(True)
        
        # Student ID input
        manual_input_layout = QGridLayout()
        
        manual_student_label = QLabel("Student ID:")
        manual_student_label.setFont(QFont("Segoe UI", 10, QFont.Bold))
        self.manual_student_id = QLineEdit()
        self.manual_student_id.setPlaceholderText("Enter Student ID to mark present")
        
        # Student name input (optional)
        manual_name_label = QLabel("Student Name (optional):")
        manual_name_label.setFont(QFont("Segoe UI", 10, QFont.Bold))
        self.manual_student_name = QLineEdit()
        self.manual_student_name.setPlaceholderText("Enter student name if known")
        
        manual_input_layout.addWidget(manual_student_label, 0, 0)
        manual_input_layout.addWidget(self.manual_student_id, 0, 1)
        manual_input_layout.addWidget(manual_name_label, 1, 0)
        manual_input_layout.addWidget(self.manual_student_name, 1, 1)
        
        # Mark button with animated effects
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        
        self.mark_attendance_btn = AnimatedButton("Mark Present", color=RIT_SUCCESS)
        self.mark_attendance_btn.setFixedWidth(200)
        self.mark_attendance_btn.setFont(QFont("Segoe UI", 12, QFont.Bold))
        self.mark_attendance_btn.clicked.connect(self.mark_manual_attendance)
        
        button_layout.addWidget(self.mark_attendance_btn)
        button_layout.addStretch()
        
        # Status label with stylish frame
        status_frame = QFrame()
        status_frame.setStyleSheet(f"""
            QFrame {{
                background-color: {RIT_DARK};
                border-radius: 8px;
                padding: 10px;
            }}
        """)
        
        status_layout = QHBoxLayout(status_frame)
        
        self.manual_status_label = QLabel("Ready to mark attendance")
        self.manual_status_label.setStyleSheet(f"color: {RIT_ACCENT}; font-weight: bold; font-size: 14px;")
        self.manual_status_label.setAlignment(Qt.AlignCenter)
        
        status_layout.addWidget(self.manual_status_label)
        
        # Add all sections to the manual layout
        manual_layout.addWidget(manual_title)
        manual_layout.addWidget(manual_desc)
        manual_layout.addLayout(manual_input_layout)
        manual_layout.addLayout(button_layout)
        manual_layout.addWidget(status_frame)
        
        # Information panel
        info_frame = CardFrame()
        info_layout = QVBoxLayout(info_frame)
        
        info_title = QLabel("Important Information")
        info_title.setFont(QFont("Segoe UI", 14, QFont.Bold))
        info_title.setStyleSheet(f"color: {RIT_WARNING};")
        
        info_text = QLabel(
            "• Manual attendance should only be used when the voice recognition system fails\n"
            "• Use student's official ID number\n"
            "• Each student can only be marked present once per day\n"
            "• All manual entries are logged for audit purposes"
        )
        info_text.setWordWrap(True)
        
        info_layout.addWidget(info_title)
        info_layout.addWidget(info_text)
        
        # Add to main layout
        layout.addWidget(manual_frame)
        layout.addWidget(info_frame)
        layout.addStretch()
        
        tab.setLayout(layout)
        return tab
    
    def view_attendance_by_date(self):
        """Fetches and displays attendance records for a specific date."""
        date = self.date_picker.date().toString("yyyy-MM-dd")
        
        # Show loading animation
        self.records_label.setText("Loading records...")
        QApplication.processEvents()
        
        try:
            records = fetch_attendance_by_date(date)
            self.display_attendance_records(records)
            self.records_label.setText(f"Showing {len(records)} records for {date}")
            
            # Track last view type
            self.last_view_type = 'date'
            
            # Highlight the table for attention
            self.pulse_effect(self.attendance_table)
            
        except Exception as e:
            self.show_message(f"Error fetching records: {str(e)}", "Error", QMessageBox.Critical)

    def view_attendance_by_range(self):
        """Fetches and displays attendance records for a date range."""
        start_date = self.start_date.date().toString("yyyy-MM-dd")
        end_date = self.end_date.date().toString("yyyy-MM-dd")
        
        if start_date > end_date:
            self.show_message("Start date must be before end date.", "Date Error", QMessageBox.Warning)
            return
            
        # Show loading animation
        self.records_label.setText("Loading records...")
        QApplication.processEvents()
        
        try:
            records = fetch_attendance_by_range(start_date, end_date)
            self.display_attendance_records(records)
            self.records_label.setText(f"Showing {len(records)} records from {start_date} to {end_date}")
            
            # Track last view type
            self.last_view_type = 'range'
            
            # Highlight the table for attention
            self.pulse_effect(self.attendance_table)
            
        except Exception as e:
            self.show_message(f"Error fetching records: {str(e)}", "Error", QMessageBox.Critical)

    def view_attendance_by_student(self):
        """Fetches and displays attendance records for a specific student."""
        student_id = self.student_id_input.text().strip()
        
        if not student_id:
            self.show_message("Please enter a student ID.", "Input Error", QMessageBox.Warning)
            return
            
        if not validate_user_id(student_id):
            self.show_message("Invalid student ID format.", "Input Error", QMessageBox.Warning)
            return
            
        # Show loading animation
        self.records_label.setText("Loading records...")
        QApplication.processEvents()
        
        try:
            records = fetch_attendance_by_student(student_id)
            self.display_attendance_records(records)
            self.records_label.setText(f"Showing {len(records)} records for student {student_id}")
            
            # Track last view type
            self.last_view_type = 'student'
            
            # Highlight the table for attention
            self.pulse_effect(self.attendance_table)
            
        except Exception as e:
            self.show_message(f"Error fetching records: {str(e)}", "Error", QMessageBox.Critical)
        
    def pulse_effect(self, widget):
        """Creates a pulse animation effect to draw attention to a widget."""
        original_stylesheet = widget.styleSheet()
        
        # Highlight animation
        widget.setStyleSheet(original_stylesheet + f"""
            border: 2px solid {RIT_ACCENT};
        """)
        
        # Reset after a delay
        QTimer.singleShot(800, lambda: widget.setStyleSheet(original_stylesheet))
        
    def display_attendance_records(self, records):
        """Populates the attendance table with records."""
        self.attendance_table.setRowCount(0)  # Clear existing rows
        
        if not records:
            self.records_label.setText("No records found")
            return
            
        for row_index, record in enumerate(records):
            self.attendance_table.insertRow(row_index)
            
            for col_index, value in enumerate(record):
                item = QTableWidgetItem(str(value))
                
                # Color code the status column
                if col_index == 3:  # Status column
                    if value.lower() == "present":
                        item.setForeground(QBrush(QColor(RIT_SUCCESS)))
                        item.setFont(QFont("Segoe UI", 9, QFont.Bold))
                    elif value.lower() == "absent":
                        item.setForeground(QBrush(QColor(RIT_ERROR)))
                        item.setFont(QFont("Segoe UI", 9, QFont.Bold))
                
                self.attendance_table.setItem(row_index, col_index, item)
    
    def export_attendance(self):
        """Exports attendance data to Excel file."""
        # Show animation during export
        self.export_btn.setText("Exporting...")
        self.export_btn.setEnabled(False)
        QApplication.processEvents()
        
        try:
            # Check which data view is currently active to determine what to export
            # This approach ensures we're exporting exactly what the user is viewing
            
            # Get which button was clicked last or which view is active
            student_id = self.student_id_input.text().strip()
            start_date = self.start_date.date().toString("yyyy-MM-dd")
            end_date = self.end_date.date().toString("yyyy-MM-dd")
            single_date = self.date_picker.date().toString("yyyy-MM-dd")
            
            # Create a clean export based on what the user is currently viewing
            if hasattr(self, 'last_view_type'):
                if self.last_view_type == 'student':
                    # Only pass the student_id parameter
                    filename = export_to_excel(user_id=student_id)
                    description = f"student ID {student_id}"
                    
                elif self.last_view_type == 'range':
                    # Only pass the date range parameters
                    filename = export_to_excel(start_date=start_date, end_date=end_date)
                    description = f"date range {start_date} to {end_date}"
                    
                elif self.last_view_type == 'date':
                    # Only pass the single date parameter
                    filename = export_to_excel(start_date=single_date, end_date=single_date)
                    description = f"date {single_date}"
                    
                else:
                    # Fallback: export current table content
                    self.show_message("Please view data first before exporting.", "Export Notice", QMessageBox.Information)
                    self.export_btn.setText("Export to Excel")
                    self.export_btn.setEnabled(True)
                    return
            else:
                self.show_message("Please view data first before exporting.", "Export Notice", QMessageBox.Information)
                self.export_btn.setText("Export to Excel")
                self.export_btn.setEnabled(True)
                return
            
            if filename:
                self.show_message(f"Data for {description} exported to {filename}", "Export Successful")
            else:
                self.show_message("Failed to export data or no records found.", "Export Failed", QMessageBox.Warning)
                
        except Exception as e:
            self.show_message(f"Error during export: {str(e)}", "Export Error", QMessageBox.Critical)
        finally:
            # Reset button
            self.export_btn.setText("Export to Excel")
            self.export_btn.setEnabled(True)
    
    def confirm_delete_student(self):
        """Confirms and processes student deletion."""
        student_id = self.delete_id_input.text().strip()
        
        if not student_id:
            self.show_message("Please enter a student ID.", "Input Error", QMessageBox.Warning)
            return
            
        if not validate_user_id(student_id):
            self.show_message("Invalid student ID format.", "Input Error", QMessageBox.Warning)
            return
        
        # Create a more visually distinctive warning dialog
        msg_box = QMessageBox(self)
        msg_box.setWindowTitle("⚠️ Confirm Deletion")
        msg_box.setText(f"<h3>Are you sure you want to delete student with ID: {student_id}?</h3>")
        msg_box.setInformativeText("<b>Warning:</b> This will permanently remove all their:<br>• Attendance records<br>• Voice samples<br>• Personal information<br><br>This action cannot be undone.")
        msg_box.setIcon(QMessageBox.Warning)
        msg_box.setStandardButtons(QMessageBox.Yes | QMessageBox.No)
        msg_box.setDefaultButton(QMessageBox.No)
        msg_box.setStyleSheet(f"""
            QMessageBox {{
                background-color: {RIT_CARD_BG};
                color: {RIT_TEXT_LIGHT};
            }}
            QPushButton {{
                background-color: {RIT_SECONDARY};
                color: white;
                border: none;
                border-radius: 5px;
                padding: 8px 16px;
                font-weight: bold;
            }}
            QPushButton:hover {{
                background-color: {RIT_ACCENT};
            }}
            QPushButton[text="&Yes"] {{
                background-color: {RIT_ERROR};
            }}
            QPushButton[text="&Yes"]:hover {{
                background-color: #F87171;
            }}
        """)
        
        result = msg_box.exec_()
        
        if result == QMessageBox.Yes:
            try:
                # Show loading animation
                self.delete_student_btn.setText("Deleting...")
                self.delete_student_btn.setEnabled(False)
                QApplication.processEvents()
                
                success = delete_student(student_id)
                
                if success:
                    self.show_message(f"Student {student_id} deleted successfully.", "Deletion Successful")
                    self.delete_id_input.clear()
                else:
                    self.show_message("Failed to delete student.", "Deletion Failed", QMessageBox.Warning)
            except Exception as e:
                self.show_message(f"Error deleting student: {str(e)}", "Error", QMessageBox.Critical)
            finally:
                # Reset button
                self.delete_student_btn.setText("Delete Student")
                self.delete_student_btn.setEnabled(True)
    
    def generate_attendance_report(self):
        """Generates and displays attendance percentage report."""
        start_date = self.report_start_date.date().toString("yyyy-MM-dd")
        end_date = self.report_end_date.date().toString("yyyy-MM-dd")
        student_id = self.report_student_id.text().strip() or None
        
        if start_date > end_date:
            self.show_message("Start date must be before end date.", "Date Error", QMessageBox.Warning)
            return
        
        # Show loading animation
        self.generate_report_btn.setText("Generating...")
        self.generate_report_btn.setEnabled(False)
        QApplication.processEvents()
            
        try:
            # Convert date strings to datetime objects as required by the function
            start_dt = datetime.strptime(start_date, "%Y-%m-%d").date()
            end_dt = datetime.strptime(end_date, "%Y-%m-%d").date()
            
            records = calculate_attendance_percentage(start_dt, end_dt, student_id)
            
            self.report_table.setRowCount(0)  # Clear existing rows
            
            if not records:
                self.show_message("No records found for the selected period.", "No Data", QMessageBox.Information)
                return
                
            for row_index, record in enumerate(records):
                self.report_table.insertRow(row_index)
                
                self.report_table.setItem(row_index, 0, QTableWidgetItem(str(record["student_id"])))
                self.report_table.setItem(row_index, 1, QTableWidgetItem(str(record["name"])))
                
                # Color-code the percentage based on value
                percentage_item = QTableWidgetItem(f"{record['percentage']:.2f}%")
                
                if record['percentage'] >= 90:
                    percentage_item.setForeground(QBrush(QColor(RIT_SUCCESS)))
                elif record['percentage'] >= 75:
                    percentage_item.setForeground(QBrush(QColor(RIT_SECONDARY)))
                elif record['percentage'] >= 60:
                    percentage_item.setForeground(QBrush(QColor(RIT_WARNING)))
                else:
                    percentage_item.setForeground(QBrush(QColor(RIT_ERROR)))
                
                percentage_item.setFont(QFont("Segoe UI", 10, QFont.Bold))
                self.report_table.setItem(row_index, 2, percentage_item)
            
            # Highlight the table for attention
            self.pulse_effect(self.report_table)
                
        except Exception as e:
            self.show_message(f"Error generating report: {str(e)}", "Error", QMessageBox.Critical)
        finally:
            # Reset button
            self.generate_report_btn.setText("Generate Attendance Report")
            self.generate_report_btn.setEnabled(True)
    
    def export_report(self):
        """Exports the current report to Excel."""
        # Show animation during export
        self.export_report_btn.setText("Exporting...")
        self.export_report_btn.setEnabled(False)
        QApplication.processEvents()
        
        try:
            start_date = self.report_start_date.date().toString("yyyy-MM-dd")
            end_date = self.report_end_date.date().toString("yyyy-MM-dd")
            student_id = self.report_student_id.text().strip() or None
            
            filename = export_to_excel(start_date=start_date, end_date=end_date, user_id=student_id)
            
            if filename:
                self.show_message(f"Report exported to {filename}", "Export Successful")
            else:
                self.show_message("Failed to export report or no records to export.", "Export Failed", QMessageBox.Warning)
                
        except Exception as e:
            self.show_message(f"Error exporting report: {str(e)}", "Error", QMessageBox.Critical)
        finally:
            # Reset button
            self.export_report_btn.setText("Export Report")
            self.export_report_btn.setEnabled(True)
    
    def mark_manual_attendance(self):
        """Manually marks a student as present."""
        student_id = self.manual_student_id.text().strip()
        student_name = self.manual_student_name.text().strip() or student_id  # Use ID as name if not provided
        
        if not student_id:
            self.show_message("Please enter a student ID.", "Input Error", QMessageBox.Warning)
            return
            
        if not validate_user_id(student_id):
            self.show_message("Invalid student ID format.", "Input Error", QMessageBox.Warning)
            return
        
        try:
            # Animation effect
            self.manual_status_label.setText("Processing attendance...")
            self.manual_status_label.setStyleSheet(f"color: {RIT_SECONDARY}; font-weight: bold; font-size: 14px;")
            self.mark_attendance_btn.setText("Marking...")
            self.mark_attendance_btn.setEnabled(False)
            QApplication.processEvents()
            
            # Simulate a small delay to show the process (optional)
            QTimer.singleShot(800, lambda: self.complete_mark_attendance(student_id, student_name))
            
        except Exception as e:
            self.manual_status_label.setText(f"❌ Error: {str(e)}")
            self.manual_status_label.setStyleSheet(f"color: {RIT_ERROR}; font-weight: bold; font-size: 14px;")
            logger.error(f"Manual attendance error: {str(e)}")
            
            # Reset button
            self.mark_attendance_btn.setText("Mark Present")
            self.mark_attendance_btn.setEnabled(True)
    
    def complete_mark_attendance(self, student_id, student_name):
        """Completes the attendance marking process after animation."""
        try:
            success = mark_attendance(student_id, student_name)
            
            if success:
                self.manual_status_label.setText(f"✅ Attendance marked for {student_name} (ID: {student_id})")
                self.manual_status_label.setStyleSheet(f"color: {RIT_SUCCESS}; font-weight: bold; font-size: 14px;")
                logger.info(f"Manual attendance marked by admin for {student_id}")
                
                # Success effect
                self.pulse_effect(self.manual_student_id)
                self.pulse_effect(self.manual_student_name)
                
                # Clear fields after successful marking
                self.manual_student_id.clear()
                self.manual_student_name.clear()
            else:
                self.manual_status_label.setText("❌ Failed to mark attendance (already present today?)")
                self.manual_status_label.setStyleSheet(f"color: {RIT_ERROR}; font-weight: bold; font-size: 14px;")
        except Exception as e:
            self.manual_status_label.setText(f"❌ Error: {str(e)}")
            self.manual_status_label.setStyleSheet(f"color: {RIT_ERROR}; font-weight: bold; font-size: 14px;")
            logger.error(f"Manual attendance error: {str(e)}")
        finally:
            # Reset button
            self.mark_attendance_btn.setText("Mark Present")
            self.mark_attendance_btn.setEnabled(True)
    
    def go_to_register_page(self):
        """Navigates to the register student page."""
        if self.stack:
            from gui.register_student import RegisterStudentPage
            register_page = RegisterStudentPage(stack=self.stack)
            self.stack.addWidget(register_page)
            self.stack.setCurrentWidget(register_page)
        else:
            self.show_message("Error: Navigation stack not available", "Error", QMessageBox.Critical)
    
    def logout(self):
        """Logs out and returns to the main menu."""
        # Create a logout confirmation dialog
        msg_box = QMessageBox(self)
        msg_box.setWindowTitle("Confirm Logout")
        msg_box.setText("<h3>Are you sure you want to logout?</h3>")
        msg_box.setInformativeText("Any unsaved changes will be lost.")
        msg_box.setIcon(QMessageBox.Question)
        msg_box.setStandardButtons(QMessageBox.Yes | QMessageBox.No)
        msg_box.setDefaultButton(QMessageBox.No)
        msg_box.setStyleSheet(f"""
            QMessageBox {{
                background-color: {RIT_CARD_BG};
                color: {RIT_TEXT_LIGHT};
            }}
            QPushButton {{
                background-color: {RIT_SECONDARY};
                color: white;
                border: none;
                border-radius: 5px;
                padding: 8px 16px;
                font-weight: bold;
            }}
            QPushButton:hover {{
                background-color: {RIT_ACCENT};
            }}
        """)
        
        result = msg_box.exec_()
        
        if result == QMessageBox.Yes and self.stack:
            # Return to main menu (index 1)
            self.stack.setCurrentIndex(1)
            logger.info(f"Admin user {self.username} logged out")
        elif not self.stack:
            self.show_message("Error: Navigation stack not available", "Error", QMessageBox.Critical)
    
    def show_message(self, message, title, icon=QMessageBox.Information):
        """Display a message box to the user."""
        msg_box = QMessageBox(icon, title, message, parent=self)
        
        # Add RIT styling to the message box
        msg_box.setStyleSheet(f"""
            QMessageBox {{
                background-color: {RIT_CARD_BG};
                color: {RIT_TEXT_LIGHT};
            }}
            QPushButton {{
                background-color: {RIT_SECONDARY};
                color: white;
                border: none;
                border-radius: 5px;
                padding: 8px 16px;
                font-weight: bold;
            }}
            QPushButton:hover {{
                background-color: {RIT_ACCENT};
            }}
        """)
        
        msg_box.exec_()

# For standalone testing
if __name__ == "__main__":
    from PyQt5.QtWidgets import QApplication
    app = QApplication(sys.argv)
    window = AdminDashboard("admin")
    window.show()
    sys.exit(app.exec_())