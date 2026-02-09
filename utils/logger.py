# utils/logger.py
# DESIGN PATTERN: Singleton
# Ensures only one instance of Logger exists throughout the application

class Logger:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            print("[Singleton] Creez instanța unică a Logger...")
            cls._instance = super().__new__(cls)
            cls._instance.messages = []
        return cls._instance

    def log(self, message: str, level: str = "INFO"):
        # Poți adăuga timestamp real cu datetime
        timestamp = "2026-02-XX"
        entry = f"[{level}] {timestamp} - {message}"
        self.messages.append(entry)
        print(entry)

    def get_all_logs(self):
        return "\n".join(self.messages)


# Instanța globală (o poți importa oriunde)
logger = Logger()