from telegram import Update
from telegram.ext import ApplicationBuilder, MessageHandler, ContextTypes, filters
import re

TOKEN ="8771703967:AAGZg1hbOwDpi6rPJNapLccNrBHpDrdhwZg"  
 
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # ambil text dari user
    text = update.message.text or ""
    lines = [line.strip() for line in text.split("\n") if line.strip()]

    resi = "-"
    isi = "-"

    for i, line in enumerate(lines):

        # ambil resi
        if "No Resi" in line:
            try:
                resi = line.split(":", 1)[1].strip()
            except:
                pass

        # ambil isi paket
        if "Barang" in line:
            try:
                isi = lines[i + 1].replace("┗", "").strip()
            except:
                pass

    # pesan balasan
    pesan = f"""Halo kk  
Kami dari *JNT*  
Penyedia ekspedisih pengiriman *JNT XPRESS EXPRESS*  
mau konfirmasi Pesanan di *Lazada.id.com*

*Nomor Resi*: {resi}
*Isi paket*: {isi}

*Kami informasikan Paket saat ini tidak dapat di lanjut ke alamat Anda, karena kesalahan proses input nomor resi oleh tim ekspedisi, sehingga paket tertukar dengan customer lain*

*Bisa di screenshot dari total harga yang dibayar berapa untuk diproses pengembalian dana*

"Elevate Your Style with *Lazada Indonesia.id.com*!"
"""

    await update.message.reply_text(pesan)


def main():
    app = ApplicationBuilder().token(TOKEN).build()

    app.add_handler(
        MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message)
    )

    print("Bot jalan...")
    app.run_polling()


if __name__ == "__main__":
    main()
