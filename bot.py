import os
import requests
from telegram import Update
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    filters,
)

TOKEN = os.getenv("TOKEN")
API_KEY = os.getenv("API_KEY")

BASE_URL = "https://api.biteship.com/v1"


def detect_primary_couriers(resi: str):
    r = resi.upper().strip().replace(" ", "")

    # Lazada J&T / J&T umum
    if r.startswith("JZ"):
        return ["jnt"]
    if r.startswith(("JT", "JP", "JX")):
        return ["jnt"]

    # JNE
    if r.startswith("JNE"):
        return ["jne"]

    # Kalau angka semua, coba beberapa kurir
    if r.isdigit():
        return ["jne", "jnt", "sicepat", "ninja", "anteraja"]

    # fallback
    return ["jnt", "jne", "sicepat", "ninja", "anteraja"]


def request_tracking(resi: str, courier: str):
    url = f"{BASE_URL}/trackings/{resi}/couriers/{courier}"
    headers = {
        "Authorization": f"Bearer {API_KEY}"
    }

    try:
        response = requests.get(url, headers=headers, timeout=20)
        if response.status_code == 200:
            return response.json()
        return None
    except Exception:
        return None


def pick_latest_history(data: dict):
    history = data.get("history", [])
    if not history:
        return None
    return history[-1]


def extract_payment_label(data: dict):
    courier_info = data.get("courier", {})
    service = data.get("service", {})
    payment_type = (
        service.get("payment_type")
        or courier_info.get("payment_type")
        or ""
    )

    price = (
        service.get("price")
        or courier_info.get("price")
        or data.get("price")
        or ""
    )

    if str(payment_type).upper() == "COD":
        return f"COD | Rp{price}" if price else "COD"
    if price:
        return f"Non COD | Rp{price}"
    return "Non COD"


def build_result_text(resi: str, courier: str, data: dict):
    latest = pick_latest_history(data)

    courier_name = courier.upper()
    if courier == "jnt":
        courier_name = "J&T Express"
    elif courier == "jne":
        courier_name = "JNE"
    elif courier == "sicepat":
        courier_name = "SiCepat"
    elif courier == "ninja":
        courier_name = "Ninja Xpress"
    elif courier == "anteraja":
        courier_name = "AnterAja"

    receiver = data.get("destination", {})
    receiver_name = receiver.get("contact_name") or "-"
    receiver_address = receiver.get("address") or "-"

    item_name = (
        data.get("order", {}).get("items_name")
        or data.get("item_name")
        or "-"
    )

    status = data.get("status") or "-"
    updated_at = data.get("updated_at") or "-"

    latest_note = "-"
    latest_status = status
    latest_time = updated_at
    latest_location = "-"
    latest_courier = courier_name

    if latest:
        latest_note = latest.get("note") or "-"
        latest_status = latest.get("status") or status or "-"
        latest_time = latest.get("updated_at") or updated_at or "-"
        latest_location = latest.get("location") or "-"

    payment_label = extract_payment_label(data)

    text = (
        f"📦 EKSPEDISI {courier_name.upper()}\n\n"
        f"📩 Resi\n"
        f"└ No Resi : {resi}\n"
        f"└ Service : {payment_label}\n\n"
        f"📮 Status\n"
        f"└ {latest_status}\n"
        f"└ {latest_time}\n\n"
        f"🚩 Penerima\n"
        f"└ {receiver_name}\n"
        f"└ {receiver_address}\n\n"
        f"🛍 Barang\n"
        f"└ {item_name}\n\n"
        f"📍 Update Terakhir\n"
        f"└ Kurir : {latest_courier}\n"
        f"└ Lokasi Terakhir : {latest_location}\n"
        f"└ Status : {latest_note}\n"
        f"└ Waktu : {latest_time}"
    )
    return text


def check_tracking(resi: str):
    couriers = detect_primary_couriers(resi)

    for courier in couriers:
        data = request_tracking(resi, courier)
        if isinstance(data, dict):
            return build_result_text(resi, courier, data)

    return (
        "❌ Resi tidak ditemukan.\n\n"
        "Coba pastikan:\n"
        "- nomor resi benar\n"
        "- resi sudah aktif di sistem kurir\n"
        "- resi bukan baru dibuat beberapa menit lalu"
    )


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = (
        "Bot aktif ✅\n\n"
        "Cara pakai:\n"
        "1. Kirim langsung nomor resi\n"
        "2. Atau pakai /cek NOMOR_RESI\n\n"
        "Contoh:\n"
        "JZ10828890501\n"
        "/cek JZ10828890501"
    )
    await update.message.reply_text(text)


async def cek(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text(
            "Format salah.\nContoh:\n/cek JZ10828890501"
        )
        return

    resi = context.args[0].strip().replace(" ", "")
    await update.message.reply_text("🔎 Sedang cek resi...")

    try:
        result = check_tracking(resi)
        await update.message.reply_text(result)
    except Exception as e:
        await update.message.reply_text(f"❌ Terjadi error:\n{e}")


async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message or not update.message.text:
        return

    text = update.message.text.strip()

    # kalau command lain, abaikan
    if text.startswith("/"):
        return

    resi = text.replace(" ", "")
    await update.message.reply_text("🔎 Sedang cek resi...")

    try:
        result = check_tracking(resi)
        await update.message.reply_text(result)
    except Exception as e:
        await update.message.reply_text(f"❌ Terjadi error:\n{e}")


def main():
    if not TOKEN:
        raise ValueError("TOKEN belum diisi di Railway Variables")
    if not API_KEY:
        raise ValueError("API_KEY belum diisi di Railway Variables")

    app = ApplicationBuilder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("cek", cek))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))

    print("Bot jalan...")
    app.run_polling()


if __name__ == "__main__":
    main()
