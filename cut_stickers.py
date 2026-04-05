"""
Нарезка картинки на отдельные стикеры для Telegram.
Каждый стикер = 512x512 PNG с прозрачным фоном.
"""
from PIL import Image, ImageOps
import os

INPUT = r"c:\Users\lnoobl\Pictures\memnye_kotiki_stikerpak.png"
OUTPUT_DIR = r"c:\QWEN-CODE\tg-bot\stickers"

# Координаты котов (примерные, по сетке 3x2)
# Увеличим картинку сначала до 1200x900 чтобы коты были крупнее
# Затем нарежем 6 частей

# Читаем оригинал
img = Image.open(INPUT)

# Масштабируем для удобства нарезки (увеличиваем в 3 раза)
w, h = img.size
img_large = img.resize((w * 3, h * 3), Image.LANCZOS)
print(f"Увеличенная картинка: {img_large.size}")

# Нарезка на 6 частей (3 колонки x 2 ряда)
cols, rows = 3, 2
part_w = img_large.size[0] // cols
part_h = img_large.size[1] // rows

names = [
    "mayu",        # верх-лево: MAY? MAY! РРРЯУ
    "zadumchivo",  # верх-центр: ЗАСУДНИУЮ
    "aaaaaa",      # верх-право: ААААААААААА
    "norm",        # низ-лево: НОРМ
    "kykyky",      # низ-центр: КЬКЬ-КЬКЬКЬ
    "khyk",        # низ-право: КЬКЬ
]

os.makedirs(OUTPUT_DIR, exist_ok=True)

for i in range(rows):
    for j in range(cols):
        idx = i * cols + j
        if idx >= len(names):
            break
        
        name = names[idx]
        left = j * part_w
        top = i * part_h
        right = left + part_w
        bottom = top + part_h
        
        # Вырезаем часть
        part = img_large.crop((left, top, right, bottom))
        
        # Масштабируем до 512x512
        sticker = part.resize((512, 512), Image.LANCZOS)
        
        # Сохраняем
        path = os.path.join(OUTPUT_DIR, f"sticker_{idx:02d}_{name}.png")
        sticker.save(path, "PNG")
        print(f"✅ {name}: {path}")

print(f"\n📁 Все стикеры в: {OUTPUT_DIR}")
print("\nЗагрузите их через @Stickers бота!")
