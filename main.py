import asyncio
import logging
from aiohttp import web, ClientSession
from telegram import BotCommand
from telegram.ext import Application, CommandHandler, CallbackQueryHandler

from config import BOT_TOKEN
from commands import (
    add_abonement, mark_visit, check_abonements, past_use,
    rename_abonement, delete_abonement, list_abonements, show_history
)
from handlers import handle_callback_query, scheduler
from storage import save_abons, abon_data

logging.basicConfig(level=logging.INFO)

# URL своего проекта на Render
RENDER_URL = "https://acrobotreminder.onrender.com"  # ← Замени на свой адрес

# Telegram Webhook Ping Handler (для Render или Heroku)
async def handle(request):
    return web.Response(text="Бот работает!")

# Установка команд в Telegram
async def set_commands(application: Application):
    commands = [
        BotCommand("add", "Добавить абонемент"),
        BotCommand("mark", "Отметить посещение"),
        BotCommand("check", "Проверить абонементы"),
        BotCommand("pastuse", "Отметить прошлое посещение"),
        BotCommand("rename", "Переименовать абонемент"),
        BotCommand("delete", "Удалить абонемент"),
        BotCommand("list", "Список абонементов"),
        BotCommand("history", "История изменений"),
    ]
    await application.bot.set_my_commands(commands)

# 🔁 Периодический самопинг
async def self_ping():
    while True:
        try:
            async with ClientSession() as session:
                async with session.get(RENDER_URL) as response:
                    print("Pinged self:", response.status)
        except Exception as e:
            print("Ошибка самопинга:", e)
        await asyncio.sleep(300)  # каждые 5 минут

# Основная функция запуска
async def main():
    app = Application.builder().token(BOT_TOKEN).build()

    # Команды
    app.add_handler(CommandHandler("add", add_abonement))
    app.add_handler(CommandHandler("mark", mark_visit))
    app.add_handler(CommandHandler("check", check_abonements))
    app.add_handler(CommandHandler("pastuse", past_use))
    app.add_handler(CommandHandler("rename", rename_abonement))
    app.add_handler(CommandHandler("delete", delete_abonement))
    app.add_handler(CommandHandler("list", list_abonements))
    app.add_handler(CommandHandler("history", show_history))

    # CallbackQuery обработчик (универсальный)
    app.add_handler(CallbackQueryHandler(handle_callback_query))

    # Планировщик напоминаний
    scheduler()

    # Запуск aiohttp-сервера (для Render ping)
    web_app = web.Application()
    web_app.router.add_get("/", handle)
    runner = web.AppRunner(web_app)
    await runner.setup()
    site = web.TCPSite(runner, "0.0.0.0", 8080)
    await site.start()

       # Старт самопинга
    asyncio.create_task(self_ping())
    
    await set_commands(app)

    print("Бот запущен")
    await app.run_polling()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        save_abons(abon_data)
        print("Бот остановлен. Данные сохранены.")
