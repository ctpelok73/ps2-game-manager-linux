import sys
import os
import re
import json
import read_udf
import iso9660

IS_PY2 = sys.version_info[0] == 2

BUFFER_SIZE = 1024 * 1024 * 10
MAX_PREFIX_LEN = 6

# Все возможные префиксы серийных номеров
PREFIXES = [
    b'SLPM', b'SLES', b'SCES', b'SLUS', b'SLPS', b'SCUS', b'SCPS', b'SCAJ',
    b'SLKA', b'SCKA', b'SLAJ', b'NPJD', b'TCPS', b'KOEI', b'NPUD', b'ALCH',
    b'PBGP', b'NPED', b'CPCS', b'FVGK', b'SCED', b'NPJC', b'GN', b'GUST',
    b'HSN', b'SLED', b'DMP', b'INCH', b'PBPX', b'KAD', b'SLPN', b'TCES',
    b'NPUC', b'DESR', b'PAPX', b'PBPS', b'PCPX', b'ROSE', b'SRPM', b'SCEE',
    b'HAKU', b'GER', b'HKID', b'MPR', b'GWS', b'HKHS', b'NS', b'XSPL',
    b'Sierra', b'ARZE', b'VUGJ', b'VO', b'WFLD'
]

def get_resource_path(relative_path):
    """Получает абсолютный путь к ресурсу"""
    try:
        # PyInstaller создает временную папку и хранит путь в _MEIPASS
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(os.path.dirname(__file__))
    
    return os.path.join(base_path, relative_path)

# Используйте эту функцию для пути к JSON файлу
DB_PATH = get_resource_path('db_playstation2_official_au.json')

try:
    with open(DB_PATH, 'r', encoding='utf-8') as f:
        DB = json.load(f)
except Exception as e:
    print(f"Ошибка при загрузке базы данных: {str(e)}")
    print(f"Искомый путь: {DB_PATH}")
    sys.exit(1)

# Загрузка баз данных
db_files = [
    'db_playstation2_official_as.json',
    'db_playstation2_official_au.json',
    'db_playstation2_official_eu.json',
    'db_playstation2_official_jp.json',
    'db_playstation2_official_ko.json',
    'db_playstation2_official_us.json'
]

dbs = {}
for db_file in db_files:
    db_path = get_resource_path(db_file)
    with open(db_path, 'rb') as f:
        dbs[db_file] = json.loads(f.read().decode('utf8'))

# Преобразование ключей в байты
for db in dbs.values():
    keys = list(db.keys())
    for key in keys:
        if isinstance(key, str):
            val = db[key]
            db.pop(key)
            db[bytes(key, 'utf-8')] = val
        else:
            print(f"Неверный тип ключа: {key} (тип: {type(key)})")

def _find_in_binary(file_name):
    f = open(file_name, 'rb')
    file_size = os.path.getsize(file_name)
    while True:
        # Чтение в буфер
        rom_data = f.read(BUFFER_SIZE)

        # Проверка конца файла
        if not rom_data:
            return None

        # Поиск серийного номера
        for prefix in PREFIXES:
            m = re.search(prefix + br"[-_][\d\.]+;", rom_data)
            if m and m.group() and b'999.99' not in m.group():
                serial_number = m.group().replace(b'.', b'').replace(b'_', b'-').replace(b';', b'')
                return serial_number

        # Перемещение в файле
        pos = f.tell()
        if pos > MAX_PREFIX_LEN and pos < file_size:
            f.seek(pos - MAX_PREFIX_LEN)

    return None

def get_playstation2_game_info(file_name):
    # Пропуск, если не ISO или BIN
    if not os.path.splitext(file_name)[1].lower() in ['.iso', '.bin']:
        raise Exception("Not an ISO or BIN file.")

    # Поиск серийного номера в файле
    serial_number = _find_in_binary(file_name)
    if not serial_number:
        raise Exception("Failed to find serial number in file.")

    # Поиск названия игры в базах данных
    for db_name, db in dbs.items():
        if serial_number in db:
            region = db_name.split('_')[-1].upper()  # Извлекаем регион из имени файла
            title = db[serial_number]
            return {
                'serial_number': serial_number,
                'region': region,
                'title': title,
                'disc_type': 'Binary'  # Упрощенно, можно добавить логику для CD/DVD
            }

    raise Exception("Failed to find game in database.")
