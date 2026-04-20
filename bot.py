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

TOKEN = "8675610533:AAFsOqT3x4BFTg0pI-Gj5YB3sNk95kmVSyA"
API_KEY = "fdaf0fcf9147f733bcf54b30347d4b377460725818298587ced74e13b3850301"

ASK_RESI = 1

keyboard = [["🛒 Lazada J&T", "🛒 Lazada Ninja"]]
reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

user_courier = {}


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = (
        "🛒 BOT CEK RESI LAZADA\n\n"
        "Pilih ekspedisi di bawah:\n"
        "• Lazada J&T\n"
        "• Lazada Ninja\n\n"
        "Kamu juga bisa cek banyak resi sekaligus.\n"
        "Pisahkan dengan enter, spasi, atau koma."
    )
    await update.message.reply_text(text, reply_markup=reply_markup)


async def pilih_jnt(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_courier[update.effective_user.id] = "jnt"
    await update.message.reply_text(
        "📩 Masukkan nomor resi Lazada J&T:\n\n"
        "Bisa 1 resi atau banyak resi sekaligus.",
        reply_markup=reply_markup
    )
    return ASK_RESI


async def pilih_ninja(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_courier[update.effective_user.id] = "ninja"
    await update.message.reply_text(
        "📩 Masukkan nomor resi Lazada Ninja:\n\n"
        "Bisa 1 resi atau banyak resi sekaligus.",
        reply_markup=reply_markup
    )
    return ASK_RESI


async def cek_resi(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text_input = update.message.text.strip().upper()

    # support banyak resi: enter, spasi, koma
    resi_list = text_input.replace(",", " ").split()

    if not resi_list:
        await update.message.reply_text("❌ Masukkan nomor resi dulu.", reply_markup=reply_markup)
        return ConversationHandler.END

    courier = user_courier.get(update.effective_user.id, "jnt")

    if courier == "jnt":
        courier_label = "J&T Express"
        title_label = "🛒 PESANAN LAZADA J&T"
    else:
        courier_label = "Ninja Xpress"
        title_label = "🛒 PESANAN LAZADA NINJA"

    hasil_text = []

    for resi in resi_list:
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
            hasil_text.append(
                f"❌ *{resi}*\n"
                f"Gagal mengambil data resi.\n"
            )
            continue

        if data.get("status") != 200:
            hasil_text.append(
                f"❌ *{resi}*\n"
                f"Resi tidak ditemukan.\n"
            )
            continue

        hasil = data.get("data", {})
        summary = hasil.get("summary", {})
        detail = hasil.get("detail", {})
        history = hasil.get("history", [])
        last = history[0] if history else {}

        status_pengiriman = summary.get("status", "-")
        date_pengiriman = summary.get("date", "-")

        hasil_text.append(
            f"{title_label}\n"
            f"📦 *EKSPEDISI*\n"
            f"└ {courier_label}\n\n"
            f"📩 *Resi*\n"
            f"├ No Resi : `{resi}`\n"
            f"└ Service : {summary.get('service', '-')}\n\n"
            f"📮 *Status*\n"
            f"├ {status_pengiriman}\n"
            f"└ {date_pengiriman}\n\n"
            f"🚩 *Penerima*\n"
            f"├ {detail.get('receiver', '-')}\n"
            f"└ {detail.get('destination', '-')}\n\n"
            f"📍 *Update Terakhir*\n"
            f"├ Lokasi : {last.get('location', '-')}\n"
            f"├ Status : {last.get('desc', '-')}\n"
            f"└ Waktu : {last.get('date', '-')}\n"
        )

    final_text = "\n━━━━━━━━━━━━━━\n\n".join(hasil_text)

    # kalau hasil terlalu panjang, kirim per bagian
    if len(final_text) <= 4000:
        await update.message.reply_text(final_text, parse_mode="Markdown", reply_markup=reply_markup)
    else:
        potongan = ""
        for bagian in hasil_text:
            teks_bagian = bagian + "\n━━━━━━━━━━━━━━\n\n"
            if len(potongan) + len(teks_bagian) > 4000:
                await update.message.reply_text(potongan, parse_mode="Markdown", reply_markup=reply_markup)
                potongan = teks_bagian
            else:
                potongan += teks_bagian

        if potongan:
            await update.message.reply_text(potongan, parse_mode="Markdown", reply_markup=reply_markup)

    return ConversationHandler.END


async def batal(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("❌ Dibatalkan.", reply_markup=reply_markup)
    return ConversationHandler.END


def main():
    app = ApplicationBuilder().token(TOKEN).build()

    conv_handler = ConversationHandler(
        entry_points=[
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

    app.run_polling()


if __name__ == "__main__":
    main()
    
