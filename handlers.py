from telegram.ext import Application, CallbackQueryHandler
from notify import handle_callback_query

def register_handlers(application: Application):
    # Обработка inline-кнопок (Да / Нет / причины отмены)
    application.add_handler(CallbackQueryHandler(handle_callback_query))
