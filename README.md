## Generar el .exe

- PyInstaller es una herramienta que genera un archivo .exe a partir de tu programa principal, incluyendo el intérprete de Python y todas las dependencias necesarias, de modo que se pueda ejecutar en otra PC sin necesidad de instalar Python ni librerías adicionales.

### Pasos para incluir Flet Desktop correctamente

1. Determinar la ubicación de flet_desktop ejecutando Python (IDLE o PowerShell):

```python
import flet_desktop
print(flet_desktop.__file__)
```
Esto devuelve la ruta de instalación de flet_desktop, que será la carpeta que hay que usar en --add-data.

2. Incluir las dos carpetas necesarias en PyInstaller:
   1. flet_desktop
   2. flet
   
   ####
3. Generar el .exe incluyendo estas carpetas con --add-data:

```python
pyinstaller --onefile --console --add-data "C:\Users\TU_USUARIO\AppData\Local\Python\pythoncore-3.14-64\Lib\site-packages\flet_desktop;flet_desktop"  --add-data "C:\Users\TU_USUARIO\AppData\Local\Python\pythoncore-3.14-64\Lib\site-packages\flet;flet" main.py
```
Al finalizar, PyInstaller crea el .exe dentro de la carpeta dist del proyecto, listo para ejecutarse en cualquier PC con Windows.