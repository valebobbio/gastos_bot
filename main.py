# De momento solo reconoce el formato de boleta del Disco (y otras cadenas grandes como Kinko) y pretendo permitir ingreso manual
# correr con: .\.venv\Scripts\activate
#             python main.py
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
import pytesseract
from PIL import Image
import requests
import io
import os
from dotenv import load_dotenv
import re
from sheet_utils import create_new_month, append_row
import gspread

load_dotenv()  # Busca un .env en la carpeta
# Token del bot de telegram
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

# VARIABLES GLOBALES
productos_en_fila = "" 
hay_error_en_datos = []


# FUNCIONES
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("👋 Mandame una foto de tu ticket para leerla.")

async def handle_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    photo = update.message.photo[-1]
    file = await photo.get_file()
    file_bytes = requests.get(file.file_path).content
    image = Image.open(io.BytesIO(file_bytes))

    # Leo texto
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

            if not linea:
                i += 1
                continue
            
            # Si la línea termina con ":" o con una letra es un nombre de producto
            if linea[-1].isalpha():
                nombre_producto = linea[:-1]
                
                # Buscar la siguiente línea que contiene cantidad y precio
                if i + 1 < len(lineas):
                    siguiente_linea = lineas[i + 1].strip()
                    
                    # Buscar el patrón: cantidad UN X precio
                    match = re.search(r'(\d+\.?\d*)\s*(?:UN|KG)\s*X\s*(\d+\.?\d*)', siguiente_linea)
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
                productos_formateados += f"{producto['nombre']}: {producto['cantidad']} UN/KG X {producto['precio']}\n"
        else:
            productos_formateados = "No se detectaron productos"

    resultado = f"🧾 Datos detectados:\n\nFecha: {fecha}\n Productos:\n{productos_formateados}"
    await update.message.reply_text(resultado+"\n"+text)
    
    # Guardamos para uso posterior
    context.user_data["last_text"] = text
    context.user_data["productos"] = productos_formateados
    context.user_data["fecha"] = fecha

# Handler para ingreso manual de datos
async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    texto = update.message.text
    
    if texto.strip().lower() == 'ok':
        if (productos_en_fila==""): 
            await update.message.reply_text(f"No hay productos para guardar :/ \nEnvíe /help para obtener información")
        try:
            append_row(productos_en_fila) 
            await update.message.reply_text(f"Productos añadidos con éxito :)") 
        except Exception as e:
            error_message = str(e)
            await update.message.reply_text(f"Error al guardar datos :( \n{error_message}")

        await update.message.reply_text(mensaje)

        return
    
    lineas = texto.split('\n')
    
    productos_detallados = []
    nro_linea = 0
    for linea in lineas:
        nro_linea+=1
        linea = linea.strip()
        if not linea: 
            continue

        atributos = linea.split(';')
        
        # Limpiar cada atributo de espacios y verificar que haya al menos 4 atributos
        atributos = [attr.strip() for attr in atributos]
        
        if len(atributos) >= 4:
            # Extraer primera y última palabra de atributos[3]
            palabras = atributos[3].split(".")
            comprador = palabras[0]
            destinatario = palabras[1].split()
            
            if len(palabras) <= 2:
                quien = f"{palabras[0]} {palabras[-1]}"
            elif len(palabras)>2:
                quien = 
            else:
                quien = atributos[3]
            productos_detallados.append({
                'nombre': atributos[0],
                'precio': atributos[1],
                'fecha': atributos[2],
                'comprador': comprador,
                'destinatario': destinatario
            })
        else:
            hay_error_en_datos.append({nro_linea})
            print(f"Error en los datos del producto {nro_linea}, por favor corrija con /edit")
        productos_en_fila = productos_detallados

    # Mensaje de respuesta
    if productos_detallados:
        # Formatear cada producto en una línea separada e indexada
        mensaje = ""
        it = 1
        for producto in productos_detallados:
            mensaje += f"{it}) {producto['nombre']} {producto['precio']} {producto['fecha']} {producto['quien']}\n"
            it+=1
        if hay_error_en_datos:
            mensaje += f"Faltan datos en las líneas: "
            for nro in hay_error_en_datos:
                mensaje += nro
            mensaje += f"\nCorrija con /edit, el error puede deberse a falta de datos o falta de separadores ';' "
        await update.message.reply_text(mensaje.strip())
    else:
        await update.message.reply_text("No se detectaron productos válidos en el texto.")


# Handler para /mes
async def cambiar_mes(update, context):
    if not context.args:
        await update.message.reply_text("Usá: /mes <NombreDelMes> <Importe Inicial (opcional)> (ej: /mes Noviembre 20000)")
        return
    
    mes = context.args[0].capitalize()
    
    # Verificar si se proporcionó un importe
    if len(context.args) > 1:
        try:
            importe = float(context.args[1])
        except ValueError:
            await update.message.reply_text("❌ El importe debe ser un número válido")
            return
    else:
        importe = 13000  
    
    create_new_month(mes, importe)
    await update.message.reply_text(f"📁 Hoja activa: {mes}") # Tal vez luego especifique si se creó o solo se cambió a la existente

# handler para /help
async def ayuda(update, context):
    await update.message.reply_text("Formatos de entrada: \n" \
    "/mes <NombreDelMes> <Importe Inicial (opt)>\n" \
    "/edit --sin definir--\n" \
    "Ingreso de datos por mensaje: <nombreDelProducto; precio; fecha; comprador a destinatario/s>\n" \
    "---Si alguno de los datos queda vacío, se deben igualmente respetar los ; separadores\n" \
    # Idea intuitiva de lo de abajo: comprador C y destinatario D, D es el dueño de la cuenta
    # C compra algo para D, ahora D le debe el costo del producto a C, se escribe "C a D"
    # C compra algo para D y C, ahora D le debe la mitad del costo del producto a C, se escribe "C a D y C"
    "---Formato comp a dest: <nombre_comprador a nombre_destinatario1> <y nombre_destinatario2 (opcional si es igual a nombre_comprador)>")

async def edit(update, context):
    if not context.args:
        await update.message.reply_text("Usá: /mes <NombreDelMes> <Importe Inicial (opcional)> (ej: /mes Noviembre 20000)")
        return


# al aceptar el ticket:
#append_row([fecha, tipo, total])

app = Application.builder().token(TOKEN).build()
app.add_handler(CommandHandler("start", start))
app.add_handler(CommandHandler("mes", cambiar_mes))
app.add_handler(CommandHandler("help", ayuda))
app.add_handler(MessageHandler(filters.PHOTO, handle_photo))
app.add_handler(MessageHandler(filters.TEXT, handle_text))
app.add_handler(CommandHandler("edit", edit))

app.run_polling()
