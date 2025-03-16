from PIL import Image, ImageDraw, ImageFont
import os
from pathlib import Path

def create_icons():
    # Создаем папки
    assets_dir = Path('assets')
    assets_dir.mkdir(exist_ok=True)
    
    linux_icons_dir = assets_dir / 'linux'
    linux_icons_dir.mkdir(exist_ok=True)
    
    # Размеры иконки
    size = (256, 256)
    
    # Создаем новое изображение с прозрачным фоном
    image = Image.new('RGBA', size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(image)
    
    # Рисуем тёмный круг с градиентом
    margin = 10
    box = (margin, margin, size[0] - margin, size[1] - margin)
    draw.ellipse(box, fill='#1a1a1a', outline='#2FA572', width=3)
    
    # Добавляем текст PS2
    text = "PS2"
    try:
        # Пробуем использовать системный шрифт
        font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 100)
    except:
        # Если не получилось, используем дефолтный шрифт
        font = ImageFont.load_default()
    
    # Центрируем текст
    text_bbox = draw.textbbox((0, 0), text, font=font)
    text_width = text_bbox[2] - text_bbox[0]
    text_height = text_bbox[3] - text_bbox[1]
    text_position = ((size[0] - text_width) // 2, (size[1] - text_height) // 2)
    
    # Рисуем текст с эффектом свечения
    draw.text((text_position[0]+2, text_position[1]+2), text, font=font, fill='#1F6AA5')  # Тень
    draw.text(text_position, text, font=font, fill='#2FA572')  # Основной текст
    
    # Добавляем маленький текст "Games"
    small_text = "Games"
    try:
        small_font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 40)
    except:
        small_font = ImageFont.load_default()
    
    small_bbox = draw.textbbox((0, 0), small_text, font=small_font)
    small_width = small_bbox[2] - small_bbox[0]
    small_position = ((size[0] - small_width) // 2, text_position[1] + text_height)
    draw.text((small_position[0]+1, small_position[1]+1), small_text, font=small_font, fill='#1F6AA5')  # Тень
    draw.text(small_position, small_text, font=small_font, fill='#2FA572')  # Основной текст
    
    # Сохраняем иконки разных размеров для Linux
    icon_sizes = [16, 32, 48, 64, 128, 256]
    for size in icon_sizes:
        icon_path = linux_icons_dir / f'ps2gamesmanager_{size}x{size}.png'
        resized_image = image.resize((size, size), Image.LANCZOS)
        resized_image.save(icon_path, 'PNG')
    
    # Создаем .desktop файл
    desktop_content = """[Desktop Entry]
Name=PS2 Games Manager
Comment=Менеджер игр для PlayStation 2
Exec=ps2gamesmanager
Icon=ps2gamesmanager
Terminal=false
Type=Application
Categories=Game;Utility;
"""
    
    with open(assets_dir / 'ps2gamesmanager.desktop', 'w') as f:
        f.write(desktop_content)
    
    # Сохраняем основную иконку
    image.save(assets_dir / 'ps2gamesmanager.png', 'PNG')
    
    print("Иконки для Linux успешно созданы в папке assets/linux")
    print("Файл .desktop создан в папке assets")

if __name__ == '__main__':
    create_icons() 