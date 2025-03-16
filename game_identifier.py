import tkinter as tk
from pathlib import Path
from identify_playstation2_games import get_playstation2_game_info

def identify_games(folder_path, log_callback, progress_callback=None):
    total_files = 0
    game_info_list = []
    folder_path = Path(folder_path)

    log_callback("🔍 Начинается идентификация игр...", "info")

    # Подсчет общего количества файлов
    file_list = list(folder_path.rglob("*"))
    total_files = len(file_list)

    for idx, file_path in enumerate(file_list):
        if file_path.is_file() and file_path.suffix.lower() in ('.iso', '.bin', '.img'):
            if 'CD' in file_path.parts or 'DVD' in file_path.parts:
                try:
                    info = get_playstation2_game_info(str(file_path))
                    serial = info['serial_number'].decode('utf-8').strip()
                    title = info['title'].strip()
                    
                    game_info_list.append((str(file_path), serial, title))
                    
                    log_callback(f"✅ Найдено: {file_path.name} | {serial} - {title}", "success")
                    if progress_callback:
                        progress_callback(idx + 1, total_files)

                except Exception as e:
                    log_callback(f"⚠ Ошибка {file_path.name}: {str(e)}", "error")
                    if progress_callback:
                        progress_callback(idx + 1, total_files)

    log_callback(f"\n🎮 Всего найдено игр: {len(game_info_list)}", "info")
    return game_info_list