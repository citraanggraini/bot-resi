import requests
from telegram import Update
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    ConversationHandler,
    ContextTypes,
    filters,
)

TOKEN = "8675610533:AAHANBzZHAA9VBzgPGNW4SxWKsBSJV9z2GU"
API_KEY = "fdaf0fcf9147f733bcf54b30347d4b377460725818298587ced74e13b3850301"

ASK_RESI, ASK_BARANG, ASK_PEMBAYARAN = range(3)


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🔎 Selamat datang di bot cek resi\n\n"
        "Ketik /cek untuk mulai cek resi."
    )


async def mulai_cek(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("📩 Masukkan nomor resi:")
    return ASK_RESI


async def simpan_resi(update: Update, context: ContextTypes.DEFAULT_TYPE):
    resi = update.message.text.strip().upper()
    context.user_data["resi"] = resi

    await update.message.reply_text("🛍️ Masukkan isi paket:")
    return ASK_BARANG


async def simpan_barang(update: Update, context: ContextTypes.DEFAULT_TYPE):
    barang = update.message.text.strip()
    context.user_data["barang"] = barang

    await update.message.reply_text("💰 Pembayaran? Ketik: COD atau NON COD")
    return ASK_PEMBAYARAN


async def simpan_pembayaran(update: Update, context: ContextTypes.DEFAULT_TYPE):
    pembayaran = update.message.text.strip().upper()
    if pembayaran not in ["COD", "NON COD"]:
        await update.message.reply_text("❌ Ketik hanya: COD atau NON COD")
        return ASK_PEMBAYARAN

    context.user_data["pembayaran"] = pembayaran

    resi = context.user_data["resi"]
    barang = context.user_data["barang"]

    url = "https://api.binderbyte.com/v1/track"
    params = {
        "api_key": API_KEY,
        "courier": "jnt",
        "awb": resi
    }

    try:
        response = requests.get(url, params=params, timeout=30)
        data = response.json()
    except Exception:
        await update.message.reply_text("❌ Gagal mengambil data resi.")
        return ConversationHandler.END

    if data.get("status") != 200:
        await update.message.reply_text("❌ Resi tidak ditemukan.")
        return ConversationHandler.END

    hasil = data.get("data", {})
    summary = hasil.get("summary", {})
    detail = hasil.get("detail", {})
    history = hasil.get("history", [])

    last = history[0] if history else {}

    receiver = detail.get("receiver", "-")
    destination = detail.get("destination", "-")
    service = summary.get("service", "-")
    status_pengiriman = summary.get("status", "-")
    date_pengiriman = summary.get("date", "-")

    lokasi_terakhir = last.get("location", "-")
    desc_terakhir = last.get("desc", "-")
    waktu_terakhir = last.get("date", "-")

    pembayaran = context.user_data["pembayaran"]

    text = (
        "📦 EKSPEDISI JNT\n"
        "└ J&T Express\n\n"
        "📩 Resi\n"
        f"├ No Resi : {resi}\n"
        f"└ Service : {pembayaran} | {service}\n\n"
        "📮 Status\n"
        f"├ {status_pengiriman}\n"
        f"└ {date_pengiriman}\n\n"
        "🚩 Penerima\n"
        f"├ {receiver}\n"
        f"└ {destination}\n\n"
        "🛍️ Barang\n"
        f"└ {barang}\n\n"
        "📍 Update Terakhir\n"
        "├ Kurir : -\n"
        f"├ Lokasi Terakhir : {lokasi_terakhir}\n"
        f"├ Status : {desc_terakhir}\n"
        f"└ Waktu : {waktu_terakhir}"
    )

    await update.message.reply_text(text)
    return ConversationHandler.END


async def batal(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("❌ Dibatalkan.")
    return ConversationHandler.END


def main():
    app = ApplicationBuilder().token(TOKEN).build()

    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("cek", mulai_cek)],
        states={
            ASK_RESI: [MessageHandler(filters.TEXT & ~filters.COMMAND, simpan_resi)],
            ASK_BARANG: [MessageHandler(filters.TEXT & ~filters.COMMAND, simpan_barang)],
            ASK_PEMBAYARAN: [MessageHandler(filters.TEXT & ~filters.COMMAND, simpan_pembayaran)],
        },
        fallbacks=[CommandHandler("batal", batal)],
    )

    app.add_handler(CommandHandler("start", start))
    app.add_handler(conv_handler)

    app.run_polling()


if __name__ == "__main__":
    main()
