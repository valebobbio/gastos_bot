from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
import pytesseract
from PIL import Image
import requests
import io
import os
from dotenv import load_dotenv
import re
from sheets_utils import set_month, append_row
import gspread

load_dotenv()  # busca un .env en la carpeta
TOKEN = os.environ.get("TOKEN")

#TODO ESTO VA PARA VAR DE ENTORNO
# no tengo tesseract en el path, de lo contrario comentar esta línea
pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"

# no tengo TESSDATA_PREFIX en el path, después lo agrego
if os.name == 'nt' and "TESSDATA_PREFIX" not in os.environ:
    possible = r"C:\Program Files\Tesseract-OCR\tessdata"
    if os.path.isdir(possible):
        os.environ["TESSDATA_PREFIX"] = r"C:\Program Files\Tesseract-OCR\tessdata\\"
    else:
        # lanza error de todos modos si esto está mal
        pass


# conexión con la hoja
gc = gspread.service_account(filename="credentials.json")
sh = gc.open("Gastos")


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("👋 Mandame una foto de tu ticket para leerla.")

async def handle_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    photo = update.message.photo[-1]
    file = await photo.get_file()
    file_bytes = requests.get(file.file_path).content
    image = Image.open(io.BytesIO(file_bytes))

    #leo texto
    text = pytesseract.image_to_string(image, lang='spa')

    # --- Buscar la FECHA (formato DD/MM/AAAA)
    fecha = re.search(r"\b(\d{1,2}/\d{1,2}/\d{2,4})\b", text)
    fecha = fecha.group(1) if fecha else "No detectada"

    # --- Buscar la línea 'CONSUMO FINAL' (ignora mayúsculas/minúsculas)
    consumo = re.search(r"(consumo\s*final)", text, re.IGNORECASE)
    consumo = consumo.group(1).upper() if consumo else "No encontrado"

    resultado = f"🧾 Datos detectados:\n\nFecha: {fecha}\nTipo: {consumo}"

    # Guardamos para uso posterior
    context.user_data["last_text"] = text
    context.user_data["fecha"] = fecha
    context.user_data["tipo"] = consumo

# handler para /mes
async def cambiar_mes(update, context):
    if not context.args:
        await update.message.reply_text("Usá: /mes <NombreDelMes> (ej: /mes Noviembre)")
        return
    nuevo = context.args[0]
    set_month(nuevo)
    await update.message.reply_text(f"📁 Hoja activa: {nuevo.capitalize()}")

# al aceptar el ticket:
append_row([fecha, tipo, total])

app = Application.builder().token(TOKEN).build()
app.add_handler(CommandHandler("start", start))
app.add_handler(CommandHandler("mes", cambiar_mes))
app.add_handler(MessageHandler(filters.PHOTO, handle_photo))

app.run_polling()
