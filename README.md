# Gastos App — Bot de Telegram (lector de tickets)

Este proyecto es un bot de Telegram que recibe una foto de un ticket y usa Tesseract (pytesseract) para extraer texto.

¿Para qué sirve este README?
- Explica cómo preparar el entorno de desarrollo en Windows.
- Muestra cómo crear y activar un venv, instalar dependencias y seleccionar el intérprete en VS Code.
- Proporciona instrucciones para instalar y configurar Tesseract (requisito externo) y solucionar errores comunes.

Requisitos
- Python 3.13 (el proyecto fue probado con 3.13.7 dentro de `.venv`).
- Tesseract OCR instalado en Windows (opcionalmente en `C:\Program Files\Tesseract-OCR`).

Pasos rápidos (Windows - PowerShell)
1. Crear y activar un entorno virtual en la carpeta del proyecto:

```powershell
python -m venv .venv
& .\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
```

2. Seleccionar el intérprete en VS Code (recomendado):
- Abrir Command Palette (Ctrl+Shift+P) → `Python: Select Interpreter` → seleccionar `C:\Users\<tu_usuario>\gastos_app\.venv\Scripts\python.exe`.
- Luego recargar la ventana: Command Palette → `Developer: Reload Window`.

3. Ejecutar el bot localmente (desde el venv activado):

```powershell
python main.py
```

Configurar Tesseract (Windows)
- Descarga e instala Tesseract desde: https://github.com/UB-Mannheim/tesseract/wiki (o el instalador oficial)
- Asegúrate de que el binario `tesseract.exe` esté en `C:\Program Files\Tesseract-OCR\` y que el subdirectorio `tessdata` contenga los archivos `.traineddata` que necesitas (por ejemplo `spa.traineddata` para español).
- El script `main.py` intenta automáticamente fijar `TESSDATA_PREFIX` a `C:\Program Files\Tesseract-OCR\` si detecta `C:\Program Files\Tesseract-OCR\tessdata`.

Si Tesseract no encuentra los datos de idioma, verás un error como:
```
TesseractError: Error opening data file ... Please make sure the TESSDATA_PREFIX environment variable is set to your "tessdata" directory.
```
Solución rápida temporal (PowerShell):
```powershell
$env:TESSDATA_PREFIX = 'C:\Program Files\Tesseract-OCR\'
```
Para fijarlo permanentemente, añade la variable en las Variables de entorno del sistema.

Notas sobre dependencias y compatibilidad
- Cambié `Pillow==10.0.1` a `Pillow==12.0.0` porque tu entorno usa Python 3.13 y la versión 10 no tenía ruedas (wheels) precompiladas para esa versión; pip intentaba compilar Pillow desde fuente y el proceso fallaba. Pillow 12 tiene ruedas para Python 3.13 en Windows, por eso lo actualicé.
- Si por alguna razón necesitas exactamente `Pillow==10.0.1`, lo recomendable es usar Python 3.11/3.10 o instalar las herramientas de compilación en Windows (difícil y propenso a errores).

Solución de problemas comunes
- Pylance muestra "Import could not be resolved from source": asegúrate de seleccionar el intérprete `.venv` en VS Code y recargar la ventana.
- Si recibes `TesseractError` por falta de `spa.traineddata`, instala el paquete de idiomas de Tesseract o coloca `spa.traineddata` en `C:\Program Files\Tesseract-OCR\tessdata`.

Siguientes pasos sugeridos
- Añadir tests mínimos para validar la función de extracción de texto (requiere imágenes de ejemplo).
- Añadir manejo de errores en el bot (capturar excepciones y responder al usuario con mensajes claros).

Si querés, puedo:
- Añadir un mensaje de consola más claro cuando falten datos de Tesseract.
- Agregar tests o plantillas para deploy.
- Dejar `requirements.txt` con un rango para Pillow en lugar de una versión fija.

---
Creado automáticamente para ayudarte a configurar y ejecutar el proyecto en Windows.
