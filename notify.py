import datetime
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, update
from config import ADMIN_ID, NOTIFY_ID, GROUP_ID, TIMEZONE_OFFSET

# Список групп и их расписания
groups = [
    {
        "name": "Старшей начинающей группы",
        "days": ["Monday", "Wednesday", "Friday"],
        "time": "17:15",
        "thread_id": 2225,
    },
    {
        "name": "Старшей продолжающей группы",
        "days": ["Monday", "Wednesday", "Friday"],
        "time": "18:30",
        "thread_id": 7,
    },
    {
        "name": "Младшей группы",
        "days": ["Tuesday", "Thursday", "Saturday"],
        "time": "17:30",
        "thread_id": 105,
    },
]

cancel_messages = {
    "visa": "Всем доброго дня! 🛂 Сегодня я на визаране, поэтому занятия не будет. Отдохните хорошо, увидимся совсем скоро на тренировке! ☀️",
    "illness": "Всем доброго дня! 🤒 К сожалению, я приболел и не смогу провести сегодняшнее занятие. Надеюсь быстро восстановиться и скоро увидеться с вами! Берегите себя! 🌷",
    "unwell": "Всем доброго дня! 😌 Сегодня, к сожалению, чувствую себя неважно и не смогу провести тренировку. Спасибо за понимание — совсем скоро вернусь с новыми силами! 💪",
    "unexpected": "Всем доброго дня! ⚠️ По непредвиденным обстоятельствам сегодня не смогу провести занятие. Спасибо за понимание, увидимся в следующий раз! 😊",
    "tech": "Всем доброго дня! ⚙️ Сегодня, к сожалению, в зале возникли технические сложности, и мы не сможем провести тренировку. Уже работаем над тем, чтобы всё наладить. До скорой встречи! 🤸‍♀️",
}

def get_decision_keyboard(group_id):
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("✅ Да", callback_data=f"yes|{group_id}")],
        [InlineKeyboardButton("❌ Нет, отмена", callback_data=f"no|{group_id}")],
        [InlineKeyboardButton("⏭ Нет, но я сам напишу в группу", callback_data=f"skip|{group_id}")],
    ])

def get_reason_keyboard(group_id):
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🤒 Болезнь", callback_data=f"reason|{group_id}|illness")],
        [InlineKeyboardButton("🛂 Визаран", callback_data=f"reason|{group_id}|visa")],
        [InlineKeyboardButton("😌 Плохое самочувствие", callback_data=f"reason|{group_id}|unwell")],
        [InlineKeyboardButton("⚠️ Непредвиденное", callback_data=f"reason|{group_id}|unexpected")],
        [InlineKeyboardButton("⚙️ Тех. неполадки", callback_data=f"reason|{group_id}|tech")],
    ])

# Отправка опроса админу
async def send_admin_reminders(context: ContextTypes.DEFAULT_TYPE):
    now = datetime.datetime.utcnow() + datetime.timedelta(hours=TIMEZONE_OFFSET)
    weekday = now.strftime("%A")
    for idx, group in enumerate(groups):
        if weekday in group["days"]:
            await context.bot.send_message(
                chat_id=ADMIN_ID,
                text=f"Сегодня занятие для {group['name']} в {group['time']} по расписанию?",
                reply_markup=get_decision_keyboard(idx)
            )

# Обработка всех callback'ов
async def handle_callback_query(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    data = query.data
    await query.answer()

    if data.startswith("yes|"):
        group_id = int(data.split("|")[1])
        group = groups[group_id]
        await context.bot.send_message(
            chat_id=GROUP_ID,
            message_thread_id=group["thread_id"],
            text=f"Всем доброго дня! Занятие для {group['name']} по расписанию в {group['time']} 🤸🏻🤸🏻‍♀️"
        )

    elif data.startswith("no|"):
        group_id = int(data.split("|")[1])
        await query.message.reply_text(
            "Выберите причину отмены:",
            reply_markup=get_reason_keyboard(group_id)
        )

    elif data.startswith("skip|"):
        await query.message.reply_text("Хорошо, ничего не пишу в группу.")

    elif data.startswith("reason|"):
        _, group_id, reason_code = data.split("|")
        group_id = int(group_id)
        group = groups[group_id]
        message = cancel_messages.get(reason_code, "Сегодняшнее занятие отменяется.")
        await context.bot.send_message(
            chat_id=GROUP_ID,
            message_thread_id=group["thread_id"],
            text=message)

# Уведомление при старте бота
async def send_startup_notification(app):
    try:
        await app.bot.send_message(chat_id=NOTIFY_ID, text="🤖 Бот запущен и работает.")
    except Exception as e:
        print(f"Ошибка при отправке уведомления: {e}")

# Уведомление при сбое
async def send_crash_notification(app, error: Exception):
    try:
        await app.bot.send_message(
            chat_id=NOTIFY_ID,
            text=f"❌ Бот упал с ошибкой:\n{str(error)}"
        )
    except Exception as e:
        print(f"Ошибка при отправке crash-уведомления: {e}")

# Планировщик опроса в 12:30 по Вьетнаму
def setup_daily_jobs(application):
    from datetime import time
    job_time = time(hour=12, minute=53)
    application.job_queue.run_daily(
        send_admin_reminders,
        time=job_time,
        name="daily_admin_check"
    )
