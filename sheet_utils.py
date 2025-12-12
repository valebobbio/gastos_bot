# Por ahora los nombres son bastante específicos, luego ver
import gspread

# Ruta a las credenciales de mi proyecto (APIs de Google)
gc = gspread.service_account(filename="credentials.json")

MESES_A_NUMERO = {    'Enero': 1, 'Febrero': 2, 'Marzo': 3, 'Abril': 4, 'Mayo': 5, 'Junio': 6,
    'Julio': 7, 'Agosto': 8, 'Setiembre': 9, 'Octubre': 10, 'Noviembre': 11, 'Diciembre': 12}

COLUMNAS = ["Producto",
            "Tipo",
            "Establecimiento",
            "Fecha",
            "Sofi-yo",
            #"Cant (UN|KG)"
            "Precio total ($)",
            "Precio total (U$S)",
            "Total sofi-yo",
            "Llevo ($)",
            "Llevo (U$S)",
            "Queda (aprox)",
            "Queda (1/3)",
            "Queda (2/3)",
            "Queda (3/3)",
            #"CRÉDITO",
            "Reservado"]

# Nombre del archivo en Drive
sh = gc.open("Gastos")  
# Valor por defecto
_active_month = "Octubre"

# Por ahora no la uso
def set_month(month_name):
    global _active_month
    _active_month = month_name.capitalize()

def get_column_letter(column_name): # Genialidad que solo se le ocurre a chadGPT
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

    month_name = month_name.capitalize() # Innecesario pero idk

    if (month_name == 'Septiembre'): 
        month_name='Setiembre'
    
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
            ws = sh.add_worksheet(
            title=month_name, 
            rows="1000", 
            cols="1000",
            )
        
            # Agrego los encabezados pre-seteados
            ws.append_row(COLUMNAS)
            
            # Primera fila en negrita
            try:
                ws.format('A1:Z1', {'textFormat': {'bold': True}})
            except:
               pass  # No pasa nada si falla

            #----------------------------------------------------------------------------------------------------------
            #----------------------------------------------------------------------------------------------------------
            # -----------Agrego los cálculos de atributos (hardcodeado porque tienen cosas diferentes)-----------------
            #----------------------------------------------------------------------------------------------------------
            #----------------------------------------------------------------------------------------------------------


            #------------------
            #Gastos compartidos
            #------------------
            # Colmna sofi-yo (gestión de gastos en pareja)
            cell_totalsy = ws.find("Total sofi-yo")
            sofiyo_letter = get_column_letter("Sofi-yo")

            # Crear la fórmula
            formula_sofiyo = f"=SUM({sofiyo_letter}2:{sofiyo_letter})"

            ws.update_cell(cell_totalsy.row+1,cell_totalsy.col,formula_sofiyo)
            

            #-------------------
            # Gasto total ($) 
            #-------------------
            # Mi intención es sacar los finds y que esto pase a ser estático. Luego se verá qué es lo mejor
            cell_total_pesos_titulo = ws.find("Llevo ($)")
            total_letter = get_column_letter("Precio total ($)")
            formula_total_pesos = f'=SUM({total_letter}2:{total_letter})'
            ws.update_cell(cell_total_pesos_titulo.row+1, cell_total_pesos_titulo.col, formula_total_pesos)


            #------------------
            # Gasto total (U$S)   
            #------------------
            cell_total_uss_titulo = ws.find("Llevo (U$S)")
            total_uss_letter =get_column_letter("Precio total (U$S)")
            formula_total_uss = f'=SUM({total_uss_letter}2:{total_uss_letter})'
            ws.update_cell(cell_total_uss_titulo.row+1,cell_total_uss_titulo.col,formula_total_uss)


            #-------------------------------------------------------
            # Queda (aproximadamente, valor del dolar no exacto yet)  
            #-------------------------------------------------------
            cell_queda = ws.find("Queda (aprox)")
            suma_pesos_letter = get_column_letter("Llevo ($)")
            suma_uss_letter = get_column_letter("Llevo (U$S)")

            # Aproximo el valor del dolar a 44, aunque mi intención es hacer un scraper a https://www.brou.com.uy/cotizaciones
            ws.update_cell(cell_queda.row+1, cell_queda.col, f'=SUM({monto_inicial};-{suma_pesos_letter}{cell_total_pesos_titulo.row + 1};-{suma_uss_letter}{cell_total_uss_titulo.row + 1}*44)') # Debería funcar bien si lo que multiplico es una celda nomás


            #-------------------
            # División semanal
            #-------------------
            # Obtener el año actual y el número del mes desde el nombre de la hoja
            from datetime import datetime
            current_year = datetime.now().year

            month_number = MESES_A_NUMERO.get(month_name)#, datetime.now().month) por ahora es redundante, salvo que quite la opción de crear cualquier mes
            #day_number = datetime.now().day; # De momento no lo voy a usar, tengo que ver luego si hago las formulas adaptables al día en que creo el mes o no
            
            # Obtener letras de columnas
            fecha_letter = get_column_letter("Fecha")
            total_letter = get_column_letter("Precio total ($)")
            reservado_letter = get_column_letter("Reservado")

            # Estoy seguro de que existen pero podría meterle try-catch por si algo falla en el proceso
            cell_uno = ws.find("Queda (1/3)")
            cell_dos = ws.find("Queda (2/3)")
            cell_tres = ws.find("Queda (3/3)")
            month_tres = month_number%12+1
            
            # Construir fórmulas. División de dinero en tercios mensuales y consideración del valor de "Reservado"
            # En mi caso, $3000 es lo que pretendo gastar cada x días. Podría también hacerlo como un porcentaje del total 
            formula_uno = (f'=3000 - SUMIFS({total_letter}2:{total_letter}; ' # Sumif 1 (Reservado = No)
                           f'{fecha_letter}2:{fecha_letter}; ">="&DATE({current_year};{month_number};1); ' 
                           f'{fecha_letter}2:{fecha_letter}; "<="&DATE({current_year};{month_number};14); '
                           f'{reservado_letter}2:{reservado_letter}; "No") '
                           f'- SUMIFS({total_letter}2:{total_letter}; '# Sumif 2 (Reservado = vacío)
                           f'{fecha_letter}2:{fecha_letter}; ">="&DATE({current_year};{month_number};1); '
                           f'{fecha_letter}2:{fecha_letter}; "<="&DATE({current_year};{month_number};14); {reservado_letter}2:{reservado_letter}; "")')

            formula_dos = (f'=3000 - SUMIFS({total_letter}2:{total_letter}; ' 
                           f'{fecha_letter}2:{fecha_letter}; ">="&DATE({current_year};{month_number};15); '
                           f'{fecha_letter}2:{fecha_letter}; "<="&DATE({current_year};{month_number};25); '
                           f'{reservado_letter}2:{reservado_letter}; "No") '
                           f'- SUMIFS({total_letter}2:{total_letter}; '
                           f'{fecha_letter}2:{fecha_letter}; ">="&DATE({current_year};{month_number};15); '
                           f'{fecha_letter}2:{fecha_letter}; "<="&DATE({current_year};{month_number};25); {reservado_letter}2:{reservado_letter}; "")') 
              
            formula_tres = (f'=3000 - SUMIFS({total_letter}2:{total_letter}; '
                            f'{fecha_letter}2:{fecha_letter}; ">="&DATE({current_year};{month_number};26); '
                            f'{fecha_letter}2:{fecha_letter}; "<="&DATE({current_year};{month_tres};5); ' # Primero %12 luego +1, por el caso de noviembre->diciembre (da 0 sino)
                            f'{reservado_letter}2:{reservado_letter}; "No") '
                            f'- SUMIFS({total_letter}2:{total_letter}; '
                            f'{fecha_letter}2:{fecha_letter}; ">="&DATE({current_year};{month_number};26); '
                            f'{fecha_letter}2:{fecha_letter}; "<="&DATE({current_year};{month_tres};5); {reservado_letter}2:{reservado_letter}; "")')
            # Actualizo los valores (las filas deberían ser todas las mismas pero por las dudas hago los cálculos)
            ws.update_cell(cell_uno.row+1, cell_uno.col, formula_uno)
            ws.update_cell(cell_dos.row+1, cell_dos.col, formula_dos)
            ws.update_cell(cell_tres.row+1, cell_tres.col, formula_tres)


            #----------
            # Reservado
            #----------
            # Bastante ineficiente esto. Aunque solo se ejecute una vez, debo mejorarlo. Cuando haga todo estático se mejora
            # El problema es que no estoy 100% seguro de no agregar más columnas
            cell_reservado_letter = get_column_letter("Reservado")
            cell_reservado_titulo = ws.find("Reservado")
            formula_reservado = f'=SUM({cell_reservado_letter}{cell_reservado_titulo.row+2}:{cell_reservado_letter})'
            ws.update_cell(cell_reservado_titulo.row+1,cell_reservado_titulo.col,formula_reservado) 
            
            # Configurar como mes activo
            _active_month = month_name
            print(f"✅ Hoja '{month_name}' creada")
            return True
            
        except Exception as e:
            print(f"❌ Error creando hoja '{month_name}': {e}")
            return False

# Recibo los productos en filas formato: nombre precio fecha comp-dest
def append_row(productos_en_filas):
    try:
        ws = sh.worksheet(_active_month)

        producto_cell = ws.find("Producto")
        fecha_cell = ws.find("Fecha")
        precio_cell = ws.find("Precio total ($)")
        comp_dest_cell = ws.find("Sofi-yo")

        # Obtengo primera fila vacía
        all_values = ws.get_all_values()
    
        # Si la hoja está vacía hay algo mal. Igualmente nunca debería pasar
        if not all_values:
            raise Exception(f"Error, hoja vacía")
        
        # Buscar desde la primera fila
        for row_num, row in enumerate(all_values, start=3):
            # Si todas las celdas de la fila están vacías
            if all(cell == '' for cell in row):
                return row_num
        
        # Si no encuentra ninguna fila vacía, uso la siguiente a la última
        new_row = len(all_values) + 1
        
        lineas = productos_en_filas.split("\n") # Tengo que hacer esto más eficiente porque esta recorrida la hago mil veces

        for linea in lineas:
            # Hago el cálculo del precio

            # Lógica de comprador-destinatario:
            # -si el comprador no soy yo y no hay destinatario, asumo que (dest.) soy yo
            # -si el destinatario no soy yo y no hay comprador, asumo que (comp.) es sofi (o la persona con quien comparta gastos más seguido, la col. <nombre>-yo)
            # -si no hay ninguno, soy ambos (es decir, no es necesario aclarar cuando compro algo para mí)
            # -si hay ambos, pero ambos son el mismo: si soy yo se ingresa normal, si es otra persona no se hace nada

            comprador = linea['comprador'].lower()
            destinatario = linea['comprador'].lower()

            precio = linea['precio']
            precio_total = 0
            precio_sofi_yo = 0

            # Obtengo los prefijos para poder comparar. En resumen, alcanza con
            if "sofia".startswith(comprador) and (destinatario=="" or "valentino".startswith(destinatario)):
                precio_sofi_yo = precio
            elif "valentino".startswith(comprador) and (destinatario=="" or "sofia".startswith(destinatario)):
                precio_sofi_yo = -precio
            

            #if len(quien.split()==2): 
            #    if "valentino".startswith(quien[0]) and "sofia".startswith(quien[0]):


            # Agrego producto
            ws.update_cell(new_row, producto_cell.col, linea['nombre'])
            # Agrego fecha
            ws.update_cell(new_row, fecha_cell.col, linea['fecha'])
            # Hago el cálculo de precio


        ws.append_row(new_row)
        
        return True, "Fila agregada exitosamente"
        
    except gspread.exceptions.APIError as e:
        # Captura errores de la API de Google Sheets
        raise Exception(f"Error de API de Google Sheets: {e}")
    except Exception as e:
        # Captura cualquier otro error y lo relanza
        raise Exception(f"Error al agregar fila: {e}")
