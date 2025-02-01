from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
    QTextEdit, QPushButton, QApplication
)
from PyQt6.QtCore import Qt, QThread, pyqtSignal
from PyQt6.QtGui import QColor, QTextCharFormat, QTextCursor
from src.utils.colors import Colors

class OutputRedirector:
    def __init__(self, text_widget):
        self.text_widget = text_widget
        self.color_map = {
            Colors.SYSTEM: QColor(0, 255, 255),    # Cyan
            Colors.ERROR: QColor(255, 0, 0),       # Red
            Colors.SUCCESS: QColor(0, 255, 0),     # Green
            Colors.WARNING: QColor(255, 255, 0),   # Yellow
            Colors.FIRST_AGENT: QColor(173, 216, 230),    # Light blue
            Colors.SECOND_AGENT: QColor(144, 238, 144),   # Light green
            Colors.ANALYZER: QColor(255, 182, 193),       # Light magenta
            Colors.SUMMARY: QColor(0, 255, 255)           # Cyan
        }
        self.current_color = None

    def write(self, text):
        cursor = self.text_widget.textCursor()
        format = QTextCharFormat()
        
        if any(color in text for color in self.color_map.keys()):
            for color_code, qt_color in self.color_map.items():
                if color_code in text:
                    format.setForeground(qt_color)
                    text = text.replace(color_code, '')
                    break
        
        cursor.movePosition(QTextCursor.MoveOperation.End)
        cursor.insertText(text, format)
        self.text_widget.setTextCursor(cursor)
        self.text_widget.ensureCursorVisible()

    def flush(self):
        pass

class AssistantThread(QThread):
    finished = pyqtSignal()
    error = pyqtSignal(str)

    def __init__(self, assistant, input_text):
        super().__init__()
        self.assistant = assistant
        self.input_text = input_text

    def run(self):
        try:
            self.assistant.process_input(self.input_text)
            self.finished.emit()
        except Exception as e:
            self.error.emit(str(e))
            self.finished.emit()

class MainWindow(QMainWindow):
    def __init__(self, assistant):
        super().__init__()
        self.assistant = assistant
        self.init_ui()

    def init_ui(self):
        self.setWindowTitle('AI Assistant')
        self.setGeometry(100, 100, 800, 600)

        # Create central widget and layout
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)

        # Create output text area
        self.output_text = QTextEdit()
        self.output_text.setReadOnly(True)
        layout.addWidget(self.output_text)

        # Create input area
        input_layout = QHBoxLayout()
        self.input_text = QTextEdit()
        self.input_text.setMaximumHeight(100)
        input_layout.addWidget(self.input_text)

        # Create send button
        send_button = QPushButton('Send')
        send_button.clicked.connect(self.send_message)
        send_button.setMaximumWidth(100)
        input_layout.addWidget(send_button)

        layout.addLayout(input_layout)

        # Redirect stdout to our text widget
        import sys
        self.redirector = OutputRedirector(self.output_text)
        sys.stdout = self.redirector

    def send_message(self):
        input_text = self.input_text.toPlainText().strip()
        if not input_text:
            return

        self.input_text.clear()
        self.input_text.setEnabled(False)

        # Process input in a separate thread
        self.thread = AssistantThread(self.assistant, input_text)
        self.thread.finished.connect(self.on_response_complete)
        self.thread.error.connect(self.on_error)
        self.thread.start()

    def on_error(self, error_msg):
        Colors.print(f"Error: {error_msg}", Colors.ERROR)

    def on_response_complete(self):
        self.input_text.setEnabled(True)
        self.input_text.setFocus()

    def closeEvent(self, event):
        # Stop any running threads
        if hasattr(self, 'thread') and self.thread.isRunning():
            self.thread.terminate()
            self.thread.wait()
        
        # Restore stdout
        import sys
        sys.stdout = sys.__stdout__
        event.accept() 