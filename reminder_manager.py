import json
import uuid
from datetime import datetime
from pathlib import Path

DATA_FILE = Path("data/reminders.json")

class ReminderManager:
    def __init__(self):
        self.reminders = {}
        self.load()

    def load(self):
        if DATA_FILE.exists():
            with open(DATA_FILE, "r", encoding="utf-8") as f:
                self.reminders = json.load(f)
        else:
            self.reminders = {}

    def save(self):
        with open(DATA_FILE, "w", encoding="utf-8") as f:
            json.dump(self.reminders, f, ensure_ascii=False, indent=2)

    def add(self, time, title):
        reminder_id = str(uuid.uuid4())[:8]
        self.reminders[reminder_id] = {
            "time": time,
            "title": title,
        }
        self.save()
        return reminder_id

    def delete(self, reminder_id):
        if reminder_id in self.reminders:
            del self.reminders[reminder_id]
            self.save()
            return True
        return False

    def get_id(self, reminder_id):
        return self.reminders.get(reminder_id)

    def get_all(self):
        return self.reminders

