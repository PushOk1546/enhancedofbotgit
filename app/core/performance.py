"""
Модуль управления производительностью системы
"""

import asyncio
import time
from typing import Any, Dict, Optional
from functools import wraps
from cachetools import TTLCache, LRUCache
from datetime import datetime, timedelta

class PerformanceManager:
    """Менеджер производительности с многоуровневым кэшированием"""
    
    def __init__(self):
        # Быстрый кэш для частых запросов (5 минут)
        self.quick_cache = TTLCache(maxsize=1000, ttl=300)
        # Долгосрочный кэш для стабильных данных (1 час)
        self.long_term_cache = TTLCache(maxsize=10000, ttl=3600)
        # Кэш для результатов API (15 минут)
        self.api_cache = TTLCache(maxsize=5000, ttl=900)
        # Метрики производительности
        self.metrics: Dict[str, list] = {
            'response_times': [],
            'cache_hits': [],
            'cache_misses': [],
            'api_calls': []
        }
        # Ограничения запросов
        self.rate_limits: Dict[str, list] = {}
        
    async def get_cached_data(self, key: str, cache_type: str = 'quick') -> Optional[Any]:
        """Получение данных из кэша с учетом типа"""
        start_time = time.time()
        
        cache = getattr(self, f'{cache_type}_cache')
        result = cache.get(key)
        
        if result is not None:
            self.metrics['cache_hits'].append(time.time() - start_time)
            return result
            
        self.metrics['cache_misses'].append(time.time() - start_time)
        return None
        
    async def set_cached_data(self, key: str, value: Any, cache_type: str = 'quick') -> None:
        """Сохранение данных в кэш"""
        cache = getattr(self, f'{cache_type}_cache')
        cache[key] = value
        
    def check_rate_limit(self, user_id: str, limit: int = 60, window: int = 60) -> bool:
        """Проверка ограничения частоты запросов"""
        now = time.time()
        if user_id not in self.rate_limits:
            self.rate_limits[user_id] = []
            
        # Очистка старых запросов
        self.rate_limits[user_id] = [
            req_time for req_time in self.rate_limits[user_id]
            if now - req_time < window
        ]
        
        if len(self.rate_limits[user_id]) >= limit:
            return False
            
        self.rate_limits[user_id].append(now)
        return True
        
    def track_metric(self, metric_name: str, value: float) -> None:
        """Отслеживание метрики производительности"""
        if metric_name in self.metrics:
            self.metrics[metric_name].append(value)
            
    def get_performance_stats(self) -> Dict[str, float]:
        """Получение статистики производительности"""
        stats = {}
        for metric_name, values in self.metrics.items():
            if values:
                stats[f'{metric_name}_avg'] = sum(values) / len(values)
                stats[f'{metric_name}_max'] = max(values)
                stats[f'{metric_name}_min'] = min(values)
        return stats

def performance_tracker(func):
    """Декоратор для отслеживания производительности функций"""
    @wraps(func)
    async def wrapper(self, *args, **kwargs):
        start_time = time.time()
        try:
            result = await func(self, *args, **kwargs)
            execution_time = time.time() - start_time
            self.performance_manager.track_metric('response_times', execution_time)
            return result
        except Exception as e:
            execution_time = time.time() - start_time
            self.performance_manager.track_metric('response_times', execution_time)
            raise
    return wrapper

class PerformanceOptimizer:
    """Оптимизатор производительности"""
    
    def __init__(self, performance_manager: PerformanceManager):
        self.performance_manager = performance_manager
        self.optimization_threshold = 1.0  # секунды
        
    async def optimize_if_needed(self, metric_name: str) -> None:
        """Проверка необходимости оптимизации"""
        stats = self.performance_manager.get_performance_stats()
        if f'{metric_name}_avg' in stats and stats[f'{metric_name}_avg'] > self.optimization_threshold:
            await self._apply_optimizations(metric_name)
            
    async def _apply_optimizations(self, metric_name: str) -> None:
        """Применение оптимизаций"""
        if metric_name == 'response_times':
            # Увеличиваем размер кэша
            self.performance_manager.quick_cache.maxsize *= 2
        elif metric_name == 'api_calls':
            # Увеличиваем TTL для API кэша
            self.performance_manager.api_cache.ttl *= 2 