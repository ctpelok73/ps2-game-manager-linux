import requests
from pathlib import Path
from PIL import Image
import logging

# Константы
COVER_SIZE = (140, 200)
BASE_COVER_URL = "https://raw.githubusercontent.com/xlenore/ps2-covers/main/covers/default/"

# Настройка логгера
logger = logging.getLogger(__name__)

def sanitize_filename(filename: str) -> str:
    """Очищает имя файла от недопустимых символов."""
    return ''.join(c for c in filename if c.isalnum() or c in (' ', '_', '-')).rstrip()

def download_cover(title: str, serial_number: str, art_folder: str) -> tuple[Path | None, str | None]:
    """Загружает и обрабатывает обложку игры."""
    formatted_serial = serial_number  # Сохраняем оригинальный формат серийника
    cover_url = f"{BASE_COVER_URL}{formatted_serial}.jpg"
    art_folder = Path(art_folder)
    art_folder.mkdir(parents=True, exist_ok=True)

    try:
        response = requests.get(cover_url, timeout=15)
        
        # Обработка 404
        if response.status_code == 404:
            logger.warning(f"Обложка не найдена: {formatted_serial}")
            return None, None
        
        response.raise_for_status()

        # Проверка типа контента
        if 'image' not in response.headers.get('Content-Type', ''):
            logger.error(f"Некорректный тип контента: {cover_url}")
            return None, None

        # Сохранение с серийным номером в имени
        cover_name = f"{formatted_serial}.jpg"
        cover_path = art_folder / cover_name
        
        with open(cover_path, 'wb') as f:
            f.write(response.content)

        new_cover_path = resize_and_rename_cover(cover_path, serial_number)
        return new_cover_path, new_cover_path.name

    except requests.RequestException as e:
        logger.error(f"Ошибка запроса: {str(e)}")
        return None, None
    except Exception as e:
        logger.error(f"Неожиданная ошибка: {str(e)}", exc_info=True)
        return None, None

def resize_and_rename_cover(cover_path: Path, serial_number: str) -> Path:
    """Изменяет размер и переименовывает обложку."""
    try:
        formatted_serial = serial_number.replace("-", "_")
        new_filename = f"{formatted_serial[:-2]}.{formatted_serial[-2:]}_COV.png"
        new_cover_path = cover_path.with_name(new_filename)

        if new_cover_path.exists():
            logger.info(f"Обложка уже обработана: {new_cover_path}")
            return new_cover_path

        with Image.open(cover_path) as img:
            img.thumbnail(COVER_SIZE, Image.LANCZOS)
            img.save(new_cover_path, format='PNG', optimize=True)

        if new_cover_path.exists():
            cover_path.unlink()
            logger.info(f"Удалён исходник: {cover_path}")

        return new_cover_path
        
    except Exception as e:
        logger.error(f"Ошибка обработки: {str(e)}", exc_info=True)
        return cover_path