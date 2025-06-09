"""
Тесты для системы мониторинга производительности
"""

import pytest
import asyncio
import time
from datetime import datetime, timedelta
from app.core.monitoring import (
    PerformanceMonitor,
    PerformanceTracker,
    ResourceMonitor,
    MetricPoint
)

@pytest.fixture
def performance_monitor():
    """Фикстура для создания монитора производительности"""
    return PerformanceMonitor(history_size=100)

@pytest.fixture
def performance_tracker(performance_monitor):
    """Фикстура для создания трекера производительности"""
    return PerformanceTracker(performance_monitor)

@pytest.fixture
def resource_monitor(performance_monitor):
    """Фикстура для создания монитора ресурсов"""
    return ResourceMonitor(performance_monitor)

@pytest.mark.asyncio
async def test_metric_tracking(performance_monitor):
    """Тест отслеживания метрик"""
    # Отслеживание метрики
    await performance_monitor.track_metric("test_metric", 1.0, {"label": "test"})
    
    # Проверка статистики
    stats = await performance_monitor.get_metric_stats("test_metric")
    assert stats["count"] == 1
    assert stats["min"] == 1.0
    assert stats["max"] == 1.0
    assert stats["avg"] == 1.0

@pytest.mark.asyncio
async def test_metric_window(performance_monitor):
    """Тест окна времени для метрик"""
    # Отслеживание метрик в разное время
    await performance_monitor.track_metric("test_metric", 1.0)
    await asyncio.sleep(0.1)
    await performance_monitor.track_metric("test_metric", 2.0)
    
    # Проверка статистики за последние 0.05 секунд
    stats = await performance_monitor.get_metric_stats(
        "test_metric",
        window=timedelta(seconds=0.05)
    )
    assert stats["count"] == 1
    assert stats["min"] == 2.0

@pytest.mark.asyncio
async def test_api_tracking(performance_monitor):
    """Тест отслеживания API вызовов"""
    # Отслеживание успешного вызова
    await performance_monitor.track_api_call(
        "/test",
        duration=0.1,
        status=200
    )
    
    # Отслеживание вызова с ошибкой
    await performance_monitor.track_api_call(
        "/test",
        duration=0.2,
        status=500,
        error=True
    )
    
    # Проверка статистики
    api_stats = await performance_monitor.get_metric_stats("api_calls")
    error_stats = await performance_monitor.get_metric_stats("error_rate")
    
    assert api_stats["count"] == 2
    assert error_stats["count"] == 1

@pytest.mark.asyncio
async def test_cache_tracking(performance_monitor):
    """Тест отслеживания операций с кэшем"""
    # Отслеживание попадания в кэш
    await performance_monitor.track_cache_operation("get", hit=True)
    
    # Отслеживание промаха кэша
    await performance_monitor.track_cache_operation("get", hit=False)
    
    # Проверка статистики
    hits = await performance_monitor.get_metric_stats("cache_hits")
    misses = await performance_monitor.get_metric_stats("cache_misses")
    
    assert hits["count"] == 1
    assert misses["count"] == 1

@pytest.mark.asyncio
async def test_performance_tracker(performance_tracker):
    """Тест трекера производительности"""
    @performance_tracker.track("test_function")
    async def test_function():
        await asyncio.sleep(0.1)
        return "success"
        
    # Вызов функции
    result = await test_function()
    assert result == "success"
    
    # Проверка метрик
    stats = await performance_tracker.monitor.get_metric_stats("test_function")
    assert stats["count"] == 1
    assert stats["min"] >= 0.1

@pytest.mark.asyncio
async def test_resource_monitor(resource_monitor):
    """Тест монитора ресурсов"""
    # Проверка ресурсов
    warnings = await resource_monitor.check_resources()
    assert isinstance(warnings, dict)
    
    # Получение использования ресурсов
    usage = await resource_monitor.get_resource_usage()
    assert "memory_percent" in usage
    assert "cpu_percent" in usage

@pytest.mark.asyncio
async def test_performance_report(performance_monitor):
    """Тест отчета о производительности"""
    # Добавление тестовых данных
    await performance_monitor.track_api_call("/test", 0.1, 200)
    await performance_monitor.track_cache_operation("get", True)
    
    # Получение отчета
    report = await performance_monitor.get_performance_report()
    
    assert "uptime" in report
    assert "system_metrics" in report
    assert "api_metrics" in report
    assert "cache_metrics" in report

@pytest.mark.asyncio
async def test_metric_history(performance_monitor):
    """Тест истории метрик"""
    # Добавление метрик
    for i in range(150):  # Больше чем history_size
        await performance_monitor.track_metric("test_metric", float(i))
        
    # Проверка размера истории
    stats = await performance_monitor.get_metric_stats("test_metric")
    assert stats["count"] == 100  # history_size

@pytest.mark.asyncio
async def test_error_tracking(performance_tracker):
    """Тест отслеживания ошибок"""
    @performance_tracker.track("error_function")
    async def error_function():
        raise ValueError("Test error")
        
    # Вызов функции с ошибкой
    with pytest.raises(ValueError):
        await error_function()
        
    # Проверка метрик
    stats = await performance_tracker.monitor.get_metric_stats("error_function")
    assert stats["count"] == 1 