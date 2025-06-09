"""
Тесты для системы управления состоянием
"""

import pytest
import asyncio
import json
from pathlib import Path
from app.core.state import StateManager

@pytest.fixture
async def state_manager(tmp_path):
    """Фикстура для создания менеджера состояния"""
    state_file = tmp_path / "test_state.json"
    manager = StateManager(str(state_file))
    await manager.initialize()
    yield manager
    # Очистка после тестов
    if state_file.exists():
        state_file.unlink()

@pytest.mark.asyncio
async def test_state_initialization(state_manager):
    """Тест инициализации состояния"""
    assert isinstance(state_manager._state, dict)
    assert len(state_manager._state) == 0

@pytest.mark.asyncio
async def test_set_get_operations(state_manager):
    """Тест операций установки и получения значений"""
    # Установка значения
    await state_manager.set("test_key", "test_value")
    # Получение значения
    value = await state_manager.get("test_key")
    assert value == "test_value"
    # Получение несуществующего значения
    default_value = await state_manager.get("non_existent", "default")
    assert default_value == "default"

@pytest.mark.asyncio
async def test_delete_operation(state_manager):
    """Тест операции удаления"""
    # Установка и удаление значения
    await state_manager.set("test_key", "test_value")
    await state_manager.delete("test_key")
    value = await state_manager.get("test_key")
    assert value is None

@pytest.mark.asyncio
async def test_lock_operations(state_manager):
    """Тест операций с блокировками"""
    # Получение блокировки
    await state_manager.acquire_lock("test_key")
    assert state_manager._locks["test_key"].locked()
    # Освобождение блокировки
    await state_manager.release_lock("test_key")
    assert not state_manager._locks["test_key"].locked()

@pytest.mark.asyncio
async def test_get_with_lock(state_manager):
    """Тест получения значения с блокировкой"""
    await state_manager.set("test_key", "test_value")
    value = await state_manager.get_with_lock("test_key")
    assert value == "test_value"
    assert not state_manager._locks["test_key"].locked()

@pytest.mark.asyncio
async def test_set_with_lock(state_manager):
    """Тест установки значения с блокировкой"""
    await state_manager.set_with_lock("test_key", "test_value")
    value = await state_manager.get("test_key")
    assert value == "test_value"
    assert not state_manager._locks["test_key"].locked()

@pytest.mark.asyncio
async def test_update_operation(state_manager):
    """Тест массового обновления"""
    updates = {
        "key1": "value1",
        "key2": "value2"
    }
    await state_manager.update(updates)
    assert await state_manager.get("key1") == "value1"
    assert await state_manager.get("key2") == "value2"

@pytest.mark.asyncio
async def test_clear_operation(state_manager):
    """Тест очистки состояния"""
    await state_manager.set("test_key", "test_value")
    await state_manager.clear()
    assert len(state_manager._state) == 0

@pytest.mark.asyncio
async def test_persistence(state_manager):
    """Тест персистентности состояния"""
    # Установка значений
    await state_manager.set("key1", "value1")
    await state_manager.set("key2", "value2")
    
    # Создание нового менеджера с тем же файлом
    new_manager = StateManager(str(state_manager.state_file))
    await new_manager.initialize()
    
    # Проверка сохраненных значений
    assert await new_manager.get("key1") == "value1"
    assert await new_manager.get("key2") == "value2"

@pytest.mark.asyncio
async def test_concurrent_operations(state_manager):
    """Тест конкурентных операций"""
    async def update_value(key: str, value: str):
        await state_manager.set_with_lock(key, value)
        
    # Запуск конкурентных операций
    tasks = [
        update_value("test_key", f"value_{i}")
        for i in range(5)
    ]
    await asyncio.gather(*tasks)
    
    # Проверка финального значения
    value = await state_manager.get("test_key")
    assert value in [f"value_{i}" for i in range(5)] 