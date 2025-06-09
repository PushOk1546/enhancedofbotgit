"""
Инициализация модуля app.core
"""

from .cache import MemoryCache
from .state import StateManager

# Глобальные экземпляры для использования в боте
memory_cache = MemoryCache()
state_manager = StateManager()

__all__ = ['memory_cache', 'state_manager', 'MemoryCache', 'StateManager'] 