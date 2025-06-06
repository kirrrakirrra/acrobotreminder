from telegram import Update
from telegram.ext import ContextTypes
from storage_module import abon_data, save_abons, ADMIN_ID
from keyboards_module import (
    get_mark_keyboard, get_check_keyboard, get_pastuse_keyboard,
    get_rename_keyboard
)


async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Бот активен и готов к работе!")


async def add_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        return
    args = context.args
    if not args:
        await update.message.reply_text("Введите имя абонемента: /add Имя")
        return
    name = " ".join(args)
    if name in abon_data and not abon_data[name].get("deleted"):
        await update.message.reply_text("Абонемент с таким именем уже существует")
        return
    abon_data[name] = {
        "used_sessions": [],
        "start_date": None,
        "deleted": False,
    }
    save_abons()
    await update.message.reply_text(f"Абонемент {name} добавлен ✅")


async def list_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        return
    text = "Активные абонементы:\n"
    for name, data in abon_data.items():
        if not data.get("deleted"):
            text += f"- {name}: {len(data['used_sessions'])}/8\n"
    await update.message.reply_text(text.strip())


async def mark_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        return
    await update.message.reply_text("Выберите абонементы для отметки посещения:", reply_markup=get_mark_keyboard())


async def check_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Выберите абонемент для проверки:", reply_markup=get_check_keyboard())


async def pastuse_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        return
    await update.message.reply_text("Выберите абонемент для добавления прошедших посещений:", reply_markup=get_pastuse_keyboard())


async def rename_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        return
    await update.message.reply_text("Выберите абонемент для переименования:", reply_markup=get_rename_keyboard())


async def delete_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        return
    from keyboards_module import get_rename_keyboard  # переиспользуем клавиатуру
    await update.message.reply_text("Выберите абонемент для удаления:", reply_markup=get_rename_keyboard())


async def history_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        return
    from keyboards_module import get_date_history_keyboard
    await update.message.reply_text("Выберите дату для просмотра истории:", reply_markup=get_date_history_keyboard())
