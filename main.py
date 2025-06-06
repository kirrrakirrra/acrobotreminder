import asyncio
import datetime
import logging
import json
import os
from aiohttp import web
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardRemove
from telegram.ext import (
    ApplicationBuilder,
    ContextTypes,
    CallbackQueryHandler,
    CommandHandler,
    MessageHandler,
    filters,
    ConversationHandler,
)

# Базовая настройка логов
logging.basicConfig(
    filename="bot.log",
    filemode="a",
    format="%(asctime)s - %(levelname)s - %(message)s",
    level=logging.INFO
)

# Константы и переменные
BOT_TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID = 986242491
NOTIFY_ID = 1291715324
GROUP_ID = -1001820363527

abon_file = "abons.json"
abon_data = {}
abon_history = []
abon_pastuse_pending = {}  # Для хранения выбранного абонемента перед выбором даты
abon_pastuse_dates = {}  # Временное хранилище выбранных дат для pastuse
abon_rename_pending = set()  # Абонементы ожидающие переименования
abon_add_pending = set()  # Для добавления новых абонементов
abon_mark_pending = set()  # Для команды mark (выбранные абонементы в мультиселекте)

# Структура групп
groups = [
    {"name": "Старшей начинающей группы", "days": ["Monday", "Wednesday", "Friday"], "time": "17:15", "thread_id": 2225},
    {"name": "Старшей продолжающей группы", "days": ["Monday", "Wednesday", "Friday"], "time": "18:30", "thread_id": 7},
    {"name": "Младшей группы", "days": ["Tuesday", "Thursday"], "time": "17:30", "thread_id": 2226},
]

pending = {}

cancel_messages = {
    "visa": "Всем доброго дня! 🌂 Сегодня я на визаране, поэтому занятия не будет. Отдохните хорошо, увидимся совсем скоро на тренировке! ☀️",
    "illness": "Всем доброго дня! 🤔 К сожалению, я приболел и не смогу провести сегодняшнее занятие. Надеюсь быстро восстановиться и скоро увидеться с вами! Берегите себя! 🌷",
    "unwell": "Всем доброго дня! 😌 Сегодня, к сожалению, чувствую себя неважно и не смогу провести тренировку. Спасибо за понимание — совсем скоро вернусь с новыми силами! 💪",
    "unexpected": "Всем доброго дня! ⚠️ По непредвиденным обстоятельствам сегодня не смогу провести занятие. Спасибо за понимание, увидимся в следующий раз! 😊",
    "tech": "Всем доброго дня! ⚙️ Сегодня, к сожалению, в зале возникли технические сложности, и мы не сможем провести тренировку. Уже работаем над тем, чтобы всё наладить. До скорой встречи! 🧘‍♀️",
}

# Утилиты

def save_abons():
    with open(abon_file, "w", encoding="utf-8") as f:
        json.dump(abon_data, f, ensure_ascii=False, indent=2)

def load_abons():
    global abon_data
    if os.path.exists(abon_file):
        with open(abon_file, "r", encoding="utf-8") as f:
            abon_data = json.load(f)

def log_action(action, name, date, extra=None):
    abon_history.append({"action": action, "name": name, "date": date, "extra": extra})

def get_actions_by_date(date):
    return [entry for entry in abon_history if entry["date"] == date]

# Клавиатуры

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

# Команды

async def pastuse_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        return
    await update.message.reply_text("Выберите абонемент для добавления прошлых посещений:", reply_markup=get_pastuse_keyboard())

# Callback

async def handle_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data.split("|")

    if data[0] == "check":
        name = data[1]
        if name in abon_data:
            used = abon_data[name]["used_sessions"]
            start_date = abon_data[name].get("start_date")
            text = f"{name}\nИспользовано занятий: {len(used)}/8\n"
            if start_date:
                text += f"Абонемент действует 1 календарный месяц с первого использования: {start_date}"
            else:
                text += "Абонемент ещё не активирован."
            await query.edit_message_text(text)
        else:
            await query.edit_message_text("Абонемент не найден.")

    elif data[0] == "rename":
        name = data[1]
        abon_rename_pending.add(name)
        await query.edit_message_text(f"Введите новое имя для абонемента '{name}':", reply_markup=ReplyKeyboardRemove())

    elif data[0] == "marktoggle":
        name = data[1]
        if name in abon_mark_pending:
            abon_mark_pending.remove(name)
        else:
            abon_mark_pending.add(name)
        await query.edit_message_reply_markup(reply_markup=get_mark_keyboard())

    elif data[0] == "markconfirm":
        today = datetime.date.today().isoformat()
        count = 0
        for name in abon_mark_pending:
            if name in abon_data and not abon_data[name].get("deleted"):
                if today not in abon_data[name]["used_sessions"]:
                    abon_data[name]["used_sessions"].append(today)
                    if not abon_data[name]["start_date"]:
                        abon_data[name]["start_date"] = today
                    log_action("mark", name, today)
                    count += 1
        save_abons()
        abon_mark_pending.clear()
        await query.edit_message_text(f"Отмечено {count} посещений на {today}.")

    elif data[0] == "pastuse":
        name = data[1]
        abon_pastuse_dates[name] = set()
        await query.edit_message_text(f"Выберите даты для абонемента '{name}':", reply_markup=get_date_multiselect_keyboard(name))

    elif data[0] == "pastusetoggle":
        name, date = data[1], data[2]
        abon_pastuse_dates.setdefault(name, set())
        if date in abon_pastuse_dates[name]:
            abon_pastuse_dates[name].remove(date)
        else:
            abon_pastuse_dates[name].add(date)
        await query.edit_message_reply_markup(reply_markup=get_date_multiselect_keyboard(name))

    elif data[0] == "pastuseconfirm":
        name = data[1]
        dates = abon_pastuse_dates.get(name, set())
        count = 0
        for date in dates:
            if name in abon_data and not abon_data[name].get("deleted"):
                if date not in abon_data[name]["used_sessions"]:
                    abon_data[name]["used_sessions"].append(date)
                    if not abon_data[name]["start_date"]:
                        abon_data[name]["start_date"] = date
                    log_action("pastuse", name, date)
                    count += 1
        save_abons()
        abon_pastuse_dates.pop(name, None)
        await query.edit_message_text(f"Добавлено {count} посещений задним числом.")

# Регистрация

app = ApplicationBuilder().token(BOT_TOKEN).build()
app.add_handler(CommandHandler("check", check_command))
app.add_handler(CommandHandler("list", list_command))
app.add_handler(CommandHandler("rename", rename_command))
app.add_handler(CommandHandler("add", add_command))
app.add_handler(CommandHandler("mark", mark_command))
app.add_handler(CommandHandler("pastuse", pastuse_command))
app.add_handler(CallbackQueryHandler(handle_callback))
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))
