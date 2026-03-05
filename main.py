import os
import re
import threading
import shutil
import requests
import win32file
import flet as ft
from yt_dlp import YoutubeDL

# ---------------------------------------------
# Rutas de Descargas
descargas_path = os.path.join(os.path.expanduser('~'), 'Downloads')
dsdownload_path = os.path.join(descargas_path, 'DSDownload')
os.makedirs(dsdownload_path, exist_ok=True)

# ---------------------------------------------
# Conexión a internet
def check_internet_connection():
    try:
        return requests.get('https://www.google.com', timeout=5).status_code == 200
    except requests.ConnectionError:
        return False

def actualizar_estado_conectividad():
    if check_internet_connection():
        return ft.Text("ONLINE   ", size=14, color=ft.Colors.GREEN, weight="normal")
    else:
        return ft.Text("OFFLINE   ", size=14, color=ft.Colors.RED, weight="normal")

# ---------------------------------------------
#Guia
def check_item_guia(e, page):

    def close_dialog(e):
        dialogo_guia.open = False
        page.update()

    contenido_popup = ft.Column(controls=[
        ft.Text("Guía de uso", size=20, weight="bold"),
        ft.Text("Aquí puedes incluir las instrucciones para el uso de la aplicación."),
        ft.Text("1. Indica un artista y una cantidad para descargar sus videos."),
        ft.Text("2. Usa la URL para descargar directamente un video o una lista de reproducción."),
    ])

    dialogo_guia = ft.AlertDialog(
        title=ft.Text("Guía de Uso"),
        content=contenido_popup,
        actions=[
            ft.Button(content=ft.Text("Cerrar"), on_click=close_dialog)
        ],
    )

    # NUEVA FORMA
    page.overlay.append(dialogo_guia)
    dialogo_guia.open = True
    page.update()

def info(e, page):

    def close_dialog(e):
        dialogo_guia.open = False
        page.update()

    contenido_popup = ft.Column(controls=[
        ft.Text("Info DS Download", size=20, weight="bold"),
        ft.Text("Version 1.0.0"),
        ft.Text("Design System"),
        ft.Text(""),
    ])

    dialogo_guia = ft.AlertDialog(
        #title=ft.Text("Guía de Uso"),
        content=contenido_popup,
        actions=[
            ft.Button(content=ft.Text("Cerrar"), on_click=close_dialog)
        ],
    )

    # NUEVA FORMA
    page.overlay.append(dialogo_guia)
    dialogo_guia.open = True
    page.update()
# ---------------------------------------------
# Detectar USB
def get_usb_drives():
    drives = []
    for letter in range(65, 91):
        drive = f"{chr(letter)}:\\"
        if os.path.exists(drive) and win32file.GetDriveType(drive) == win32file.DRIVE_REMOVABLE:
            drives.append(drive)
    return drives

# ---------------------------------------------
# Sanitizar nombres de archivo
def sanitize_filename(filename):
    return re.sub(r'[<>:"/\\|?*()]', '_', filename)

# ---------------------------------------------
# Opciones YTDL
def get_ydl_opts(video=True, nosig=False, outtmpl=None):
    opts = {
        'outtmpl': outtmpl,
        'noplaylist': False,
        'ignoreerrors': True,
        'retries': 10,
        'fragment_retries': 10,
        'http_chunk_size': 10485760,
        'concurrent_fragment_downloads': 4,
        'quiet': False,
        'no_warnings': True,

        # ESTO ES LO CLAVE
        'extractor_args': {
            'youtube': {
                'player_client': [
                    'android',
                    'web',
                    'tv_embedded'
                ],
                'po_token': 'web'
            }
        },

        'http_headers': {
            'User-Agent': 'Mozilla/5.0'
        },
    }

    if video:
        opts.update({
            # formato compatible 2026
            'format': 'bestvideo*+bestaudio/best',
            'merge_output_format': 'mp4'
        })
    else:
        opts.update({
            'format': 'bestaudio/best',
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': '192',
            }]
        })

    return opts

# ---------------------------------------------
# Clase para manejar descargas y progreso
class Downloader:
    def __init__(self, page, switch_video):
        self.page = page
        self.switch_video = switch_video
        self.progreso_dict = {'actual': 0, 'por_video': 0, 'lock': threading.Lock()}

    def actualizar_progreso(self, valor):
        self.page.progreso.value = valor/100 if valor <= 100 else 1
        self.page.update()

    def actualizar_mensaje(self, texto):
        self.page.mensaje.value = texto
        self.page.update()

    def descargar_video(self, video_url, outtmpl):
        MAX_HILOS = 4
        sem = threading.Semaphore(MAX_HILOS)

        def worker(url, outtmpl):
            with sem:
                try:
                    with YoutubeDL(get_ydl_opts(video=self.switch_video.value, outtmpl=outtmpl)) as ydl:
                        ydl.download([url])
                except Exception:
                    try:
                        with YoutubeDL(get_ydl_opts(video=self.switch_video.value, nosig=True, outtmpl=outtmpl)) as ydl:
                            ydl.download([url])
                    except Exception as ex:
                        self.actualizar_mensaje(f"Error en un video: {str(ex)}")
                finally:
                    with self.progreso_dict['lock']:
                        self.progreso_dict['actual'] += self.progreso_dict['por_video']
                        self.actualizar_progreso(min(self.progreso_dict['actual'], 100))

        return worker

    def descargar_playlist(self, url):
        self.actualizar_progreso(0)
        try:
            self.actualizar_mensaje("Buscando información...")
            with YoutubeDL(get_ydl_opts(video=self.switch_video.value)) as ydl:
                info_dict = ydl.extract_info(url, download=False)

            if not isinstance(info_dict, dict):
                self.actualizar_mensaje("Error: información inválida.")
                return

            # ---------------------------------
            # Playlist
            if 'entries' in info_dict:
                playlist_title = sanitize_filename(
                    info_dict.get('title') or
                    info_dict.get('playlist_title') or
                    info_dict.get('uploader') or
                    'Playlist'
                )
                playlist_path = os.path.join(dsdownload_path, playlist_title)
                os.makedirs(playlist_path, exist_ok=True)

                entries = [e for e in info_dict.get('entries', []) if e]
                total = len(entries)
                if total == 0:
                    self.actualizar_mensaje("No hay videos para descargar.")
                    return

                self.progreso_dict['actual'] = 0
                self.progreso_dict['por_video'] = 100 / total

                threads = []
                for idx, entry in enumerate(entries, start=1):
                    outtmpl = os.path.join(playlist_path, f"{idx:02d} - %(title)s.%(ext)s")
                    # Crear el worker y pasarlo al thread
                    worker_fn = self.descargar_video(entry['webpage_url'], outtmpl)
                    t = threading.Thread(target=worker_fn, args=(entry['webpage_url'], outtmpl))
                    threads.append(t)
                    t.start()

                for t in threads:
                    t.join()

                self.actualizar_mensaje(f"Descarga de playlist '{playlist_title}' completada.")
                self.actualizar_progreso(100)

            # ---------------------------------
            # Video individual
            else:
                video_title = sanitize_filename(info_dict.get('title', 'video'))
                video_path = os.path.join(dsdownload_path, video_title)
                os.makedirs(video_path, exist_ok=True)
                outtmpl = os.path.join(video_path, '%(title)s.%(ext)s')

                self.progreso_dict['actual'] = 0
                self.progreso_dict['por_video'] = 100
                # Llamar directamente al worker
                worker_fn = self.descargar_video(url, outtmpl)
                worker_fn(url, outtmpl)

                self.actualizar_mensaje("Descarga completa.")
                self.actualizar_progreso(100)

        except Exception as e:
            self.actualizar_mensaje(f"Error general: {str(e)}")

    def descargar_artista(self, artista, cantidad, factor):
        self.actualizar_progreso(0)
        artista = artista.lower()
        artista_path = os.path.join(dsdownload_path, sanitize_filename(artista))
        os.makedirs(artista_path, exist_ok=True)

        ydl_opts_base = get_ydl_opts(video=self.switch_video.value)
        search_query = f"ytsearch{cantidad*factor}:{artista} Videoclip"

        try:
            self.actualizar_mensaje(f"Buscando videos para '{artista}'...")
            with YoutubeDL(ydl_opts_base) as ydl:
                search_results = ydl.extract_info(search_query, download=False)['entries']

            if not search_results:
                self.actualizar_mensaje(f"No se encontraron videos para {artista}.")
                return

            filtered_results = [
                v for v in search_results
                if v['title'].lower().startswith(artista)
                   and v['duration'] > 120
                   and all(x not in v['title'].lower() for x in ['#short','cover','live','tutorial','cifra'])
            ]

            if not filtered_results:
                self.actualizar_mensaje("No se encontraron videos que coincidan con los criterios.")
                return

            total_videos = min(len(filtered_results), cantidad)
            self.progreso_dict['actual'] = 0
            self.progreso_dict['por_video'] = 100 / total_videos

            threads = []
            for video in filtered_results[:total_videos]:
                outtmpl = os.path.join(artista_path, f"{sanitize_filename(video['title'])}.%(ext)s")

                worker_fn = self.descargar_video(video['webpage_url'], outtmpl)

                t = threading.Thread(
                    target=worker_fn,
                    args=(video['webpage_url'], outtmpl)
                )

                threads.append(t)
                t.start()

            for t in threads:
                t.join()

            self.actualizar_mensaje(f"Se han descargado {total_videos} videos de {artista}.")
            self.actualizar_progreso(100)

        except Exception as e:
            self.actualizar_mensaje(f"Error al descargar los videos: {str(e)}")

# ---------------------------------------------
# Función para copiar a USB
def copy_to_usb(page, usb_drives, multiple=False):
    status_message = ft.Text("Listo para copiar archivos.", size=20)
    dropdowns = []
    for i in range(10 if multiple else 1):
        dropdowns.append(ft.Dropdown(options=[ft.dropdown.Option(d) for d in usb_drives] +
                                             [ft.dropdown.Option("null","Ninguna selección")] if multiple else [ft.dropdown.Option(d) for d in usb_drives],
                                     label=f"Selecciona USB {i+1}" if multiple else "Selecciona tu USB",
                                     hint_text="Selecciona una unidad USB"))
    button_row = ft.Row(controls=[ft.Button(content=ft.Text("Iniciar copia"), on_click=lambda e: start_copy(dropdowns))], alignment=ft.MainAxisAlignment.CENTER)

    col1 = ft.Column(controls=dropdowns[:5])
    col2 = ft.Column(controls=dropdowns[5:10])

    contenido_popup = ft.Column(controls=[
        status_message,
        ft.Row(controls=[col1, col2], alignment=ft.MainAxisAlignment.CENTER),
        ft.Container(content=button_row, alignment=ft.Alignment.BOTTOM_CENTER, expand=True),
    ])
    dialog = ft.AlertDialog(title=ft.Text("Grabar en USB"), content=contenido_popup, actions=[ft.Button(content=ft.Text("Cerrar"), on_click=lambda e: close_dialog(dialog))],)


    def close_dialog(d):
        d.open = False
        page.update()

    def copy_folder_multi(drive):
        if not drive or drive=="null":
            status_message.value="USB no seleccionado, se omitirá."
            status_message.color="blue"; page.update(); return
        source = dsdownload_path
        destination = drive
        os.makedirs(destination, exist_ok=True)
        try:
            items = os.listdir(source)
            for item in items:
                s,dst = os.path.join(source,item), os.path.join(destination,item)
                if os.path.isdir(s): shutil.copytree(s,dst,dirs_exist_ok=True)
                else: shutil.copy2(s,dst)
            status_message.value=f"Copia completada a {drive}"; status_message.color="green"; page.update()
        except Exception as ex:
            status_message.value=f"Error al copiar a {drive}: {str(ex)}"; status_message.color="red"; page.update()

    def start_copy(dropdowns):
        threads=[]
        for dd in dropdowns:
            t=threading.Thread(target=copy_folder_multi,args=(dd.value,))
            threads.append(t); t.start()
        for t in threads: t.join()
        status_message.value="Todas las copias finalizadas."; status_message.color="green"; page.update()

    page.overlay.append(dialog)
    dialog.open=True
    dialog.content.width = 1500
    dialog.content.height = 800
    page.update()

# ---------------------------------------------
def main(page: ft.Page):
    ft.Text(""),
    page.title="DS Downloader - © 2004-2028 Design System"
    page.window.width=910; page.window.height=750; page.window.resizable=False; page.window.maximizable = False

    title_style=ft.Text("Download Manager DS", size=24, color=ft.Colors.GREEN, weight="bold")
    Config=ft.Text("Configuración", size=16, color=ft.Colors.BLUE, weight="bold")
    title_Artista_style=ft.Text("Descarga por nombre de Artista", size=16, color=ft.Colors.BLUE, weight="bold")
    title_URL_style=ft.Text("Descarga un link o una lista de Reproducción", size=16, color=ft.Colors.BLUE, weight="bold")
    horizontal_line = ft.Divider(height=0.1, color=ft.Colors.BLUE_ACCENT_700, thickness=1)

    # Mensajes y barra
    page.mensaje=ft.Text(value="", size=14, color=ft.Colors.RED)
    page.progreso=ft.ProgressBar(value=0, width=910, height=20, bgcolor="lightgray", color="green")

    switch_Video = ft.Switch(value=False, label="   Video", scale=0.8)
    switch_Multiplicador = ft.Switch(value=False, label="     x2   ", scale=0.8)

    buscar_artista = ft.TextField(label="Indique un Artista", width=440, height=40,
                                  border_color=ft.Colors.BLUE_ACCENT_700, fill_color=ft.Colors.GREY_900)
    cantidad_musicas = ft.TextField(label="Cantidad", width=150, height=40,
                                    border_color=ft.Colors.BLUE_ACCENT_700, fill_color=ft.Colors.GREY_900)
    buscar_URL = ft.TextField(label="Indique la URL a descargar", width=600, height=40,
                              border_color=ft.Colors.BLUE_ACCENT_700, fill_color=ft.Colors.GREY_900)

    downloader = Downloader(page, switch_Video)

    boton_descargar_artista = ft.Button(content=ft.Text("Descargar Artista"), on_click=lambda e: threading.Thread(target=lambda: downloader.descargar_artista(buscar_artista.value, int(cantidad_musicas.value), 2 if switch_Multiplicador.value else 1)).start(), bgcolor="blue", height=40)
    boton_descargar_url = ft.Button(content=ft.Text("Descargar - URL "), on_click=lambda e: downloader.descargar_playlist(buscar_URL.value), bgcolor="blue", height=40)

    usb_drives = get_usb_drives()
    button_gravar_row = ft.Row(controls=[
        ft.Button(content=ft.Text("Grabar en USB"), on_click=lambda e: copy_to_usb(page, usb_drives, multiple=False)),
        ft.Button(content=ft.Text("Grabar en múltiples USBs"), on_click=lambda e: copy_to_usb(page, usb_drives, multiple=True)),
        ft.Button(content=ft.Text("Formatear USB"), on_click=lambda e: (setattr(page.mensaje, "value", "Función en construcción..."), page.update())),
        ft.Button(content=ft.Text("Abrir Carpeta"), on_click=lambda e: os.startfile(dsdownload_path)),
        ft.Button(content=ft.Text("Guia de Uso"), on_click=lambda e: check_item_guia(e, page)),
        ft.Button(content=ft.Text("Info"), on_click=lambda e: info(e, page)),

    ], alignment=ft.MainAxisAlignment.START)

    #boton y estato de conectividad
    def refrescar(e):
        button_info.controls[1].content = actualizar_estado_conectividad()
        page.update()

    button_info = ft.Row(controls=[
        # Puedes agregar botones u otros widgets aquí
        ft.IconButton(ft.Icons.INFO_OUTLINED, ft.Colors.BLUE_ACCENT_700,
                      on_click=refrescar,
                      ),
        ft.Container(
            # función para verificar el estado de la coneccion
            content=actualizar_estado_conectividad(),

        ),
    ],
    alignment=ft.MainAxisAlignment.END,
    )

    page.add(
        title_style,
        button_gravar_row,
        ft.Text(""),
        Config,
        horizontal_line,
        ft.Column(controls=[
            ft.Row(controls=[ft.Text("Indique el tipo de archivo"), ft.Row(controls=[ft.Text("Mp3", size=10), switch_Video], alignment=ft.MainAxisAlignment.END, spacing=10)], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
            ft.Row(controls=[ft.Text("Indique el Factor de Multiplición de busqueda"), ft.Row(controls=[ft.Text("x1", size=10), switch_Multiplicador], alignment=ft.MainAxisAlignment.END, spacing=10)], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
            horizontal_line, ft.Text(""),
            title_Artista_style,
            horizontal_line,
            ft.Row(controls=[buscar_artista, cantidad_musicas, ft.Row(controls=[boton_descargar_artista], alignment=ft.MainAxisAlignment.END)], alignment=ft.MainAxisAlignment.START, spacing=10),
            ft.Text(""), title_URL_style, horizontal_line,
            ft.Row(controls=[buscar_URL, ft.Row(controls=[boton_descargar_url], alignment=ft.MainAxisAlignment.END)]),
            ft.Text(""), page.mensaje, ft.Text(""), page.progreso
        ], alignment=ft.MainAxisAlignment.CENTER),
        button_info,
    )

ft.run(main)
