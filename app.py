import os
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer

from telegram import Update
from telegram.ext import (
    ApplicationBuilder, CommandHandler, MessageHandler,
    ContextTypes, filters
)


# --- конфиг ---
TOKEN = os.getenv("TELEGRAM_TOKEN")
if not TOKEN:
    raise RuntimeError("TELEGRAM_TOKEN is not set")

PORT = int(os.getenv("PORT", "10000"))

# Render сам проставляет публичный URL в RENDER_EXTERNAL_URL (после первого деплоя).
# Можно вручную задать PUBLIC_URL в переменных окружения, тогда он перекроет автозначение.
PUBLIC_URL = os.getenv("PUBLIC_URL") or os.getenv("RENDER_EXTERNAL_URL")
if not PUBLIC_URL:
    # если вдруг переменная ещё не доступна во время 1-го старта — покажем подсказку и выйдем
    raise RuntimeError(
        "PUBLIC_URL/RENDER_EXTERNAL_URL is not set yet. "
        "Подожди первый деплой, скопируй URL вида https://xxxx.onrender.com "
        "и запиши его в переменную PUBLIC_URL, затем запусти деплой ещё раз."
    )

# --- health-сервер, чтобы Render проверял / ---
class HealthHandler(BaseHTTPRequestHandler):
    def do_HEAD(self):
        self.send_response(200); self.end_headers()
    def do_GET(self):
        self.send_response(200); self.end_headers()
        self.wfile.write(b"ok")

def start_health_server():
    HTTPServer(("0.0.0.0", PORT), HealthHandler).serve_forever()


# --- handlers ---
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Привет! Я живой на вебхуках 🚀")

async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Текст принят ✅")

async def handle_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Фото принято ✅")


async def main():
    # 1) фоновый health-сервер
    threading.Thread(target=start_health_server, daemon=True).start()

    # 2) Telegram Application
    app = (
        ApplicationBuilder()
        .token(TOKEN)
        .build()
    )

    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))
    app.add_handler(MessageHandler(filters.PHOTO, handle_photo))

    # Путь для вебхука — закрываем его “секретом”, чтобы посторонние не дергали
    webhook_path = f"/bot/{TOKEN}"
    webhook_url = f"{PUBLIC_URL}{webhook_path}"

    # 3) Запускаем вебхук (бот слушает POST на webhook_path, а Render пингует /)
    await app.run_webhook(
        listen="0.0.0.0",
        port=PORT,
        url_path=webhook_path,
        webhook_url=webhook_url,
        drop_pending_updates=True,
    )


if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
