from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QPushButton, QMessageBox, 
    QProgressBar, QHBoxLayout, QFrame, QSizePolicy
)
from PyQt5.QtCore import (
    Qt, QThread, pyqtSignal, QPropertyAnimation, 
    QEasingCurve, QTimer, QSize, QPoint, QRect
)
from PyQt5.QtGui import (
    QFont, QColor, QPainter, QBrush, QPen, 
    QLinearGradient, QRadialGradient, QPainterPath, QPixmap
)
import traceback
import sys
import os
import math
import random
import time
import pyaudio
import numpy as np
import struct

# Add the root directory to the path to ensure imports work correctly
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Import required backend functions directly
from modules.audio_processor import record_attendance_sample
from modules.voice_processor import identify_speaker
from modules.db_manager import mark_attendance
from modules.utils import CONFIG

# Import visual components from register_student
from .register_student import (
    DynamicBackgroundFrame, FloatingParticle, 
    IlluminatedText, AnimatedButton, WaveEffect,
    RIT_PRIMARY, RIT_SECONDARY, RIT_ACCENT, RIT_LIGHT, 
    RIT_DARK, RIT_TEXT_LIGHT, RIT_SUCCESS, RIT_ERROR, RIT_BG,
    RIT_WARNING  # Added warning color
)

class EnhancedProgressBar(QProgressBar):
    """Custom progress bar with modern styling"""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setTextVisible(False)
        self.setFixedHeight(8)
        self.setStyleSheet(f"""
            QProgressBar {{
                background-color: {RIT_DARK}80;
                border: none;
                border-radius: 4px;
                min-height: 8px;
                max-height: 8px;
            }}
            QProgressBar::chunk {{
                background-color: qlineargradient(
                    x1: 0, y1: 0, x2: 1, y2: 0,
                    stop: 0 {RIT_SECONDARY},
                    stop: 1 {RIT_ACCENT}
                );
                border-radius: 4px;
            }}
        """)

class AudioLevelMeter(QWidget):
    """Visual meter showing microphone input level."""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMinimumHeight(120)
        self.setMinimumWidth(300)
        
        # Audio level parameters
        self.level = 0
        self.peak_level = 0
        self.decay_rate = 0.05  # How quickly the peak falls
        
        # Buffer for smooth animation
        self.level_buffer = [0] * 20
        self.buffer_pos = 0
        
        # Start with no movement
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.decay_peak)
        self.timer.start(30)
    
    def set_level(self, level):
        """Set current audio level (0-100)."""
        # Update rolling buffer for smoothing
        self.level_buffer[self.buffer_pos] = level
        self.buffer_pos = (self.buffer_pos + 1) % len(self.level_buffer)
        
        # Smooth level is average of buffer
        self.level = sum(self.level_buffer) / len(self.level_buffer)
        
        # Update peak if needed
        if self.level > self.peak_level:
            self.peak_level = self.level
        
        self.update()
    
    def decay_peak(self):
        """Gradually lower peak level for natural fall-off."""
        if self.peak_level > self.level:
            self.peak_level -= self.decay_rate
        self.update()
    
    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        
        # Draw background
        painter.fillRect(self.rect(), QColor(RIT_DARK))
        
        # Calculate metrics
        width = self.width() - 20  # Margin
        height = self.height() - 20  # Margin
        
        # Create gradient for level bar
        gradient = QLinearGradient(0, 0, width, 0)
        gradient.setColorAt(0, QColor(RIT_SUCCESS))
        gradient.setColorAt(0.7, QColor(RIT_SECONDARY))
        gradient.setColorAt(1, QColor(RIT_ACCENT))
        
        # Draw level bar
        level_width = int((width * self.level) / 100)
        level_rect = QRect(10, 10, level_width, height)
        painter.setBrush(QBrush(gradient))
        painter.setPen(Qt.NoPen)
        painter.drawRoundedRect(level_rect, 5, 5)
        
        # Draw peak marker
        peak_x = 10 + int((width * self.peak_level) / 100)
        if peak_x > 10:
            peak_rect = QRect(peak_x - 2, 8, 4, height + 4)
            painter.setBrush(QColor(RIT_TEXT_LIGHT))
            painter.drawRoundedRect(peak_rect, 2, 2)
        
        # Draw level markers
        painter.setPen(QPen(QColor(RIT_TEXT_LIGHT + "40"), 1))
        for i in range(1, 10):
            x = 10 + (width * i) / 10
            painter.drawLine(int(x), 10, int(x), height + 10)

class AudioLevelThread(QThread):
    """Thread to monitor audio levels during recording."""
    level_updated = pyqtSignal(float)
    
    def __init__(self):
        super().__init__()
        self.running = True
    
    def run(self):
        """Monitor audio levels from system microphone."""
        try:
            CHUNK = 1024
            FORMAT = pyaudio.paInt16
            CHANNELS = 1
            RATE = 44100
            
            p = pyaudio.PyAudio()
            stream = p.open(
                format=FORMAT,
                channels=CHANNELS,
                rate=RATE,
                input=True,
                frames_per_buffer=CHUNK
            )
            
            while self.running:
                try:
                    data = stream.read(CHUNK, exception_on_overflow=False)
                    # Convert to integers
                    fmt = "%dh" % (len(data) // 2)
                    data_int = struct.unpack(fmt, data)
                    
                    # Calculate RMS and convert to level (0-100)
                    rms = np.sqrt(np.mean(np.array(data_int)**2))
                    level = min(100, max(0, rms / 500 * 100))  # Scale to 0-100
                    
                    # Emit level update signal
                    self.level_updated.emit(level)
                    time.sleep(0.03)  # Small delay to avoid excessive updates
                except Exception as e:
                    print(f"Error reading audio: {e}")
                    time.sleep(0.1)
            
            stream.stop_stream()
            stream.close()
            p.terminate()
        except Exception as e:
            print(f"Error in audio monitoring: {e}")
    
    def stop(self):
        """Stop the audio monitoring."""
        self.running = False
        self.wait()

class AttendanceWorker(QThread):
    """Background worker for attendance marking"""
    update_status = pyqtSignal(str)
    update_progress = pyqtSignal(int)  # Added for progress updates
    done = pyqtSignal(bool, str, bool)  # success, message, low_confidence
    
    def run(self):
        try:
            # 1. Record sample - show progress during recording
            self.update_status.emit("Please speak for attendance verification...")
            self.update_progress.emit(0)
            
            # Simulate progress during recording
            for i in range(1, 101):
                self.update_progress.emit(i)
                time.sleep(0.03)  # Smooth 3-second recording visualization
            
            audio_sample = record_attendance_sample()
            
            if audio_sample is None:
                self.done.emit(False, "Failed to record voice. Please try again.", False)
                return
            
            # 2. Identify speaker
            self.update_status.emit("Analyzing voice...")
            self.update_progress.emit(0)
            
            # Show progress during analysis
            for i in range(1, 101):
                self.update_progress.emit(i)
                time.sleep(0.01)  # Faster 1-second analysis visualization
                
            match, confidence = identify_speaker(audio_sample)
            
            if match is None:
                self.done.emit(False, f"Voice not recognized (Confidence: {confidence:.2f}). Please try again.", False)
                return
            
            user_id, name = match
            
            # 3. Check confidence threshold
            if confidence < CONFIG['min_voice_confidence']:
                self.done.emit(True, f"Voice confidence too low ({confidence:.2f}). Please try again or contact admin.", True)
                return
            
            # 4. Mark attendance
            self.update_status.emit("Marking attendance...")
            if mark_attendance(user_id, name):
                self.done.emit(True, f"Welcome, {name}! Attendance marked successfully.", False)
            else:
                self.done.emit(False, "Failed to mark attendance. You may already be marked present today.", False)
                
        except Exception as e:
            traceback.print_exc()
            self.done.emit(False, f"Error: {str(e)}", False)

class AttendancePage(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.main_window = self.get_main_window()
        self.opacity = 0.0
        self.level_thread = None  # Added for audio monitoring
        
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
        self.title_label = IlluminatedText("Voice Attendance")
        self.title_label.setFont(QFont("Segoe UI", 30, QFont.Bold))
        self.title_label.setFixedHeight(80)
        self.title_label.setAlignment(Qt.AlignCenter)
        card_layout.addWidget(self.title_label)
        
        # Subtitle
        subtitle = QLabel("Speak naturally to mark your attendance")
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
        
        # Status section
        self.status_label = QLabel("Click the button below to begin.")
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
        card_layout.addWidget(self.status_label)
        
        # Audio level meter
        self.level_meter = AudioLevelMeter()
        self.level_meter.setVisible(False)  # Hidden initially
        card_layout.addWidget(self.level_meter)
        
        # Progress bar
        self.progress = EnhancedProgressBar()
        self.progress.setVisible(False)
        card_layout.addWidget(self.progress)
        
        # Button layout with fixed widths
        button_layout = QHBoxLayout()
        button_layout.setSpacing(20)
        button_layout.setContentsMargins(20, 0, 20, 0)  # Add horizontal margins
        
        # Enhanced animated buttons with gradients and fixed widths
        self.back_button = AnimatedButton("Back", "#64748B", RIT_PRIMARY)
        self.back_button.setFixedWidth(180)  # Fixed width for consistent layout
        
        self.listen_button = AnimatedButton("Start Listening", RIT_SECONDARY, RIT_ACCENT)
        self.listen_button.setFixedWidth(180)  # Fixed width for consistent layout
        
        # Connect button signals
        self.back_button.clicked.connect(self.go_back)
        self.listen_button.clicked.connect(self.mark_attendance)
        
        # Center the buttons
        button_layout.addStretch()  # Add stretching space before buttons
        button_layout.addWidget(self.back_button)
        button_layout.addWidget(self.listen_button)
        button_layout.addStretch()  # Add stretching space after buttons
        
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

    def get_main_window(self):
        """Try to find the main window by traversing the widget hierarchy"""
        parent = self.parent()
        while parent:
            if hasattr(parent, 'navigate_to_main_menu'):
                return parent
            parent = parent.parent()
        return None

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
        if self.parent() and hasattr(self.parent(), 'setCurrentIndex'):
            self.parent().setCurrentIndex(1)  # Return to main menu

    def mark_attendance(self):
        """Start the attendance marking process."""
        self.listen_button.setDisabled(True)
        self.listen_button.setText("Recording...")
        
        # Start audio monitoring
        self.level_meter.setVisible(True)
        self.start_audio_monitoring()
        
        self.status_label.setText("Please speak naturally...")
        self.status_label.setStyleSheet(f"""
            color: {RIT_SECONDARY};
            font-weight: bold;
            letter-spacing: 1px;
            background-color: {RIT_DARK}50;
            border-radius: 10px;
            padding: 10px;
        """)

        self.worker = AttendanceWorker()
        self.worker.update_status.connect(self.status_label.setText)
        self.worker.update_progress.connect(self.progress.setValue)  # Connect progress updates
        self.worker.done.connect(self.attendance_done)
        self.worker.start()

    def attendance_done(self, success, message, low_confidence=False):
        """Handle completion of attendance marking."""
        # Stop audio monitoring
        self.stop_audio_monitoring()
        self.level_meter.setVisible(False)
        
        self.listen_button.setEnabled(True)
        self.listen_button.setText("Start Listening")
        
        # Update status with appropriate color
        color = RIT_SUCCESS if success and not low_confidence else RIT_ERROR if not success else RIT_WARNING
        self.status_label.setStyleSheet(f"""
            color: {color};
            font-weight: bold;
            letter-spacing: 1px;
            background-color: {RIT_DARK}50;
            border-radius: 10px;
            padding: 10px;
        """)
        self.status_label.setText(message)
        
        # Show message box
        title = "Attendance Status"
        icon = QMessageBox.Warning if low_confidence else QMessageBox.Information if success else QMessageBox.Critical
        
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
        """Return to the main menu with fade effect."""
        self.fade_out()

    def start_audio_monitoring(self):
        """Start the audio level monitoring thread."""
        # Stop any existing thread
        self.stop_audio_monitoring()
        
        # Create and start new thread
        self.level_thread = AudioLevelThread()
        self.level_thread.level_updated.connect(self.level_meter.set_level)
        self.level_thread.start()
    
    def stop_audio_monitoring(self):
        """Stop the audio level monitoring thread."""
        if self.level_thread and self.level_thread.isRunning():
            self.level_thread.stop()
            self.level_thread.wait()
            self.level_thread = None

    def resizeEvent(self, event):
        """Handle widget resize events to update particle system."""
        super().resizeEvent(event)
        if hasattr(self, 'particles'):
            self.particles.setGeometry(0, 0, self.width(), self.height())
