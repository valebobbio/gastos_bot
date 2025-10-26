import gspread


# ruta a las credenciales de mi proy
gc = gspread.service_account(filename="credentials.json")

COLUMNAS = ["Producto",
            "Tipo",
            "Establecimiento",
            "Fecha",
            "Sofi-yo",
            "Precio total ($)",
            "Precio total (U$S)",
            "Total sofi-yo",
            "Llevo ($)",
            "Llevo (U$S)",
            "Queda (aprox)",
            "Queda (1/3)",
            "Queda (2/3)",
            "Queda (3/3)",
            "CRÉDITO",
            "Reservado"]

#Esto a partir de la columna
DEF_COLUMNAS = ["=SUMA(D10:d200)","=SUMA()"]
sh = gc.open("Gastos")  # nombre del archivo en Drive
_active_month = "Octubre"

def set_month(month_name):
    global _active_month
    _active_month = month_name.capitalize()

def get_column_letter(column_name):
    """
    Obtiene la letra de la columna basada en su nombre en los encabezados
    """
    if column_name not in COLUMNAS:
        raise ValueError(f"Columna '{column_name}' no encontrada en los encabezados")
    
    column_index = COLUMNAS.index(column_name)
    return chr(65 + column_index)  # 65 = 'A' en ASCII

def create_new_month(month_name,monto_inicial):
    """
    Crea una nueva hoja para el mes indicado
    Si ya existe cambia a él
    """
    global _active_month

    month_name = month_name.capitalize()
    
    try:
        # Intentar acceder a la hoja para ver si existe
        existing_worksheet = sh.worksheet(month_name)
        # Si existe, cambiar a él
        _active_month = month_name
        print(f"✅ Cambiado a hoja existente: '{month_name}'")
        return True
    except gspread.exceptions.WorksheetNotFound:
        try:
            # Nueva hoja
            new_worksheet = sh.add_worksheet(
            title=month_name, 
            rows="1000", 
            cols=str(len(COLUMNAS))
            )
        
            # Agrego los encabezados pre-seteados
            new_worksheet.append_row(COLUMNAS)
            
            # Primera fila en negrita
            #try:
            new_worksheet.format('A1:Z1', {'textFormat': {'bold': True}})
            #except:
            #   pass  # No pasa nada si falla

            #---------------------------------
            # Agrego los cálculos de atributos
            #---------------------------------
            ws = sh.worksheet(month_name) # Obtener la hoja

            # Colmna sofi-yo
            target = get_column_letter("Total sofi-yo")
            source = get_column_letter("Sofi-yo")
            last_row=len(ws.get_all_values())

            # Crear la fórmula
            formula = f"=SUM({source}{2}:{source}{last_row})"

            # Insertar la fórmula en la primera celda vacía de la columna target
            target_col_values = ws.col_values(COLUMNAS.index(target) + 1)
            first_empty_row = len(target_col_values) + 1            
            ws.update(f"{target}{first_empty_row}", [[formula]])
            




            
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