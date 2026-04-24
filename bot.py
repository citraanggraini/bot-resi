from telegram import Update
from telegram.ext import ApplicationBuilder, MessageHandler, ContextTypes, filters
import re

TOKEN = "8771703967:AAGZg1hbOwDpi6rPJNapLccNrBHpDrdhwZg"


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # ambil text dari user
    text = update.message.text or ""
    lines = [line.strip() for line in text.split("\n") if line.strip()]

    resi = "-"
    isi = "-"
    total = "-"
    nomor = "-"  # tetap kosong

    for i, line in enumerate(lines):

        # ambil resi
        if "No Resi" in line:
            try:
                resi = line.split(":", 1)[1].strip()
            except:
                pass

        # ambil isi paket (baris setelah "Barang")
        if "Barang" in line:
            try:
                isi = lines[i + 1].replace("┗", "").strip()
            except:
                pass

        # ambil total harga (hanya Rp)
        if "Rp" in line:
            cocok = re.search(r"Rp[\d\.\,]+", line)
            if cocok:
                total = cocok.group()

    # pesan balasan
    pesan = f"""Halo! Ini adalah *kurir Anda dari JNT Xpress!* ini ada paket.

*Resi:* {resi}
*Isi paket:* {isi}
*Total:* {total}

Mohon maaf sebelumnya, untuk *paket dengan metode pembayaran COD*, sesuai *ketentuan operasional agen JNE wilayah*, pembayaran *dimohon untuk ditransfer terlebih dahulu* agar paket dapat diproses keluar dari gudang pengiriman dan langsung diantar ke alamat tujuan.

*Bank BTN*
*No. Rekening :* 100301700002153
*Atas Nama :* Angga Darma Saputra

Apabila tidak ada konfirmasi pembayaran, maka paket akan *diproses retur ke pihak pengirim sesuai prosedur pengiriman yang berlaku*

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
 
