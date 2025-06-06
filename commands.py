from telegram import Update
from telegram.ext import ContextTypes
from storage import abon_data, save_abons
from keyboards import get_mark_keyboard

# Добавить абонемент
async def add_abonement(update: Update, context: ContextTypes.DEFAULT_TYPE):
    group_name = update.effective_chat.title or "test"
    if group_name not in abon_data:
        abon_data[group_name] = {}

    args = context.args
    if not args:
        await update.message.reply_text("Пожалуйста, укажите имя абонемента после команды.")
        return

    abonement_name = " ".join(args)
    abon_data[group_name][abonement_name] = []
    save_abons(abon_data)  # ✅ сохранить после добавления
    await update.message.reply_text(f"Абонемент \"{abonement_name}\" добавлен.")

# Отметить посещение
async def mark_visit(update: Update, context: ContextTypes.DEFAULT_TYPE):
    group_name = update.effective_chat.title or "test"
    if group_name not in abon_data or not abon_data[group_name]:
        await update.message.reply_text("Нет доступных абонементов для отметки.")
        return

    reply_markup = get_mark_keyboard(group_name)
    await update.message.reply_text("Отметьте посещения:", reply_markup=reply_markup)

# Отметить прошлое посещение (через аргумент)
async def past_use(update: Update, context: ContextTypes.DEFAULT_TYPE):
    group_name = update.effective_chat.title or "test"
    args = context.args
    if len(args) < 2:
        await update.message.reply_text("Формат: /pastuse [имя] [YYYY-MM-DD]")
        return

    abonement_name = " ".join(args[:-1])
    date = args[-1]
    if group_name not in abon_data or abonement_name not in abon_data[group_name]:
        await update.message.reply_text("Такой абонемент не найден.")
        return

    abon_data[group_name][abonement_name].append(date)
    save_abons(abon_data)  # ✅ сохранить после добавления даты
    await update.message.reply_text(f"Добавлено посещение {abonement_name} за {date}.")

# Переименовать абонемент
async def rename_abonement(update: Update, context: ContextTypes.DEFAULT_TYPE):
    group_name = update.effective_chat.title or "test"
    args = context.args
    if len(args) < 2:
        await update.message.reply_text("Формат: /rename [старое имя] [новое имя]")
        return

    old_name = args[0]
    new_name = " ".join(args[1:])
    if group_name not in abon_data or old_name not in abon_data[group_name]:
        await update.message.reply_text("Такой абонемент не найден.")
        return

    abon_data[group_name][new_name] = abon_data[group_name].pop(old_name)
    save_abons(abon_data)  # ✅ сохранить после переименования
    await update.message.reply_text(f"Абонемент \"{old_name}\" переименован в \"{new_name}\".")

# Удалить абонемент
async def delete_abonement(update: Update, context: ContextTypes.DEFAULT_TYPE):
    group_name = update.effective_chat.title or "test"
    args = context.args
    if not args:
        await update.message.reply_text("Пожалуйста, укажите имя абонемента для удаления.")
        return

    abonement_name = " ".join(args)
    if group_name not in abon_data or abonement_name not in abon_data[group_name]:
        await update.message.reply_text("Такой абонемент не найден.")
        return

    del abon_data[group_name][abonement_name]
    save_abons(abon_data)  # ✅ сохранить после удаления
    await update.message.reply_text(f"Абонемент \"{abonement_name}\" удалён.")

# Показать список абонементов
async def list_abonements(update: Update, context: ContextTypes.DEFAULT_TYPE):
    group_name = update.effective_chat.title or "test"
    if group_name not in abon_data or not abon_data[group_name]:
        await update.message.reply_text("Нет активных абонементов.")
        return

    message = "📋 Список абонементов:\n\n"
    for name, visits in abon_data[group_name].items():
        message += f"🔹 {name} — {len(visits)} посещений\n"
    await update.message.reply_text(message)

# Показать историю посещений
async def show_history(update: Update, context: ContextTypes.DEFAULT_TYPE):
    group_name = update.effective_chat.title or "test"
    if group_name not in abon_data or not abon_data[group_name]:
        await update.message.reply_text("Нет абонементов.")
        return

    message = "📖 История посещений:\n\n"
    for name, visits in abon_data[group_name].items():
        dates = ", ".join(visits) if visits else "нет посещений"
        message += f"🔹 {name}: {dates}\n"
    await update.message.reply_text(message)
