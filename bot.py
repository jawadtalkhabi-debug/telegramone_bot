import os
import asyncio
import re
import requests
import cloudscraper
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes

BOT_TOKEN = os.environ.get("BOT_TOKEN")
BROWSERLESS_URL = os.environ.get("BROWSERLESS_URL")
BROWSERLESS_TOKEN = os.environ.get("BROWSERLESS_TOKEN")


def clean_text(text: str) -> str:
    text = re.sub(r'!\[[^\]]*\]\([^)]*\)', '', text)
    text = re.sub(r'\[([^\]]*)\]\([^)]*\)', r'\1', text)
    text = re.sub(r'\[\]\([^)]*\)', '', text)
    text = re.sub(r'https?://[^\s\)\]\}]+', '', text)
    text = re.sub(r'www\.[^\s\)\]\}]+', '', text)
    text = re.sub(r'\[https?://[^\]]*\]', '', text)
    text = re.sub(r'\[(Image|Figure|Picture|Photo|Table|Chart|Graph|Diagram)\s*\d*\]', '', text, flags=re.IGNORECASE)
    text = re.sub(r'\[\d+\]', '', text)
    text = re.sub(r'\(\s*\)', '', text)
    text = re.sub(r'\n{3,}', '\n\n', text)
    text = re.sub(r'[ \t]{2,}', ' ', text)
    text = re.sub(r'\s+([.,;:!?])', r'\1', text)
    return text.strip()


def fetch_via_jina(url: str) -> str:
    response = requests.get(f"https://r.jina.ai/{url}", timeout=60)
    if response.status_code == 200:
        text = response.text
        if "captcha" not in text.lower() and "verify" not in text.lower() and len(text) > 500:
            return text
    raise Exception("Jina failed")


def fetch_via_archive_today(url: str) -> str:
    domains = ["archive.ph", "archive.md", "archive.li", "archive.is"]
    for domain in domains:
        try:
            response = requests.get(
                f"https://{domain}/newest/{url}",
                timeout=30,
                allow_redirects=True,
                headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
            )
            if response.status_code == 200 and len(response.text) > 2000:
                if "This page is not available" not in response.text and "Just a moment" not in response.text:
                    return response.text
        except Exception:
            continue
    raise Exception("Archive.today failed")


def fetch_via_cloudscraper(url: str) -> str:
    scraper = cloudscraper.create_scraper(interpreter='hybrid', impersonate='chrome120')
    response = scraper.get(url, timeout=60)
    if response.status_code == 200 and len(response.text) > 2000:
        return response.text
    raise Exception("Cloudscraper failed")


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("سلام! لینک مقاله را بفرست تا پردازش کنم.")


async def handle_link(update: Update, context: ContextTypes.DEFAULT_TYPE):
    url = update.message.text
    await update.message.reply_text("در حال پردازش لینک...")

    content = None

    for fetcher in [fetch_via_jina, fetch_via_archive_today, fetch_via_cloudscraper]:
        try:
            raw = fetcher(url)
            cleaned = clean_text(raw)
            if len(cleaned) > 500:
                content = cleaned
                break
        except Exception:
            continue

    if content:
        chunk_size = 4000
        chunks = [content[i:i+chunk_size] for i in range(0, len(content), chunk_size)]
        for i, chunk in enumerate(chunks):
            await update.message.reply_text(chunk)
            if i < len(chunks) - 1:
                await asyncio.sleep(1)
        return

    await update.message.reply_text("متن این صفحه قابل دریافت نیست.")


app = ApplicationBuilder().token(BOT_TOKEN).build()
app.add_handler(CommandHandler("start", start))
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_link))
app.run_polling()