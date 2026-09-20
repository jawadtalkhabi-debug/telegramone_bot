import os
import asyncio
import re
import requests
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes

BOT_TOKEN = os.environ.get("BOT_TOKEN")
BROWSERLESS_URL = os.environ.get("BROWSERLESS_URL")
BROWSERLESS_TOKEN = os.environ.get("BROWSERLESS_TOKEN")


def clean_text(text: str) -> str:
    """حذف کامل لینک‌ها و ارجاعات از متن"""
    
    # ۱. حذف تصاویر Markdown: ![alt](url)
    text = re.sub(r'!\[[^\]]*\]\([^)]*\)', '', text)
    
    # ۲. حذف لینک‌های Markdown: [متن](url) → فقط متن را نگه دار
    text = re.sub(r'\[([^\]]*)\]\([^)]*\)', r'\1', text)
    
    # ۳. حذف لینک‌های خالی Markdown: [](url)
    text = re.sub(r'\[\]\([^)]*\)', '', text)
    
    # ۴. حذف لینک‌های ساده http/https
    text = re.sub(r'https?://[^\s\)\]\}]+', '', text)
    
    # ۵. حذف لینک‌های www بدون پروتکل
    text = re.sub(r'www\.[^\s\)\]\}]+', '', text)
    
    # ۶. حذف لینک‌هایی که داخل براکت هستند: [https://...]
    text = re.sub(r'\[https?://[^\]]*\]', '', text)
    
    # ۷. حذف ارجاعات تصویری: [Image 1]، [Figure 2]، [Photo]
    text = re.sub(r'\[(Image|Figure|Picture|Photo|Table|Chart|Graph|Diagram)\s*\d*\]', '', text, flags=re.IGNORECASE)
    
    # ۸. حذف ارجاعات پاورقی: [1]، [2]، [12]
    text = re.sub(r'\[\d+\]', '', text)
    
    # ۹. حذف پرانتزهای خالی: ()
    text = re.sub(r'\(\s*\)', '', text)
    
    # ۱۰. حذف فاصله‌های اضافی و خطوط خالی پشت سر هم
    text = re.sub(r'\n{3,}', '\n\n', text)
    text = re.sub(r'[ \t]{2,}', ' ', text)
    
    # ۱۱. حذف فاصله قبل از نقطه و ویرگول
    text = re.sub(r'\s+([.,;:!?])', r'\1', text)
    
    return text.strip()


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("سلام! لینک مقاله را بفرست تا پردازش کنم.")


async def get_screenshot(url: str) -> bytes:
    """از Browserless می‌خواهد یک اسکرین‌شات کامل از صفحه بگیرد."""
    api_url = f"{BROWSERLESS_URL}/screenshot?token={BROWSERLESS_TOKEN}"
    payload = {
        "url": url,
        "options": {
            "fullPage": True,
            "type": "png"
        }
    }
    response = requests.post(api_url, json=payload, timeout=90)
    if response.status_code == 200:
        return response.content
    else:
        raise Exception(f"Browserless error: {response.status_code}")


async def handle_link(update: Update, context: ContextTypes.DEFAULT_TYPE):
    url = update.message.text
    await update.message.reply_text("در حال پردازش لینک...")
    
    try:
        # ۱. اول متن را با Jina بگیر
        response = requests.get(f"https://r.jina.ai/{url}", timeout=60)
        content = response.text
        
        # ۲. متن را پاک‌سازی کن (حذف لینک‌ها و ارجاعات)
        content = clean_text(content)
        
        # ۳. چک کن که آیا کپچا یا خطا دارد
        if "captcha" in content.lower() or "verify" in content.lower() or len(content) < 500:
            await update.message.reply_text("متن مسدود شد. در حال گرفتن اسکرین‌شات...")
            image_bytes = await get_screenshot(url)
            await update.message.reply_document(document=image_bytes, filename="page.png")
        else:
            # ۴. متن را به تکه‌های ۴۰۰۰ کاراکتری تقسیم کن
            chunk_size = 4000
            chunks = [content[i:i+chunk_size] for i in range(0, len(content), chunk_size)]
            for i, chunk in enumerate(chunks):
                await update.message.reply_text(chunk)
                if i < len(chunks) - 1:
                    await asyncio.sleep(1)
                    
    except Exception as e:
        # ۵. اگر همه چیز خطا داد، حداقل اسکرین‌شات را بفرست
        try:
            image_bytes = await get_screenshot(url)
            await update.message.reply_document(document=image_bytes, filename="page.png")
        except Exception as screenshot_error:
            await update.message.reply_text(f"خطا: {screenshot_error}")


app = ApplicationBuilder().token(BOT_TOKEN).build()
app.add_handler(CommandHandler("start", start))
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_link))
app.run_polling()