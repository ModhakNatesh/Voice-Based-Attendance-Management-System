# pages/register_student.py

from PyQt5.QtWidgets import (
    QWidget, QLabel, QLineEdit, QPushButton, QVBoxLayout, QMessageBox, 
    QHBoxLayout, QApplication, QFrame, QSizePolicy, QSpacerItem, QDialog, QProgressBar
)
from PyQt5.QtCore import (
    Qt, QPropertyAnimation, QEasingCurve, QTimer, QSize, 
    QPoint, QRect, QRectF, pyqtProperty, pyqtSignal, QThread, QRunnable, QThreadPool, QObject, QThread
)
from PyQt5.QtGui import (
    QFont, QPixmap, QPainter, QColor, QBrush, QPen, 
    QLinearGradient, QRadialGradient, QPainterPath
)
import os
import math
import random
import time
import numpy as np
import pyaudio
import struct
import wave

# Import backend functions
from modules.db_manager import (
    register_student_db,  
    rollback_student_registration
)
from modules.audio_processor import (
    record_voice_samples
)
from modules.voice_processor import (
    generate_speaker_embeddings
)

import json

# Add this function to load the config
def load_config():
    try:
        with open('config.json', 'r') as f:
            return json.load(f)
    except Exception as e:
        print(f"Error loading config: {e}")
        # Return a default configuration with a fallback path
        return {"audio_folder": "voice_samples/"}
    
# Import visual components from main_menu
# RIT Theme Colors from main_menu
RIT_PRIMARY = "#1E3A8A"     # Deep blue for primary elements
RIT_SECONDARY = "#4F46E5"   # Bright blue for accent and highlights
RIT_ACCENT = "#7C3AED"      # Purple accent for special elements
RIT_LIGHT = "#F1F5F9"       # Light background
RIT_DARK = "#1E293B"        # Dark background
RIT_TEXT_LIGHT = "#F8FAFC"  # Light text
RIT_TEXT_DARK = "#334155"   # Dark text
RIT_SUCCESS = "#10B981"     # Green for success
RIT_ERROR = "#EF4444"       # Red for errors
RIT_WARNING = "#F59E0B"     # Orange for warnings
RIT_BG = "#0F172A"          # Main background


class FloatingParticle(QWidget):
    """Enhanced particle system with dynamic behavior - reused from main_menu"""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAttribute(Qt.WA_TransparentForMouseEvents)
        self.setAttribute(Qt.WA_NoSystemBackground)
        self.setAttribute(Qt.WA_TranslucentBackground)
        
        # Create more particle types for visual interest
        self.particles = []
        
        # Small floating dots
        for _ in range(30):
            self.particles.append({
                'x': random.randint(0, self.width() or 1000),
                'y': random.randint(0, self.height() or 800),
                'size': random.randint(2, 5),
                'speed': random.uniform(0.2, 0.8),
                'opacity': random.uniform(0.1, 0.4),
                'color': random.choice([RIT_PRIMARY, RIT_SECONDARY, RIT_ACCENT]),
                'type': 'dot'
            })
        
        # Larger glowing orbs
        for _ in range(8):
            self.particles.append({
                'x': random.randint(0, self.width() or 1000),
                'y': random.randint(0, self.height() or 800),
                'size': random.randint(20, 50),
                'speed': random.uniform(0.05, 0.15),
                'opacity': random.uniform(0.05, 0.12),
                'color': random.choice([RIT_PRIMARY, RIT_SECONDARY, RIT_ACCENT]),
                'type': 'orb'
            })
            
        # Flowing lines
        for _ in range(15):
            self.particles.append({
                'x': random.randint(0, self.width() or 1000),
                'y': random.randint(0, self.height() or 800),
                'size': random.randint(30, 100),  # Length of line
                'width': random.uniform(0.5, 1.5),  # Line width
                'speed': random.uniform(0.3, 0.7),
                'opacity': random.uniform(0.1, 0.3),
                'angle': random.uniform(0, 360),  # Line angle
                'color': random.choice([RIT_PRIMARY, RIT_SECONDARY, RIT_ACCENT]),
                'type': 'line'
            })
        
        # Start animation timer
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_particles)
        self.timer.start(30)  # Update more frequently for smoother animation
    
    def update_particles(self):
        for p in self.particles:
            # Different movement patterns based on particle type
            if p['type'] == 'dot':
                # Dots move upward with slight horizontal drift
                p['y'] -= p['speed']
                p['x'] += random.uniform(-0.3, 0.3)
                
                # Reset particles that move out of view
                if p['y'] < -10:
                    p['y'] = self.height() + 10
                    p['x'] = random.randint(0, self.width() or 1)
                    p['opacity'] = random.uniform(0.1, 0.4)
            
            elif p['type'] == 'orb':
                # Orbs move slowly and more randomly
                p['y'] -= p['speed'] * 0.7
                p['x'] += random.uniform(-0.2, 0.2)
                p['opacity'] = max(0.05, min(0.12, p['opacity'] + random.uniform(-0.005, 0.005)))  # Pulsing effect
                
                # Reset orbs that move out of view
                if p['y'] < -p['size']:
                    p['y'] = self.height() + p['size']
                    p['x'] = random.randint(0, self.width() or 1)
                    p['size'] = random.randint(20, 50)
            
            elif p['type'] == 'line':
                # Lines flow in their angle direction
                rad_angle = p['angle'] * (math.pi / 180)
                p['x'] += p['speed'] * 0.5 * math.cos(rad_angle)
                p['y'] -= p['speed'] * 0.5 * math.sin(rad_angle)
                
                # Reset lines that move out of view
                if (p['x'] < -p['size'] or p['x'] > (self.width() or 1000) + p['size'] or 
                    p['y'] < -p['size'] or p['y'] > (self.height() or 800) + p['size']):
                    p['x'] = random.randint(0, self.width() or 1000)
                    p['y'] = random.randint(0, self.height() or 800)
                    p['angle'] = random.uniform(0, 360)
                    
        self.update()  # Trigger repaint
    
    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        
        for p in self.particles:
            painter.setOpacity(p['opacity'])
            
            if p['type'] == 'dot':
                # Draw simple dots
                painter.setBrush(QBrush(QColor(p['color'])))
                painter.setPen(Qt.NoPen)
                painter.drawEllipse(int(p['x']), int(p['y']), p['size'], p['size'])
            
            elif p['type'] == 'orb':
                # Draw orbs with gradient for glow effect
                gradient = QRadialGradient(p['x'] + p['size']/2, p['y'] + p['size']/2, p['size']/2)
                color = QColor(p['color'])
                gradient.setColorAt(0, QColor(color.red(), color.green(), color.blue(), 80))
                gradient.setColorAt(1, QColor(color.red(), color.green(), color.blue(), 0))
                
                painter.setBrush(QBrush(gradient))
                painter.setPen(Qt.NoPen)
                painter.drawEllipse(int(p['x']), int(p['y']), p['size'], p['size'])
            
            elif p['type'] == 'line':
                # Draw flowing lines
                painter.setPen(QPen(QColor(p['color']), p['width'], Qt.SolidLine, Qt.RoundCap))
                
                rad_angle = p['angle'] * (math.pi / 180)
                x2 = p['x'] + p['size'] * math.cos(rad_angle)
                y2 = p['y'] - p['size'] * math.sin(rad_angle)
                
                painter.drawLine(int(p['x']), int(p['y']), int(x2), int(y2))

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


# Add an audio recorder worker class to handle recording in background
class AudioRecorderSignals(QObject):
    """Signals for the audio recorder thread."""
    level_updated = pyqtSignal(float)
    sample_completed = pyqtSignal(bool, str)
    recording_status = pyqtSignal(str)


class AudioRecorderWorker(QRunnable):
    """Worker for recording audio samples in a background thread."""
    def __init__(self, filepath, duration=3, sample_number=1):
        super().__init__()
        self.filepath = filepath
        self.duration = duration
        self.sample_number = sample_number
        self.signals = AudioRecorderSignals()
        self.is_running = True
        
        # Audio parameters matching your backend
        self.format = pyaudio.paInt16
        self.channels = 1
        self.rate = 44100
        self.chunk = 1024
        
    def run(self):
        """Record audio and emit signals with level updates."""
        p = pyaudio.PyAudio()
        frames = []
        
        try:
            # Open audio stream
            stream = p.open(
                format=self.format,
                channels=self.channels,
                rate=self.rate,
                input=True,
                frames_per_buffer=self.chunk
            )
            
            self.signals.recording_status.emit(f"Recording sample {self.sample_number}...")
            
            # Record for specified duration
            for i in range(0, int(self.rate / self.chunk * self.duration)):
                if not self.is_running:
                    raise InterruptedError("Recording canceled")
                    
                # Read chunk and calculate RMS volume
                data = stream.read(self.chunk, exception_on_overflow=False)
                frames.append(data)
                
                # Convert to integers using struct
                fmt = "%dh" % (len(data) // 2)
                data_int = struct.unpack(fmt, data)
                
                # Calculate RMS and convert to level (0-100)
                rms = np.sqrt(np.mean(np.array(data_int)**2))
                level = min(100, max(0, rms / 500 * 100))  # Scale to 0-100
                
                # Emit level update signal
                self.signals.level_updated.emit(level)
            
            # Close stream
            stream.stop_stream()
            stream.close()
            
            # Save recording to file
            with wave.open(self.filepath, 'wb') as wf:
                wf.setnchannels(self.channels)
                wf.setsampwidth(p.get_sample_size(self.format))
                wf.setframerate(self.rate)
                wf.writeframes(b''.join(frames))
            
            # Indicate completion (backend will apply noise reduction & validation)
            self.signals.sample_completed.emit(True, "")
            
        except Exception as e:
            self.signals.sample_completed.emit(False, str(e))
        finally:
            p.terminate()
    
    def stop(self):
        """Stop the recording process."""
        self.is_running = False

class AudioLevelThread(QThread):
    """Thread to monitor audio levels during recording."""
    level_updated = pyqtSignal(float)
    
    def __init__(self):
        super().__init__()
        self.running = True
        
    def run(self):
        """Monitor audio levels from system microphone."""
        try:
            import pyaudio
            import numpy as np
            import struct
            
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


# Now add this dialog class for recording interface
class VoiceRecordingDialog(QDialog):
    """Dialog for voice recording process with visual feedback."""
    def __init__(self, student_name, student_id, parent=None):
        super().__init__(parent)
        self.student_name = student_name
        self.student_id = student_id
        self.sample_results = []
        self.current_sample = 1
        self.max_samples = 3
        self.level_thread = None
        self.recording_in_progress = False
        
        # Flags to communicate with backend
        self.recording_complete = False
        self.recording_success = False
        
        # Setup window properties
        self.setWindowTitle("Voice Enrollment")
        self.setFixedSize(600, 500)  # Slightly wider for better layout
        self.setStyleSheet(f"""
            QDialog {{
                background-color: {RIT_BG};
                color: {RIT_TEXT_LIGHT};
                border: 1px solid {RIT_PRIMARY}30;
                border-radius: 12px;
            }}
        """)
        
        self.init_ui()
    
    def init_ui(self):
        # Create layout
        layout = QVBoxLayout(self)
        layout.setContentsMargins(25, 25, 25, 25)  # Increased padding
        layout.setSpacing(15)  # Adjusted spacing
        
        # Title
        title = IlluminatedText("Voice Enrollment")
        title.setFont(QFont("Segoe UI", 26, QFont.Bold))  # Slightly larger font
        title.setFixedHeight(50)  # Reduced height
        layout.addWidget(title)
        
        # Instructions
        instructions = QLabel(
            "Please speak clearly for each recording sample.\n"
            "We'll need 3 samples to create your voice profile."
        )
        instructions.setFont(QFont("Segoe UI", 12))  # Slightly smaller font
        instructions.setAlignment(Qt.AlignCenter)
        instructions.setStyleSheet(f"color: {RIT_LIGHT}DD;")  # More visible text
        layout.addWidget(instructions)
        
        # Progress indicators for each sample
        progress_layout = QHBoxLayout()
        progress_layout.setSpacing(10)  # Reduced spacing between indicators
        self.sample_indicators = []
        
        for i in range(1, self.max_samples + 1):
            indicator = QFrame()
            indicator.setFixedSize(150, 6)  # Wider but thinner indicators
            indicator.setStyleSheet(f"""
                background-color: {RIT_DARK};
                border: 1px solid {RIT_PRIMARY}30;
                border-radius: 3px;  # Smaller radius for thinner bar
            """)
            progress_layout.addWidget(indicator)
            self.sample_indicators.append(indicator)
        
        layout.addLayout(progress_layout)
        
        # Status label
        self.status_label = QLabel("Ready to begin recording")
        self.status_label.setFont(QFont("Segoe UI", 14))  # Slightly smaller font
        self.status_label.setAlignment(Qt.AlignCenter)
        self.status_label.setStyleSheet(f"""
            color: {RIT_SECONDARY};
            background-color: {RIT_DARK}80;
            border-radius: 8px;
            padding: 12px;
            margin-top: 5px;
        """)
        layout.addWidget(self.status_label)
        
        # Audio level meter with adjusted styling
        self.level_meter = AudioLevelMeter()
        self.level_meter.setMinimumHeight(100)  # Slightly shorter
        self.level_meter.setStyleSheet(f"""
            QWidget {{
                background-color: {RIT_DARK}80;
                border-radius: 8px;
            }}
        """)
        layout.addWidget(self.level_meter)
        
        # Progress bar with modern styling
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        self.progress_bar.setTextVisible(False)
        self.progress_bar.setFixedHeight(4)  # Thinner bar
        self.progress_bar.setStyleSheet(f"""
            QProgressBar {{
                border: none;
                border-radius: 2px;
                background-color: {RIT_DARK};
            }}
            QProgressBar::chunk {{
                background-color: {RIT_ACCENT};
                border-radius: 2px;
            }}
        """)
        layout.addWidget(self.progress_bar)
        
        # Button layout with adjusted spacing
        button_layout = QHBoxLayout()
        button_layout.setSpacing(15)
        
        self.cancel_button = AnimatedButton("Cancel", "#64748B", RIT_PRIMARY)
        self.cancel_button.setFixedWidth(120)  # Fixed width buttons
        self.cancel_button.clicked.connect(self.reject)
        
        self.action_button = AnimatedButton("Start", RIT_SECONDARY, RIT_ACCENT)
        self.action_button.setFixedWidth(120)  # Fixed width buttons
        self.action_button.clicked.connect(self.handle_action_button)
        
        button_layout.addWidget(self.cancel_button)
        button_layout.addWidget(self.action_button)
        
        layout.addLayout(button_layout)
    
    def handle_action_button(self):
        """Handle action button clicks based on current state."""
        if self.recording_in_progress:
            # Can't do anything during recording
            return
        
        if self.current_sample > self.max_samples:
            # All samples done, finish process
            self.recording_complete = True
            self.recording_success = True
            self.accept()
            return
        
        # Start recording the current sample
        self.start_recording_sample()
    
    def start_recording_sample(self):
        """Start the countdown and recording process for current sample."""
        self.action_button.setEnabled(False)
        self.cancel_button.setEnabled(False)
        self.recording_in_progress = True
        
        # Update status
        self.status_label.setText(f"Prepare to speak sample {self.current_sample}/{self.max_samples}")
        
        # Start audio level monitoring
        self.start_audio_monitoring()
        
        # Countdown before recording
        self.countdown_seconds = 3
        self.progress_bar.setValue(0)
        self.countdown_timer = QTimer(self)
        self.countdown_timer.timeout.connect(self.update_countdown)
        self.countdown_timer.start(1000)  # 1 second intervals
    
    def update_countdown(self):
        """Update countdown timer before recording."""
        if self.countdown_seconds > 0:
            self.status_label.setText(f"Starting in {self.countdown_seconds}...")
            self.countdown_seconds -= 1
        else:
            # Countdown complete, start actual recording
            self.countdown_timer.stop()
            self.start_actual_recording()
    
    def start_actual_recording(self):
        """Begin the actual recording process."""
        # Update UI
        self.status_label.setText(f"Recording sample {self.current_sample}... Speak naturally")
        
        # Start progress bar for recording duration
        self.record_progress = 0
        self.recording_timer = QTimer(self)
        self.recording_timer.timeout.connect(self.update_recording_progress)
        self.recording_timer.start(30)  # Update every 30ms for smooth animation
        
        # This is where we would normally start recording directly,
        # but instead we'll simulate the progress and then trigger the backend
        # function at the end
    
    def update_recording_progress(self):
        """Update recording progress bar."""
        # Simulate recording for 3 seconds
        self.record_progress += 1
        progress_percent = min(100, int(self.record_progress * 100 / 100))  # 3 seconds = 100 intervals
        self.progress_bar.setValue(progress_percent)
        
        if progress_percent >= 100:
            # Recording complete
            self.recording_timer.stop()
            self.process_recording()
    
    def process_recording(self):
        """Process the completed recording."""
        # Call the actual backend recording function
        try:
            # Actually record the sample using your backend function
            # This is a key part - we're now using your actual recording function
            config = load_config()
            audio_folder = config.get("Audio_folder", "voice_samples/")
            
            # Make sure the directory exists
            os.makedirs(audio_folder, exist_ok=True)
            filepath = os.path.join(audio_folder, f"{self.student_id}_{self.student_name}_{self.current_sample}.wav")
            
            # Directly call your backend record_single_sample function
            # Import it here to avoid circular imports
            from modules.audio_processor import record_single_sample
            
            # Show recording status
            self.status_label.setText("Processing recording...")
            
            # We're calling your actual recording function here
            # Execute in a separate thread to keep UI responsive
            self.record_thread = QThread()
            self.worker = RecordWorker(record_single_sample, filepath)
            self.worker.moveToThread(self.record_thread)
            self.record_thread.started.connect(self.worker.run)
            self.worker.finished.connect(self.handle_recording_result)
            self.record_thread.start()
            
        except Exception as e:
            # Handle recording failure
            self.status_label.setText(f"Recording failed: {str(e)}")
            self.status_label.setStyleSheet(f"""
                color: #ef4444;
                background-color: {RIT_DARK}80;
                border-radius: 10px;
                padding: 10px;
            """)
            self.sample_recording_done(False)
    
    def handle_recording_result(self, success, error=""):
        """Handle the result of the backend recording function."""
        if success:
            self.status_label.setText(f"Sample {self.current_sample} recorded successfully!")
            self.sample_indicators[self.current_sample - 1].setStyleSheet(f"""
                background-color: {RIT_SUCCESS};
                border: 1px solid {RIT_SUCCESS};
                border-radius: 6px;
            """)
            self.sample_results.append(True)
            self.current_sample += 1
        else:
            self.status_label.setText(f"Recording failed: {error}")
            self.status_label.setStyleSheet(f"""
                color: #ef4444;
                background-color: {RIT_DARK}80;
                border-radius: 10px;
                padding: 10px;
            """)
            
        # Clean up thread
        self.record_thread.quit()
        self.record_thread.wait()
        
        # Reset UI for next sample
        self.sample_recording_done(success)
    
    def sample_recording_done(self, success):
        """Reset UI after a sample recording."""
        # Stop audio monitoring
        self.stop_audio_monitoring()
        
        # Reset progress bar
        self.progress_bar.setValue(0)
        
        # Update button text
        if self.current_sample > self.max_samples:
            self.action_button.setText("Complete Enrollment")
        else:
            self.action_button.setText(f"Record {self.current_sample}")
        
        # Re-enable buttons
        self.action_button.setEnabled(True)
        self.cancel_button.setEnabled(True)
        self.recording_in_progress = False
        
        # Reset status label style if it was showing an error
        if not success:
            QTimer.singleShot(3000, self.reset_status_style)
    
    def reset_status_style(self):
        """Reset status label style to normal."""
        self.status_label.setStyleSheet(f"""
            color: {RIT_SECONDARY};
            background-color: {RIT_DARK}80;
            border-radius: 10px;
            padding: 10px;
        """)
    
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
            self.level_thread = None
    
    def closeEvent(self, event):
        """Handle window close event."""
        self.stop_audio_monitoring()
        super().closeEvent(event)
    
    def reject(self):
        """Handle dialog rejection (cancel button)."""
        self.stop_audio_monitoring()
        self.recording_complete = False
        self.recording_success = False
        super().reject()


# Worker class for recording in a separate thread
class RecordWorker(QObject):
    """Worker to execute recording function in a separate thread."""
    finished = pyqtSignal(bool, str)
    
    def __init__(self, record_func, filepath):
        super().__init__()
        self.record_func = record_func
        self.filepath = filepath
    
    def run(self):
        """Execute the recording function."""
        try:
            success = self.record_func(self.filepath)
            self.finished.emit(success, "")
        except Exception as e:
            self.finished.emit(False, str(e))


class DynamicBackgroundFrame(QFrame):
    """Enhanced background with dynamic gradient and subtle effects - from main_menu"""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.animation_offset = 0
        self.animation_direction = 1
        
        # Timer for animated background
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_animation)
        self.timer.start(50)
    
    def update_animation(self):
        # Slowly animate the gradient position
        self.animation_offset += 0.2 * self.animation_direction
        
        # Reverse direction at limits
        if self.animation_offset > 30:
            self.animation_direction = -1
        elif self.animation_offset < -30:
            self.animation_direction = 1
            
        self.update()
    
    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        
        # Create dynamic gradient background
        center_x = self.width() // 2 + int(self.animation_offset)
        center_y = self.height() // 2
        radius = max(self.width(), self.height()) * 0.7
        
        # Main gradient
        gradient = QRadialGradient(center_x, center_y, radius)
        gradient.setColorAt(0, QColor(RIT_DARK))
        gradient.setColorAt(0.5, QColor(RIT_BG))
        gradient.setColorAt(1, QColor("#0a0f1c"))  # Darker edge
        
        painter.fillRect(self.rect(), QBrush(gradient))
        
        # Draw subtle hexagonal grid pattern
        painter.setPen(QPen(QColor(RIT_PRIMARY + "15"), 0.5, Qt.SolidLine))  # Very transparent
        
        # Hexagonal grid
        hex_size = 50
        x_offset = 0
        for y in range(-hex_size, self.height() + hex_size, int(hex_size * 0.75)):
            x_offset = (x_offset + hex_size) % (hex_size * 2)
            for x in range(-hex_size + x_offset, self.width() + hex_size, hex_size * 2):
                # Draw hexagon
                points = []
                for i in range(6):
                    angle_rad = 2 * math.pi * i / 6
                    px = x + hex_size * 0.5 * math.cos(angle_rad)
                    py = y + hex_size * 0.5 * math.sin(angle_rad)
                    points.append(QPoint(int(px), int(py)))
                    
                painter.drawPolygon(points)


class IlluminatedText(QLabel):
    """Text with illuminated glow effect - from main_menu"""
    def __init__(self, text, parent=None):
        super().__init__(text, parent)
        
        # Animation properties
        self.glow_intensity = 0
        self.glow_direction = 1
        
        # Start animation
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_glow)
        self.timer.start(50)
    
    def update_glow(self):
        # Update glow intensity
        self.glow_intensity += 0.02 * self.glow_direction
        
        # Reverse direction at limits
        if self.glow_intensity > 1:
            self.glow_direction = -1
        elif self.glow_intensity < 0:
            self.glow_direction = 1
            
        self.update()
    
    def paintEvent(self, event):
        # Create a new painter for this widget
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        
        # Create text gradient
        gradient = QLinearGradient(0, 0, self.width(), 0)
        gradient.setColorAt(0, QColor(RIT_SECONDARY))
        gradient.setColorAt(1, QColor(RIT_ACCENT))
        
        # Set font
        font = self.font()
        painter.setFont(font)
        
        # Create text path
        path = QPainterPath()
        # Fix the text positioning with proper metrics
        metrics = painter.fontMetrics()
        text_width = metrics.horizontalAdvance(self.text())
        x_pos = self.width()/2 - text_width/2
        y_pos = self.height()/2 + metrics.ascent()/2 - 5
        
        path.addText(x_pos, y_pos, font, self.text())
        
        # Fill text with gradient
        painter.setBrush(QBrush(gradient))
        painter.setPen(Qt.NoPen)
        painter.drawPath(path)
        
        # Add dynamic glow effect based on animation
        glow_intensity = 0.3 + (self.glow_intensity * 0.2)  # Subtle pulsing
        for i in range(5):
            painter.setOpacity(glow_intensity - (i * 0.06))
            painter.setPen(QPen(QColor(RIT_ACCENT), 1 + i))
            painter.drawPath(path)


class AnimatedButton(QPushButton):
    """Animated button with hover effects - from main_menu"""
    def __init__(self, text, color_start, color_end, parent=None):
        super().__init__(text, parent)
        self.color_start = color_start
        self.color_end = color_end
        self.setMinimumHeight(60)
        self.setFont(QFont("Segoe UI", 14))
        self.setCursor(Qt.PointingHandCursor)
        
        # Control opacity directly in the paintEvent
        self.glow_value = 0.8
        self.glow_direction = 1
        
        # Timer for pulsing effect
        self.glow_timer = QTimer(self)
        self.glow_timer.timeout.connect(self.update_glow)
        self.glow_timer.start(50)
        
    def update_glow(self):
        # Subtle pulsing effect when idle
        if not self.underMouse():
            self.glow_value += 0.01 * self.glow_direction
            
            if self.glow_value > 1:
                self.glow_direction = -1
            elif self.glow_value < 0.8:
                self.glow_direction = 1
        
        self.update()  # Request repaint
        
    def enterEvent(self, event):
        # Set to full opacity immediately
        self.glow_value = 1.0
        self.update()
        
        # Scale animation on hover with more dynamic effect
        self.hover_scale_anim = QPropertyAnimation(self, b"size")
        self.hover_scale_anim.setDuration(200)
        current_size = self.size()
        self.hover_scale_anim.setStartValue(current_size)
        self.hover_scale_anim.setEndValue(QSize(current_size.width(), current_size.height() + 8))
        self.hover_scale_anim.setEasingCurve(QEasingCurve.OutCubic)
        self.hover_scale_anim.start()
        
        super().enterEvent(event)
        
    def leaveEvent(self, event):
        # Restore original size with smooth animation
        self.leave_scale_anim = QPropertyAnimation(self, b"size")
        self.leave_scale_anim.setDuration(200)
        current_size = self.size()
        self.leave_scale_anim.setStartValue(current_size)
        self.leave_scale_anim.setEndValue(QSize(current_size.width(), 60))
        self.leave_scale_anim.setEasingCurve(QEasingCurve.OutCubic)
        self.leave_scale_anim.start()
        
        super().leaveEvent(event)
        
    def paintEvent(self, event):
        # Custom drawing for better visual appearance
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        
        # Apply opacity directly in the painter
        painter.setOpacity(0.95 + (self.glow_value * 0.05))
        
        # Create gradient based on button state
        if self.underMouse():
            gradient = QLinearGradient(0, 0, self.width(), 0)
            gradient.setColorAt(0, QColor(self.color_end))
            gradient.setColorAt(1, QColor(self.color_start))
        else:
            gradient = QLinearGradient(0, 0, self.width(), 0)
            gradient.setColorAt(0, QColor(self.color_start))
            gradient.setColorAt(1, QColor(self.color_end))
        
        # Draw button background
        painter.setBrush(QBrush(gradient))
        painter.setPen(Qt.NoPen)
        painter.drawRoundedRect(0, 0, self.width(), self.height(), 12, 12)
        
        # Save state before drawing highlight
        painter.save()
        
        # Add subtle glossy highlight effect
        highlight_path = QPainterPath()
        highlight_path.addRoundedRect(QRectF(2, 2, self.width()-4, self.height()/2-4), 10, 10)
        highlight_gradient = QLinearGradient(0, 0, 0, self.height()/2)
        highlight_gradient.setColorAt(0, QColor(255, 255, 255, 40))
        highlight_gradient.setColorAt(1, QColor(255, 255, 255, 0))
        
        painter.setBrush(highlight_gradient)
        painter.drawPath(highlight_path)
        
        # Restore state
        painter.restore()
        
        # Draw text with proper centering
        painter.setPen(QPen(QColor(RIT_TEXT_LIGHT)))
        painter.setFont(self.font())
        painter.drawText(self.rect(), Qt.AlignCenter, self.text())


class WaveEffect(QWidget):
    """Wave animation effect for bottom of card - from main_menu"""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAttribute(Qt.WA_TransparentForMouseEvents)
        self.setAttribute(Qt.WA_NoSystemBackground)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setFixedHeight(80)
        
        # Wave properties
        self.wave_offset = 0
        self.wave_speed = 0.05
        
        # Start wave animation
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_wave)
        self.timer.start(20)  # Update frequency
    
    def update_wave(self):
        self.wave_offset += self.wave_speed
        self.update()
    
    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        
        # Create wave path
        path = QPainterPath()
        
        # Start at bottom left
        path.moveTo(0, self.height())
        
        # Define wave parameters
        amplitude = 15
        period = 200
        wave_height = self.height() - 40
        
        # Calculate wave points
        for x in range(0, self.width(), 2):
            # Two overlapping waves with different phases
            wave1 = math.sin((x + self.wave_offset) * 2 * math.pi / period) * amplitude
            wave2 = math.sin((x + self.wave_offset * 1.5) * 2 * math.pi / (period * 1.5)) * (amplitude * 0.7)
            y = wave_height + wave1 + wave2
            
            path.lineTo(x, y)
        
        # Complete the path to bottom right
        path.lineTo(self.width(), self.height())
        path.lineTo(0, self.height())
        
        # Create gradient for wave
        gradient = QLinearGradient(0, wave_height - amplitude, 0, self.height())
        gradient.setColorAt(0, QColor(RIT_SECONDARY + "30"))
        gradient.setColorAt(1, QColor(RIT_ACCENT + "10"))
        
        # Draw wave
        painter.fillPath(path, QBrush(gradient))
        
        # Draw subtle outline
        painter.setPen(QPen(QColor(RIT_PRIMARY + "20"), 0.5))
        painter.drawPath(path)


class EnhancedInputField(QLineEdit):
    """Custom input field with animation effects"""
    def __init__(self, placeholder="", parent=None):
        super().__init__(parent)
        self.setPlaceholderText(placeholder)
        self.setMinimumHeight(60)
        self.setFont(QFont("Segoe UI", 14))
        
        # Style with modern, clean look
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
        
        # Animation effect when focused
        self.focus_anim = None
    
    def focusInEvent(self, event):
        super().focusInEvent(event)
        
        # Scale animation on focus
        self.focus_anim = QPropertyAnimation(self, b"size")
        self.focus_anim.setDuration(200)
        current_size = self.size()
        self.focus_anim.setStartValue(current_size)
        self.focus_anim.setEndValue(QSize(current_size.width(), current_size.height() + 6))
        self.focus_anim.setEasingCurve(QEasingCurve.OutQuad)
        self.focus_anim.start()
    
    def focusOutEvent(self, event):
        super().focusOutEvent(event)
        
        # Restore original size
        if self.focus_anim:
            self.focus_anim.stop()
        
        self.restore_anim = QPropertyAnimation(self, b"size")
        self.restore_anim.setDuration(200)
        current_size = self.size()
        self.restore_anim.setStartValue(current_size)
        self.restore_anim.setEndValue(QSize(current_size.width(), 60))
        self.restore_anim.setEasingCurve(QEasingCurve.OutQuad)
        self.restore_anim.start()


class RegisterStudentPage(QWidget):
    def __init__(self, main_window=None, stack=None):
        super().__init__()
        self.main_window = main_window
        self.stack = stack or (main_window.stack if main_window else None)
        self.opacity = 0.0  # For fade-in effect
        self.init_ui()
        
        # Trigger fade-in animation after initialization
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
        
        # Logo section (optional - using small logo at the top)
        logo_layout = QHBoxLayout()
        logo_layout.setAlignment(Qt.AlignCenter)
        
        logo_label = QLabel()
        logo_size = 60  # Smaller than main menu
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
        self.title_label = IlluminatedText("Register New Student")
        self.title_label.setFont(QFont("Segoe UI", 30, QFont.Bold))
        self.title_label.setFixedHeight(80)
        self.title_label.setAlignment(Qt.AlignCenter)
        card_layout.addWidget(self.title_label)
        
        # Subtitle
        subtitle = QLabel("Voice Biometric Enrollment")
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
        self.name_input = EnhancedInputField("Full Name")
        self.id_input = EnhancedInputField("Student ID")
        
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
        self.status_label.setVisible(False)  # Hide initially
        
        # Add input fields to layout
        form_layout.addWidget(self.name_input)
        form_layout.addWidget(self.id_input)
        form_layout.addWidget(self.status_label)
        
        card_layout.addLayout(form_layout)
        
        # Button layout
        button_layout = QHBoxLayout()
        button_layout.setSpacing(20)
        
        # Enhanced animated buttons with gradients
        self.back_button = AnimatedButton("Back", "#64748B", RIT_PRIMARY)
        self.register_button = AnimatedButton("Register", RIT_SECONDARY, RIT_ACCENT)
        
        # Connect button signals - maintaining functionality
        self.back_button.clicked.connect(self.go_back)
        self.register_button.clicked.connect(self.register_student)
        
        # Add buttons to layout
        button_layout.addWidget(self.back_button)
        button_layout.addWidget(self.register_button)
        
        card_layout.addLayout(button_layout)
        
        # Add wave effect at the bottom of the card
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

    def go_back(self):
        """Navigate back to the main menu."""
        print("Go back button clicked")
        if self.stack:
            print("Stack found, starting fade out")
            self.fade_out()
        else:
            print("Stack is None, cannot navigate back")

    def fade_in(self):
        """Fade in animation for smooth transition."""
        self.opacity = 0.0
        self.setStyleSheet(f"background-color: rgba(0, 0, 0, {self.opacity});")
        
        # Create fade-in animation
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
        print("Animation completed, attempting navigation")
        if self.stack:
            print(f"Setting stack index to 0, current index: {self.stack.currentIndex()}")
            self.stack.setCurrentIndex(1)
        else:
            print("Stack is still None, navigation failed")

    def register_student(self):
        """Handle student registration process."""
        # Get input values
        student_name = self.name_input.text().strip()
        student_id = self.id_input.text().strip()
        
        # Validate inputs
        if not student_name:
            self.show_status("Please enter student name", is_error=True)
            return
        
        if not student_id:
            self.show_status("Please enter student ID", is_error=True)
            return
        
        # Show status
        self.show_status("Registering student...")
        
        try:
            # First register in database
            register_student_db(student_name, student_id)

            recording_dialog = VoiceRecordingDialog(student_name, student_id, self)
            result = recording_dialog.exec_()
            
            # Launch voice recording dialog
            if result == QDialog.Accepted and recording_dialog.recording_complete:
            # Use your existing function to process the voice samples
                self.show_status("Processing voice profile...")
                
                try:
                    # Since the individual samples were already recorded using your backend function,
                    # just generate the embeddings now
                    embedding_success = generate_speaker_embeddings()
                    
                    if not embedding_success:
                        self.show_status("Voice processing failed", is_error=True)
                        rollback_student_registration(student_id)
                        return
                    
                    # Success!
                    self.show_status("Student registered successfully!")
                    
                    # Clear fields for next entry
                    self.name_input.clear()
                    self.id_input.clear()
                        
                except Exception as e:
                    self.show_status(f"Voice processing failed: {str(e)}", is_error=True)
                    rollback_student_registration(student_id)
            else:
                # User canceled or didn't complete all samples
                self.show_status("Voice enrollment canceled", is_error=True)
                rollback_student_registration(student_id)
            
        except Exception as e:
            self.show_status(f"Registration failed: {str(e)}", is_error=True)
            # Attempt rollback
            try:
                rollback_student_registration(student_id)
            except:
                pass

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

    def resizeEvent(self, event):
        """Handle widget resize events to update particle system."""
        super().resizeEvent(event)
        # Update particle system geometry to match new size
        if hasattr(self, 'particles'):
            self.particles.setGeometry(0, 0, self.width(), self.height())