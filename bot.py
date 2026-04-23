from telegram import Update
from telegram.ext import ApplicationBuilder, MessageHandler, ContextTypes, filters

TOKEN = "8771703967:AAH9-l96ZZ7DQkuvYJwM7ZL9qplpD9j8DQs"


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip()
    lines = text.split("\n")

    resi = "-"
    isi = "-"
    total = "-"
    status = "-"
    update_terakhir = "-"

    for line in lines:
        if ":" not in line:
            continue

        key, value = line.split(":", 1)
        key = key.strip().upper()
        value = value.strip()

        if key == "RESI":
            resi = value
        elif key == "ISI":
            isi = value
        elif key == "TOTAL":
            total = value

    pesan = f"""Halo! Ini adalah kurir anda dari JNT Xpress! Ini ada paket. 

📦 Resi: {resi}
📄 Isi paket: {isi}
💰 Total: Rp{total}

Mohon maaf sebelum nya untuk paket COD harap melakukan transfer dahulu ke

*BTN*
Rek :*100301700002153* 
A/n : Angga Darma Saputra 
sesuai ketentuan agent yang berlaku, jika tidak bersedia,paket izin kita retur, jika sudah melakukan TF pada hari ini paket nya langsung kami kirim terimakasih

def main():
    app = ApplicationBuilder().token(TOKEN).build()
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    print("Bot jalan...")
    app.run_polling()


if __name__ == "__main__":
    main()
