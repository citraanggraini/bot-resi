import os
import requests
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes

TOKEN = os.getenv("TOKEN")
API_KEY = os.getenv("API_KEY")

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Kirim nomor resi J&T kamu")

async def cek_resi(update: Update, context: ContextTypes.DEFAULT_TYPE):
    resi = update.message.text.strip().upper()

    url = f"https://api.binderbyte.com/v1/track?api_key={API_KEY}&courier=jnt&awb={resi}"

    try:
        response = requests.get(url).json()
    except:
        await update.message.reply_text("❌ Gagal mengambil data")
        return

    if response.get("status") == 200:
        data = response["data"]
        summary = data.get("summary", {})
        detail = data.get("detail", {})
        history = data.get("history", [])

        last = history[0] if history else {}

        text = f"""
📦 EKSPEDISI J&T
└ J&T Express

📩 Resi
├ No Resi : {resi}
└ Service : {summary.get("service", "-")}

📮 Status
├ {summary.get("status", "-")}
└ {summary.get("date", "-")}

🚩 Penerima
├ {detail.get("receiver", "-")}
└ {detail.get("destination", "-")}

📍 Update Terakhir
├ Lokasi : {last.get("location", "-")}
├ Status : {last.get("desc", "-")}
└ Waktu : {last.get("date", "-")}
"""
        await update.message.reply_text(text)
    else:
        await update.message.reply_text("❌ Resi tidak ditemukan")

app = ApplicationBuilder().token(TOKEN).build()

app.add_handler(CommandHandler("start", start))
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, cek_resi))

app.run_polling()
