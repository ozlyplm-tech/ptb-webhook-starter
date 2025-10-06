import os
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, ContextTypes, filters
from aiohttp import web

# === настройки ===
TOKEN = os.environ["TELEGRAM_TOKEN"]  # обязательно задана в Render → Environment
PORT = int(os.getenv("PORT", "10000"))

PUBLIC_URL = (
    os.getenv("PUBLIC_URL")
    or os.getenv("RENDER_EXTERNAL_URL")
    or "https://<your-service>.onrender.com"  # при желании замени на свой URL и удали .rstrip('/')
).rstrip("/")

# === хендлеры ===
async def start(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Привет! Пришли текст или фото.")

async def handle_text(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Текст получил ✅")

async def handle_photo(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Фото получил ✅")

# === health для Render на '/' ===
async def health(_request):
    return web.Response(text="ok")

def main():
    app = Application.builder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.PHOTO, handle_photo))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))

    # aiohttp-приложение для health-роута
    web_app = web.Application()
    web_app.router.add_get("/", health)
    web_app.router.add_head("/", health)

    # запускаем webhook (PTB сам управляет event loop — НИКАКОГО asyncio.run)
    app.run_webhook(
        listen="0.0.0.0",
        port=PORT,
        url_path=TOKEN,
        webhook_url=f"{PUBLIC_URL}/{TOKEN}",
        web_app=web_app,
        drop_pending_updates=True,
    )

if __name__ == "__main__":
    main()
