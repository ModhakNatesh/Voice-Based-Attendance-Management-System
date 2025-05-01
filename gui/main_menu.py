# pages/main_menu.py

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QPushButton, QStackedWidget,
    QGraphicsOpacityEffect, QHBoxLayout, QSpacerItem, QSizePolicy,
    QFrame  
)
from PyQt5.QtCore import Qt, QPropertyAnimation, QEasingCurve, QTimer, QSize, QPoint, QRect, QRectF, pyqtProperty
from PyQt5.QtGui import QFont, QPixmap, QPainter, QColor, QBrush, QPen, QLinearGradient, QRadialGradient, QPainterPath
import os
import random
import math

# Import RIT Theme Colors from SplashScreen
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
    """Enhanced particle system with dynamic behavior - reused from splash screen"""
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


class DynamicBackgroundFrame(QFrame):
    """Enhanced background with dynamic gradient and subtle effects - from splash screen"""
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


# First, fix the IlluminatedText class
class IlluminatedText(QLabel):
    """Text with illuminated glow effect - from splash screen"""
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
        
        # Let Qt handle painter cleanup automatically

# Fix AnimatedButton class
class AnimatedButton(QPushButton):
    def __init__(self, text, color_start, color_end, parent=None):
        super().__init__(text, parent)
        self.color_start = color_start
        self.color_end = color_end
        self.setMinimumHeight(60)
        self.setFont(QFont("Segoe UI", 14))
        self.setCursor(Qt.PointingHandCursor)
        
        # IMPORTANT: Don't use QGraphicsOpacityEffect - it's causing the painter issues
        # Instead, we'll control opacity directly in the paintEvent
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

# Fix the WaveEffect class
class WaveEffect(QWidget):
    """Wave animation effect for bottom of card - from splash screen"""
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

# Fix MainMenu class - most importantly, remove opacity effect
class MainMenu(QWidget):
    def __init__(self, stack=None):
        super().__init__()
        
        # Store reference to stack widget
        self.stack = stack

        self.setWindowTitle("Voice Based Attendance System - Main Menu")
        self.setGeometry(400, 100, 800, 700)  # Larger dimensions for better layout
        
        # IMPORTANT: Remove the opacity effect and directly implement fade-in
        self.opacity = 0.0
        
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
        content_layout.setSpacing(20)
        content_layout.setAlignment(Qt.AlignCenter)
        
        # Logo section (keep size and position as requested)
        logo_layout = QHBoxLayout()
        logo_layout.setAlignment(Qt.AlignCenter)
        
        logo_label = QLabel()
        logo_size = 100  # Keep original size
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
            
            # Create gradient for logo
            gradient = QLinearGradient(0, 0, logo_size, logo_size)
            gradient.setColorAt(0, QColor(RIT_PRIMARY))
            gradient.setColorAt(1, QColor(RIT_ACCENT))
            
            # Draw circle with gradient
            painter.setBrush(QBrush(gradient))
            painter.setPen(QPen(Qt.NoPen))
            painter.drawEllipse(5, 5, logo_size-10, logo_size-10)
            
            # Draw "RIT" text
            painter.setPen(QPen(QColor(RIT_TEXT_LIGHT)))
            painter.setFont(QFont("Arial", int(logo_size/3), QFont.Bold))
            painter.drawText(logo_pixmap.rect(), Qt.AlignCenter, "RIT")
            painter.end()  # End painter for QPixmap - this is needed for pixmap
            
            logo_label.setPixmap(logo_pixmap)
        
        logo_layout.addWidget(logo_label)
        content_layout.addLayout(logo_layout)
        
        # Create modern card with frosted glass effect (similar to splash screen)
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
        card_layout.setContentsMargins(40, 50, 40, 30)
        card_layout.setSpacing(30)
        
        # Title with illuminated effect (like splash screen)
        self.title_label = IlluminatedText("VBAMS")
        self.title_label.setFont(QFont("Segoe UI", 40, QFont.Bold))
        self.title_label.setFixedHeight(80)
        self.title_label.setAlignment(Qt.AlignCenter)
        card_layout.addWidget(self.title_label)
        
        # Subtitle
        subtitle = QLabel("Voice Based Attendance Management System")
        subtitle.setFont(QFont("Segoe UI", 20, QFont.Light))
        subtitle.setStyleSheet(f"""
            color: {RIT_LIGHT};
            letter-spacing: 2px;
        """)
        subtitle.setAlignment(Qt.AlignCenter)
        card_layout.addWidget(subtitle)
        
        # Description text with subtle styling
        description = QLabel("Secure authentication through voice biometrics")
        description.setFont(QFont("Segoe UI", 14, QFont.Light))
        description.setStyleSheet(f"color: {RIT_LIGHT}80;")
        description.setAlignment(Qt.AlignCenter)
        card_layout.addWidget(description)
        
        # Add decorative separator
        separator = QFrame()
        separator.setFrameShape(QFrame.HLine)
        separator.setFixedHeight(1)
        separator.setStyleSheet(f"background-color: {RIT_PRIMARY}30;")
        card_layout.addWidget(separator)
        
        # Button section
        button_layout = QVBoxLayout()
        button_layout.setSpacing(20)
        
        # Enhanced animated buttons with gradients
        self.attendance_btn = AnimatedButton("Mark Attendance (Voice)", RIT_SECONDARY, RIT_ACCENT)
        self.register_btn = AnimatedButton("Register New Student", RIT_PRIMARY, RIT_SECONDARY)
        self.admin_login_btn = AnimatedButton("Admin Panel", RIT_ACCENT, "#9061F9")  # Lighter purple

        # Connect Buttons (maintaining functionality)
        self.attendance_btn.clicked.connect(self.go_to_attendance)
        self.register_btn.clicked.connect(self.go_to_register)
        self.admin_login_btn.clicked.connect(self.go_to_admin_login)

        # Add buttons to layout
        button_layout.addWidget(self.attendance_btn)
        button_layout.addWidget(self.register_btn)
        button_layout.addWidget(self.admin_login_btn)
        
        card_layout.addLayout(button_layout)
        
        # Add wave effect at the bottom of the card
        wave_effect = WaveEffect()
        card_layout.addWidget(wave_effect)
        
        # Bottom credit (matching splash screen)
        credit_label = QLabel("© Rajeev Institute of Technology")
        credit_label.setFont(QFont("Segoe UI", 11))
        credit_label.setStyleSheet(f"color: {RIT_LIGHT}90;")
        credit_label.setAlignment(Qt.AlignCenter)
        card_layout.addWidget(credit_label)
        
        # Add card to content container
        content_layout.addWidget(card_frame)
        
        # Add content to background frame
        bg_layout.addWidget(content_container)
        
    def resizeEvent(self, event):
        """Handle resize events to adjust particle area"""
        super().resizeEvent(event)
        if hasattr(self, 'particles'):
            self.particles.setGeometry(0, 0, self.width(), self.height())

    def paintEvent(self, event):
        """Handle custom painting for fade effect"""
        super().paintEvent(event)
        # If we're fading in, paint an overlay
        if self.opacity > 0:
            painter = QPainter(self)
            painter.setRenderHint(QPainter.Antialiasing)
            
            # Create semi-transparent overlay for fade effect
            color = QColor(0, 0, 0, int(255 * self.opacity))
            painter.fillRect(self.rect(), color)

    def fade_in(self):
        """Create fade-in animation effect without using QGraphicsOpacityEffect"""
        self.opacity = 1.0  # Start fully opaque (black)
        
        # Use animation to control the custom opacity
        self.fade_anim = QPropertyAnimation(self, b"_opacity")
        self.fade_anim.setDuration(800)
        self.fade_anim.setStartValue(1.0)
        self.fade_anim.setEndValue(0.0)
        self.fade_anim.setEasingCurve(QEasingCurve.InOutQuad)
        self.fade_anim.start()
    
    def get_opacity(self):
        return self.opacity
        
    def set_opacity(self, value):
        self.opacity = value
        self.update()  # Trigger repaint
        
    # Property for animation to target
    _opacity = pyqtProperty(float, get_opacity, set_opacity)
    
    def fade_out(self, callback):
        """Create fade-out animation effect without QGraphicsOpacityEffect"""
        self.opacity = 0.0  # Start transparent
        
        # Use animation to control the custom opacity
        self.fade_out_anim = QPropertyAnimation(self, b"_opacity")
        self.fade_out_anim.setDuration(300)
        self.fade_out_anim.setStartValue(0.0)
        self.fade_out_anim.setEndValue(1.0)
        self.fade_out_anim.setEasingCurve(QEasingCurve.InOutQuad)
        self.fade_out_anim.finished.connect(callback)
        self.fade_out_anim.start()

    # Navigation methods remain the same
    def go_to_attendance(self):
        if self.stack is None:
            print("Error: Stack widget not set")
            return
            
        def navigate():
            from gui.attendance_page import AttendancePage
            self.attendance_page = AttendancePage()
            self.stack.addWidget(self.attendance_page)
            self.stack.setCurrentWidget(self.attendance_page)
        
        self.fade_out(navigate)

    def go_to_register(self):
        if self.stack is None:
            print("Error: Stack widget not set")
            return
            
        def navigate():
            from gui.register_student import RegisterStudentPage
            self.register_page = RegisterStudentPage(main_window=self, stack=self.stack)
            self.stack.addWidget(self.register_page)
            self.stack.setCurrentWidget(self.register_page)
        
        self.fade_out(navigate)

    def go_to_admin_login(self):
        if self.stack is None:
            print("Error: Stack widget not set")
            return
            
        def navigate():
            from gui.admin_login_page import AdminLoginPage
            self.admin_login_page = AdminLoginPage(stack=self.stack)
            self.stack.addWidget(self.admin_login_page)
            self.stack.setCurrentWidget(self.admin_login_page)
        
        self.fade_out(navigate)