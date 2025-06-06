from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, CallbackQueryHandler
from storage import abon_data, save_abons, ADMIN_ID, history_data, save_history
from keyboards import (
    get_mark_keyboard, get_check_keyboard, get_pastuse_keyboard,
    get_rename_keyboard, get_date_history_keyboard
)
import datetime


def get_back_keyboard():
    return InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Назад", callback_data="back")]])


async def handle_mark_selection(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    selected = context.user_data.setdefault("selected_abons", set())
    abon_name = query.data.replace("mark_", "")
    if abon_name in selected:
        selected.remove(abon_name)
    else:
        selected.add(abon_name)
    await query.edit_message_reply_markup(reply_markup=get_mark_keyboard(selected))


async def handle_mark_finish(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    selected = context.user_data.pop("selected_abons", set())
    if not selected:
        await query.edit_message_text("Ничего не выбрано")
        return
    now = datetime.datetime.now().strftime("%Y-%m-%d")
    for name in selected:
        if now not in abon_data[name]["used_sessions"]:
            abon_data[name]["used_sessions"].append(now)
        if not abon_data[name]["start_date"]:
            abon_data[name]["start_date"] = now
        history_data[now].append({"action": "mark", "abon": name})
    save_abons()
    save_history()
    await query.edit_message_text("Посещения отмечены ✅")


async def handle_check_selection(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    abon_name = query.data.replace("check_", "")
    data = abon_data[abon_name]
    used = data["used_sessions"]
    text = f"Абонемент *{abon_name}*\n"
    text += f"Использовано: {len(used)}/8\n"
    if used:
        text += f"Первое занятие: {data['start_date']}\n"
        text += "Абонемент действует 1 календарный месяц с первого использования."
    await query.edit_message_text(text, parse_mode="Markdown", reply_markup=get_back_keyboard())


async def handle_back(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    await query.edit_message_text("Выберите абонемент для проверки:", reply_markup=get_check_keyboard())


# --- pastuse: выбор абонемента → мультиселект последних 30 дней ---

async def handle_pastuse_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    abon_name = query.data.replace("pastuse_", "")
    context.user_data["pastuse_abon"] = abon_name
    context.user_data["selected_dates"] = set()
    await query.edit_message_text(f"Выберите даты использования для абонемента *{abon_name}*:",
                                  parse_mode="Markdown",
                                  reply_markup=get_pastuse_keyboard(set()))


async def handle_pastuse_toggle(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    date = query.data.replace("date_", "")
    selected = context.user_data.setdefault("selected_dates", set())
    if date in selected:
        selected.remove(date)
    else:
        selected.add(date)
    await query.edit_message_reply_markup(reply_markup=get_pastuse_keyboard(selected))


async def handle_pastuse_finish(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    abon_name = context.user_data.pop("pastuse_abon", None)
    selected = context.user_data.pop("selected_dates", set())
    if not abon_name or not selected:
        await query.edit_message_text("Ничего не выбрано")
        return
    for date in selected:
        if date not in abon_data[abon_name]["used_sessions"]:
            abon_data[abon_name]["used_sessions"].append(date)
        if not abon_data[abon_name]["start_date"]:
            abon_data[abon_name]["start_date"] = date
        history_data[date].append({"action": "pastuse", "abon": abon_name})
    save_abons()
    save_history()
    await query.edit_message_text("Прошлые посещения добавлены ✅")

# --- rename ---

async def handle_rename_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    abon_name = query.data.replace("rename_", "")
    context.user_data["rename_abon"] = abon_name
    await query.edit_message_text(f"Введите новое имя для абонемента *{abon_name}*:", parse_mode="Markdown")


async def handle_rename_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        return
    abon_name = context.user_data.pop("rename_abon", None)
    if not abon_name:
        return
    new_name = update.message.text.strip()
    if new_name in abon_data:
        await update.message.reply_text("Абонемент с таким именем уже существует")
        return
    abon_data[new_name] = abon_data.pop(abon_name)
    save_abons()
    today = datetime.datetime.now().strftime("%Y-%m-%d")
    history_data[today].append({"action": "rename", "abon": abon_name, "new": new_name})
    save_history()
    await update.message.reply_text("Имя абонемента обновлено ✅")

# --- delete ---

async def handle_delete_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    abon_name = query.data.replace("delete_", "")
    if abon_name in abon_data:
        abon_data[abon_name]["deleted"] = True
        today = datetime.datetime.now().strftime("%Y-%m-%d")
        history_data[today].append({"action": "delete", "abon": abon_name})
        save_abons()
        save_history()
        await query.edit_message_text(f"Абонемент *{abon_name}* помечен как неактивный ❌", parse_mode="Markdown")
    else:
        await query.edit_message_text("Абонемент не найден")

# --- list ---

async def handle_list(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        return
    if not abon_data:
        await update.message.reply_text("Нет абонементов.")
        return

    active_abons = {
        name: data for name, data in abon_data.items()
        if not data.get("deleted", False)
    }

    if not active_abons:
        await update.message.reply_text("Нет активных абонементов.")
        return

    text = "📋 *Список активных абонементов:*\n\n"
    for name, data in active_abons.items():
        used = len(data["used_sessions"])
        start = data["start_date"]
        text += f"• *{name}*: {used}/8"
        if start:
            text += f" (с {start})"
        text += "\n"

    await update.message.reply_text(text, parse_mode="Markdown")




# --- cancel messages & reminders ---

cancel_messages = {
    "visa": "Всем доброго дня! 🛂 Сегодня я на визаране, поэтому занятия не будет. Отдохните хорошо, увидимся совсем скоро на тренировке! ☀️",
    "illness": "Всем доброго дня! 🤒 К сожалению, я приболел и не смогу провести сегодняшнее занятие. Надеюсь быстро восстановиться и скоро увидеться с вами! Берегите себя! 🌷",
    "unwell": "Всем доброго дня! 😌 Сегодня, к сожалению, чувствую себя неважно и не смогу провести тренировку. Спасибо за понимание — совсем скоро вернусь с новыми силами! 💪",
    "unexpected": "Всем доброго дня! ⚠️ По непредвиденным обстоятельствам сегодня не смогу провести занятие. Спасибо за понимание, увидимся в следующий раз! 😊",
    "tech": "Всем доброго дня! ⚙️ Сегодня, к сожалению, в зале возникли технические сложности, и мы не сможем провести тренировку. Уже работаем над тем, чтобы всё наладить. До скорой встречи! 🤸‍♀️",
}


groups = [
    {"name": "Старшей начинающей группы", "days": ["Monday", "Wednesday", "Friday"], "time": "17:15", "thread_id": 2225},
    {"name": "Старшей продолжающей группы", "days": ["Monday", "Wednesday", "Friday"], "time": "18:30", "thread_id": 7},
    {"name": "Младшей группы", "days": ["Tuesday", "Thursday"], "time": "17:30", "thread_id": 2226},
]

pending = {}

async def ask_admin(app, group_id, group):
    msg = await app.bot.send_message(
        chat_id=ADMIN_ID,
        text=f"Сегодня занятие для {group['name']} в {group['time']} по расписанию?",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("✅ Да", callback_data=f"yes|{group_id}"),
             InlineKeyboardButton("❌ Нет, отмена", callback_data=f"no|{group_id}")],
            [InlineKeyboardButton("⏭ Нет, но я сам напишу в группу", callback_data=f"skip|{group_id}")],
        ])
    )
    pending[msg.message_id] = group


async def scheduler(app):
    while True:
        now_utc = datetime.datetime.utcnow()
        now = now_utc + datetime.timedelta(hours=7)
        if now.hour == 12 and now.minute == 30:
            weekday = now.strftime("%A")
            for idx, group in enumerate(groups):
                if weekday in group["days"]:
                    await ask_admin(app, idx, group)
            await asyncio.sleep(60)
        await asyncio.sleep(20)


async def handle_callback_query(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data.split("|")
    action = data[0]
    group_id = int(data[1])
    group = groups[group_id]

    if action == "yes":
        await context.bot.send_message(
            chat_id=-1001820363527,
            message_thread_id=group["thread_id"],
            text=f"Всем доброго дня! Занятие для {group['name']} по расписанию в {group['time']} 🤸🏻🤸🏻‍♀️"
        )
        await query.edit_message_text("Напоминание отправлено ✅")

    elif action == "no":
        await query.edit_message_text("Выберите причину отмены занятия:",
                                      reply_markup=InlineKeyboardMarkup([
                                          [InlineKeyboardButton("🤒 Болезнь", callback_data=f"reason|{group_id}|illness")],
                                          [InlineKeyboardButton("🛂 Визаран", callback_data=f"reason|{group_id}|visa")],
                                          [InlineKeyboardButton("😌 Плохое самочувствие", callback_data=f"reason|{group_id}|unwell")],
                                          [InlineKeyboardButton("⚠️ Непредвиденное", callback_data=f"reason|{group_id}|unexpected")],
                                          [InlineKeyboardButton("⚙️ Тех. неполадки", callback_data=f"reason|{group_id}|tech")],
                                      ]))

    elif action == "reason":
        reason_key = data[2]
        message = cancel_messages.get(reason_key, "Занятие отменяется.")
        await context.bot.send_message(
            chat_id=-1001820363527,
            message_thread_id=group["thread_id"],
            text=message
        )
        await query.edit_message_text("Отмена опубликована ❌")

    elif action == "skip":
        await query.edit_message_text("Хорошо, ничего не публикуем.")
