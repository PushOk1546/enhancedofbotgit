"""
Вспомогательные функции для работы с асинхронным кодом.
Обеспечивает правильное взаимодействие между async и sync компонентами.
"""

import asyncio
import functools
import time
import threading
from typing import Any, Callable, Coroutine, Optional, TypeVar, Union
from concurrent.futures import ThreadPoolExecutor, Future
import inspect
import logging

from .exceptions import BotException

T = TypeVar('T')
logger = logging.getLogger(__name__)


class AsyncManager:
    """Менеджер для управления асинхронными операциями"""
    
    def __init__(self, max_workers: int = 10):
        self.max_workers = max_workers
        self._executor: Optional[ThreadPoolExecutor] = None
        self._loop: Optional[asyncio.AbstractEventLoop] = None
        self._lock = threading.Lock()
    
    @property
    def executor(self) -> ThreadPoolExecutor:
        """Получение ThreadPoolExecutor с ленивой инициализацией"""
        if self._executor is None:
            with self._lock:
                if self._executor is None:
                    self._executor = ThreadPoolExecutor(max_workers=self.max_workers)
        return self._executor
    
    @property
    def loop(self) -> asyncio.AbstractEventLoop:
        """Получение текущего event loop"""
        try:
            return asyncio.get_running_loop()
        except RuntimeError:
            if self._loop is None:
                self._loop = asyncio.new_event_loop()
                asyncio.set_event_loop(self._loop)
            return self._loop
    
    def cleanup(self):
        """Очистка ресурсов"""
        if self._executor:
            self._executor.shutdown(wait=True)
            self._executor = None
        
        if self._loop and not self._loop.is_running():
            self._loop.close()
            self._loop = None


# Глобальный экземпляр менеджера
async_manager = AsyncManager()


def run_async(coro: Coroutine[Any, Any, T]) -> T:
    """
    Безопасный запуск корутины в синхронном контексте.
    
    Args:
        coro: Корутина для выполнения
        
    Returns:
        Результат выполнения корутины
        
    Raises:
        BotException: При ошибке выполнения
    """
    try:
        # Проверяем, есть ли уже запущенный event loop
        try:
            loop = asyncio.get_running_loop()
            # Если loop уже запущен, выполняем в отдельном потоке
            future = asyncio.run_coroutine_threadsafe(coro, loop)
            return future.result(timeout=30)  # 30 секунд timeout
        except RuntimeError:
            # Нет запущенного loop, создаем новый
            return asyncio.run(coro)
    except Exception as e:
        logger.error(f"Error running async function: {e}")
        raise BotException(f"Async execution failed: {str(e)}")


def make_async(func: Callable[..., T]) -> Callable[..., Coroutine[Any, Any, T]]:
    """
    Преобразование синхронной функции в асинхронную.
    
    Args:
        func: Синхронная функция
        
    Returns:
        Асинхронная обертка функции
    """
    @functools.wraps(func)
    async def async_wrapper(*args, **kwargs) -> T:
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(async_manager.executor, func, *args, **kwargs)
    
    return async_wrapper


def make_sync(func: Callable[..., Coroutine[Any, Any, T]]) -> Callable[..., T]:
    """
    Преобразование асинхронной функции в синхронную.
    
    Args:
        func: Асинхронная функция
        
    Returns:
        Синхронная обертка функции
    """
    @functools.wraps(func)
    def sync_wrapper(*args, **kwargs) -> T:
        coro = func(*args, **kwargs)
        return run_async(coro)
    
    return sync_wrapper


def async_timeout(seconds: float):
    """
    Декоратор для установки timeout на асинхронные функции.
    
    Args:
        seconds: Время ожидания в секундах
    """
    def decorator(func: Callable[..., Coroutine[Any, Any, T]]) -> Callable[..., Coroutine[Any, Any, T]]:
        @functools.wraps(func)
        async def wrapper(*args, **kwargs) -> T:
            try:
                return await asyncio.wait_for(func(*args, **kwargs), timeout=seconds)
            except asyncio.TimeoutError:
                logger.error(f"Function {func.__name__} timed out after {seconds} seconds")
                raise BotException(f"Operation timed out after {seconds} seconds")
        
        return wrapper
    return decorator


def retry_async(max_attempts: int = 3, delay: float = 1.0, backoff: float = 2.0):
    """
    Декоратор для повторных попыток выполнения асинхронных функций.
    
    Args:
        max_attempts: Максимальное количество попыток
        delay: Начальная задержка между попытками
        backoff: Множитель для увеличения задержки
    """
    def decorator(func: Callable[..., Coroutine[Any, Any, T]]) -> Callable[..., Coroutine[Any, Any, T]]:
        @functools.wraps(func)
        async def wrapper(*args, **kwargs) -> T:
            current_delay = delay
            last_exception = None
            
            for attempt in range(max_attempts):
                try:
                    return await func(*args, **kwargs)
                except Exception as e:
                    last_exception = e
                    if attempt == max_attempts - 1:
                        break
                    
                    logger.warning(
                        f"Attempt {attempt + 1} failed for {func.__name__}: {e}. "
                        f"Retrying in {current_delay} seconds..."
                    )
                    
                    await asyncio.sleep(current_delay)
                    current_delay *= backoff
            
            logger.error(f"All {max_attempts} attempts failed for {func.__name__}")
            raise BotException(f"Function failed after {max_attempts} attempts") from last_exception
        
        return wrapper
    return decorator


class AsyncContextManager:
    """Базовый класс для асинхронных контекстных менеджеров"""
    
    async def __aenter__(self):
        await self.setup()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.cleanup()
        if exc_type is not None:
            logger.error(f"Exception in async context manager: {exc_val}")
        return False
    
    async def setup(self):
        """Инициализация ресурсов"""
        pass
    
    async def cleanup(self):
        """Очистка ресурсов"""
        pass


class AsyncBatch:
    """Класс для пакетной обработки асинхронных операций"""
    
    def __init__(self, batch_size: int = 10, max_concurrency: int = 5):
        self.batch_size = batch_size
        self.max_concurrency = max_concurrency
        self.semaphore = asyncio.Semaphore(max_concurrency)
    
    async def process_batch(
        self,
        items: list,
        processor: Callable[[Any], Coroutine[Any, Any, T]]
    ) -> list[T]:
        """
        Обработка элементов пакетами с ограничением конкурентности.
        
        Args:
            items: Список элементов для обработки
            processor: Асинхронная функция обработки
            
        Returns:
            Список результатов
        """
        results = []
        
        for i in range(0, len(items), self.batch_size):
            batch = items[i:i + self.batch_size]
            
            async def process_with_semaphore(item):
                async with self.semaphore:
                    return await processor(item)
            
            batch_results = await asyncio.gather(
                *[process_with_semaphore(item) for item in batch],
                return_exceptions=True
            )
            
            # Обрабатываем результаты и исключения
            for result in batch_results:
                if isinstance(result, Exception):
                    logger.error(f"Error processing item: {result}")
                    results.append(None)
                else:
                    results.append(result)
        
        return results


class AsyncCache:
    """Простой асинхронный кеш с TTL"""
    
    def __init__(self, default_ttl: float = 300):  # 5 минут по умолчанию
        self.default_ttl = default_ttl
        self._cache: dict = {}
        self._lock = asyncio.Lock()
    
    async def get(self, key: str) -> Optional[Any]:
        """Получение значения из кеша"""
        async with self._lock:
            if key in self._cache:
                value, expiry = self._cache[key]
                if time.time() < expiry:
                    return value
                else:
                    del self._cache[key]
            return None
    
    async def set(self, key: str, value: Any, ttl: Optional[float] = None) -> None:
        """Установка значения в кеш"""
        if ttl is None:
            ttl = self.default_ttl
        
        expiry = time.time() + ttl
        async with self._lock:
            self._cache[key] = (value, expiry)
    
    async def delete(self, key: str) -> bool:
        """Удаление значения из кеша"""
        async with self._lock:
            if key in self._cache:
                del self._cache[key]
                return True
            return False
    
    async def clear_expired(self):
        """Очистка истекших записей"""
        current_time = time.time()
        async with self._lock:
            expired_keys = [
                key for key, (_, expiry) in self._cache.items()
                if current_time >= expiry
            ]
            for key in expired_keys:
                del self._cache[key]
        
        if expired_keys:
            logger.info(f"Cleared {len(expired_keys)} expired cache entries")


def cached_async(ttl: float = 300, key_func: Optional[Callable] = None):
    """
    Декоратор для кеширования результатов асинхронных функций.
    
    Args:
        ttl: Время жизни кеша в секундах
        key_func: Функция для генерации ключа кеша
    """
    cache = AsyncCache(default_ttl=ttl)
    
    def decorator(func: Callable[..., Coroutine[Any, Any, T]]) -> Callable[..., Coroutine[Any, Any, T]]:
        @functools.wraps(func)
        async def wrapper(*args, **kwargs) -> T:
            # Генерируем ключ кеша
            if key_func:
                cache_key = key_func(*args, **kwargs)
            else:
                cache_key = f"{func.__name__}:{hash((args, tuple(sorted(kwargs.items()))))}"
            
            # Проверяем кеш
            cached_result = await cache.get(cache_key)
            if cached_result is not None:
                return cached_result
            
            # Выполняем функцию и кешируем результат
            result = await func(*args, **kwargs)
            await cache.set(cache_key, result, ttl)
            
            return result
        
        # Добавляем методы для управления кешем
        wrapper.cache = cache
        wrapper.clear_cache = cache.clear_expired
        
        return wrapper
    return decorator


def ensure_async(func_or_coro: Union[Callable, Coroutine]) -> Coroutine:
    """
    Гарантирует, что результат будет корутиной.
    
    Args:
        func_or_coro: Функция или корутина
        
    Returns:
        Корутина
    """
    if inspect.iscoroutine(func_or_coro):
        return func_or_coro
    elif inspect.iscoroutinefunction(func_or_coro):
        return func_or_coro()
    elif callable(func_or_coro):
        return make_async(func_or_coro)()
    else:
        async def return_value():
            return func_or_coro
        return return_value()


async def safe_gather(*coros, return_exceptions: bool = True, max_concurrency: int = 10):
    """
    Безопасное выполнение множественных корутин с ограничением конкурентности.
    
    Args:
        *coros: Корутины для выполнения
        return_exceptions: Возвращать исключения вместо их поднятия
        max_concurrency: Максимальное количество одновременных операций
        
    Returns:
        Список результатов
    """
    semaphore = asyncio.Semaphore(max_concurrency)
    
    async def run_with_semaphore(coro):
        async with semaphore:
            return await coro
    
    limited_coros = [run_with_semaphore(coro) for coro in coros]
    return await asyncio.gather(*limited_coros, return_exceptions=return_exceptions) 