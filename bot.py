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

# ================== CONFIG ==================
TOKEN = "8675610533:AAFsOqT3x4BFTg0pI-Gj5YB3sNk95kmVSyA"
BITESHIP_API_KEY = "biteship_live.eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJuYW1lIjoiYm90LXJlc2kiLCJ1c2VySWQiOiI2OWU1ODc4MGRhZTM3ODU2ZjBmNjYzM2IiLCJpYXQiOjE3NzY2NzYxNzR9.-UHMIAwRuONnVcoT63X2k41wYVc_EOBsa1pjxbZW3b4"
BINDERBYTE_API_KEY = "14405dde2386cb602140b0f9a69489b781a9896b6ccbddd1e0c924f7c073dc64"

ASK_RESI = 1

keyboard = [["🛒 Lazada J&T", "🛒 Lazada Ninja"]]
reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

user_courier = {}


# ================== HELPER ==================
def detect_cod_from_binderbyte(summary: dict, history: list) -> tuple[bool, str]:
    service = str(summary.get("service", "")).upper()
    desc = str(summary.get("desc", "")).upper()
    amount = str(summary.get("amount", "")).strip()

    history_text = " ".join(
        str(item.get("desc", "")).upper() for item in history if isinstance(item, dict)
    )

    full_text = f"{service} {desc} {history_text}"

    cod_keywords = ["COD", "CASH ON DELIVERY", "BAYAR DI TEMPAT"]

    is_cod = any(keyword in full_text for keyword in cod_keywords)

    if is_cod and amount and amount != "-":
        return True, amount

    if is_cod:
        return True, ""

    return False, ""


def check_biteship(resi: str, courier: str):
    url = f"https://api.biteship.com/v1/trackings/{resi}/couriers/{courier}"
    headers = {
        "Authorization": BITESHIP_API_KEY
    }

    response = requests.get(url, headers=headers, timeout=10)
    return response.json()


def check_binderbyte(resi: str, courier: str):
    url = "https://api.binderbyte.com/v1/track"
    params = {
        "api_key": BINDERBYTE_API_KEY,
        "courier": courier,
        "awb": resi
    }

    response = requests.get(url, params=params, timeout=10)
    return response.json()


# ================== START ==================
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


# ================== PILIH KURIR ==================
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


# ================== CEK RESI ==================
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
        biteship_ok = False

        # ===== Coba Biteship dulu =====
        try:
            biteship_data = check_biteship(resi, courier)

            if biteship_data.get("success", False):
                biteship_ok = True

                history = biteship_data.get("history", [])
                last = history[-1] if history else {}

                status = biteship_data.get("status", "-")
                note = last.get("note", "-")
                waktu = last.get("updated_at", "-")

                text = (
                    f"{title_label}\n"
                    f"📦 EKSPEDISI\n└ {courier_label}\n\n"
                    f"📩 Resi\n└ {resi}\n\n"
                    f"📮 Status\n└ {status}\n\n"
                    f"📍 Update Terakhir\n"
                    f"├ Keterangan : {note}\n"
                    f"└ Waktu : {waktu}\n\n"
                    f"🔎 Sumber: Biteship"
                )

                await update.message.reply_text(text, reply_markup=reply_markup)

        except Exception:
            biteship_ok = False

        # ===== Kalau Biteship gagal, fallback ke Binderbyte =====
        if not biteship_ok:
            try:
                binder_data = check_binderbyte(resi, courier)

                if binder_data.get("status") != 200:
                    await update.message.reply_text(
                        f"❌ {resi}\nResi tidak ditemukan.",
                        reply_markup=reply_markup
                    )
                    continue

                hasil = binder_data.get("data", {})
                summary = hasil.get("summary", {})
                detail = hasil.get("detail", {})
                history = hasil.get("history", [])
                last = history[0] if history else {}

                is_cod, cod_amount = detect_cod_from_binderbyte(summary, history)
                service = str(summary.get("service", "-"))

                text = (
                    f"{title_label}\n"
                    f"📦 EKSPEDISI\n└ {courier_label}\n\n"
                    f"📩 Resi\n├ No Resi : {resi}\n"
                    f"└ Service : {service}\n\n"
                    f"📮 Status\n├ {summary.get('status', '-')}\n"
                    f"└ {summary.get('date', '-')}\n\n"
                    f"🚩 Penerima\n├ {detail.get('receiver', '-')}\n"
                    f"└ {detail.get('destination', '-')}\n\n"
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
                    f"└ Waktu : {last.get('date', '-')}\n\n"
                    f"🔎 Sumber: Binderbyte"
                )

                await update.message.reply_text(text, reply_markup=reply_markup)

            except Exception:
                await update.message.reply_text(
                    f"❌ {resi}\nGagal mengambil data dari semua sumber.",
                    reply_markup=reply_markup
                )

        await asyncio.sleep(1)

    await update.message.reply_text("✅ Semua resi selesai dicek.", reply_markup=reply_markup)
    return ConversationHandler.END


# ================== BATAL ==================
async def batal(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("❌ Dibatalkan.", reply_markup=reply_markup)
    return ConversationHandler.END


# ================== MAIN ==================
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
