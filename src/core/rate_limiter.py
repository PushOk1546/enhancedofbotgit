"""
Система ограничения частоты запросов (Rate Limiting).
Защищает от злоупотреблений и DoS атак.
"""

import time
import asyncio
from typing import Dict, Optional, Tuple, Callable
from collections import defaultdict, deque
from dataclasses import dataclass
from threading import Lock
import logging
import functools

from .exceptions import RateLimitError


@dataclass
class RateLimit:
    """Конфигурация ограничения частоты"""
    requests: int  # Количество запросов
    window: int    # Временное окно в секундах
    burst: Optional[int] = None  # Burst лимит


class TokenBucket:
    """Реализация алгоритма Token Bucket для rate limiting"""
    
    def __init__(self, capacity: int, refill_rate: float):
        """
        Args:
            capacity: Размер ведра (максимальное количество токенов)
            refill_rate: Скорость пополнения токенов в секунду
        """
        self.capacity = capacity
        self.refill_rate = refill_rate
        self.tokens = capacity
        self.last_refill = time.time()
        self.lock = Lock()
    
    def consume(self, tokens: int = 1) -> bool:
        """
        Попытка получить токены из ведра.
        
        Args:
            tokens: Количество токенов для получения
            
        Returns:
            True если токены получены, False если недостаточно токенов
        """
        with self.lock:
            now = time.time()
            # Пополняем токены
            time_passed = now - self.last_refill
            self.tokens = min(
                self.capacity,
                self.tokens + time_passed * self.refill_rate
            )
            self.last_refill = now
            
            # Проверяем доступность токенов
            if self.tokens >= tokens:
                self.tokens -= tokens
                return True
            return False


class SlidingWindowCounter:
    """Реализация алгоритма Sliding Window Counter"""
    
    def __init__(self, limit: int, window: int):
        """
        Args:
            limit: Максимальное количество запросов
            window: Размер окна в секундах
        """
        self.limit = limit
        self.window = window
        self.requests = deque()
        self.lock = Lock()
    
    def can_proceed(self) -> bool:
        """Проверка возможности выполнения запроса"""
        with self.lock:
            now = time.time()
            # Удаляем старые запросы
            while self.requests and self.requests[0] <= now - self.window:
                self.requests.popleft()
            
            # Проверяем лимит
            if len(self.requests) < self.limit:
                self.requests.append(now)
                return True
            return False


class RateLimiter:
    """Основной класс для ограничения частоты запросов"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        
        # Конфигурации лимитов для разных типов операций
        self.limits = {
            'message': RateLimit(requests=30, window=60),      # 30 сообщений в минуту
            'api_call': RateLimit(requests=10, window=60),     # 10 API вызовов в минуту
            'callback': RateLimit(requests=50, window=60),     # 50 callback в минуту
            'command': RateLimit(requests=20, window=60),      # 20 команд в минуту
            'global': RateLimit(requests=100, window=60)       # 100 любых действий в минуту
        }
        
        # Хранилища для разных алгоритмов
        self.sliding_windows: Dict[str, SlidingWindowCounter] = {}
        self.token_buckets: Dict[str, TokenBucket] = {}
        
        # Блокировки пользователей
        self.blocked_users: Dict[int, float] = {}  # user_id -> timestamp до которого заблокирован
        
        self.lock = Lock()
    
    def _get_key(self, user_id: int, operation_type: str) -> str:
        """Генерация ключа для хранения состояния лимитера"""
        return f"{user_id}:{operation_type}"
    
    def _is_user_blocked(self, user_id: int) -> bool:
        """Проверка блокировки пользователя"""
        with self.lock:
            if user_id in self.blocked_users:
                if time.time() < self.blocked_users[user_id]:
                    return True
                else:
                    # Снимаем блокировку
                    del self.blocked_users[user_id]
            return False
    
    def _block_user(self, user_id: int, duration: int = 300):
        """Блокировка пользователя на определенное время"""
        with self.lock:
            self.blocked_users[user_id] = time.time() + duration
            self.logger.warning(f"User {user_id} blocked for {duration} seconds due to rate limit violation")
    
    def check_rate_limit(self, user_id: int, operation_type: str) -> bool:
        """
        Проверка ограничения частоты для пользователя и типа операции.
        
        Args:
            user_id: ID пользователя
            operation_type: Тип операции
            
        Returns:
            True если запрос разрешен, False если превышен лимит
            
        Raises:
            RateLimitError: При превышении лимита
        """
        # Проверяем блокировку
        if self._is_user_blocked(user_id):
            raise RateLimitError(user_id, 0, 0)
        
        # Проверяем существование лимита для типа операции
        if operation_type not in self.limits:
            self.logger.warning(f"Unknown operation type: {operation_type}")
            operation_type = 'global'
        
        limit_config = self.limits[operation_type]
        key = self._get_key(user_id, operation_type)
        
        # Создаем или получаем sliding window counter
        if key not in self.sliding_windows:
            with self.lock:
                if key not in self.sliding_windows:
                    self.sliding_windows[key] = SlidingWindowCounter(
                        limit_config.requests,
                        limit_config.window
                    )
        
        # Проверяем лимит
        if not self.sliding_windows[key].can_proceed():
            # Проверяем глобальный лимит
            global_key = self._get_key(user_id, 'global')
            if global_key not in self.sliding_windows:
                with self.lock:
                    if global_key not in self.sliding_windows:
                        self.sliding_windows[global_key] = SlidingWindowCounter(
                            self.limits['global'].requests,
                            self.limits['global'].window
                        )
            
            if not self.sliding_windows[global_key].can_proceed():
                # Блокируем пользователя при превышении глобального лимита
                self._block_user(user_id)
            
            raise RateLimitError(
                user_id,
                limit_config.requests,
                limit_config.window
            )
        
        return True
    
    def get_rate_limit_info(self, user_id: int, operation_type: str) -> Dict[str, int]:
        """
        Получение информации о текущем состоянии лимитов.
        
        Args:
            user_id: ID пользователя
            operation_type: Тип операции
            
        Returns:
            Словарь с информацией о лимитах
        """
        if operation_type not in self.limits:
            operation_type = 'global'
        
        limit_config = self.limits[operation_type]
        key = self._get_key(user_id, operation_type)
        
        if key in self.sliding_windows:
            window = self.sliding_windows[key]
            with window.lock:
                now = time.time()
                # Подсчитываем активные запросы
                active_requests = sum(1 for req_time in window.requests 
                                    if req_time > now - window.window)
                remaining = max(0, limit_config.requests - active_requests)
        else:
            remaining = limit_config.requests
        
        return {
            'limit': limit_config.requests,
            'window': limit_config.window,
            'remaining': remaining,
            'blocked': self._is_user_blocked(user_id)
        }
    
    def cleanup_old_data(self):
        """Очистка старых данных для освобождения памяти"""
        current_time = time.time()
        
        with self.lock:
            # Очищаем старые sliding windows
            keys_to_remove = []
            for key, window in self.sliding_windows.items():
                with window.lock:
                    # Если нет активных запросов в последние 10 минут
                    if (not window.requests or 
                        current_time - window.requests[-1] > 600):
                        keys_to_remove.append(key)
            
            for key in keys_to_remove:
                del self.sliding_windows[key]
            
            # Очищаем истекшие блокировки
            expired_blocks = [user_id for user_id, until_time in self.blocked_users.items()
                            if current_time >= until_time]
            for user_id in expired_blocks:
                del self.blocked_users[user_id]
        
        if keys_to_remove or expired_blocks:
            self.logger.info(f"Cleaned up {len(keys_to_remove)} rate limit entries and "
                           f"{len(expired_blocks)} expired blocks")

    def rate_limit_decorator(self, operation_type: str) -> Callable:
        """Декоратор для проверки rate limit"""
        def decorator(func: Callable) -> Callable:
            @functools.wraps(func)
            async def async_wrapper(*args, **kwargs):
                # Предполагаем, что user_id передается как аргумент
                user_id = None
                if args and hasattr(args[0], 'user_id'):
                    user_id = args[0].user_id
                elif 'user_id' in kwargs:
                    user_id = kwargs['user_id']
                
                if user_id:
                    self.check_rate_limit(user_id, operation_type)
                
                return await func(*args, **kwargs)
            
            @functools.wraps(func)
            def sync_wrapper(*args, **kwargs):
                # Аналогично для синхронных функций
                user_id = None
                if args and hasattr(args[0], 'user_id'):
                    user_id = args[0].user_id
                elif 'user_id' in kwargs:
                    user_id = kwargs['user_id']
                
                if user_id:
                    self.check_rate_limit(user_id, operation_type)
                
                return func(*args, **kwargs)
            
            return async_wrapper if asyncio.iscoroutinefunction(func) else sync_wrapper
        return decorator


# Глобальный экземпляр rate limiter
rate_limiter = RateLimiter()


def check_rate_limit(operation_type: str):
    """Декоратор для проверки rate limit"""
    def decorator(func):
        async def async_wrapper(*args, **kwargs):
            # Предполагаем, что user_id передается как аргумент
            user_id = None
            if args and hasattr(args[0], 'user_id'):
                user_id = args[0].user_id
            elif 'user_id' in kwargs:
                user_id = kwargs['user_id']
            
            if user_id:
                rate_limiter.check_rate_limit(user_id, operation_type)
            
            return await func(*args, **kwargs)
        
        def sync_wrapper(*args, **kwargs):
            # Аналогично для синхронных функций
            user_id = None
            if args and hasattr(args[0], 'user_id'):
                user_id = args[0].user_id
            elif 'user_id' in kwargs:
                user_id = kwargs['user_id']
            
            if user_id:
                rate_limiter.check_rate_limit(user_id, operation_type)
            
            return func(*args, **kwargs)
        
        return async_wrapper if asyncio.iscoroutinefunction(func) else sync_wrapper
    return decorator 