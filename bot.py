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
API_KEY = "biteship_live.eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJuYW1lIjoiYm90LXJlc2kiLCJ1c2VySWQiOiI2OWU1ODc4MGRhZTM3ODU2ZjBmNjYzM2IiLCJpYXQiOjE3NzY2NzYxNzR9.-UHMIAwRuONnVcoT63X2k41wYVc_EOBsa1pjxbZW3b4
"

ASK_RESI = 1

keyboard = [["🛒 Lazada J&T", "🛒 Lazada Ninja"]]
reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

user_courier = {}


def map_status(status: str) -> str:
    status_map = {
        "confirmed": "Pesanan dikonfirmasi",
        "allocated": "Kurir dialokasikan",
        "pickingUp": "Kurir menuju pickup",
        "picked": "Paket sudah diambil",
        "droppingOff": "Paket dalam pengiriman",
        "returnInTransit": "Paket retur dalam perjalanan",
        "onHold": "Paket ditahan sementara",
        "delivered": "Paket sudah diterima",
        "rejected": "Paket ditolak",
        "courierNotFound": "Kurir tidak ditemukan",
        "returned": "Paket berhasil diretur",
        "cancelled": "Pesanan dibatalkan",
        "disposed": "Pesanan dibuang",
    }
    return status_map.get(status, status)


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
        courier_code = "jnt"
    else:
        courier_label = "Ninja Xpress"
        title_label = "🛒 PESANAN LAZADA NINJA"
        courier_code = "ninja"

    await update.message.reply_text(
        f"🔍 Mengecek {len(resi_list)} resi...\nMohon tunggu ⏳",
        reply_markup=reply_markup
    )

    headers = {
        "Authorization": API_KEY
    }

    for resi in resi_list:
        url = f"https://api.biteship.com/v1/trackings/{resi}/couriers/{courier_code}"

        try:
            response = requests.get(url, headers=headers, timeout=15)
            data = response.json()
        except Exception:
            await update.message.reply_text(
                f"❌ {resi}\nGagal mengambil data tracking.",
                reply_markup=reply_markup
            )
            continue

        if not data.get("success", False):
            message = data.get("message", "Resi tidak ditemukan atau belum aktif.")
            await update.message.reply_text(
                f"❌ {resi}\n{message}",
                reply_markup=reply_markup
            )
            continue

        history = data.get("history", [])
        last = history[-1] if history else {}

        status_raw = data.get("status", "-")
        status_text = map_status(status_raw)

        penerima = data.get("destination", {}).get("contact_name", "-")
        alamat = data.get("destination", {}).get("address", "-")
        driver_name = data.get("courier", {}).get("driver_name", "-")
        driver_phone = data.get("courier", {}).get("driver_phone", "-")
        link = data.get("link", "-")

        note = last.get("note", "-")
        updated_at = last.get("updated_at", "-")
        hist_status = map_status(last.get("status", "-"))

        text = (
            f"{title_label}\n"
            f"📦 EKSPEDISI\n└ {courier_label}\n\n"
            f"📩 Resi\n├ No Resi : {resi}\n└ Kurir Code : {courier_code}\n\n"
            f"📮 Status\n├ {status_text}\n└ Update : {updated_at}\n\n"
            f"🚩 Penerima\n├ {penerima}\n└ {alamat}\n\n"
            f"🛵 Kurir\n├ Nama : {driver_name}\n└ Telepon : {driver_phone}\n\n"
            f"📍 Update Terakhir\n"
            f"├ Status : {hist_status}\n"
            f"├ Catatan : {note}\n"
            f"└ Waktu : {updated_at}\n\n"
            f"🔗 Link Tracking\n└ {link}"
        )

        await update.message.reply_text(text, reply_markup=reply_markup)
        await asyncio.sleep(0.5)

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
