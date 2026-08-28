#!/usr/bin/env python3
"""
Скрипт для скачивания подписок и загрузки в SourceCraft.dev
Проект: https://sourcecraft.dev/furiplay52yt/submirror
API: https://api.sourcecraft.tech
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

class SourceCraftUploader:
    """Класс для работы с SourceCraft.dev API"""
    
    def __init__(self, api_key: str, base_url: str = "https://api.sourcecraft.tech"):
        self.api_key = api_key
        self.base_url = base_url.rstrip('/')
        self.headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
        logger.info(f"🌐 Используется API: {self.base_url}")
    
    def get_project_by_name(self, username: str, project_name: str) -> Optional[Dict]:
        """Получение проекта по имени пользователя и названию проекта"""
        try:
            url = f"{self.base_url}/projects"
            logger.info(f"🔍 Запрос проектов: {url}")
            response = requests.get(url, headers=self.headers, timeout=30)
            response.raise_for_status()
            projects = response.json()
            
            for project in projects:
                if project.get('name') == project_name:
                    logger.info(f"✅ Найден проект: {project.get('id')} - {project.get('name')}")
                    return project
            
            logger.info(f"📦 Проект '{project_name}' не найден, будет создан новый")
            return None
            
        except requests.exceptions.RequestException as e:
            logger.error(f"❌ Ошибка при поиске проекта: {e}")
            if hasattr(e, 'response') and e.response:
                logger.error(f"Ответ сервера: {e.response.text}")
            return None
    
    def create_project(self, name: str, description: str = "") -> Dict:
        """Создание нового проекта"""
        url = f"{self.base_url}/projects"
        data = {
            "name": name,
            "description": description or "Автоматически загружаемые подписки для обхода блокировок"
        }
        
        try:
            logger.info(f"📦 Создание проекта: {name}")
            response = requests.post(url, headers=self.headers, json=data, timeout=30)
            response.raise_for_status()
            result = response.json()
            logger.info(f"✅ Проект создан: {result.get('id')} - {name}")
            return result
        except requests.exceptions.RequestException as e:
            logger.error(f"❌ Ошибка создания проекта: {e}")
            if hasattr(e, 'response') and e.response:
                logger.error(f"Ответ сервера: {e.response.text}")
            raise
    
    def get_files(self, project_id: str) -> List[Dict]:
        """Получение списка файлов в проекте"""
        try:
            url = f"{self.base_url}/projects/{project_id}/files"
            response = requests.get(url, headers=self.headers, timeout=30)
            response.raise_for_status()
            files = response.json()
            logger.info(f"📋 Найдено файлов в проекте: {len(files)}")
            return files
        except requests.exceptions.RequestException as e:
            logger.error(f"❌ Ошибка получения списка файлов: {e}")
            return []
    
    def upload_file(self, project_id: str, filename: str, content: str, original_url: str = "", checksum: str = "") -> Dict:
        """Загрузка файла в проект"""
        url = f"{self.base_url}/projects/{project_id}/files"
        
        data = {
            "filename": filename,
            "content": content,
            "file_type": self._detect_file_type(filename),
            "metadata": {
                "source_url": original_url,
                "uploaded_at": datetime.now().isoformat(),
                "size_bytes": len(content),
                "checksum": checksum,
                "last_updated": datetime.now().strftime('%Y-%m-%d %H:%M:%S UTC')
            }
        }
        
        try:
            logger.info(f"📤 Загрузка файла: {filename}")
            response = requests.post(url, headers=self.headers, json=data, timeout=30)
            response.raise_for_status()
            result = response.json()
            logger.info(f"✅ Файл загружен: {filename}")
            return result
        except requests.exceptions.RequestException as e:
            logger.error(f"❌ Ошибка загрузки файла {filename}: {e}")
            if hasattr(e, 'response') and e.response:
                logger.error(f"Ответ сервера: {e.response.text}")
            raise
    
    def update_file(self, project_id: str, file_id: str, filename: str, content: str, original_url: str = "", checksum: str = "") -> Dict:
        """Обновление существующего файла"""
        url = f"{self.base_url}/projects/{project_id}/files/{file_id}"
        data = {
            "content": content,
            "metadata": {
                "source_url": original_url,
                "updated_at": datetime.now().isoformat(),
                "size_bytes": len(content),
                "checksum": checksum,
                "last_updated": datetime.now().strftime('%Y-%m-%d %H:%M:%S UTC')
            }
        }
        
        try:
            logger.info(f"🔄 Обновление файла: {filename}")
            response = requests.put(url, headers=self.headers, json=data, timeout=30)
            response.raise_for_status()
            result = response.json()
            logger.info(f"✅ Файл обновлен: {filename}")
            return result
        except requests.exceptions.RequestException as e:
            logger.error(f"❌ Ошибка обновления файла {filename}: {e}")
            if hasattr(e, 'response') and e.response:
                logger.error(f"Ответ сервера: {e.response.text}")
            raise
    
    def _detect_file_type(self, filename: str) -> str:
        """Определение типа файла по расширению"""
        ext = os.path.splitext(filename)[1].lower()
        type_map = {
            '.txt': 'text',
            '.json': 'json',
            '.xml': 'xml',
            '.yml': 'yaml',
            '.yaml': 'yaml',
            '.csv': 'csv',
            '.m3u': 'playlist',
            '.m3u8': 'playlist',
            '.conf': 'config',
            '.list': 'list'
        }
        return type_map.get(ext, 'text')

class SubscriptionDownloader:
    """Класс для скачивания подписок"""
    
    def __init__(self, download_dir: str = "subscriptions"):
        self.download_dir = download_dir
        os.makedirs(download_dir, exist_ok=True)
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
    
    def download_from_url(self, url: str, filename: str) -> Optional[Tuple[str, str, str]]:
        """Скачивание подписки по URL"""
        try:
            file_path = os.path.join(self.download_dir, filename)
            
            logger.info(f"📥 Скачивание: {url}")
            
            time.sleep(0.5)
            
            response = self.session.get(url, timeout=30)
            response.raise_for_status()
            
            # Определяем кодировку
            encoding = 'utf-8'
            if 'charset' in response.headers.get('content-type', '').lower():
                content_type = response.headers['content-type'].lower()
                if 'charset=' in content_type:
                    encoding = content_type.split('charset=')[-1].split(';')[0].strip()
            
            content = response.content.decode(encoding, errors='ignore')
            checksum = hashlib.md5(content.encode('utf-8')).hexdigest()
            
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            
            file_size = os.path.getsize(file_path)
            line_count = len(content.splitlines())
            logger.info(f"✅ Файл сохранен: {filename} ({file_size} байт, {line_count} строк)")
            
            return file_path, content, checksum
            
        except requests.exceptions.RequestException as e:
            logger.error(f"❌ Ошибка скачивания {url}: {e}")
            return None
        except Exception as e:
            logger.error(f"❌ Непредвиденная ошибка: {e}")
            return None

def get_subscriptions() -> List[Dict[str, str]]:
    """Список подписок с правильными именами файлов"""
    return [
        {"url": "https://hub.mos.ru/LinSpisokObhod/LInSpisokObhod/-/raw/main/sub/ALL.txt", "filename": "lso.all.txt"},
        {"url": "https://hub.mos.ru/LinSpisokObhod/LInSpisokObhod/-/raw/main/sub/LTE.txt", "filename": "lso.lte.txt"},
        {"url": "https://hub.mos.ru/LinSpisokObhod/LInSpisokObhod/-/raw/main/sub/WIFI.txt", "filename": "lso.wifi.txt"},
        {"url": "https://gitverse.ru/api/repos/RKP_channel/RKP_bypass_configs/raw/branch/master/whitelist.txt", "filename": "rkp.lte.txt"},
        {"url": "https://raw.githubusercontent.com/RKPchannel/RKP_bypass_configs/refs/heads/main/blacklist.txt", "filename": "rkp.wifi.txt"},
        {"url": "https://mifa.world/bingo", "filename": "mifa.world.txt"},
        {"url": "https://raw.githubusercontent.com/ksenkovsolo/HardVPN-bypass-WhiteLists-/refs/heads/main/vpn-lte/WHITELIST-ALL.txt", "filename": "hardvpn.all.txt"},
        {"url": "https://raw.githubusercontent.com/prominbro/sub/refs/heads/main/212.txt", "filename": "kwfl.txt"},
        {"url": "https://etoneya.su/1", "filename": "etoneya.all.txt"},
        {"url": "https://etoneya.su/whitelist", "filename": "etoneya.lte.txt"},
        {"url": "https://etoneya.su/other", "filename": "etoneya.othet.txt"}
    ]

def get_api_key():
    """Получение API ключа из переменных окружения"""
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
    
    logger.error("❌ API ключ не найден. Проверьте переменные окружения:")
    for name in possible_names:
        logger.info(f"   - {name}")
    return None

def main():
    """Главная функция"""
    
    # Получение API ключа
    api_key = get_api_key()
    if not api_key:
        logger.info("Установите переменную окружения:")
        logger.info("   export SOURCECRAFT_API_KEY='ваш_ключ'")
        exit(1)
    
    logger.info(f"✅ API ключ получен (длина: {len(api_key)} символов)")
    
    # Настройки проекта
    project_name = "submirror"
    username = "furiplay52yt"
    
    # Инициализация
    uploader = SourceCraftUploader(api_key)
    downloader = SubscriptionDownloader()
    
    # Проверка подключения к API
    try:
        test_url = f"{uploader.base_url}/projects"
        response = requests.get(test_url, headers=uploader.headers, timeout=10)
        if response.status_code == 200:
            logger.info("✅ API доступен")
        else:
            logger.error(f"❌ API вернул код: {response.status_code}")
            logger.error(f"Ответ: {response.text}")
            exit(1)
    except Exception as e:
        logger.error(f"❌ Ошибка подключения к API: {e}")
        exit(1)
    
    # Получение или создание проекта
    logger.info(f"🔍 Поиск проекта: {project_name}")
    project = uploader.get_project_by_name(username, project_name)
    
    if not project:
        logger.info(f"📦 Создание нового проекта: {project_name}")
        project = uploader.create_project(project_name)
    
    project_id = project.get('id')
    logger.info(f"✅ Работа с проектом: {project.get('name')} (ID: {project_id})")
    logger.info(f"🔗 URL: https://sourcecraft.dev/{username}/{project_name}")
    
    # Получение списка существующих файлов
    existing_files = uploader.get_files(project_id)
    existing_filenames = {f.get('filename'): f.get('id') for f in existing_files}
    
    # Список подписок
    subscriptions = get_subscriptions()
    success_count = 0
    fail_count = 0
    results = []
    
    logger.info(f"\n📋 Всего подписок: {len(subscriptions)}")
    
    for sub in subscriptions:
        filename = sub['filename']
        url = sub['url']
        
        logger.info(f"\n{'='*60}")
        logger.info(f"📄 Обработка: {filename}")
        logger.info(f"{'='*60}")
        
        # Скачивание
        result = downloader.download_from_url(url, filename)
        if not result:
            fail_count += 1
            results.append({'filename': filename, 'status': 'failed', 'error': 'Download error'})
            continue
        
        file_path, content, checksum = result
        
        # Проверка содержимого
        if len(content.strip()) < 10:
            logger.warning(f"⚠️ Файл {filename} пустой или слишком маленький")
            fail_count += 1
            results.append({'filename': filename, 'status': 'failed', 'error': 'Empty content'})
            continue
        
        # Загрузка или обновление
        try:
            if filename in existing_filenames:
                file_id = existing_filenames[filename]
                uploader.update_file(project_id, file_id, filename, content, url, checksum)
                logger.info(f"🔄 Обновлен: {filename}")
            else:
                uploader.upload_file(project_id, filename, content, url, checksum)
                logger.info(f"📤 Загружен: {filename}")
            
            success_count += 1
            results.append({
                'filename': filename,
                'status': 'success',
                'size': len(content),
                'checksum': checksum[:8]
            })
            
        except Exception as e:
            logger.error(f"❌ Ошибка загрузки {filename}: {e}")
            fail_count += 1
            results.append({'filename': filename, 'status': 'failed', 'error': str(e)})
    
    # Итоговый отчет
    logger.info(f"\n{'='*60}")
    logger.info("📊 ИТОГОВЫЙ ОТЧЕТ")
    logger.info(f"{'='*60}")
    logger.info(f"✅ Успешно: {success_count}")
    logger.info(f"❌ Неудачно: {fail_count}")
    logger.info(f"📊 Всего: {len(subscriptions)}")
    
    logger.info(f"\n📋 Детали:")
    for result in results:
        status = "✅" if result['status'] == 'success' else "❌"
        details = f"({result.get('size', 0)} байт)" if result.get('size') else ""
        error = f" - {result.get('error', '')}" if result.get('error') else ""
        logger.info(f"  {status} {result['filename']}: {result['status']} {details}{error}")
    
    logger.info(f"\n🔗 Проект: https://sourcecraft.dev/{username}/{project_name}")
    
    return success_count, fail_count

if __name__ == "__main__":
    success, failed = main()
    exit(0 if failed == 0 else 1)