"""
Модуль мониторинга производительности
"""

import asyncio
import time
import psutil
from typing import Any, Dict, List, Optional, Callable
from datetime import datetime, timedelta
from collections import deque
from dataclasses import dataclass
from loguru import logger

@dataclass
class MetricPoint:
    """Точка метрики"""
    timestamp: datetime
    value: float
    labels: Dict[str, str]

class PerformanceMonitor:
    """Монитор производительности"""
    
    def __init__(self, history_size: int = 1000):
        self.metrics: Dict[str, deque] = {}
        self.history_size = history_size
        self.start_time = datetime.now()
        self._setup_metrics()
        
    def _setup_metrics(self) -> None:
        """Настройка базовых метрик"""
        self._add_metric("response_time", "Время ответа")
        self._add_metric("memory_usage", "Использование памяти")
        self._add_metric("cpu_usage", "Использование CPU")
        self._add_metric("api_calls", "Вызовы API")
        self._add_metric("cache_hits", "Попадания в кэш")
        self._add_metric("cache_misses", "Промахи кэша")
        self._add_metric("error_rate", "Частота ошибок")
        
    def _add_metric(self, name: str, description: str) -> None:
        """Добавление новой метрики"""
        self.metrics[name] = {
            "data": deque(maxlen=self.history_size),
            "description": description
        }
        
    async def track_metric(self, name: str, value: float, labels: Dict[str, str] = None) -> None:
        """Отслеживание метрики"""
        if name not in self.metrics:
            self._add_metric(name, name)
            
        point = MetricPoint(
            timestamp=datetime.now(),
            value=value,
            labels=labels or {}
        )
        self.metrics[name]["data"].append(point)
        
    async def get_metric_stats(self, name: str, 
                             window: Optional[timedelta] = None) -> Dict[str, float]:
        """Получение статистики по метрике"""
        if name not in self.metrics:
            return {}
            
        data = self.metrics[name]["data"]
        if window:
            cutoff = datetime.now() - window
            data = [p for p in data if p.timestamp > cutoff]
            
        if not data:
            return {}
            
        values = [p.value for p in data]
        return {
            "min": min(values),
            "max": max(values),
            "avg": sum(values) / len(values),
            "count": len(values)
        }
        
    async def get_system_metrics(self) -> Dict[str, float]:
        """Получение системных метрик"""
        process = psutil.Process()
        return {
            "memory_percent": process.memory_percent(),
            "cpu_percent": process.cpu_percent(),
            "threads": process.num_threads(),
            "open_files": len(process.open_files()),
            "connections": len(process.connections())
        }
        
    async def track_api_call(self, endpoint: str, duration: float, 
                           status: int, error: bool = False) -> None:
        """Отслеживание вызова API"""
        await self.track_metric("api_calls", 1, {
            "endpoint": endpoint,
            "status": str(status),
            "error": str(error)
        })
        await self.track_metric("response_time", duration, {
            "endpoint": endpoint
        })
        if error:
            await self.track_metric("error_rate", 1, {
                "endpoint": endpoint
            })
            
    async def track_cache_operation(self, operation: str, hit: bool) -> None:
        """Отслеживание операций с кэшем"""
        metric = "cache_hits" if hit else "cache_misses"
        await self.track_metric(metric, 1, {
            "operation": operation
        })
        
    def get_uptime(self) -> timedelta:
        """Получение времени работы"""
        return datetime.now() - self.start_time
        
    async def get_performance_report(self) -> Dict[str, Any]:
        """Получение отчета о производительности"""
        return {
            "uptime": str(self.get_uptime()),
            "system_metrics": await self.get_system_metrics(),
            "api_metrics": {
                name: await self.get_metric_stats(name)
                for name in ["api_calls", "response_time", "error_rate"]
            },
            "cache_metrics": {
                name: await self.get_metric_stats(name)
                for name in ["cache_hits", "cache_misses"]
            }
        }

class PerformanceTracker:
    """Трекер производительности для функций"""
    
    def __init__(self, monitor: PerformanceMonitor):
        self.monitor = monitor
        
    def track(self, metric_name: str):
        """Декоратор для отслеживания производительности функции"""
        def decorator(func: Callable):
            @wraps(func)
            async def wrapper(*args, **kwargs):
                start_time = time.time()
                try:
                    result = await func(*args, **kwargs)
                    duration = time.time() - start_time
                    await self.monitor.track_metric(metric_name, duration, {
                        "function": func.__name__,
                        "status": "success"
                    })
                    return result
                except Exception as e:
                    duration = time.time() - start_time
                    await self.monitor.track_metric(metric_name, duration, {
                        "function": func.__name__,
                        "status": "error",
                        "error": str(e)
                    })
                    raise
            return wrapper
        return decorator

class ResourceMonitor:
    """Монитор ресурсов"""
    
    def __init__(self, monitor: PerformanceMonitor):
        self.monitor = monitor
        self.warning_thresholds = {
            "memory_percent": 80.0,
            "cpu_percent": 90.0
        }
        
    async def check_resources(self) -> Dict[str, bool]:
        """Проверка ресурсов"""
        metrics = await self.monitor.get_system_metrics()
        warnings = {}
        
        for metric, threshold in self.warning_thresholds.items():
            if metrics[metric] > threshold:
                warnings[metric] = True
                logger.warning(f"High {metric}: {metrics[metric]}%")
                
        return warnings
        
    async def get_resource_usage(self) -> Dict[str, float]:
        """Получение использования ресурсов"""
        return await self.monitor.get_system_metrics() 