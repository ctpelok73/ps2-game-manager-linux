import PyInstaller.__main__
import sys
import os
from pathlib import Path

def build_exe():
    # Определяем разделитель в зависимости от ОС
    separator = ';' if sys.platform.startswith('win') else ':'
    
    # Определяем расширение исполняемого файла
    exe_extension = '.exe' if sys.platform.startswith('win') else ''
    
    # Список всех файлов баз данных
    db_files = [
        'db_playstation2_official_as.json',
        'db_playstation2_official_au.json',
        'db_playstation2_official_eu.json',
        'db_playstation2_official_jp.json',
        'db_playstation2_official_ko.json',
        'db_playstation2_official_us.json'
    ]
    
    # Проверяем наличие файлов баз данных
    missing_files = [f for f in db_files if not Path(f).exists()]
    if missing_files:
        print("ОШИБКА: Следующие файлы баз данных не найдены:")
        for f in missing_files:
            print(f"- {f}")
        return
    
    # Базовые параметры
    params = [
        'gui.py',  # Основной файл
        f'--name=PS2GamesManager{exe_extension}',  # Имя исполняемого файла
        '--noconsole',  # Без консоли
        '--onefile',  # Один файл
        '--clean',  # Очистка предыдущей сборки
        '--hidden-import=PIL._tkinter_finder',
        '--hidden-import=customtkinter',
    ]
    
    # Добавляем все файлы баз данных
    for db_file in db_files:
        params.append(f'--add-data={db_file}{separator}.')
    
    # Добавляем специфичные для Linux зависимости
    if not sys.platform.startswith('win'):
        params.extend([
            '--hidden-import=PIL._tkinter_finder',
            '--hidden-import=PIL._imaging',
            '--hidden-import=PIL._imagingft',
            '--hidden-import=PIL._imagingmath',
        ])
    
    # Добавляем assets только если папка существует
    assets_path = Path('assets')
    if assets_path.exists() and assets_path.is_dir():
        params.append(f'--add-data=assets{separator}assets')
        
        # Добавляем иконку, если она существует
        icon_path = assets_path / 'icon.ico'
        if icon_path.exists():
            params.append(f'--icon={icon_path}')
    
    # Добавляем Linux-специфичные файлы
    if not sys.platform.startswith('win'):
        linux_assets = assets_path / 'linux'
        if linux_assets.exists() and linux_assets.is_dir():
            params.append(f'--add-data={linux_assets}{separator}linux')
        
        desktop_file = assets_path / 'ps2gamesmanager.desktop'
        if desktop_file.exists():
            params.append(f'--add-data={desktop_file}{separator}.')
        
        main_icon = assets_path / 'ps2gamesmanager.png'
        if main_icon.exists():
            params.append(f'--add-data={main_icon}{separator}.')
    
    print(f"Сборка для платформы: {sys.platform}")
    print(f"Используемый разделитель: {separator}")
    print("Файлы баз данных:")
    for db_file in db_files:
        print(f"- {db_file}")
    print("Параметры сборки:", params)
    
    try:
        # Запускаем сборку
        PyInstaller.__main__.run(params)
        print("\nСборка успешно завершена!")
        print(f"Исполняемый файл находится в папке dist/")
    except Exception as e:
        print(f"\nОшибка при сборке: {str(e)}")

if __name__ == '__main__':
    build_exe() 