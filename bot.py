 from telegram import Update
from telegram.ext import ApplicationBuilder, MessageHandler, ContextTypes, filters

# MASUKKAN TOKEN BOT DI SINI
TOKEN = "8771703967:AAH9-l96ZZ7DQkuvYJwM7ZL9qplpD9j8DQs"


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip()

    # pisah paket berdasarkan ---
    blocks = [b.strip() for b in text.split("---") if b.strip()]

    for block in blocks:
        lines = block.split("\n")

        resi = "-"
        isi = "-"
        nomor = "-"
        harga = "-"

        for line in lines:
            if ":" not in line:
                continue

            key, value = line.split(":", 1)
            key = key.strip().lower()
            value = value.strip()

            if "resi" in key:
                resi = value
            elif "isi" in key:
                isi = value
            elif "nomor" in key or "hp" in key:
                nomor = value
            elif "harga" in key:
                harga = value

        pesan = f"""Halo! Ini adalah kurir anda dari *JNT Xpress*! Ini ada paket.

Resi: {resi}
Isi paket: {isi}
Nomor: {nomor}
Total: Rp{harga}

Mohon maaf sebelum nya untuk paket COD harap melakukan transfer dahulu ke

*BTN*
*Rek : 100301700002153*
*A/n : Angga Darma Saputra*

Sesuai ketentuan yang berlaku, apabila tidak bersedia melanjutkan, paket akan dikembalikan.
Jika pembayaran telah dilakukan hari ini, paket akan segera diproses untuk pengiriman.

Terima kasih.
"""

        await update.message.reply_text(pesan, parse_mode="Markdown")


def main():
    app = ApplicationBuilder().token(TOKEN).build()

    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    print("Bot jalan...")
    app.run_polling()


if __name__ == "__main__":
    main()
