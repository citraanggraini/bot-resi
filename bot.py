import requests
from telegram import Update, ReplyKeyboardMarkup
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

ASK_RESI = 1

keyboard = [
    ["🛒 Lazada J&T", "🛒 Lazada Ninja"]
]
reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

user_courier = {}


def get_payment_type(summary: dict) -> str:
    service = str(summary.get("service", "")).upper()
    desc = str(summary.get("desc", "")).upper()
    amount = str(summary.get("amount", "")).strip()

    if "COD" in service or "COD" in desc:
        if amount and amount != "-":
            return f"COD | {amount}"
        return "COD"

    if amount and amount != "-":
        return "NON COD"

    return "NON COD"


def get_amount(summary: dict) -> str:
    amount = str(summary.get("amount", "")).strip()
    if amount and amount != "-":
        return amount
    return "-"


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = (
        "🛒 *BOT CEK RESI LAZADA*\n\n"
        "Pilih ekspedisi di bawah:\n"
        "• 🛒 Lazada J&T\n"
        "• 🛒 Lazada Ninja"
    )
    await update.message.reply_text(
        text,
        parse_mode="Markdown",
        reply_markup=reply_markup
    )


async def pilih_jnt(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_courier[update.effective_user.id] = "jnt"
    await update.message.reply_text(
        "📩 Masukkan nomor resi Lazada J&T:",
        reply_markup=reply_markup
    )
    return ASK_RESI


async def pilih_ninja(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_courier[update.effective_user.id] = "ninja"
    await update.message.reply_text(
        "📩 Masukkan nomor resi Lazada Ninja:",
        reply_markup=reply_markup
    )
    return ASK_RESI


async def cek_resi(update: Update, context: ContextTypes.DEFAULT_TYPE):
    resi = update.message.text.strip().upper()
    courier = user_courier.get(update.effective_user.id, "jnt")

    if courier == "jnt":
        courier_label = "J&T Express"
        title_label = "🛒 PESANAN LAZADA J&T"
    else:
        courier_label = "Ninja Xpress"
        title_label = "🛒 PESANAN LAZADA NINJA"

    url = "https://api.binderbyte.com/v1/track"
    params = {
        "api_key": API_KEY,
        "courier": courier,
        "awb": resi
    }

    try:
        response = requests.get(url, params=params, timeout=30)
        data = response.json()
    except Exception:
        await update.message.reply_text("❌ Gagal mengambil data resi.", reply_markup=reply_markup)
        return ConversationHandler.END

    if data.get("status") != 200:
        await update.message.reply_text("❌ Resi tidak ditemukan.", reply_markup=reply_markup)
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
    pembayaran = get_payment_type(summary)
    harga_paket = get_amount(summary)

    lokasi_terakhir = last.get("location", "-")
    desc_terakhir = last.get("desc", "-")
    waktu_terakhir = last.get("date", "-")

    text = (
        f"{title_label}\n"
        "📦 *EKSPEDISI*\n"
        f"└ {courier_label}\n\n"
        "📩 *Resi*\n"
        f"├ No Resi : `{resi}`\n"
        f"├ Service : {service}\n"
        f"├ Pembayaran : {pembayaran}\n"
        f"└ Harga Paket : {harga_paket}\n\n"
        "📮 *Status*\n"
        f"├ {status_pengiriman}\n"
        f"└ {date_pengiriman}\n\n"
        "🚩 *Penerima*\n"
        f"├ {receiver}\n"
        f"└ {destination}\n\n"
        "📍 *Update Terakhir*\n"
        f"├ Lokasi : {lokasi_terakhir}\n"
        f"├ Status : {desc_terakhir}\n"
        f"└ Waktu : {waktu_terakhir}\n\n"
        "ℹ️ _Bot ini khusus cek resi pesanan Lazada._"
    )

    await update.message.reply_text(
        text,
        parse_mode="Markdown",
        reply_markup=reply_markup
    )
    return ConversationHandler.END


async def handle_button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text

    if text == "🛒 Lazada J&T":
        return await pilih_jnt(update, context)

    if text == "🛒 Lazada Ninja":
        return await pilih_ninja(update, context)

    await update.message.reply_text(
        "Pilih tombol yang tersedia atau ketik /start",
        reply_markup=reply_markup
    )
    return ConversationHandler.END


async def batal(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("❌ Pengecekan dibatalkan.", reply_markup=reply_markup)
    return ConversationHandler.END


def main():
    app = ApplicationBuilder().token(TOKEN).build()

    conv_handler = ConversationHandler(
        entry_points=[
            CommandHandler("cek", start),
            MessageHandler(filters.Regex("^🛒 Lazada J&T$"), pilih_jnt),
            MessageHandler(filters.Regex("^🛒 Lazada Ninja$"), pilih_ninja),
        ],
        states={
            ASK_RESI: [MessageHandler(filters.TEXT & ~filters.COMMAND, cek_resi)],
        },
        fallbacks=[CommandHandler("batal", batal)],
    )

    app.add_handler(CommandHandler("start", start))
    app.add_handler(conv_handler)
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_button))

    app.run_polling()


if __name__ == "__main__":
    main()
