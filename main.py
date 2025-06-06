import asyncio
import logging
import nest_asyncio
from aiohttp import web
from telegram.ext import (
    ApplicationBuilder,
    CallbackQueryHandler,
    CommandHandler,
)

from commands_module import (
    start_command, add_command, mark_command, check_command,
    pastuse_command, rename_command, delete_command,
    list_command, history_command
)
from handlers_module import handle_callback, handle_callback_response
from notify_module import (
    send_admin_reminders,
    send_startup_notification,
    send_crash_notification,
)
from config import BOT_TOKEN

import datetime
import time

nest_asyncio.apply()

logging.basicConfig(
    filename="bot.log",
    filemode="a",
    format="%(asctime)s - %(levelname)s - %(message)s",
    level=logging.INFO
)

# aiohttp ping endpoint
async def handle_ping(request):
    return web.Response(text="I'm alive!")

async def start_webserver():
    app = web.Application()
    app.router.add_get("/", handle_ping)
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, "0.0.0.0", 8080)
    await site.start()

# Main scheduler
async def scheduler(app):
    while True:
        try:
            now = datetime.datetime.utcnow() + datetime.timedelta(hours=7)
            if now.hour == 12 and now.minute == 30:
                await send_admin_reminders(app)
                await asyncio.sleep(60)
            await asyncio.sleep(20)
        except Exception as e:
            logging.exception("Ошибка в scheduler")
            await asyncio.sleep(10)

# Main entry point
async def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    # Register commands
    app.add_handler(CommandHandler("start", start_command))
    app.add_handler(CommandHandler("add", add_command))
    app.add_handler(CommandHandler("mark", mark_command))
    app.add_handler(CommandHandler("check", check_command))
    app.add_handler(CommandHandler("pastuse", pastuse_command))
    app.add_handler(CommandHandler("rename", rename_command))
    app.add_handler(CommandHandler("delete", delete_command))
    app.add_handler(CommandHandler("list", list_command))
    app.add_handler(CommandHandler("history", history_command))

    # Register button callbacks
    app.add_handler(CallbackQueryHandler(handle_callback))
    app.add_handler(CallbackQueryHandler(handle_callback_response))

    asyncio.create_task(scheduler(app))
    asyncio.create_task(start_webserver())
    await send_startup_notification(app)
    await app.run_polling()

if __name__ == "__main__":
    while True:
        try:
            asyncio.run(main())
        except Exception as e:
            logging.exception("Бот упал с ошибкой. Перезапуск через 5 секунд...")
            try:
                app = ApplicationBuilder().token(BOT_TOKEN).build()
                asyncio.run(send_crash_notification(app, e))
            except:
                pass
            time.sleep(5)
