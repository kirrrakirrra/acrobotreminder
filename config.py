import os

BOT_TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID = int(os.getenv("ADMIN_ID"))
GROUP_ID = int(os.getenv("GROUP_ID"))
NOTIFY_ID = int(os.getenv("NOTIFY_ID"))

# Файлы
ABON_FILE = "abons.json"
LOG_FILE = "bot.log"

# Часовой пояс (Вьетнам UTC+7)
TIMEZONE_OFFSET = 7
