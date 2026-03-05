# utils/logger.py
# DESIGN PATTERN: Singleton
# Ensures only one instance of Logger exists throughout the application

from datetime import datetime
from threading import Lock

class Logger:
    _instance = None
    _lock = Lock()

    def __new__(cls):
        if cls._instance is None:
            # Double-checked locking evită crearea a două instanțe în multi-threading.
            with cls._lock:
                if cls._instance is None:
                    print("[Singleton] Creez instanța unică a Logger...")
                    cls._instance = super().__new__(cls)
                    cls._instance.messages = []
        return cls._instance

    def log(self, message: str, level: str = "INFO"):
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]
        entry = f"[{level}] {timestamp} - {message}"
        self.messages.append(entry)
        print(entry)

    def get_all_logs(self):
        return "\n".join(self.messages)


# Instanța globală (o poți importa oriunde)
logger = Logger()