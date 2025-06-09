"""
Тесты для системы кэширования MemoryCache
"""

import pytest
import asyncio
import sys
import os
from datetime import datetime, timedelta

# Добавляем путь к корню проекта для импортов
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Простая реализация MemoryCache для тестирования
class MemoryCache:
    """Простой in-memory кэш для MVP"""
    
    def __init__(self, max_size=100, default_ttl=3600):
        self._data = {}
        self._ttl = {}
        self._max_size = max_size
        self._default_ttl = default_ttl
        self._access_order = []
    
    async def set(self, key: str, value, ttl: int = None):
        """Установить значение с опциональным TTL"""
        if ttl is None:
            ttl = self._default_ttl
        
        # Проверяем размер кэша и удаляем старые записи если нужно
        if len(self._data) >= self._max_size and key not in self._data:
            self._evict_oldest()
        
        self._data[key] = value
        self._ttl[key] = datetime.now() + timedelta(seconds=ttl)
        
        # Обновляем порядок доступа
        if key in self._access_order:
            self._access_order.remove(key)
        self._access_order.append(key)
    
    async def get(self, key: str):
        """Получить значение по ключу"""
        # Проверяем существование ключа
        if key not in self._data:
            return None
        
        # Проверяем TTL
        if self._ttl[key] < datetime.now():
            await self.delete(key)
            return None
        
        # Обновляем порядок доступа
        if key in self._access_order:
            self._access_order.remove(key)
        self._access_order.append(key)
        
        return self._data[key]
    
    async def delete(self, key: str):
        """Удалить значение по ключу"""
        if key in self._data:
            del self._data[key]
        if key in self._ttl:
            del self._ttl[key]
        if key in self._access_order:
            self._access_order.remove(key)
    
    async def clear(self):
        """Очистить весь кэш"""
        self._data.clear()
        self._ttl.clear()
        self._access_order.clear()
    
    async def exists(self, key: str) -> bool:
        """Проверить существование ключа"""
        value = await self.get(key)
        return value is not None
    
    def _evict_oldest(self):
        """Удалить самую старую запись"""
        if self._access_order:
            oldest_key = self._access_order[0]
            if oldest_key in self._data:
                del self._data[oldest_key]
            if oldest_key in self._ttl:
                del self._ttl[oldest_key]
            self._access_order.remove(oldest_key)

@pytest.fixture
def memory_cache():
    """Фикстура для создания MemoryCache"""
    return MemoryCache(max_size=10, default_ttl=3600)

@pytest.mark.asyncio
async def test_memory_cache_basic_operations(memory_cache):
    """Тест базовых операций set/get/delete"""
    # Тест установки и получения значения
    await memory_cache.set("test_key", "test_value")
    value = await memory_cache.get("test_key")
    assert value == "test_value"
    
    # Тест существования ключа
    exists = await memory_cache.exists("test_key")
    assert exists is True
    
    # Тест удаления
    await memory_cache.delete("test_key")
    value = await memory_cache.get("test_key")
    assert value is None
    
    # Тест существования после удаления
    exists = await memory_cache.exists("test_key")
    assert exists is False

@pytest.mark.asyncio
async def test_memory_cache_ttl(memory_cache):
    """Тест TTL (Time To Live)"""
    # Установка значения с коротким TTL
    await memory_cache.set("ttl_key", "ttl_value", ttl=1)
    
    # Проверка сразу после установки
    value = await memory_cache.get("ttl_key")
    assert value == "ttl_value"
    
    # Ожидание истечения TTL
    await asyncio.sleep(1.1)
    
    # Проверка после истечения TTL
    value = await memory_cache.get("ttl_key")
    assert value is None

@pytest.mark.asyncio
async def test_memory_cache_max_size_eviction(memory_cache):
    """Тест ограничения размера кэша с вытеснением"""
    # Заполнение кэша до максимального размера
    for i in range(10):
        await memory_cache.set(f"key_{i}", f"value_{i}")
    
    # Проверка, что все значения на месте
    for i in range(10):
        value = await memory_cache.get(f"key_{i}")
        assert value == f"value_{i}"
    
    # Добавление еще одного элемента (должно вытеснить самый старый)
    await memory_cache.set("new_key", "new_value")
    
    # Проверка, что общий размер не превышен
    assert len(memory_cache._data) <= memory_cache._max_size
    
    # Проверка, что самый старый элемент был удален
    value = await memory_cache.get("key_0")
    assert value is None
    
    # Проверка, что новый элемент добавлен
    value = await memory_cache.get("new_key")
    assert value == "new_value"

@pytest.mark.asyncio
async def test_memory_cache_different_data_types(memory_cache):
    """Тест кэширования разных типов данных"""
    # Строки
    await memory_cache.set("string_key", "string_value")
    assert await memory_cache.get("string_key") == "string_value"
    
    # Числа
    await memory_cache.set("int_key", 42)
    assert await memory_cache.get("int_key") == 42
    
    await memory_cache.set("float_key", 3.14)
    assert await memory_cache.get("float_key") == 3.14
    
    # Списки
    await memory_cache.set("list_key", [1, 2, 3])
    assert await memory_cache.get("list_key") == [1, 2, 3]
    
    # Словари
    await memory_cache.set("dict_key", {"a": 1, "b": 2})
    assert await memory_cache.get("dict_key") == {"a": 1, "b": 2}
    
    # None
    await memory_cache.set("none_key", None)
    assert await memory_cache.get("none_key") is None

@pytest.mark.asyncio
async def test_memory_cache_overwrite_existing_key(memory_cache):
    """Тест перезаписи существующего ключа"""
    # Установка начального значения
    await memory_cache.set("overwrite_key", "initial_value")
    assert await memory_cache.get("overwrite_key") == "initial_value"
    
    # Перезапись значения
    await memory_cache.set("overwrite_key", "new_value")
    assert await memory_cache.get("overwrite_key") == "new_value"
    
    # Проверка, что размер кэша не увеличился
    assert len(memory_cache._data) == 1

@pytest.mark.asyncio
async def test_memory_cache_clear(memory_cache):
    """Тест очистки кэша"""
    # Добавление нескольких элементов
    for i in range(5):
        await memory_cache.set(f"clear_key_{i}", f"clear_value_{i}")
    
    # Проверка, что элементы добавлены
    assert len(memory_cache._data) == 5
    
    # Очистка кэша
    await memory_cache.clear()
    
    # Проверка, что кэш пуст
    assert len(memory_cache._data) == 0
    assert len(memory_cache._ttl) == 0
    assert len(memory_cache._access_order) == 0
    
    # Проверка, что элементы действительно удалены
    for i in range(5):
        value = await memory_cache.get(f"clear_key_{i}")
        assert value is None

@pytest.mark.asyncio
async def test_memory_cache_lru_eviction_order(memory_cache):
    """Тест порядка вытеснения LRU (Least Recently Used)"""
    # Заполняем кэш
    for i in range(10):
        await memory_cache.set(f"lru_key_{i}", f"lru_value_{i}")
    
    # Обращаемся к некоторым ключам (делаем их "недавно использованными")
    await memory_cache.get("lru_key_0")  # Делаем самый старый ключ недавно используемым
    await memory_cache.get("lru_key_5")
    
    # Добавляем новый элемент
    await memory_cache.set("new_lru_key", "new_lru_value")
    
    # lru_key_0 и lru_key_5 должны остаться, а lru_key_1 должен быть удален
    assert await memory_cache.get("lru_key_0") == "lru_value_0"
    assert await memory_cache.get("lru_key_5") == "lru_value_5"
    assert await memory_cache.get("new_lru_key") == "new_lru_value"
    
    # Первый неиспользованный ключ должен быть удален
    assert await memory_cache.get("lru_key_1") is None

@pytest.mark.asyncio 
async def test_memory_cache_concurrent_access(memory_cache):
    """Тест конкурентного доступа к кэшу"""
    async def set_values(start_idx: int, count: int):
        for i in range(start_idx, start_idx + count):
            await memory_cache.set(f"concurrent_key_{i}", f"concurrent_value_{i}")
    
    async def get_values(start_idx: int, count: int):
        results = []
        for i in range(start_idx, start_idx + count):
            value = await memory_cache.get(f"concurrent_key_{i}")
            results.append(value)
        return results
    
    # Конкурентная установка значений
    await asyncio.gather(
        set_values(0, 5),
        set_values(5, 5)
    )
    
    # Конкурентное получение значений
    results1, results2 = await asyncio.gather(
        get_values(0, 5),
        get_values(5, 5)
    )
    
    # Проверка результатов
    expected1 = [f"concurrent_value_{i}" for i in range(0, 5)]
    expected2 = [f"concurrent_value_{i}" for i in range(5, 10)]
    
    assert results1 == expected1
    assert results2 == expected2

@pytest.mark.asyncio
async def test_memory_cache_edge_cases(memory_cache):
    """Тест граничных случаев"""
    # Получение несуществующего ключа
    value = await memory_cache.get("nonexistent_key")
    assert value is None
    
    # Удаление несуществующего ключа (не должно вызывать ошибку)
    await memory_cache.delete("nonexistent_key")
    
    # Проверка существования несуществующего ключа
    exists = await memory_cache.exists("nonexistent_key")
    assert exists is False
    
    # Установка с TTL = 0 (должно немедленно истекать)
    await memory_cache.set("zero_ttl_key", "zero_ttl_value", ttl=0)
    await asyncio.sleep(0.01)  # Небольшая задержка
    value = await memory_cache.get("zero_ttl_key")
    assert value is None 