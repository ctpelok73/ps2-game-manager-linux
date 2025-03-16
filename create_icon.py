from PIL import Image, ImageDraw, ImageFont
import os
from pathlib import Path

def create_icon():
    # Создаем папку assets если её нет
    assets_dir = Path('assets')
    assets_dir.mkdir(exist_ok=True)
    
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
    # Пробуем использовать системный шрифт
    try:
        if os.name == 'nt':  # Windows
            font = ImageFont.truetype("arial.ttf", 100)
        else:  # Linux/Mac
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
        small_font = ImageFont.truetype("arial.ttf", 40) if os.name == 'nt' else ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 40)
    except:
        small_font = ImageFont.load_default()
    
    small_bbox = draw.textbbox((0, 0), small_text, font=small_font)
    small_width = small_bbox[2] - small_bbox[0]
    small_position = ((size[0] - small_width) // 2, text_position[1] + text_height)
    draw.text((small_position[0]+1, small_position[1]+1), small_text, font=small_font, fill='#1F6AA5')  # Тень
    draw.text(small_position, small_text, font=small_font, fill='#2FA572')  # Основной текст
    
    # Сохраняем в разных размерах для иконки
    icon_sizes = [(16, 16), (32, 32), (48, 48), (64, 64), (128, 128), (256, 256)]
    icons = []
    for icon_size in icon_sizes:
        icons.append(image.resize(icon_size, Image.LANCZOS))
    
    # Сохраняем как .ico
    icons[0].save(
        assets_dir / "icon.ico",
        format='ICO',
        sizes=icon_sizes,
        append_images=icons[1:]
    )
    
    print("Иконка успешно создана в папке assets")

if __name__ == '__main__':
    create_icon() 