#!/usr/bin/env python3
"""
Скрипт для скачивания подписок и загрузки в SourceCraft.dev
Использует правильные эндпоинты API согласно документации
"""

import os
import json
import requests
import time
import hashlib
import base64
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
    
    def get_user_repos(self) -> List[Dict]:
        """Получение списка репозиториев пользователя"""
        try:
            url = f"{self.base_url}/user/repos"
            logger.info(f"🔍 Запрос репозиториев: {url}")
            response = requests.get(url, headers=self.headers, timeout=30)
            response.raise_for_status()
            repos = response.json()
            logger.info(f"📋 Найдено репозиториев: {len(repos)}")
            return repos
        except requests.exceptions.RequestException as e:
            logger.error(f"❌ Ошибка получения репозиториев: {e}")
            if hasattr(e, 'response') and e.response:
                logger.error(f"Ответ сервера: {e.response.text}")
            return []
    
    def get_repository(self, owner: str, repo: str) -> Optional[Dict]:
        """Получение информации о репозитории"""
        try:
            url = f"{self.base_url}/repos/{owner}/{repo}"
            logger.info(f"🔍 Поиск репозитория: {url}")
            response = requests.get(url, headers=self.headers, timeout=30)
            
            if response.status_code == 200:
                repo_data = response.json()
                logger.info(f"✅ Найден репозиторий: {repo_data.get('name')}")
                return repo_data
            elif response.status_code == 404:
                logger.info(f"📦 Репозиторий '{repo}' не найден")
                return None
            else:
                logger.warning(f"⚠️ Неожиданный ответ: {response.status_code}")
                return None
                
        except requests.exceptions.RequestException as e:
            logger.error(f"❌ Ошибка при поиске репозитория: {e}")
            return None
    
    def create_repository(self, name: str, description: str = "") -> Dict:
        """Создание нового репозитория"""
        url = f"{self.base_url}/user/repos"
        data = {
            "name": name,
            "description": description or "Автоматически загружаемые подписки для обхода блокировок",
            "private": False
        }
        
        try:
            logger.info(f"📦 Создание репозитория: {name}")
            response = requests.post(url, headers=self.headers, json=data, timeout=30)
            response.raise_for_status()
            result = response.json()
            logger.info(f"✅ Репозиторий создан: {result.get('name')}")
            return result
        except requests.exceptions.RequestException as e:
            logger.error(f"❌ Ошибка создания репозитория: {e}")
            if hasattr(e, 'response') and e.response:
                logger.error(f"Ответ сервера: {e.response.text}")
            raise
    
    def get_file_contents(self, owner: str, repo: str, path: str) -> Optional[Dict]:
        """Получение содержимого файла из репозитория"""
        try:
            url = f"{self.base_url}/repos/{owner}/{repo}/contents/{path}"
            logger.info(f"🔍 Проверка файла: {path}")
            response = requests.get(url, headers=self.headers, timeout=30)
            
            if response.status_code == 200:
                return response.json()
            elif response.status_code == 404:
                return None
            else:
                logger.warning(f"⚠️ Неожиданный ответ: {response.status_code}")
                return None
                
        except requests.exceptions.RequestException as e:
            logger.error(f"❌ Ошибка проверки файла: {e}")
            return None
    
    def create_or_update_file(self, owner: str, repo: str, path: str, content: str, message: str, sha: Optional[str] = None) -> Dict:
        """Создание или обновление файла в репозитории"""
        url = f"{self.base_url}/repos/{owner}/{repo}/contents/{path}"
        
        # Кодируем содержимое в base64
        encoded_content = base64.b64encode(content.encode('utf-8')).decode('utf-8')
        
        data = {
            "message": message,
            "content": encoded_content
        }
        
        if sha:
            data["sha"] = sha
        
        try:
            if sha:
                logger.info(f"🔄 Обновление файла: {path}")
                response = requests.put(url, headers=self.headers, json=data, timeout=30)
            else:
                logger.info(f"📤 Создание файла: {path}")
                response = requests.post(url, headers=self.headers, json=data, timeout=30)
            
            response.raise_for_status()
            result = response.json()
            logger.info(f"✅ Файл сохранен: {path}")
            return result
            
        except requests.exceptions.RequestException as e:
            logger.error(f"❌ Ошибка сохранения файла {path}: {e}")
            if hasattr(e, 'response') and e.response:
                logger.error(f"Ответ сервера: {e.response.text}")
            raise

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
    # Согласно документации SourceCraft, правильное имя переменной - SOURCECRAFT_TOKEN
    possible_names = [
        'SOURCECRAFT_TOKEN',
        'SOURCECRAFT_API_KEY',
        'SOURCE_CRAFT_API_KEY',
        'SC_API_KEY'
    ]
    
    for name in possible_names:
        value = os.getenv(name)
        if value:
            logger.info(f"✅ Найден API ключ в переменной: {name}")
            return value
    
    logger.error("❌ API ключ не найден. Используйте переменную SOURCECRAFT_TOKEN")
    return None

def main():
    """Главная функция"""
    
    # Получение API ключа
    api_key = get_api_key()
    if not api_key:
        logger.info("Установите переменную окружения:")
        logger.info("   export SOURCECRAFT_TOKEN='ваш_ключ'")
        exit(1)
    
    logger.info(f"✅ API ключ получен (длина: {len(api_key)} символов)")
    
    # Настройки проекта
    repo_name = "submirror"
    owner = "furiplay52yt"
    
    # Инициализация
    uploader = SourceCraftUploader(api_key)
    downloader = SubscriptionDownloader()
    
    # Проверка подключения к API
    try:
        test_url = f"{uploader.base_url}/user/repos"
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
    
    # Получение или создание репозитория
    logger.info(f"🔍 Поиск репозитория: {repo_name}")
    repo = uploader.get_repository(owner, repo_name)
    
    if not repo:
        logger.info(f"📦 Создание нового репозитория: {repo_name}")
        repo = uploader.create_repository(repo_name)
    
    logger.info(f"✅ Работа с репозиторием: {repo.get('name')}")
    logger.info(f"🔗 URL: https://sourcecraft.dev/{owner}/{repo_name}")
    
    # Скачиваем и загружаем подписки
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
        
        # Проверяем, существует ли файл в репозитории
        file_info = uploader.get_file_contents(owner, repo_name, filename)
        existing_sha = file_info.get('sha') if file_info else None
        
        # Загрузка или обновление файла
        try:
            message = f"Update {filename} from source at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
            uploader.create_or_update_file(
                owner, 
                repo_name, 
                filename, 
                content, 
                message,
                existing_sha
            )
            
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
    
    logger.info(f"\n🔗 Репозиторий: https://sourcecraft.dev/{owner}/{repo_name}")
    
    return success_count, fail_count

if __name__ == "__main__":
    success, failed = main()
    exit(0 if failed == 0 else 1)ons)}")
    
    logger.info(f"\n📋 Детали:")
    for result in results:
        status = "✅" if result['status'] == 'success' else "❌"
        details = f"({result.get('size', 0)} байт)" if result.get('size') else ""
        error = f" - {result.get('error', '')}" if result.get('error') else ""
        logger.info(f"  {status} {result['filename']}: {result['status']} {details}{error}")
    
    logger.info(f"\n🔗 Репозиторий: https://sourcecraft.dev/{owner}/{repo_name}")
    
    return success_count, fail_count

if __name__ == "__main__":
    success, failed = main()
    exit(0 if failed == 0 else 1) == 'success' else "❌"
        details = f"({result.get('size', 0)} байт)" if result.get('size') else ""
        error = f" - {result.get('error', '')}" if result.get('error') else ""
        logger.info(f"  {status} {result['filename']}: {result['status']} {details}{error}")
    
    logger.info(f"\n🔗 Репозиторий: https://sourcecraft.dev/{username}/{repo_name}")
    
    return success_count, fail_count

if __name__ == "__main__":
    success, failed = main()
    exit(0 if failed == 0 else 1)