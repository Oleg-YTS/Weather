#!/usr/bin/env python
"""
Скрипт для запуска бота на PythonAnywhere
Запуск: python pythonanywhere_bot.py
"""
import os
import sys

# Добавляем путь к проекту
project_path = os.path.expanduser("~/tg-bot")
if project_path not in sys.path:
    sys.path.insert(0, project_path)

# Меняем рабочую директорию
os.chdir(project_path)

# Загружаем переменные окружения
from dotenv import load_dotenv
load_dotenv(os.path.join(project_path, ".env"))

# Запускаем бота
import asyncio
from main import main

if __name__ == "__main__":
    print("=" * 50)
    print("  Запуск бота погоды и гороскопов")
    print("  PythonAnywhere")
    print("=" * 50)
    print()
    
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nБот остановлен пользователем")
    except Exception as e:
        print(f"\nОшибка: {e}")
        import traceback
        traceback.print_exc()
