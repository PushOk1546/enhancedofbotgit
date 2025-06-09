"""
Общие вспомогательные функции для OF Assistant Bot
Содержит утилиты для валидации, форматирования, работы с данными
"""

import hashlib
import re
import json
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Union
import os
import asyncio
from pathlib import Path
from logging.handlers import RotatingFileHandler
from pythonjsonlogger import jsonlogger
from telebot import types
from config import config


# === ФУНКЦИИ ДЛЯ РАБОТЫ С ТЕКСТОМ ===

def generate_message_hash(text: str, length: int = 8) -> str:
    """Генерация короткого хеша для текстового сообщения"""
    try:
        return hashlib.md5(text.encode('utf-8')).hexdigest()[:length]
    except Exception:
        # Fallback для случаев с ошибками кодирования
        return hashlib.md5(str(text).encode('utf-8', errors='ignore')).hexdigest()[:length]


def truncate_text(text: str, max_length: int = 100, suffix: str = "...") -> str:
    """Обрезка текста до указанной длины с добавлением суффикса"""
    if not text:
        return ""
    
    if len(text) <= max_length:
        return text
    
    return text[:max_length - len(suffix)] + suffix


def clean_text(text: str) -> str:
    """Очистка текста от лишних символов и пробелов"""
    if not text:
        return ""
    
    # Удаляем лишние пробелы и переносы строк
    cleaned = re.sub(r'\s+', ' ', text.strip())
    
    # Удаляем потенциально опасные символы
    cleaned = re.sub(r'[<>]', '', cleaned)
    
    return cleaned


def format_user_mention(user_id: int, username: Optional[str] = None, first_name: Optional[str] = None) -> str:
    """Форматирование упоминания пользователя"""
    if username:
        return f"@{username}"
    elif first_name:
        return first_name
    else:
        return f"User_{user_id}"


def escape_html(text: str) -> str:
    """Экранирование HTML символов для безопасного отображения"""
    if not text:
        return ""
    
    html_escape_table = {
        "&": "&amp;",
        "<": "&lt;",
        ">": "&gt;",
        '"': "&quot;",
        "'": "&#x27;"
    }
    
    return "".join(html_escape_table.get(c, c) for c in text)


# === ФУНКЦИИ ДЛЯ РАБОТЫ СО ВРЕМЕНЕМ ===

def get_current_timestamp() -> str:
    """Получение текущего времени в ISO формате"""
    return datetime.now().isoformat()


def format_datetime(dt: datetime, format_str: str = "%Y-%m-%d %H:%M:%S") -> str:
    """Форматирование datetime в строку"""
    try:
        return dt.strftime(format_str)
    except Exception:
        return str(dt)


def parse_datetime(dt_str: str) -> Optional[datetime]:
    """Парсинг строки в datetime"""
    formats = [
        "%Y-%m-%d %H:%M:%S",
        "%Y-%m-%dT%H:%M:%S",
        "%Y-%m-%d",
        "%H:%M:%S"
    ]
    
    for fmt in formats:
        try:
            return datetime.strptime(dt_str, fmt)
        except ValueError:
            continue
    
    return None


def time_ago(dt: datetime) -> str:
    """Человекочитаемое время 'назад'"""
    now = datetime.now()
    diff = now - dt
    
    if diff.days > 0:
        return f"{diff.days} дн. назад"
    elif diff.seconds > 3600:
        hours = diff.seconds // 3600
        return f"{hours} ч. назад"
    elif diff.seconds > 60:
        minutes = diff.seconds // 60
        return f"{minutes} мин. назад"
    else:
        return "только что"


# === ФУНКЦИИ ДЛЯ РАБОТЫ С ДАННЫМИ ===

def safe_json_loads(json_str: str, default: Any = None) -> Any:
    """Безопасный парсинг JSON с fallback"""
    try:
        return json.loads(json_str)
    except (json.JSONDecodeError, TypeError):
        return default


def safe_json_dumps(data: Any, default: str = "{}") -> str:
    """Безопасная сериализация в JSON с fallback"""
    try:
        return json.dumps(data, ensure_ascii=False, separators=(',', ':'))
    except (TypeError, ValueError):
        return default


def extract_numbers(text: str) -> List[int]:
    """Извлечение всех чисел из текста"""
    try:
        return [int(match) for match in re.findall(r'\d+', text)]
    except Exception:
        return []


def extract_urls(text: str) -> List[str]:
    """Извлечение URL из текста"""
    url_pattern = re.compile(
        r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+'
    )
    return url_pattern.findall(text)


def validate_email(email: str) -> bool:
    """Простая валидация email"""
    pattern = re.compile(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$')
    return bool(pattern.match(email))


# === ФУНКЦИИ ДЛЯ РАБОТЫ С ФАЙЛАМИ ===

def ensure_directory(path: Union[str, Path]) -> Path:
    """Создание директории если она не существует"""
    path_obj = Path(path)
    path_obj.mkdir(parents=True, exist_ok=True)
    return path_obj


def get_file_size(file_path: Union[str, Path]) -> int:
    """Получение размера файла в байтах"""
    try:
        return Path(file_path).stat().st_size
    except (OSError, FileNotFoundError):
        return 0


def format_file_size(size_bytes: int) -> str:
    """Форматирование размера файла в человекочитаемый вид"""
    if size_bytes == 0:
        return "0 B"
    
    size_names = ["B", "KB", "MB", "GB", "TB"]
    i = 0
    size = float(size_bytes)
    
    while size >= 1024.0 and i < len(size_names) - 1:
        size /= 1024.0
        i += 1
    
    return f"{size:.1f} {size_names[i]}"


async def read_file_async(file_path: Union[str, Path], encoding: str = 'utf-8') -> Optional[str]:
    """Асинхронное чтение файла"""
    try:
        # Пробуем использовать aiofiles для настоящего асинхронного I/O
        try:
            import aiofiles
            async with aiofiles.open(file_path, 'r', encoding=encoding) as f:
                return await f.read()
        except ImportError:
            # Fallback к выполнению в отдельном потоке если aiofiles не установлен
            import asyncio
            loop = asyncio.get_event_loop()
            def sync_read():
                with open(file_path, 'r', encoding=encoding) as f:
                    return f.read()
            return await loop.run_in_executor(None, sync_read)
    except Exception:
        return None


# === ФУНКЦИИ ДЛЯ ВАЛИДАЦИИ ===

def is_valid_telegram_username(username: str) -> bool:
    """Валидация Telegram username"""
    if not username:
        return False
    
    # Убираем @ если есть
    username = username.lstrip('@')
    
    # Проверяем паттерн: 5-32 символа, буквы, цифры, подчеркивания
    pattern = re.compile(r'^[a-zA-Z0-9_]{5,32}$')
    return bool(pattern.match(username))


def is_valid_user_id(user_id: Any) -> bool:
    """Проверка корректности Telegram user_id"""
    try:
        uid = int(user_id)
        return 1 <= uid <= 2147483647  # Максимальный user_id в Telegram
    except (ValueError, TypeError):
        return False


def sanitize_filename(filename: str) -> str:
    """Очистка имени файла от недопустимых символов"""
    # Удаляем или заменяем недопустимые символы
    sanitized = re.sub(r'[<>:"/\\|?*]', '_', filename)
    
    # Ограничиваем длину
    if len(sanitized) > 255:
        name, ext = os.path.splitext(sanitized)
        sanitized = name[:255-len(ext)] + ext
    
    return sanitized


# === ФУНКЦИИ ДЛЯ РАБОТЫ С КОНФИГУРАЦИЕЙ ===

def get_env_var(var_name: str, default: Any = None, var_type: type = str) -> Any:
    """Получение переменной окружения с типизацией"""
    value = os.getenv(var_name, default)
    
    if value is None:
        return default
    
    try:
        if var_type == bool:
            return str(value).lower() in ('true', '1', 'yes', 'on')
        elif var_type == int:
            return int(value)
        elif var_type == float:
            return float(value)
        else:
            return var_type(value)
    except (ValueError, TypeError):
        return default


def load_config_from_dict(config_dict: Dict[str, Any], defaults: Dict[str, Any] = None) -> Dict[str, Any]:
    """Загрузка конфигурации из словаря с default значениями"""
    result = defaults.copy() if defaults else {}
    result.update(config_dict)
    return result


# === ДЕКОРАТОРЫ ===

def retry_on_exception(max_attempts: int = 3, delay: float = 1.0, exceptions: tuple = (Exception,)):
    """Декоратор для повторных попыток при ошибках"""
    def decorator(func):
        async def async_wrapper(*args, **kwargs):
            last_exception = None
            
            for attempt in range(max_attempts):
                try:
                    if asyncio.iscoroutinefunction(func):
                        return await func(*args, **kwargs)
                    else:
                        return func(*args, **kwargs)
                except exceptions as e:
                    last_exception = e
                    if attempt < max_attempts - 1:
                        await asyncio.sleep(delay * (attempt + 1))
                    continue
            
            raise last_exception
        
        def sync_wrapper(*args, **kwargs):
            last_exception = None
            
            for attempt in range(max_attempts):
                try:
                    return func(*args, **kwargs)
                except exceptions as e:
                    last_exception = e
                    if attempt < max_attempts - 1:
                        import time
                        time.sleep(delay * (attempt + 1))
                    continue
            
            raise last_exception
        
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper
    
    return decorator


# === ЗАГЛУШКИ ДЛЯ БУДУЩИХ ФУНКЦИЙ ===

def format_currency(amount: float, currency: str = "USD") -> str:
    """Форматирование валютных сумм (заглушка)"""
    # TODO: Реализовать полноценное форматирование валют
    return f"${amount:.2f}" if currency == "USD" else f"{amount:.2f} {currency}"


def detect_language(text: str) -> str:
    """Определение языка текста (заглушка)"""
    # TODO: Интеграция с библиотекой определения языка
    # Простая эвристика для русского/английского
    russian_chars = len(re.findall(r'[а-яё]', text.lower()))
    english_chars = len(re.findall(r'[a-z]', text.lower()))
    
    if russian_chars > english_chars:
        return "ru"
    elif english_chars > 0:
        return "en"
    else:
        return "unknown"


def translate_text(text: str, target_lang: str = "en") -> str:
    """Перевод текста (заглушка)"""
    # TODO: Интеграция с API переводчика
    return text  # Временно возвращаем оригинальный текст


def analyze_sentiment(text: str) -> Dict[str, float]:
    """Анализ тональности текста (заглушка)"""
    # TODO: Интеграция с моделью анализа тональности
    return {
        "positive": 0.33,
        "neutral": 0.34,
        "negative": 0.33
    }


def generate_qr_code(data: str, size: int = 200) -> Optional[bytes]:
    """Генерация QR кода (заглушка)"""
    # TODO: Интеграция с библиотекой QR кодов
    return None


def compress_image(image_data: bytes, quality: int = 85) -> bytes:
    """Сжатие изображения (заглушка)"""
    # TODO: Интеграция с библиотекой обработки изображений
    return image_data


def extract_metadata(file_path: Union[str, Path]) -> Dict[str, Any]:
    """Извлечение метаданных файла (заглушка)"""
    # TODO: Реализовать извлечение метаданных различных типов файлов
    path_obj = Path(file_path)
    
    try:
        stat = path_obj.stat()
        return {
            "size": stat.st_size,
            "modified": datetime.fromtimestamp(stat.st_mtime),
            "extension": path_obj.suffix.lower(),
            "name": path_obj.name
        }
    except Exception:
        return {}


def encrypt_sensitive_data(data: str, key: Optional[str] = None) -> str:
    """Шифрование чувствительных данных (заглушка)"""
    # TODO: Реализовать реальное шифрование
    # Временно возвращаем base64 кодирование
    import base64
    return base64.b64encode(data.encode()).decode()


def decrypt_sensitive_data(encrypted_data: str, key: Optional[str] = None) -> str:
    """Расшифровка чувствительных данных (заглушка)"""
    # TODO: Реализовать реальное расшифрование
    # Временно возвращаем base64 декодирование
    import base64
    try:
        return base64.b64decode(encrypted_data.encode()).decode()
    except Exception:
        return encrypted_data


# === ЭКСПОРТ ФУНКЦИЙ ===

__all__ = [
    # Текст
    'generate_message_hash',
    'truncate_text', 
    'clean_text',
    'format_user_mention',
    'escape_html',
    
    # Время
    'get_current_timestamp',
    'format_datetime',
    'parse_datetime', 
    'time_ago',
    
    # Данные
    'safe_json_loads',
    'safe_json_dumps',
    'extract_numbers',
    'extract_urls',
    'validate_email',
    
    # Файлы
    'ensure_directory',
    'get_file_size',
    'format_file_size',
    'read_file_async',
    
    # Валидация
    'is_valid_telegram_username',
    'is_valid_user_id',
    'sanitize_filename',
    
    # Конфигурация
    'get_env_var',
    'load_config_from_dict',
    
    # Декораторы
    'retry_on_exception',
    
    # Заглушки для будущих функций
    'format_currency',
    'detect_language',
    'translate_text',
    'analyze_sentiment',
    'generate_qr_code',
    'compress_image',
    'extract_metadata',
    'encrypt_sensitive_data',
    'decrypt_sensitive_data'
] 