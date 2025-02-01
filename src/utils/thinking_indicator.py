import time
import threading
from src.utils.colors import Colors

class ThinkingIndicator:
    def __init__(self, message=""):
        self.message = message
        self.running = False
        self.spinner = ['⠋', '⠙', '⠹', '⠸', '⠼', '⠴', '⠦', '⠧', '⠇', '⠏']
        self.spinner_idx = 0
        self.thread = None
        self._lock = threading.Lock()

    def _animate(self):
        while self.running:
            with self._lock:
                if not self.running:
                    break
                Colors.stream(f'\r{self.spinner[self.spinner_idx]} {self.message}', Colors.SYSTEM)
                self.spinner_idx = (self.spinner_idx + 1) % len(self.spinner)
            time.sleep(0.1)

    def start(self, message=None):
        if message:
            self.message = message
        with self._lock:
            if not self.running:
                self.running = True
                self.thread = threading.Thread(target=self._animate)
                self.thread.daemon = True  # Make thread daemon so it exits with main program
                self.thread.start()

    def stop(self):
        with self._lock:
            self.running = False
        if self.thread and self.thread.is_alive():
            self.thread.join(timeout=1.0)  # Wait max 1 second for thread to finish
        print('\r' + ' ' * (len(self.message) + 2), end='\r')  # Clear the line 