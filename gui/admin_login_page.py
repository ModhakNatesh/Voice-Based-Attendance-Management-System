"""Admin login page for the Voice-Based Attendance System."""
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QLineEdit, QPushButton, 
    QMessageBox, QHBoxLayout, QGridLayout, QFrame, QProgressBar,
    QSizePolicy
)
from PyQt5.QtCore import (
    Qt, pyqtSignal, QPropertyAnimation, QEasingCurve, 
    QTimer, QSize, QPoint, QRect, QRectF
)
from PyQt5.QtGui import (
    QFont, QIcon, QPixmap, QPainter, QColor, QBrush, QPen,
    QLinearGradient, QRadialGradient, QPainterPath
)

import sys
import os
import math
import random

# Add the root directory to the path to ensure imports work correctly
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from modules.db_manager import verify_user, verify_2fa
from modules.utils import CONFIG, logger

# RIT Theme Colors
RIT_PRIMARY = "#1E3A8A"     # Deep blue for primary elements
RIT_SECONDARY = "#4F46E5"   # Bright blue for accent and highlights
RIT_ACCENT = "#7C3AED"      # Purple accent for special elements
RIT_LIGHT = "#F1F5F9"       # Light background
RIT_DARK = "#1E293B"        # Dark background
RIT_TEXT_LIGHT = "#F8FAFC"  # Light text
RIT_TEXT_DARK = "#334155"   # Dark text
RIT_SUCCESS = "#10B981"     # Green for success
RIT_ERROR = "#EF4444"       # Red for errors
RIT_BG = "#0F172A"          # Main background

# Import visual components from main_menu
from .register_student import (
    DynamicBackgroundFrame, FloatingParticle, 
    IlluminatedText, AnimatedButton, WaveEffect
)

class EnhancedInputField(QLineEdit):
    """Custom input field with animation effects"""
    def __init__(self, placeholder="", password_mode=False, parent=None):
        super().__init__(parent)
        self.setPlaceholderText(placeholder)
        self.setMinimumHeight(60)
        self.setFont(QFont("Segoe UI", 14))
        if password_mode:
            self.setEchoMode(QLineEdit.Password)
        
        self.setStyleSheet(f"""
            QLineEdit {{
                background-color: {RIT_DARK}80;
                color: {RIT_TEXT_LIGHT};
                border: 2px solid {RIT_PRIMARY}30;
                border-radius: 12px;
                padding: 8px 16px;
            }}
            QLineEdit:focus {{
                border: 2px solid {RIT_SECONDARY};
                background-color: {RIT_DARK}AA;
            }}
        """)
        
        self.focus_anim = None
    
    def focusInEvent(self, event):
        super().focusInEvent(event)
        self.focus_anim = QPropertyAnimation(self, b"size")
        self.focus_anim.setDuration(200)
        current_size = self.size()
        self.focus_anim.setStartValue(current_size)
        self.focus_anim.setEndValue(QSize(current_size.width(), current_size.height() + 6))
        self.focus_anim.setEasingCurve(QEasingCurve.OutQuad)
        self.focus_anim.start()
    
    def focusOutEvent(self, event):
        super().focusOutEvent(event)
        if self.focus_anim:
            self.focus_anim.stop()
        
        self.restore_anim = QPropertyAnimation(self, b"size")
        self.restore_anim.setDuration(200)
        current_size = self.size()
        self.restore_anim.setStartValue(current_size)
        self.restore_anim.setEndValue(QSize(current_size.width(), 60))
        self.restore_anim.setEasingCurve(QEasingCurve.OutQuad)
        self.restore_anim.start()

class AdminLoginPage(QWidget):
    # Signal to tell parent when login is successful
    login_successful = pyqtSignal()
    
    def __init__(self, stack=None):
        super().__init__()
        self.stack = stack
        self.username = None
        self.role = None
        self.requires_2fa = True
        self.opacity = 0.0
        
        self.init_ui()
        QTimer.singleShot(100, self.fade_in)

    def init_ui(self):
        # Main layout without margins for full-screen background
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        
        # Create dynamic background frame
        self.bg_frame = DynamicBackgroundFrame()
        main_layout.addWidget(self.bg_frame)
        
        # Layout for background frame
        bg_layout = QVBoxLayout(self.bg_frame)
        bg_layout.setContentsMargins(40, 40, 40, 40)
        bg_layout.setSpacing(0)
        
        # Add particle effect
        self.particles = FloatingParticle(self.bg_frame)
        self.particles.setGeometry(0, 0, self.width(), self.height())
        
        # Content container
        content_container = QWidget()
        content_container.setStyleSheet("background-color: transparent;")
        content_layout = QVBoxLayout(content_container)
        content_layout.setContentsMargins(30, 30, 30, 30)
        content_layout.setAlignment(Qt.AlignCenter)
        
        # Logo section
        logo_layout = QHBoxLayout()
        logo_layout.setAlignment(Qt.AlignCenter)
        
        logo_label = QLabel()
        logo_size = 60
        logo_path = os.path.join(os.path.dirname(__file__), '..', 'assets', 'rit_logo.png')
        
        if os.path.exists(logo_path):
            logo_pixmap = QPixmap(logo_path).scaled(logo_size, logo_size, 
                                                   Qt.KeepAspectRatio, 
                                                   Qt.SmoothTransformation)
            logo_label.setPixmap(logo_pixmap)
        else:
            # Fallback to programmatically generated logo
            logo_pixmap = QPixmap(logo_size, logo_size)
            logo_pixmap.fill(Qt.transparent)
            
            painter = QPainter(logo_pixmap)
            painter.setRenderHint(QPainter.Antialiasing)
            
            gradient = QLinearGradient(0, 0, logo_size, logo_size)
            gradient.setColorAt(0, QColor(RIT_PRIMARY))
            gradient.setColorAt(1, QColor(RIT_ACCENT))
            
            painter.setBrush(QBrush(gradient))
            painter.setPen(QPen(Qt.NoPen))
            painter.drawEllipse(5, 5, logo_size-10, logo_size-10)
            
            painter.setPen(QPen(QColor(RIT_TEXT_LIGHT)))
            painter.setFont(QFont("Arial", int(logo_size/3), QFont.Bold))
            painter.drawText(logo_pixmap.rect(), Qt.AlignCenter, "RIT")
            painter.end()
            
            logo_label.setPixmap(logo_pixmap)
        
        logo_layout.addWidget(logo_label)
        content_layout.addLayout(logo_layout)

        # Create modern card with frosted glass effect
        card_frame = QFrame()
        card_frame.setObjectName("cardFrame")
        card_frame.setStyleSheet(f"""
            #cardFrame {{
                background-color: rgba(15, 23, 42, 240);
                border: 1px solid {RIT_PRIMARY}30;
                border-radius: 25px;
            }}
        """)
        card_layout = QVBoxLayout(card_frame)
        card_layout.setContentsMargins(40, 40, 40, 30)
        card_layout.setSpacing(30)
        
        # Title with illuminated effect
        self.title_label = IlluminatedText("Admin Panel")
        self.title_label.setFont(QFont("Segoe UI", 30, QFont.Bold))
        self.title_label.setFixedHeight(80)
        self.title_label.setAlignment(Qt.AlignCenter)
        card_layout.addWidget(self.title_label)
        
        # Subtitle
        subtitle = QLabel("Secure Authentication Required")
        subtitle.setFont(QFont("Segoe UI", 16, QFont.Light))
        subtitle.setStyleSheet(f"""
            color: {RIT_LIGHT};
            letter-spacing: 2px;
        """)
        subtitle.setAlignment(Qt.AlignCenter)
        card_layout.addWidget(subtitle)
        
        # Add decorative separator
        separator = QFrame()
        separator.setFrameShape(QFrame.HLine)
        separator.setFixedHeight(1)
        separator.setStyleSheet(f"background-color: {RIT_PRIMARY}30;")
        card_layout.addWidget(separator)
        
        # Form section
        form_layout = QVBoxLayout()
        form_layout.setSpacing(20)
        
        # Enhanced input fields
        self.username_input = EnhancedInputField("Username")
        self.password_input = EnhancedInputField("Password", password_mode=True)
        self.twofa_input = EnhancedInputField("2FA Code (if enabled)")
        
        # Status label with modern styling
        self.status_label = QLabel("")
        self.status_label.setFont(QFont("Segoe UI", 16))
        self.status_label.setStyleSheet(f"""
            color: {RIT_SECONDARY};
            font-weight: bold;
            letter-spacing: 1px;
            background-color: {RIT_DARK}50;
            border-radius: 10px;
            padding: 10px;
        """)
        self.status_label.setAlignment(Qt.AlignCenter)
        self.status_label.setMinimumHeight(60)
        self.status_label.setVisible(False)
        
        # Add input fields to form
        form_layout.addWidget(self.username_input)
        form_layout.addWidget(self.password_input)
        form_layout.addWidget(self.twofa_input)
        form_layout.addWidget(self.status_label)
        
        card_layout.addLayout(form_layout)
        
        # Button layout
        button_layout = QHBoxLayout()
        button_layout.setSpacing(20)
        
        # Enhanced animated buttons with gradients
        self.back_button = AnimatedButton("Back", "#64748B", RIT_PRIMARY)
        self.login_button = AnimatedButton("Login", RIT_SECONDARY, RIT_ACCENT)
        
        # Connect button signals
        self.back_button.clicked.connect(self.go_back)
        self.login_button.clicked.connect(self.handle_login)
        
        # Add buttons to layout
        button_layout.addWidget(self.back_button)
        button_layout.addWidget(self.login_button)
        
        card_layout.addLayout(button_layout)
        
        # Add wave effect
        wave_effect = WaveEffect()
        card_layout.addWidget(wave_effect)
        
        # Bottom credit
        credit_label = QLabel("© Rajeev Institute of Technology")
        credit_label.setFont(QFont("Segoe UI", 10))
        credit_label.setStyleSheet(f"color: {RIT_TEXT_LIGHT};")
        credit_label.setAlignment(Qt.AlignCenter)
        card_layout.addWidget(credit_label)
        
        # Add card to content layout
        content_layout.addWidget(card_frame)
        
        # Add content to background layout
        bg_layout.addWidget(content_container)
        
        # Set enter key to trigger login
        self.username_input.returnPressed.connect(self.password_input.setFocus)
        self.password_input.returnPressed.connect(self.twofa_input.setFocus)
        self.twofa_input.returnPressed.connect(self.handle_login)

    def fade_in(self):
        """Fade in animation for smooth transition."""
        self.opacity = 0.0
        self.setStyleSheet(f"background-color: rgba(0, 0, 0, {self.opacity});")
        
        self.fade_in_anim = QPropertyAnimation(self, b"windowOpacity")
        self.fade_in_anim.setDuration(300)
        self.fade_in_anim.setStartValue(0.0)
        self.fade_in_anim.setEndValue(1.0)
        self.fade_in_anim.setEasingCurve(QEasingCurve.OutCubic)
        self.fade_in_anim.start()

    def fade_out(self):
        """Fade out animation before navigating away."""
        self.fade_out_anim = QPropertyAnimation(self, b"windowOpacity")
        self.fade_out_anim.setDuration(300)
        self.fade_out_anim.setStartValue(1.0)
        self.fade_out_anim.setEndValue(0.0)
        self.fade_out_anim.setEasingCurve(QEasingCurve.OutCubic)
        self.fade_out_anim.finished.connect(self.complete_navigation)
        self.fade_out_anim.start()

    def complete_navigation(self):
        """Complete navigation after fade out."""
        if self.stack:
            self.stack.setCurrentIndex(1)  # Return to main menu

    def show_status(self, message, is_error=False):
        """Display status message with appropriate styling."""
        self.status_label.setText(message)
        
        if is_error:
            self.status_label.setStyleSheet(f"""
                color: #ef4444;
                font-weight: bold;
                letter-spacing: 1px;
                background-color: {RIT_DARK}50;
                border-radius: 10px;
                padding: 10px;
            """)
        else:
            self.status_label.setStyleSheet(f"""
                color: {RIT_SECONDARY};
                font-weight: bold;
                letter-spacing: 1px;
                background-color: {RIT_DARK}50;
                border-radius: 10px;
                padding: 10px;
            """)
        
        self.status_label.setVisible(True)

    def handle_login(self):
        """Handle login process with 2FA verification."""
        username = self.username_input.text().strip()
        password = self.password_input.text()
        twofa_code = self.twofa_input.text().strip()
        
        # Basic validation
        if not username or not password:
            self.show_status("Please enter both username and password.", True)
            return
        
        # Step 1: Verify username and password
        self.show_status("Authenticating...")
        role = verify_user(username, password)
        
        if not role:
            self.show_status("Invalid username or password.", True)
            return
            
        if role != "admin":
            self.show_status("Access denied. Admin privileges required.", True)
            return
        
        # Store username and role for later
        self.username = username
        self.role = role
        
        # Step 2: Verify 2FA if required
        if self.requires_2fa:
            if not twofa_code:
                self.show_status("Two-factor authentication code required.", True)
                return
                
            if not verify_2fa(username, twofa_code):
                self.show_status("Invalid two-factor authentication code.", True)
                return
        
        # If we got here, authentication was successful
        self.show_status("Login successful!")
        logger.info(f"Admin user {username} logged in successfully")
        
        # Transition to admin dashboard
        self.go_to_admin_dashboard()

    def show_message(self, message, title, icon=QMessageBox.Information):
        """Display a message box to the user."""
        msg_box = QMessageBox(icon, title, message, parent=self)
        msg_box.setStyleSheet(f"""
            QMessageBox {{
                background-color: {RIT_DARK};
                color: {RIT_TEXT_LIGHT};
            }}
            QPushButton {{
                background-color: {RIT_SECONDARY};
                color: {RIT_TEXT_LIGHT};
                border: none;
                border-radius: 5px;
                padding: 8px 16px;
                min-width: 100px;
            }}
            QPushButton:hover {{
                background-color: {RIT_ACCENT};
            }}
        """)
        msg_box.exec_()

    def go_back(self):
        """Return to the main menu."""
        if self.stack:
            self.fade_out()

    def go_to_admin_dashboard(self):
        """Navigate to the admin dashboard after successful login."""
        # Import here to avoid circular imports
        from gui.admin_dashboard import AdminDashboard
        
        # Emit signal to notify of successful login
        self.login_successful.emit()
        
        if self.stack:
            # Create admin dashboard and add to stack
            admin_dashboard = AdminDashboard(self.username, self.stack)
            self.stack.addWidget(admin_dashboard)
            self.stack.setCurrentWidget(admin_dashboard)
        else:
            self.show_message("Error: Navigation stack not available", "Error", QMessageBox.Critical)

    def resizeEvent(self, event):
        """Handle widget resize events to update particle system."""
        super().resizeEvent(event)
        if hasattr(self, 'particles'):
            self.particles.setGeometry(0, 0, self.width(), self.height())

# For standalone testing
if __name__ == "__main__":
    from PyQt5.QtWidgets import QApplication
    app = QApplication(sys.argv)
    window = AdminLoginPage()
    window.show()
    sys.exit(app.exec_())