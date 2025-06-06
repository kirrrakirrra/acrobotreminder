import json
import os
from config import ABON_FILE

abon_data = {}
abon_history = []
abon_mark_pending = {}

def save_abons():
    with open(ABON_FILE, "w", encoding="utf-8") as f:
        json.dump({
            "abon_data": abon_data,
            "abon_history": abon_history,
        }, f, ensure_ascii=False, indent=2)

def load_abons():
    global abon_data, abon_history
    if os.path.exists(ABON_FILE):
        with open(ABON_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
            abon_data = data.get("abon_data", {})
            abon_history = data.get("abon_history", [])

def log_action(action, name, date, extra=None):
    abon_history.append({
        "action": action,
        "name": name,
        "date": date,
        "extra": extra
    })

def get_actions_by_date(date):
    return [entry for entry in abon_history if entry["date"] == date]
