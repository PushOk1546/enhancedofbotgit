"""
Тесты для системы очередей задач
"""

import pytest
import asyncio
from datetime import datetime
from app.core.queue import TaskQueue, TaskManager, TaskStatus, TaskPriority

@pytest.fixture
async def queue():
    """Фикстура очереди"""
    queue = TaskQueue(max_workers=2, max_queue_size=10)
    await queue.start()
    yield queue
    await queue.stop()

@pytest.fixture
def task_manager(queue):
    """Фикстура менеджера задач"""
    return TaskManager(queue)

async def test_add_task(queue):
    """Тест добавления задачи"""
    async def test_func():
        return "test"
        
    task_id = await queue.add_task(test_func)
    assert task_id in queue.tasks
    assert queue.tasks[task_id].status == TaskStatus.PENDING
    
async def test_task_execution(queue):
    """Тест выполнения задачи"""
    result = None
    
    async def test_func():
        nonlocal result
        result = "test"
        return result
        
    task_id = await queue.add_task(test_func)
    await asyncio.sleep(0.1)  # Даем время на выполнение
    
    task = queue.tasks[task_id]
    assert task.status == TaskStatus.COMPLETED
    assert task.result == "test"
    assert result == "test"
    
async def test_task_priority(queue):
    """Тест приоритетов задач"""
    results = []
    
    async def test_func(value):
        results.append(value)
        return value
        
    # Добавляем задачи с разными приоритетами
    await queue.add_task(test_func, "low", priority=TaskPriority.LOW)
    await queue.add_task(test_func, "high", priority=TaskPriority.HIGH)
    await queue.add_task(test_func, "normal", priority=TaskPriority.NORMAL)
    
    await asyncio.sleep(0.2)  # Даем время на выполнение
    
    # Проверяем порядок выполнения
    assert results == ["high", "normal", "low"]
    
async def test_task_retry(queue):
    """Тест повторных попыток"""
    attempts = 0
    
    async def failing_func():
        nonlocal attempts
        attempts += 1
        if attempts < 3:
            raise ValueError("Test error")
        return "success"
        
    task_id = await queue.add_task(
        failing_func,
        max_retries=3,
        retry_delay=0.1
    )
    
    await asyncio.sleep(0.5)  # Даем время на выполнение
    
    task = queue.tasks[task_id]
    assert task.status == TaskStatus.COMPLETED
    assert task.result == "success"
    assert attempts == 3
    
async def test_task_timeout(queue):
    """Тест таймаута задачи"""
    async def slow_func():
        await asyncio.sleep(1)
        return "slow"
        
    task_id = await queue.add_task(
        slow_func,
        timeout=0.1
    )
    
    await asyncio.sleep(0.2)  # Даем время на выполнение
    
    task = queue.tasks[task_id]
    assert task.status == TaskStatus.FAILED
    assert isinstance(task.error, asyncio.TimeoutError)
    
async def test_task_cancellation(queue):
    """Тест отмены задачи"""
    async def test_func():
        await asyncio.sleep(1)
        return "test"
        
    task_id = await queue.add_task(test_func)
    success = await queue.cancel_task(task_id)
    
    assert success
    assert queue.tasks[task_id].status == TaskStatus.CANCELLED
    
async def test_queue_stats(queue):
    """Тест статистики очереди"""
    async def test_func():
        return "test"
        
    # Добавляем несколько задач
    for _ in range(3):
        await queue.add_task(test_func)
        
    stats = await queue.get_queue_stats()
    
    assert stats["total_tasks"] == 3
    assert stats["active_workers"] == 2
    assert "queues" in stats
    assert "status_counts" in stats
    
async def test_task_manager(task_manager):
    """Тест менеджера задач"""
    async def test_func():
        return "test"
        
    # Планируем задачу
    task_id = await task_manager.schedule_task(test_func)
    
    # Получаем информацию о задаче
    task_info = await task_manager.get_task_info(task_id)
    assert task_info is not None
    assert task_info["id"] == task_id
    
    # Получаем статус очереди
    queue_status = await task_manager.get_queue_status()
    assert "total_tasks" in queue_status
    
    # Отменяем задачу
    success = await task_manager.cancel_task(task_id)
    assert success
    
async def test_concurrent_tasks(queue):
    """Тест параллельного выполнения задач"""
    results = []
    
    async def test_func(value):
        await asyncio.sleep(0.1)
        results.append(value)
        return value
        
    # Добавляем несколько задач одновременно
    tasks = []
    for i in range(5):
        task_id = await queue.add_task(test_func, i)
        tasks.append(task_id)
        
    await asyncio.sleep(0.5)  # Даем время на выполнение
    
    # Проверяем, что все задачи выполнены
    for task_id in tasks:
        task = queue.tasks[task_id]
        assert task.status == TaskStatus.COMPLETED
        
    # Проверяем, что все результаты получены
    assert len(results) == 5
    assert set(results) == set(range(5))
    
async def test_queue_overflow(queue):
    """Тест переполнения очереди"""
    async def test_func():
        await asyncio.sleep(0.1)
        return "test"
        
    # Заполняем очередь
    for _ in range(10):
        await queue.add_task(test_func)
        
    # Пытаемся добавить еще одну задачу
    with pytest.raises(ValueError):
        await queue.add_task(test_func)
        
async def test_worker_error_handling(queue):
    """Тест обработки ошибок в воркерах"""
    error_count = 0
    
    async def error_func():
        nonlocal error_count
        error_count += 1
        raise ValueError("Worker error")
        
    # Добавляем задачу, которая вызовет ошибку
    task_id = await queue.add_task(error_func)
    
    await asyncio.sleep(0.2)  # Даем время на выполнение
    
    # Проверяем, что ошибка обработана
    task = queue.tasks[task_id]
    assert task.status == TaskStatus.FAILED
    assert isinstance(task.error, ValueError)
    assert error_count == 1  # Только одна попытка выполнения 