import gspread

# ruta a las credenciales de mi proy
gc = gspread.service_account(filename="credentials.json")

gc = gspread.service_account(filename="credentials.json")
sh = gc.open("Gastos")  # nombre del archivo en Drive
_active_month = "Octubre"

def set_month(month_name):
    global _active_month
    _active_month = month_name.capitalize()

def append_row(values):
    ws = sh.worksheet(_active_month)
    ws.append_row(values)