#!/usr/bin/env python3
"""
Скрипт для скачивания подписок и загрузки в SourceCraft.dev
"""

import os
import json
import requests
import time
import hashlib
from datetime import datetime
from typing import Dict, List, Optional, Tuple
import logging

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def get_api_key():
    """Проверка нескольких вариантов названия переменной"""
    # Пробуем разные имена переменных
    possible_names = [
        'SOURCECRAFT_API_KEY',
        'SOURCECRAFT_TOKEN',
        'SOURCE_CRAFT_API_KEY',
        'SOURCE_CRAFT_TOKEN',
        'SC_API_KEY',
        'SC_TOKEN'
    ]
    
    for name in possible_names:
        value = os.getenv(name)
        if value:
            logger.info(f"✅ Найден API ключ в переменной: {name}")
            return value
    
    # Если ничего не найдено
    logger.error("❌ API ключ не найден. Проверьте переменные окружения:")
    for name in possible_names:
        logger.info(f"   - {name}")
    return None

def main():
    """Главная функция"""
    
    api_key = get_api_key()
    if not api_key:
        logger.error("❌ SOURCECRAFT_API_KEY не установлен")
        logger.info("Установите переменную окружения:")
        logger.info("   export SOURCECRAFT_API_KEY='ваш_ключ'")
        exit(1)
    
    # Остальной код скрипта...
    logger.info(f"✅ API ключ получен (длина: {len(api_key)} символов)")
    
    # Проверка работы API
    try:
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
        response = requests.get("https://api.sourcecraft.dev/projects", headers=headers)
        if response.status_code == 200:
            logger.info("✅ API ключ валидный, доступ к проектам есть")
        else:
            logger.error(f"❌ API ключ невалидный: {response.status_code}")
            logger.error(f"Ответ: {response.text}")
            exit(1)
    except Exception as e:
        logger.error(f"❌ Ошибка проверки API ключа: {e}")
        exit(1)
    
    # Дальше ваш код загрузки...

if __name__ == "__main__":
    main()