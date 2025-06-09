"""
Простая система кэширования для MVP
"""

import asyncio
import hashlib
from typing import Any, Dict, Optional
from datetime import datetime, timedelta
from config import config

class MemoryCache:
    """In-memory кэш для MVP"""
    
    def __init__(self):
        self._cache: Dict[str, Dict[str, Any]] = {}
        self._max_size = 1000  # Максимальное количество элементов
        
    async def get(self, key: str) -> Optional[Any]:
        """Получение значения из кэша"""
        if key not in self._cache:
            return None
            
        item = self._cache[key]
        
        # Проверяем не истек ли срок
        if item["expires_at"] and datetime.now() > item["expires_at"]:
            await self.delete(key)
            return None
            
        return item["value"]
        
    async def set(self, key: str, value: Any, ttl_seconds: int = None) -> None:
        """Установка значения в кэш"""
        if ttl_seconds is None:
            ttl_seconds = config.CACHE_TTL
            
        # Если кэш переполнен, удаляем самый старый элемент
        if len(self._cache) >= self._max_size:
            oldest_key = min(
                self._cache.keys(), 
                key=lambda k: self._cache[k]["created_at"]
            )
            await self.delete(oldest_key)
            
        expires_at = None
        if ttl_seconds and ttl_seconds > 0:
            expires_at = datetime.now() + timedelta(seconds=ttl_seconds)
            
        self._cache[key] = {
            "value": value,
            "created_at": datetime.now(),
            "expires_at": expires_at
        }
        
    async def delete(self, key: str) -> None:
        """Удаление значения из кэша"""
        self._cache.pop(key, None)
        
    async def clear(self) -> None:
        """Очистка всего кэша"""
        self._cache.clear()
        
    async def cleanup_expired(self) -> None:
        """Очистка истекших элементов"""
        now = datetime.now()
        expired_keys = [
            key for key, item in self._cache.items()
            if item["expires_at"] and now > item["expires_at"]
        ]
        
        for key in expired_keys:
            await self.delete(key)
            
    async def get_cache_key(self, style: str, user_message: str) -> str:
        """Генерация ключа кэша для стиля и сообщения"""
        message_hash = hashlib.md5(user_message.encode()).hexdigest()
        return f"{style}:{message_hash}"
        
    async def get_stats(self) -> Dict[str, int]:
        """Получить статистику кэша"""
        await self.cleanup_expired()
        return {
            "total_items": len(self._cache),
            "max_size": self._max_size
        }

# Заглушки для FileCache и RedisCache (для MVP)
class FileCache:
    """Заглушка для файлового кэша"""
    
    async def get(self, key: str) -> Optional[Any]:
        return None
        
    async def set(self, key: str, value: Any, ttl_seconds: int = None) -> None:
        pass

class RedisCache:
    """Заглушка для Redis кэша"""
    
    async def get(self, key: str) -> Optional[Any]:
        return None
        
    async def set(self, key: str, value: Any, ttl_seconds: int = None) -> None:
        pass 