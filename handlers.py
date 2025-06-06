from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, CallbackQueryHandler
from storage_module import abon_data, save_abons, ADMIN_ID, history_data, save_history
from keyboards_module import (
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
