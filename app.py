# app.py
import os
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer

from telegram import Update
from telegram.ext import (
    ApplicationBuilder, CommandHandler, MessageHandler,
    ContextTypes, filters
)

# === настройки ===
TOKEN = os.environ.get("TELEGRAM_TOKEN")
if not TOKEN:
    raise RuntimeError("TELEGRAM_TOKEN is not set")

PORT = int(os.environ.get("PORT", "10000"))
PUBLIC_URL = os.environ.get("PUBLIC_URL")  # например, https://uchbotik.onrender.com
if not PUBLIC_URL:
    raise RuntimeError("PUBLIC_URL is not set (e.g. https://<your>.onrender.com)")

# health-check сервер для Render
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
    await update.message.reply_text("Привет! Я живу на вебхуках ✅")

async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Текст получил 📨")

async def handle_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Фото получил 🖼️")

def main():
    # 1) health-сервер в фоне
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

    # 3) вебхук на PUBLIC_URL/bot<TOKEN>
    webhook_path = f"/bot{TOKEN}"
    webhook_url = f"{PUBLIC_URL.rstrip('/')}{webhook_path}"

    # ВАЖНО: НЕ используем asyncio.run! PTB сам управляет циклом.
    app.run_webhook(
        listen="0.0.0.0",
        port=PORT,
        url_path=webhook_path,
        webhook_url=webhook_url,
        drop_pending_updates=True,
        stop_signals=None,  # чтобы Render не ругался на сигналы
    )

if __name__ == "__main__":
    main()
