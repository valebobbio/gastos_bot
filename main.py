# De momento solo reconoce el formato de boleta del Disco
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
import pytesseract
from PIL import Image
import requests
import io
import os
from dotenv import load_dotenv
import re
from sheet_utils import set_month, append_row
import gspread

load_dotenv()  # busca un .env en la carpeta
TOKEN = os.environ.get("TOKEN")

#TODO ESTO VA PARA VAR DE ENTORNO {
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
#}

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

    # --- Buscar productos después de "MONEDA: UYU" hasta el total
    patron_productos = r"MONEDA: UYU\s*(.*?)\s*(?:TOT|TOTAL)"
    productos_match = re.search(patron_productos, text, re.DOTALL | re.IGNORECASE)

    if productos_match:
        # Limpiar y formatear el texto de productos
        productos_texto = productos_match.group(1).strip()
        productos_texto = re.sub(r'/\s*0\s*\.\s*\d*\.?\d+', '', productos_texto)
        
        # Procesar productos individualmente
        lineas = productos_texto.split('\n')
        productos_detallados = []
        i = 0

        while i < len(lineas):
            linea = lineas[i].strip()
            
            # Si la línea termina con ":" es un nombre de producto
            if linea.endswith(':'):
                nombre_producto = linea[:-1].strip()  # Eliminar los dos puntos
                
                # Buscar la siguiente línea que contiene cantidad y precio
                if i + 1 < len(lineas):
                    siguiente_linea = lineas[i + 1].strip()
                    
                    # Buscar el patrón: cantidad UN X precio
                    match = re.search(r'(\d+\.?\d*)\s*UN\s*X\s*(\d+\.?\d*)', siguiente_linea)
                    if match:
                        cantidad = match.group(1)
                        precio = match.group(2)
                        
                        productos_detallados.append({
                            'nombre': nombre_producto,
                            'cantidad': cantidad,
                            'precio': precio
                        })
                        
                        # Saltar a la siguiente línea después de procesar este producto
                        i += 2
                        continue
            
            i += 1

        # Formatear el resultado para mostrar
        if productos_detallados:
            productos_formateados = ""
            for producto in productos_detallados:
                productos_formateados += f"{producto['nombre']}: {producto['cantidad']} UN X {producto['precio']}\n"
        else:
            productos_formateados = "No se detectaron productos"

    resultado = f"🧾 Datos detectados:\n\nFecha: {fecha}\n Productos:\n{productos_formateados}"
    await update.message.reply_text(resultado)
    
    # Guardamos para uso posterior
    context.user_data["last_text"] = text
    context.user_data["fecha"] = fecha

#handler para /mes
async def cambiar_mes(update, context):
    if not context.args:
        await update.message.reply_text("Usá: /mes <NombreDelMes> (ej: /mes Noviembre)")
        return
    nuevo = context.args[0]
    set_month(nuevo)
    await update.message.reply_text(f"📁 Hoja activa: {nuevo.capitalize()}")

# al aceptar el ticket:
#append_row([fecha, tipo, total])

app = Application.builder().token(TOKEN).build()
app.add_handler(CommandHandler("start", start))
#app.add_handler(CommandHandler("mes", cambiar_mes))
app.add_handler(MessageHandler(filters.PHOTO, handle_photo))

app.run_polling()
