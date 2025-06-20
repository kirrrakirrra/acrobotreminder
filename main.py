import asyncio
import logging
from telegram.ext import Application, CommandHandler, CallbackQueryHandler
from config import BOT_TOKEN
from handlers import handle_callback_query, register_handlers
from notify import setup_daily_jobs

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)

async def main():
    application = Application.builder().token(BOT_TOKEN).build()

    # Подключаем обработчики команд и кнопок
    register_handlers(application)
    application.add_handler(CallbackQueryHandler(handle_callback_query))

    # Устанавливаем ежедневные задания (опросы, напоминания и т.д.)
    setup_daily_jobs(application)
    
    print("✅ MAIN ЗАПУСТИЛСЯ — бот сейчас запустит polling...")
    # Запуск
    await application.run_polling()

if __name__ == '__main__':
    import nest_asyncio
    import asyncio

    nest_asyncio.apply()
    asyncio.get_event_loop().run_until_complete(main())
