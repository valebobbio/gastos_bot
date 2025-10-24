import gspread


# ruta a las credenciales de mi proy
gc = gspread.service_account(filename="credentials.json")

COLUMNAS = ["Producto","Tipo","Establecimiento","Fecha","Sofi-yo","Precio total ($)","Precio total (U$S)","Total sofi-yo","Llevo ($)","Llevo (U$S)","Queda (aprox)","Queda (1/3)","Queda (2/3)","Queda (3/3)","CRÉDITO","Reservado"]

#Esto a partir de la columna
DEF_COLUMNAS = ["=SUMA(D10:d200)","=SUMA()"]
sh = gc.open("Gastos")  # nombre del archivo en Drive
_active_month = "Octubre"

def set_month(month_name):
    global _active_month
    _active_month = month_name.capitalize()

def create_new_month(month_name,monto_inicial):
    """
    Crea una nueva hoja para el mes con los encabezados predeterminados
    Verifica si el mes ya existe para evitar duplicados
    """
    global _active_month

    month_name = month_name.capitalize()
    
    try:
        # Verificar si ya existe una hoja con ese nombre
        # Intentar acceder a la hoja para ver si existe
        existing_worksheet = sh.worksheet(month_name)
        # Si existe, cambiar a él
        _active_month = month_name
        print(f"✅ Cambiado a hoja existente: '{month_name}'")
        return True
    except gspread.exceptions.WorksheetNotFound:
        try:
            # Crear nueva hoja
            new_worksheet = sh.add_worksheet(
            title=month_name, 
            rows="1000", 
            cols=str(len(COLUMNAS))
            )
        
            # Agregar los encabezados como primera fila
            new_worksheet.append_row(COLUMNAS)
            
            # Opcional: formatear la primera fila como encabezados (negrita)
            try:
                new_worksheet.format('A1:Z1', {'textFormat': {'bold': True}})
            except:
                pass  # Si falla el formateo, no es crítico
            
            # Configurar como mes activo
            _active_month = month_name
            print(f"✅ Hoja '{month_name}' creada")
            return True
            
        except Exception as e:
            print(f"❌ Error creando hoja '{month_name}': {e}")
            return False

def append_row(values):
    ws = sh.worksheet(_active_month)
    ws.append_row(values)