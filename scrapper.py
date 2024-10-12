import subprocess
import time
import pyautogui
import os
import pandas as pd
import sqlite3
import datetime

# ---------------------------
# Configuración Inicial
# ---------------------------

# Ruta al ejecutable de Chrome (ajústala según tu sistema)
chrome_path = 'C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe'

# Rutas y configuraciones de las descargas
extension_url_1 = 'chrome-extension://kicgclkbiilobmccmmidfghnijgfamdb/options.html'  # URL 1
extension_url_2 = 'chrome-extension://kicgclkbiilobmccmmidfghnijgfamdb/options.html'  # URL 2

# Rutas donde se guardarán los archivos descargados
download_folder = 'C:\\Users\\Sonia\\Downloads'  # Ajusta esta ruta
downloaded_file_1 = os.path.join(download_folder, 'caricakez_followers.csv')  # Archivo 1
downloaded_file_2 = os.path.join(download_folder, 'caricanread_followers.csv')  # Archivo 2

# Coordenadas de los elementos para el primer proceso
input_field_pos_1 = (700, 616)        # Posición del campo de entrada para el proceso 1
start_button_pos_1 = (422, 903)       # Posición del botón de iniciar para el proceso 1
download_button_pos_1 = (1190, 864)   # Posición del botón de descargar para el proceso 1

# Coordenadas de los elementos para el segundo proceso
input_field_pos_2 = (700, 616)        # Posición del campo de entrada para el proceso 2
start_button_pos_2 = (422, 903)       # Posición del botón de iniciar para el proceso 2
download_button_pos_2 = (1190, 864)   # Posición del botón de descargar para el proceso 2

# ---------------------------
# Funciones para Automatización de la Descarga
# ---------------------------

def automate_download(chrome_path, extension_url, input_field_pos, start_button_pos, download_button_pos, downloaded_file, url):
    # Abrir Chrome con la URL de la extensión
    subprocess.Popen([chrome_path, extension_url])

    # Esperar a que Chrome se inicie
    time.sleep(5)

    # Interactuar con el campo de entrada para la URL
    pyautogui.click(input_field_pos)
    pyautogui.typewrite(url, interval=0.05)  # Reemplaza con tu URL real
    pyautogui.press('enter')
    time.sleep(2)

    # Hacer clic en el botón de iniciar
    pyautogui.click(start_button_pos)

    # Esperar a que el proceso termine (ajusta el tiempo según sea necesario)
    time.sleep(30)

    # Hacer clic en el botón de descargar
    pyautogui.click(download_button_pos)

    time.sleep(2)

    # Presionar "Enter" para confirmar la descarga (si aparece el diálogo)
    # pyautogui.press('enter')

    # Cerrar Chrome
    pyautogui.hotkey('ctrl', 'w')

    # Esperar a que la descarga finalice
    time.sleep(10)

    # Verificar si el archivo se descargó correctamente
    wait_time = 0
    while not os.path.exists(downloaded_file) and wait_time < 60:
        time.sleep(1)
        wait_time += 1

    if os.path.exists(downloaded_file):
        print(f"Archivo descargado correctamente: {downloaded_file}")
    else:
        print(f"No se pudo encontrar el archivo descargado: {downloaded_file}")
        exit()

# ---------------------------
# Ejecutar los dos Procesos de Automatización
# ---------------------------

# Primer proceso de descarga
url_1 = 'https://www.instagram.com/caricakez/'
automate_download(chrome_path, extension_url_1, input_field_pos_1, start_button_pos_1, download_button_pos_1, downloaded_file_1, url_1)

# Segundo proceso de descarga
url_2 = 'https://www.instagram.com/caricanread/'
automate_download(chrome_path, extension_url_2, input_field_pos_2, start_button_pos_2, download_button_pos_2, downloaded_file_2, url_2)

# ---------------------------
# Leer y Procesar los Archivos CSV Descargados
# ---------------------------

def add_column_if_not_exists(cursor, table_name, column_name, column_type):
    cursor.execute(f"PRAGMA table_info({table_name})")
    columns = [info[1] for info in cursor.fetchall()]
    if column_name not in columns:
        cursor.execute(f"ALTER TABLE {table_name} ADD COLUMN {column_name} {column_type}")
        print(f"Columna '{column_name}' añadida a la tabla '{table_name}'.")
        cursor.connection.commit()

def process_csv(downloaded_file, db_path):
    # Leer el archivo CSV
    try:
        data = pd.read_csv(downloaded_file)
        print(f"Datos leídos exitosamente del archivo: {downloaded_file}")
    except Exception as e:
        print(f"Error al leer el archivo CSV {downloaded_file}: {e}")
        exit()

    # Seleccionar solo las columnas deseadas
    try:
        data = data[['userName', 'profileUrl', 'isVerified']]
        print("Datos filtrados a las columnas: userName, profileUrl, isVerified.")
    except KeyError as e:
        print(f"Error: La columna {e} no existe en el CSV.")
        exit()

    # Limitar a los primeros 500 seguidores si es necesario
    data = data.head(500)

    # Obtener fecha y hora actual redondeada
    current_datetime = datetime.datetime.now().replace(minute=0, second=0, microsecond=0)
    current_datetime_str = current_datetime.strftime('%Y-%m-%d %H:%M:%S')

    # Conectar a la base de datos
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # Crear la tabla 'seguidores' si no existe
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS seguidores (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        userName TEXT UNIQUE,
        profileUrl TEXT,
        isVerified INTEGER
    )
    ''')
    conn.commit()

    # Añadir las columnas 'date_added' y 'date_last_seen' si no existen
    add_column_if_not_exists(cursor, 'seguidores', 'date_added', 'TEXT')
    add_column_if_not_exists(cursor, 'seguidores', 'date_last_seen', 'TEXT')

    # Crear la tabla 'hourly_stats' para estadísticas horarias si no existe
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS hourly_stats (
        timestamp TEXT PRIMARY KEY,
        new_followers INTEGER
    )
    ''')
    conn.commit()

    # Insertar o actualizar seguidores
    new_followers_count = 0
    for _, row in data.iterrows():
        userName = row['userName']
        profileUrl = row['profileUrl']
        isVerified = 1 if str(row['isVerified']).strip().lower() == 'yes' else 0

        cursor.execute('SELECT * FROM seguidores WHERE userName = ?', (userName,))
        result = cursor.fetchone()

        if result:
            # Actualizar el seguidor existente
            cursor.execute('''
            UPDATE seguidores
            SET profileUrl = ?, isVerified = ?, date_last_seen = ?
            WHERE userName = ?
            ''', (profileUrl, isVerified, current_datetime_str, userName))
        else:
            # Insertar nuevo seguidor
            cursor.execute('''
            INSERT INTO seguidores (userName, profileUrl, isVerified, date_added, date_last_seen)
            VALUES (?, ?, ?, ?, ?)
            ''', (userName, profileUrl, isVerified, current_datetime_str, current_datetime_str))
            new_followers_count += 1

    conn.commit()

    # Actualizar las estadísticas horarias
    cursor.execute('SELECT new_followers FROM hourly_stats WHERE timestamp = ?', (current_datetime_str,))
    result = cursor.fetchone()

    if result:
        # Si ya existe, sumamos el conteo actual
        total_new_followers = result[0] + new_followers_count
        cursor.execute('''
        UPDATE hourly_stats
        SET new_followers = ?
        WHERE timestamp = ?
        ''', (total_new_followers, current_datetime_str))
    else:
        # Si no existe, insertamos el registro para la hora
        total_new_followers = new_followers_count
        cursor.execute('''
        INSERT INTO hourly_stats (timestamp, new_followers)
        VALUES (?, ?)
        ''', (current_datetime_str, total_new_followers))

    conn.commit()
    conn.close()

    print(f"Nuevos seguidores detectados en {downloaded_file}: {new_followers_count}")

# Procesar los archivos descargados
process_csv(downloaded_file_1, 'seguidores.db')
process_csv(downloaded_file_2, 'seguidores_2.db')

# ---------------------------
# Crear Base de Datos con Seguidores Comunes
# ---------------------------

def create_common_followers_db(file1, file2, common_db_path):
    # Leer los dos archivos CSV
    try:
        data1 = pd.read_csv(file1)
        data2 = pd.read_csv(file2)
        print("Archivos leídos exitosamente para encontrar seguidores comunes.")
    except Exception as e:
        print(f"Error al leer los archivos CSV: {e}")
        exit()

    # Filtrar las columnas relevantes
    try:
        data1 = data1[['userName', 'profileUrl', 'isVerified']]
        data2 = data2[['userName', 'profileUrl', 'isVerified']]
    except KeyError as e:
        print(f"Error: La columna {e} no existe en uno de los CSV.")
        exit()

    # Encontrar seguidores comunes
    common_followers = pd.merge(data1, data2, on=['userName', 'profileUrl', 'isVerified'])

    # Conectar a la base de datos
    conn = sqlite3.connect(common_db_path)
    cursor = conn.cursor()

    # Crear la tabla 'seguidores_comunes' si no existe
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS seguidores_comunes (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        userName TEXT UNIQUE,
        profileUrl TEXT,
        isVerified INTEGER
    )
    ''')
    conn.commit()

    # Insertar seguidores comunes
    for _, row in common_followers.iterrows():
        userName = row['userName']
        profileUrl = row['profileUrl']
        isVerified = row['isVerified']

        cursor.execute('SELECT * FROM seguidores_comunes WHERE userName = ?', (userName,))
        result = cursor.fetchone()

        if not result:
            cursor.execute('''
            INSERT INTO seguidores_comunes (userName, profileUrl, isVerified)
            VALUES (?, ?, ?)
            ''', (userName, profileUrl, isVerified))

    conn.commit()
    conn.close()

    print(f"Seguidores comunes insertados en la base de datos '{common_db_path}'.")

# Crear la base de datos con los seguidores comunes
create_common_followers_db(downloaded_file_1, downloaded_file_2, 'seguidores_comunes.db')