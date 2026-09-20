import os
import asyncio
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
        response = requests.get(f"https://r.jina.ai/{url}", timeout=60)
        if response.status_code == 200:
            content = response.text
            chunk_size = 4000
            chunks = [content[i:i+chunk_size] for i in range(0, len(content), chunk_size)]
            
            for i, chunk in enumerate(chunks):
                await update.message.reply_text(chunk)
                if i < len(chunks) - 1:
                    await asyncio.sleep(1)
        else:
            await update.message.reply_text("استخراج محتوا با خطا مواجه شد.")
    except Exception as e:
        await update.message.reply_text(f"خطا: {e}")

app = ApplicationBuilder().token(BOT_TOKEN).build()
app.add_handler(CommandHandler("start", start))
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_link))
app.run_polling()