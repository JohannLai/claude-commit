"""
Simple spinner for showing progress in the terminal.
"""

import sys
import time
import threading


class Spinner:
    """Simple spinner for showing progress."""
    def __init__(self, message="Processing"):
        self.message = message
        self.running = False
        self.thread = None
        
    def _spin(self):
        """Spin animation."""
        frames = ["⠋", "⠙", "⠹", "⠸", "⠼", "⠴", "⠦", "⠧", "⠇", "⠏"]
        idx = 0
        while self.running:
            frame = frames[idx % len(frames)]
            sys.stdout.write(f"\r{frame} {self.message}")
            sys.stdout.flush()
            time.sleep(0.1)
            idx += 1
        # Clear the line when done
        sys.stdout.write("\r" + " " * (len(self.message) + 3) + "\r")
        sys.stdout.flush()
    
    def start(self):
        """Start the spinner."""
        if not self.running:
            self.running = True
            self.thread = threading.Thread(target=self._spin, daemon=True)
            self.thread.start()
    
    def stop(self):
        """Stop the spinner."""
        if self.running:
            self.running = False
            if self.thread:
                self.thread.join(timeout=0.5)

