import requests
import asyncio
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
API_KEY = "06d0849cc962ff2cd360c13967443468b0a8abd7ce7e724786a585ef96573003"

ASK_RESI = 1

keyboard = [["🛒 Lazada J&T", "🛒 Lazada Ninja"]]
reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

user_courier = {}


def detect_cod(summary: dict, history: list) -> tuple[bool, str]:
    service = str(summary.get("service", "")).upper()
    desc = str(summary.get("desc", "")).upper()
    amount = str(summary.get("amount", "")).strip()

    history_text = " ".join(
        str(item.get("desc", "")).upper() for item in history if isinstance(item, dict)
    )

    full_text = f"{service} {desc} {history_text}"

    cod_keywords = [
        "COD",
        "CASH ON DELIVERY",
        "BAYAR DI TEMPAT",
    ]

    is_cod = any(keyword in full_text for keyword in cod_keywords)

    if is_cod and amount and amount != "-":
        return True, amount

    if is_cod:
        return True, ""

    return False, ""


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = (
        "🛒 BOT CEK RESI LAZADA\n\n"
        "Pilih ekspedisi di bawah:\n"
        "• Lazada J&T\n"
        "• Lazada Ninja\n\n"
        "Bisa cek banyak resi sekaligus.\n"
        "Pisahkan dengan enter, spasi, atau koma."
    )
    await update.message.reply_text(text, reply_markup=reply_markup)


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
    text_input = update.message.text.strip().upper()
    resi_list = text_input.replace(",", " ").split()

    if not resi_list:
        await update.message.reply_text("❌ Masukkan nomor resi.", reply_markup=reply_markup)
        return ConversationHandler.END

    if len(resi_list) > 5:
        await update.message.reply_text("❌ Maksimal 5 resi sekali cek.", reply_markup=reply_markup)
        return ConversationHandler.END

    courier = user_courier.get(update.effective_user.id, "jnt")

    if courier == "jnt":
        courier_label = "J&T Express"
        title_label = "🛒 PESANAN LAZADA J&T"
    else:
        courier_label = "Ninja Xpress"
        title_label = "🛒 PESANAN LAZADA NINJA"

    await update.message.reply_text(
        f"🔍 Mengecek {len(resi_list)} resi...\nMohon tunggu ⏳",
        reply_markup=reply_markup
    )

    for resi in resi_list:
        url = "https://api.binderbyte.com/v1/track"
        params = {
            "api_key": API_KEY,
            "courier": courier,
            "awb": resi
        }

        try:
            response = requests.get(url, params=params, timeout=10)
            data = response.json()
        except Exception:
            await update.message.reply_text(
                f"❌ {resi}\nGagal mengambil data (timeout).",
                reply_markup=reply_markup
            )
            continue

        if data.get("status") != 200:
            await update.message.reply_text(
                f"❌ {resi}\nResi tidak ditemukan.",
                reply_markup=reply_markup
            )
            continue

        hasil = data.get("data", {})
        summary = hasil.get("summary", {})
        detail = hasil.get("detail", {})
        history = hasil.get("history", [])
        last = history[0] if history else {}

        is_cod, cod_amount = detect_cod(summary, history)
        service = str(summary.get("service", "-"))

        text = (
            f"{title_label}\n"
            f"📦 EKSPEDISI\n└ {courier_label}\n\n"
            f"📩 Resi\n├ No Resi : {resi}\n└ Service : {service}\n\n"
            f"📮 Status\n├ {summary.get('status', '-')}\n└ {summary.get('date', '-')}\n\n"
            f"🚩 Penerima\n├ {detail.get('receiver', '-')}\n└ {detail.get('destination', '-')}\n\n"
        )

        if is_cod:
            if cod_amount:
                text += f"💰 Pembayaran : COD\n💵 Nominal COD : {cod_amount}\n\n"
            else:
                text += "💰 Pembayaran : COD\n\n"

        text += (
            f"📍 Update Terakhir\n"
            f"├ Lokasi : {last.get('location', '-')}\n"
            f"├ Status : {last.get('desc', '-')}\n"
            f"└ Waktu : {last.get('date', '-')}"
        )

        await update.message.reply_text(text, reply_markup=reply_markup)
        await asyncio.sleep(1)

    await update.message.reply_text("✅ Semua resi selesai dicek.", reply_markup=reply_markup)
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
