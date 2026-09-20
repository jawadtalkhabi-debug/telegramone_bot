import os
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes
import requests

BOT_TOKEN = os.environ.get("BOT_TOKEN")

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("سلام! لینک مقاله را بفرست تا پردازش کنم.")

async def handle_link(update: Update, context: ContextTypes.DEFAULT_TYPE):
    url = update.message.text
    await update.message.reply_text("در حال پردازش لینک...")
    try:
        response = requests.get(f"https://r.jina.ai/{url}", timeout=30)
        if response.status_code == 200:
            content = response.text[:4000]
            await update.message.reply_text(content)
        else:
            await update.message.reply_text("استخراج محتوا با خطا مواجه شد.")
    except Exception as e:
        await update.message.reply_text(f"خطا: {e}")

app = ApplicationBuilder().token(BOT_TOKEN).build()
app.add_handler(CommandHandler("start", start))
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_link))
app.run_polling()