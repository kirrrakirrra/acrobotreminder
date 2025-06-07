from telegram.ext import Application, CallbackQueryHandler
from notify import handle_callback_query

def register_handlers(application: Application):
    # Все команды (/start, /add и т.д.)
    register_commands(application)

    # Обработка нажатий на inline-кнопки (из notify.py)
    application.add_handler(CallbackQueryHandler(handle_callback_query))
