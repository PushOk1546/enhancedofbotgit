"""
Модуль системы очередей задач
"""

import asyncio
import time
import uuid
from typing import Any, Dict, List, Optional, Callable, Union
from datetime import datetime, timedelta
from dataclasses import dataclass
from enum import Enum
from loguru import logger

class TaskStatus(Enum):
    """Статусы задачи"""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    RETRYING = "retrying"
    CANCELLED = "cancelled"

class TaskPriority(Enum):
    """Приоритеты задачи"""
    LOW = 0
    NORMAL = 1
    HIGH = 2
    CRITICAL = 3

@dataclass
class Task:
    """Задача"""
    id: str
    func: Callable
    args: tuple
    kwargs: dict
    priority: TaskPriority
    max_retries: int
    retry_delay: float
    timeout: Optional[float]
    created_at: datetime
    status: TaskStatus
    result: Any = None
    error: Optional[Exception] = None
    retry_count: int = 0
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None

class TaskQueue:
    """Очередь задач"""
    
    def __init__(self, max_workers: int = 10, max_queue_size: int = 1000):
        self.max_workers = max_workers
        self.max_queue_size = max_queue_size
        self.queues: Dict[TaskPriority, asyncio.Queue] = {
            priority: asyncio.Queue(maxsize=max_queue_size)
            for priority in TaskPriority
        }
        self.tasks: Dict[str, Task] = {}
        self.workers: List[asyncio.Task] = []
        self._monitor = None
        self._stop_event = asyncio.Event()
        
    def set_monitor(self, monitor) -> None:
        """Установка монитора для отслеживания"""
        self._monitor = monitor
        
    async def start(self) -> None:
        """Запуск обработчиков задач"""
        self._stop_event.clear()
        for _ in range(self.max_workers):
            worker = asyncio.create_task(self._worker())
            self.workers.append(worker)
            
    async def stop(self) -> None:
        """Остановка обработчиков задач"""
        self._stop_event.set()
        await asyncio.gather(*self.workers, return_exceptions=True)
        self.workers.clear()
        
    async def add_task(self, func: Callable, *args, 
                      priority: TaskPriority = TaskPriority.NORMAL,
                      max_retries: int = 3,
                      retry_delay: float = 1.0,
                      timeout: Optional[float] = None,
                      **kwargs) -> str:
        """Добавление задачи в очередь"""
        if len(self.tasks) >= self.max_queue_size:
            raise ValueError("Queue is full")
            
        task_id = str(uuid.uuid4())
        task = Task(
            id=task_id,
            func=func,
            args=args,
            kwargs=kwargs,
            priority=priority,
            max_retries=max_retries,
            retry_delay=retry_delay,
            timeout=timeout,
            created_at=datetime.now(),
            status=TaskStatus.PENDING
        )
        
        self.tasks[task_id] = task
        await self.queues[priority].put(task)
        
        if self._monitor:
            await self._monitor.track_metric("queue_size", len(self.tasks))
            
        return task_id
        
    async def get_task_status(self, task_id: str) -> Optional[Task]:
        """Получение статуса задачи"""
        return self.tasks.get(task_id)
        
    async def cancel_task(self, task_id: str) -> bool:
        """Отмена задачи"""
        task = self.tasks.get(task_id)
        if task and task.status in [TaskStatus.PENDING, TaskStatus.RETRYING]:
            task.status = TaskStatus.CANCELLED
            return True
        return False
        
    async def _worker(self) -> None:
        """Обработчик задач"""
        while not self._stop_event.is_set():
            try:
                # Получение задачи с наивысшим приоритетом
                task = None
                for priority in reversed(list(TaskPriority)):
                    try:
                        task = await asyncio.wait_for(
                            self.queues[priority].get(),
                            timeout=0.1
                        )
                        break
                    except asyncio.TimeoutError:
                        continue
                        
                if task is None:
                    continue
                    
                if task.status == TaskStatus.CANCELLED:
                    self.queues[task.priority].task_done()
                    continue
                    
                # Выполнение задачи
                task.status = TaskStatus.RUNNING
                task.started_at = datetime.now()
                
                try:
                    if task.timeout:
                        result = await asyncio.wait_for(
                            task.func(*task.args, **task.kwargs),
                            timeout=task.timeout
                        )
                    else:
                        result = await task.func(*task.args, **task.kwargs)
                        
                    task.result = result
                    task.status = TaskStatus.COMPLETED
                    
                except Exception as e:
                    task.error = e
                    if task.retry_count < task.max_retries:
                        task.status = TaskStatus.RETRYING
                        task.retry_count += 1
                        await asyncio.sleep(task.retry_delay * task.retry_count)
                        await self.queues[task.priority].put(task)
                    else:
                        task.status = TaskStatus.FAILED
                        logger.error(f"Task {task.id} failed: {str(e)}")
                        
                finally:
                    task.completed_at = datetime.now()
                    if self._monitor:
                        duration = (task.completed_at - task.started_at).total_seconds()
                        await self._monitor.track_metric("task_duration", duration)
                        
                self.queues[task.priority].task_done()
                
            except Exception as e:
                logger.error(f"Worker error: {str(e)}")
                await asyncio.sleep(1)
                
    async def get_queue_stats(self) -> Dict[str, Any]:
        """Получение статистики очереди"""
        return {
            "total_tasks": len(self.tasks),
            "active_workers": len(self.workers),
            "queues": {
                priority.name: queue.qsize()
                for priority, queue in self.queues.items()
            },
            "status_counts": {
                status.name: sum(1 for t in self.tasks.values() if t.status == status)
                for status in TaskStatus
            }
        }

class TaskManager:
    """Менеджер задач"""
    
    def __init__(self, queue: TaskQueue):
        self.queue = queue
        
    async def schedule_task(self, func: Callable, *args, **kwargs) -> str:
        """Планирование задачи"""
        return await self.queue.add_task(func, *args, **kwargs)
        
    async def get_task_info(self, task_id: str) -> Optional[Dict[str, Any]]:
        """Получение информации о задаче"""
        task = await self.queue.get_task_status(task_id)
        if task:
            return {
                "id": task.id,
                "status": task.status.name,
                "created_at": task.created_at.isoformat(),
                "started_at": task.started_at.isoformat() if task.started_at else None,
                "completed_at": task.completed_at.isoformat() if task.completed_at else None,
                "retry_count": task.retry_count,
                "error": str(task.error) if task.error else None
            }
        return None
        
    async def cancel_task(self, task_id: str) -> bool:
        """Отмена задачи"""
        return await self.queue.cancel_task(task_id)
        
    async def get_queue_status(self) -> Dict[str, Any]:
        """Получение статуса очереди"""
        return await self.queue.get_queue_stats() 