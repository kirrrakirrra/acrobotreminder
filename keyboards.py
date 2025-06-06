from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from storage_module import abon_data, abon_mark_pending, abon_pastuse_dates
import datetime

def get_check_keyboard():
    buttons = []
    for name, data in abon_data.items():
        if not data.get("deleted"):
            buttons.append([InlineKeyboardButton(name, callback_data=f"check|{name}")])
    return InlineKeyboardMarkup(buttons)

def get_rename_keyboard():
    buttons = []
    for name, data in abon_data.items():
        if not data.get("deleted"):
            buttons.append([InlineKeyboardButton(name, callback_data=f"rename|{name}")])
    return InlineKeyboardMarkup(buttons)

def get_mark_keyboard():
    buttons = []
    for name, data in abon_data.items():
        if not data.get("deleted"):
            selected = "✅ " if name in abon_mark_pending else ""
            buttons.append([InlineKeyboardButton(f"{selected}{name}", callback_data=f"marktoggle|{name}")])
    if abon_mark_pending:
        buttons.append([InlineKeyboardButton("➕ Отметить посещение", callback_data="markconfirm")])
    return InlineKeyboardMarkup(buttons)

def get_pastuse_keyboard():
    buttons = []
    for name, data in abon_data.items():
        if not data.get("deleted"):
            buttons.append([InlineKeyboardButton(name, callback_data=f"pastuse|{name}")])
    return InlineKeyboardMarkup(buttons)

def get_date_multiselect_keyboard(name):
    buttons = []
    today = datetime.date.today()
    for i in range(30):
        day = today - datetime.timedelta(days=i)
        day_str = day.isoformat()
        selected = "✅ " if name in abon_pastuse_dates and day_str in abon_pastuse_dates[name] else ""
        buttons.append([InlineKeyboardButton(f"{selected}{day_str}", callback_data=f"pastusetoggle|{name}|{day_str}")])
    if name in abon_pastuse_dates and abon_pastuse_dates[name]:
        buttons.append([InlineKeyboardButton("➕ Добавить посещения", callback_data=f"pastuseconfirm|{name}")])
    return InlineKeyboardMarkup(buttons)
