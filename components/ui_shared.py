from PyQt5.QtWidgets import QWidget, QVBoxLayout, QLabel, QGraphicsDropShadowEffect
from PyQt5.QtCore import Qt, pyqtSignal, QTimer, QPropertyAnimation, QEasingCurve
from PyQt5.QtGui import QPainter, QColor, QPen, QFont
from styles.theme import PRIMARY_BLUE, LIGHT_BLUE

class SpinnerWidget(QWidget):
    """Custom animated spinner widget"""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedSize(60, 60)
        self.angle = 0
        self.timer = QTimer(self)
        self.timer.timeout.connect(self._rotate)
        
    def start(self):
        self.timer.start(30)
        
    def stop(self):
        self.timer.stop()
        
    def _rotate(self):
        self.angle = (self.angle + 10) % 360
        self.update()
        
    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        
        # Draw background circle
        pen = QPen(QColor(LIGHT_BLUE))
        pen.setWidth(5)
        pen.setCapStyle(Qt.RoundCap)
        painter.setPen(pen)
        painter.drawArc(5, 5, 50, 50, 0, 360 * 16)
        
        # Draw spinning arc
        pen.setColor(QColor(PRIMARY_BLUE))
        painter.setPen(pen)
        painter.drawArc(5, 5, 50, 50, self.angle * 16, 90 * 16)


class LoadingOverlay(QWidget):
    """Loading overlay with spinner animation"""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAttribute(Qt.WA_TransparentForMouseEvents, False)
        self.setStyleSheet("""
            QWidget {
                background-color: rgba(240, 245, 250, 0.95);
            }
        """)
        
        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignCenter)
        layout.setSpacing(20)
        
        # Container for centered content with card effect
        self.card = QWidget()
        self.card.setFixedSize(300, 180)
        self.card.setStyleSheet(f"""
            QWidget {{
                background-color: white;
                border-radius: 16px;
                border: 1px solid {LIGHT_BLUE};
            }}
        """)
        
        # Add shadow effect to card
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(25)
        shadow.setXOffset(0)
        shadow.setYOffset(4)
        shadow.setColor(QColor(0, 0, 0, 40))
        self.card.setGraphicsEffect(shadow)
        
        card_layout = QVBoxLayout(self.card)
        card_layout.setAlignment(Qt.AlignCenter)
        card_layout.setSpacing(15)
        
        # Custom spinner widget
        self.spinner = SpinnerWidget()
        
        # Loading text
        self.loading_text = QLabel("Processing...")
        self.loading_text.setAlignment(Qt.AlignCenter)
        self.loading_text.setStyleSheet(f"""
            QLabel {{
                color: {PRIMARY_BLUE};
                font-size: 16px;
                font-weight: 600;
                background: transparent;
                border: none;
            }}
        """)
        
        # Subtext
        self.subtext = QLabel("Please wait")
        self.subtext.setAlignment(Qt.AlignCenter)
        self.subtext.setStyleSheet(f"""
            QLabel {{
                color: #666;
                font-size: 12px;
                background: transparent;
                border: none;
            }}
        """)
        
        card_layout.addWidget(self.spinner, alignment=Qt.AlignCenter)
        card_layout.addWidget(self.loading_text)
        card_layout.addWidget(self.subtext)
        
        layout.addWidget(self.card, alignment=Qt.AlignCenter)
        
        self._base_message = "Processing"
        self.dot_count = 0
        self.dot_timer = None
        
        self.hide()
    
    def start_animation(self):
        """Start the loading animation"""
        self.dot_count = 0
        self.spinner.start()
        
        # Animated dots timer
        self.dot_timer = QTimer(self)
        self.dot_timer.timeout.connect(self._update_dots)
        self.dot_timer.start(400)
        
        self.show()
        self.raise_()
    
    def _update_dots(self):
        """Update animated dots in loading text"""
        self.dot_count = (self.dot_count + 1) % 4
        dots = "." * self.dot_count
        self.loading_text.setText(f"{self._base_message}{dots}")
    
    def stop_animation(self):
        """Stop the loading animation"""
        self.spinner.stop()
        if self.dot_timer:
            self.dot_timer.stop()
            self.dot_timer = None
        self.hide()
    
    def set_message(self, message: str, subtext: str = "Please wait"):
        """Set custom loading message"""
        self._base_message = message
        self.loading_text.setText(message)
        self.subtext.setText(subtext)


class InteractiveLabel(QLabel):
    """Label that emits click coordinates"""
    clicked = pyqtSignal(int, int, bool)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setCursor(Qt.CrossCursor)

    def mousePressEvent(self, event):
        is_left = event.button() == Qt.LeftButton
        self.clicked.emit(event.x(), event.y(), is_left)