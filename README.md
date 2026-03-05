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

#
### Para que funcione luego, se necesita ffmpeg para convertit mp3
### Opcion 1
- Abre PowerShell
- Ejecuta el siguiente comando

```cmd
winget install FFmpeg.FFmpeg
```
Esto ya agrega las variables de entorno en windows.
- Verifica las versiones de los productos desde una cmd:
  - ffmpeg -version
  - ffprobe -version

### Opcion 2
- Descarga los binarios desde

```url
https://ffmpeg.en.uptodown.com/windows/download
```
- Descomprime el archivo
- Copia el contenido en C:/, queda algo como:

```
C:\ffmpeg-8.0.1-full_build
```
- Agrega la carpeta bin del path a las variables de entorno de windows
  - La ubicacion seria:
   ```
  C:\ffmpeg-8.0.1-full_build\bin
  ```
  - Habre las variables de entorno del sistema
  - localiza "path" y dale a editar/nuevo
  - pega la direccion anterior
  
  ####
- verifica las versiones
  - ffmpeg -version
  - ffprobe -version