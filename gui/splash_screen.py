from PyQt5.QtWidgets import (
    QWidget, QLabel, QVBoxLayout, QApplication, QProgressBar,
    QGraphicsOpacityEffect, QDesktopWidget, QHBoxLayout, QFrame, QStackedWidget
)
from PyQt5.QtCore import Qt, QTimer, QPropertyAnimation, QEasingCurve, QSize, pyqtSignal, QPoint, QRect, QRectF
from PyQt5.QtGui import QFont, QColor, QPixmap, QPainter, QPen, QBrush, QLinearGradient, QRadialGradient, QPainterPath

import os
import sys
import math
import random  # Ensure random is imported at the top level

# RIT Theme Colors (matching admin_dashboard)
RIT_PRIMARY = "#1E3A8A"     # Deep blue for primary elements
RIT_SECONDARY = "#4F46E5"   # Bright blue for accent and highlights
RIT_ACCENT = "#7C3AED"      # Purple accent for special elements
RIT_LIGHT = "#F1F5F9"       # Light background
RIT_DARK = "#1E293B"        # Dark background
RIT_TEXT_LIGHT = "#F8FAFC"  # Light text
RIT_TEXT_DARK = "#334155"   # Dark text
RIT_SUCCESS = "#10B981"     # Green for success
RIT_BG = "#0F172A"          # Main background

class FloatingParticle(QWidget):
    """Enhanced particle system with more dynamic behavior"""
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
                rad_angle = p['angle'] * (math.pi / 180)  # Use math.pi instead of hardcoded value
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
                
                rad_angle = p['angle'] * (math.pi / 180)  # Use math.pi instead of hardcoded value
                x2 = p['x'] + p['size'] * math.cos(rad_angle)
                y2 = p['y'] - p['size'] * math.sin(rad_angle)
                
                painter.drawLine(int(p['x']), int(p['y']), int(x2), int(y2))

class GlassEffectProgressBar(QProgressBar):
    """Custom progress bar with glass effect and dynamic animations"""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setRange(0, 100)
        self.setValue(0)
        self.setTextVisible(False)  # Hide default text
        self.setFixedSize(400, 6)  # Even thinner bar for ultra-modern look
        
        # Pulse animation for loading effect
        self.pulse_timer = QTimer(self)
        self.pulse_timer.timeout.connect(self.pulse_animation)
        self.pulse_timer.start(50)
        self.pulse_offset = 0
        
    def pulse_animation(self):
        self.pulse_offset = (self.pulse_offset + 5) % 200
        self.update()
        
    def paintEvent(self, event):
        # Custom drawing for progress bar
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        
        # Draw background with rounded corners
        background_color = QColor(RIT_DARK)
        background_color.setAlpha(100)
        painter.setPen(Qt.NoPen)
        painter.setBrush(QBrush(background_color))
        painter.drawRoundedRect(0, 0, self.width(), self.height(), 3, 3)
        
        # Calculate progress width
        progress_width = int(self.width() * (self.value() / 100))
        
        if progress_width > 0:
            # Create shimmer effect gradient
            gradient = QLinearGradient(self.pulse_offset - 100, 0, self.pulse_offset + 100, 0)
            base_color_start = QColor(RIT_SECONDARY)
            base_color_end = QColor(RIT_ACCENT)
            
            # Main gradient
            gradient.setColorAt(0, base_color_start)
            gradient.setColorAt(0.5, base_color_end)
            gradient.setColorAt(1, base_color_start)
            
            # Shimmer effect - add highlight
            highlight_pos = (self.pulse_offset % 200) / 200.0
            if highlight_pos < 0.9:  # Add highlight position
                shimmer_color = QColor(RIT_TEXT_LIGHT)
                shimmer_color.setAlpha(120)
                gradient.setColorAt(highlight_pos, shimmer_color)
            
            # Draw progress with gradient
            painter.setBrush(QBrush(gradient))
            painter.drawRoundedRect(0, 0, progress_width, self.height(), 3, 3)
            
            # Draw glow effect
            glow_path = QPainterPath()
            glow_path.addRoundedRect(QRectF(0, 0, progress_width, self.height()), 3, 3)
            
            # Set blur and opacity for glow
            for i in range(3):
                painter.setOpacity(0.15 - (i * 0.05))
                painter.setPen(QPen(QColor(RIT_ACCENT), 1 + i))
                painter.drawPath(glow_path)
            
        # Draw text above progress bar
        painter.setOpacity(1.0)
        painter.setPen(QColor(RIT_TEXT_LIGHT))
        painter.setFont(QFont("Segoe UI", 9))
        text_rect = QRect(0, -20, self.width(), 20)
        painter.drawText(text_rect, Qt.AlignRight | Qt.AlignVCenter, f"{self.value()}%")

class DynamicBackgroundFrame(QFrame):
    """Enhanced background with dynamic gradient and subtle effects"""
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
        center_x = self.width() // 2 + int(self.animation_offset)  # Convert to int
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
                    angle_rad = 2 * math.pi * i / 6  # Use math.pi instead of hardcoded value
                    px = x + hex_size * 0.5 * math.cos(angle_rad)
                    py = y + hex_size * 0.5 * math.sin(angle_rad)
                    points.append(QPoint(int(px), int(py)))
                    
                painter.drawPolygon(points)

class WaveEffect(QWidget):
    """Wave animation effect for bottom of splash screen"""
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

class IlluminatedText(QLabel):
    """Text with illuminated glow effect"""
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
        font = self.font()  # Get font before setting it
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

class SplashScreen(QWidget):
    # Signal to indicate splash screen has completed
    finished = pyqtSignal()
    
    def __init__(self):
        super().__init__()
        
        # Make the splash window regular size rather than fullscreen for better stability
        self.setMinimumSize(800, 600)
        
        self.setWindowTitle("VBAMS - Voice Based Attendance Management System")
        self.setStyleSheet("background-color: transparent;")
        
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint)
        self.setAttribute(Qt.WA_TranslucentBackground)
        
        # Animation properties
        self.counter = 0
        self.progress_value = 0
        
        # For tracking active animations
        self.active_animations = []
        
        # Initialize UI elements
        self.init_ui()

    def init_ui(self):
        # Main layout
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        self.setWindowTitle("VBAMS - Voice Based Attendance Management System")

        # Background frame with enhanced dynamic gradient
        self.bg_frame = DynamicBackgroundFrame()
        main_layout.addWidget(self.bg_frame)
        
        # Layout for background frame
        bg_layout = QVBoxLayout(self.bg_frame)
        bg_layout.setContentsMargins(0, 0, 0, 0)
        bg_layout.setSpacing(0)
        
        # Add enhanced particle effect
        self.particles = FloatingParticle(self.bg_frame)
        self.particles.setGeometry(0, 0, self.width(), self.height())
        
        # Content container (center of screen)
        content_container = QWidget()
        content_container.setStyleSheet("background-color: transparent;")
        content_layout = QVBoxLayout(content_container)
        content_layout.setContentsMargins(50, 50, 50, 50)
        content_layout.setSpacing(30)
        content_layout.setAlignment(Qt.AlignCenter)
        
        # Logo section
        logo_layout = QHBoxLayout()
        logo_layout.setAlignment(Qt.AlignCenter)
        
        logo_label = QLabel()
        logo_size = 80  # Slightly smaller than main menu for splash screen
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
            painter.setPen(Qt.NoPen)
            painter.drawEllipse(5, 5, logo_size-10, logo_size-10)
            
            painter.setPen(QPen(QColor(RIT_TEXT_LIGHT)))
            painter.setFont(QFont("Arial", int(logo_size/3), QFont.Bold))
            painter.drawText(logo_pixmap.rect(), Qt.AlignCenter, "RIT")
            painter.end()
            
            logo_label.setPixmap(logo_pixmap)
        
        logo_layout.addWidget(logo_label)
        
        # Create modern card with frosted glass effect
        card_frame = QFrame()
        card_frame.setObjectName("cardFrame")
        card_frame.setStyleSheet(f"""
            #cardFrame {{
                background-color: {RIT_BG}60;
                border: 1px solid {RIT_PRIMARY}30;
                border-radius: 25px;
            }}
        """)
        card_layout = QVBoxLayout(card_frame)
        card_layout.setContentsMargins(50, 30, 50, 30)  # Reduced top/bottom padding
        card_layout.setSpacing(20)
        
        # Add logo at the top of card
        card_layout.addLayout(logo_layout)
        
        # Title section with enhanced effects
        title_container = QWidget()
        title_layout = QVBoxLayout(title_container)
        title_layout.setSpacing(10)
        title_layout.setAlignment(Qt.AlignCenter)
        
        # Create illuminated title with enhanced effect
        self.title_label = IlluminatedText("VBAMS")
        self.title_label.setFont(QFont("Segoe UI", 45, QFont.Bold))  # Slightly smaller font
        self.title_label.setFixedHeight(70)
        self.title_label.setAlignment(Qt.AlignCenter)
        title_layout.addWidget(self.title_label)
        
        # Subtitle with improved visibility
        self.subtitle_label = QLabel("Voice Based Attendance Management System")
        self.subtitle_label.setFont(QFont("Segoe UI", 16, QFont.Light))
        self.subtitle_label.setStyleSheet(f"""
            color: {RIT_LIGHT};
            letter-spacing: 1.5px;
        """)
        self.subtitle_label.setAlignment(Qt.AlignCenter)
        title_layout.addWidget(self.subtitle_label)
        
        card_layout.addWidget(title_container)
        
        # Add decorative separator
        separator = QFrame()
        separator.setFrameShape(QFrame.HLine)
        separator.setFixedHeight(1)
        separator.setStyleSheet(f"background-color: {RIT_PRIMARY}30;")
        card_layout.addWidget(separator)
        
        # Loading section with improved visuals
        loading_container = QWidget()
        loading_layout = QVBoxLayout(loading_container)
        loading_layout.setSpacing(15)
        
        # Status message with clean, modern font
        self.loading_label = QLabel("Initializing system...")
        self.loading_label.setFont(QFont("Segoe UI", 12, QFont.Light))
        self.loading_label.setStyleSheet(f"""
            color: {RIT_LIGHT};
            letter-spacing: 1px;
        """)
        self.loading_label.setAlignment(Qt.AlignCenter)
        loading_layout.addWidget(self.loading_label)
        
        # Loading progress bar with enhanced glass effect
        self.progress = GlassEffectProgressBar()
        loading_layout.addWidget(self.progress, 0, Qt.AlignCenter)
        
        card_layout.addWidget(loading_container)
        
        # Bottom info section
        footer_container = QWidget()
        footer_layout = QVBoxLayout(footer_container)
        footer_layout.setSpacing(5)
        
        footer_layout.addStretch()
        
        # Version with clean typography
        version_label = QLabel("Version 1.0.0")
        version_label.setFont(QFont("Segoe UI", 9))
        version_label.setStyleSheet(f"color: {RIT_SECONDARY}90;")
        version_label.setAlignment(Qt.AlignCenter)
        footer_layout.addWidget(version_label)
        
        # Credit label with improved visibility
        credit_label = QLabel("© Rajeev Institute of Technology")
        credit_label.setFont(QFont("Segoe UI", 11))
        credit_label.setStyleSheet(f"color: {RIT_LIGHT}90;")
        credit_label.setAlignment(Qt.AlignCenter)
        footer_layout.addWidget(credit_label)
        
        card_layout.addWidget(footer_container)
        
        # Add wave effect at the bottom of the card
        wave_effect = WaveEffect()
        card_layout.addWidget(wave_effect)
        
        # Add card to content container
        content_layout.addWidget(card_frame)
        
        # Add content container to background layout
        bg_layout.addWidget(content_container)
        
        # Center in screen
        self.center()
    
    def center(self):
        """Center the window on screen"""
        screen = QDesktopWidget().screenGeometry()
        size = self.geometry()
        self.move(int((screen.width() - size.width()) / 2),
                 int((screen.height() - size.height()) / 2))
    
    def resizeEvent(self, event):
        """Handle resize events to adjust particle area"""
        super().resizeEvent(event)
        if hasattr(self, 'particles'):
            self.particles.setGeometry(0, 0, self.width(), self.height())
    
    def start_animation(self, stack):
        """Start loading animation and transition to main menu"""
        # Start the progress timer with smoother transitions
        self.timer = QTimer(self)
        self.timer.timeout.connect(lambda: self.update_progress(stack))
        self.timer.start(25)  # Faster updates for smoother animation
        
        # Show the widget before animation
        self.show()
        
        # Wait a moment before starting fade-in
        QTimer.singleShot(100, self.fade_in)
        
    def update_progress(self, stack):
        """Update progress bar value with smoother, more natural animation"""
        if self.progress_value < 100:
            # Use a sine function to create more natural acceleration/deceleration
            # Start slower, then speed up in the middle, then slow down at the end
            stage = self.progress_value / 100.0
            
            # Calculate increment based on position
            if stage < 0.2:
                # Slow start - gradually accelerate
                increment = 0.3 + (stage * 3)
            elif stage > 0.8:
                # Slow finish - gradually decelerate
                increment = 1.3 - ((stage - 0.8) * 3)
            else:
                # Steady middle pace
                increment = 1.0
                
            self.progress_value = min(100, self.progress_value + increment)
            self.progress.setValue(int(self.progress_value))
            
            # Update loading text with more frequent, smoother transitions
            loading_texts = [
                "Initializing system components...",
                "Configuring voice recognition engine...",
                "Setting up neural processing units...",
                "Optimizing system parameters...",
                "Connecting to attendance database...",
                "Finalizing system preparation..."
            ]
            
            # Update loading text based on progress with smoother transitions
            text_index = min(len(loading_texts) - 1, int(stage * len(loading_texts)))
            
            # Only update text when changing to avoid flickering
            if self.loading_label.text() != loading_texts[text_index]:
                # Simple text change instead of animation to avoid QPainter issues
                self.loading_label.setText(loading_texts[text_index])
        else:
            # Stop timer when progress reaches 100%
            self.timer.stop()
            
            # Show complete message briefly before transitioning
            self.loading_label.setText("System Ready")
            
            # Delay before transitioning to main screen
            QTimer.singleShot(800, lambda: self.transition_to_main(stack))
    
    def transition_to_main(self, stack):
        """Safe transition to main screen using QPropertyAnimation"""
        # Create fade-out animation
        self.fade_out_anim = QPropertyAnimation(self, b"windowOpacity")
        self.fade_out_anim.setDuration(1000)
        self.fade_out_anim.setStartValue(1.0)
        self.fade_out_anim.setEndValue(0.0)
        self.fade_out_anim.setEasingCurve(QEasingCurve.InOutQuad)
        
        # Connect signal to handle completion
        self.fade_out_anim.finished.connect(lambda: stack.setCurrentIndex(1))
        self.fade_out_anim.start()
        
    def fade_in(self):
        """Create enhanced fade-in animation effect using QPropertyAnimation"""
        self.setWindowOpacity(0.0)
        
        # Use a single property animation
        self.fade_anim = QPropertyAnimation(self, b"windowOpacity")
        self.fade_anim.setDuration(1000)
        self.fade_anim.setStartValue(0.0)
        self.fade_anim.setEndValue(1.0)
        self.fade_anim.setEasingCurve(QEasingCurve.InOutQuad)
        self.fade_anim.start()

def main():
    """Main function to initialize the application"""
    app = QApplication(sys.argv)
    
    # Create a stacked widget to hold both splash screen and main app
    main_stack = QStackedWidget()
    
    # Create and add splash screen
    splash = SplashScreen()
    main_stack.addWidget(splash)
    
    # Create a placeholder for the main application window
    # This would be replaced with your actual main application
    main_window = QWidget()
    main_layout = QVBoxLayout(main_window)
    
    # Simple main window content for demonstration
    welcome_label = QLabel("VBAMS - Voice Based Attendance Management System")
    welcome_label.setFont(QFont("Segoe UI", 20, QFont.Bold))
    welcome_label.setStyleSheet(f"color: {RIT_TEXT_LIGHT};")
    welcome_label.setAlignment(Qt.AlignCenter)
    
    # Add main content to layout
    main_layout.addWidget(welcome_label)
    main_layout.setAlignment(Qt.AlignCenter)
    
    # Style main window
    main_window.setStyleSheet(f"""
        background-color: {RIT_BG};
        color: {RIT_TEXT_LIGHT};
    """)
    
    # Add main window to stack
    main_stack.addWidget(main_window)
    
    # Start with splash screen (index 0)
    main_stack.setCurrentIndex(0)
    
    # Show stacked widget and start splash animation
    main_stack.show()
    splash.start_animation(main_stack)
    
    # Connect the finished signal from splash to show main window
    splash.finished.connect(lambda: main_stack.setCurrentIndex(1))
    
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()