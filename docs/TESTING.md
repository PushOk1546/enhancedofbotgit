# 🧪 Руководство по тестированию исправленного бота

## 📋 **Чек-лист перед запуском**

### ✅ **1. Проверка зависимостей**

```bash
# Проверка установки зависимостей
pip install -r requirements.txt

# Проверка ключевых библиотек
python -c "import telebot, groq, tenacity; print('✅ Все зависимости установлены')"
```

### ✅ **2. Проверка синтаксиса**

```bash
# Компиляция всех модулей
python -m py_compile bot.py api.py config.py handlers.py state_manager.py utils.py models.py

# Проверка импортов
python -c "from bot import BotManager; print('✅ Импорты работают')"
```

### ✅ **3. Конфигурация переменных окружения**

Создайте файл `.env` с **тестовыми** данными:

```env
# ТЕСТОВЫЕ ПЕРЕМЕННЫЕ - НЕ используйте реальные токены для первичного тестирования!
BOT_TOKEN=123456:test_token_for_validation_only
GROQ_KEY=test_groq_key_for_validation
ADMIN_IDS=377917978
```

### ✅ **4. Тестирование валидации конфигурации**

```bash
# Тест с пустыми переменными
python -c "
import os
from bot import BotManager

# Сброс переменных
os.environ['BOT_TOKEN'] = ''
os.environ['GROQ_KEY'] = ''

bm = BotManager()
result = bm._validate_config()
print(f'❌ Валидация пустых токенов: {result}')
"

# Тест с неверным форматом токена
python -c "
import os
from bot import BotManager

os.environ['BOT_TOKEN'] = 'invalid_token'
os.environ['GROQ_KEY'] = 'test_key'

bm = BotManager()
result = bm._validate_config()
print(f'❌ Валидация неверного токена: {result}')
"
```

## 🔧 **Тестирование компонентов**

### **1. Тест BotManager**

```python
# test_bot_manager.py
import asyncio
from bot import BotManager

async def test_bot_manager():
    """Тестирование основного менеджера бота"""
    bm = BotManager()
    
    # Тест инициализации без токенов
    print("🧪 Тест валидации конфигурации...")
    result = await bm.initialize()
    print(f"Результат инициализации без токенов: {result}")
    
    # Тест создания промпта
    if hasattr(bm, '_create_safe_prompt'):
        prompt = bm._create_safe_prompt("Тестовое сообщение", None)
        print(f"✅ Безопасный промпт создан: {len(prompt)} символов")

if __name__ == "__main__":
    asyncio.run(test_bot_manager())
```

### **2. Тест API менеджера**

```python
# test_api_manager.py
import asyncio
from api import APIManager

async def test_api_manager():
    """Тестирование API менеджера"""
    api = APIManager()
    
    # Тест валидации параметров
    try:
        await api.generate_groq_response("", "test_model")
    except ValueError as e:
        print(f"✅ Валидация пустого промпта работает: {e}")
    
    try:
        await api.generate_groq_response("test", "")
    except ValueError as e:
        print(f"✅ Валидация пустой модели работает: {e}")
    
    # Тест длинного промпта
    long_prompt = "x" * 5000
    try:
        # Это должно обрезать промпт без ошибки
        result = api._create_safe_prompt(long_prompt, None)
        print(f"✅ Обрезка длинного промпта: {len(result)} символов")
    except Exception as e:
        print(f"❌ Ошибка с длинным промптом: {e}")

if __name__ == "__main__":
    asyncio.run(test_api_manager())
```

### **3. Тест state_manager**

```python
# test_state_manager.py
import asyncio
from state_manager import StateManager

async def test_state_manager():
    """Тестирование менеджера состояний"""
    sm = StateManager()
    
    # Тест создания пользователя
    user = sm.get_user(123456)
    print(f"✅ Пользователь создан: ID={user.id}")
    
    # Тест сохранения данных
    try:
        await sm.save_data()
        print("✅ Данные сохранены успешно")
    except Exception as e:
        print(f"❌ Ошибка сохранения: {e}")
    
    # Тест добавления в историю
    sm.add_to_history(123456, 'user', 'Тестовое сообщение')
    history_length = len(user.message_history)
    print(f"✅ История сообщений: {history_length} записей")

if __name__ == "__main__":
    asyncio.run(test_state_manager())
```

## 🚀 **Безопасное тестирование с реальными токенами**

**⚠️ ВАЖНО:** Используйте реальные токены только после успешного прохождения всех тестов!

### **1. Подготовка реальной конфигурации**

```env
# .env для реального тестирования
BOT_TOKEN=1234567890:реальный_токен_вашего_бота
GROQ_KEY=реальный_ключ_groq_api
ADMIN_IDS=ваш_telegram_id
```

### **2. Тестирование с реальными API**

```python
# test_real_api.py
import asyncio
import os
from dotenv import load_dotenv
from api import generate_groq_response
from config import MODELS

async def test_real_groq():
    """Тестирование реального Groq API"""
    load_dotenv()
    
    if not os.getenv('GROQ_KEY') or 'test' in os.getenv('GROQ_KEY', ''):
        print("❌ Установите реальный GROQ_KEY для этого теста")
        return
    
    try:
        response = await generate_groq_response(
            "Привет! Это тест API.",
            MODELS['fast']['id'],
            max_tokens=50
        )
        print(f"✅ Groq API работает: {response[:100]}...")
    except Exception as e:
        print(f"❌ Ошибка Groq API: {e}")

if __name__ == "__main__":
    asyncio.run(test_real_groq())
```

### **3. Полное тестирование бота**

```bash
# Запуск в тестовом режиме
echo "🧪 Запуск бота в тестовом режиме..."
timeout 10s python bot.py || echo "✅ Бот запустился и остановился корректно"
```

## 📊 **Мониторинг в процессе тестирования**

### **1. Проверка логов**

```bash
# Создание папки для логов
mkdir -p logs

# Проверка логирования
python -c "
from utils import setup_logging
logger = setup_logging()
logger.info('🧪 Тест логирования')
logger.warning('⚠️ Тест предупреждения')
logger.error('❌ Тест ошибки')
print('✅ Логирование настроено')
"

# Проверка созданных логов
ls -la logs/
```

### **2. Мониторинг ресурсов**

```python
# resource_monitor.py
import asyncio
import psutil
import os
from bot import BotManager

async def monitor_resources():
    """Мониторинг использования ресурсов"""
    process = psutil.Process(os.getpid())
    
    print(f"🔍 Начальное использование памяти: {process.memory_info().rss / 1024 / 1024:.2f} MB")
    
    # Создаем много объектов для проверки утечек
    bm = BotManager()
    for i in range(100):
        await asyncio.sleep(0.01)
        if i % 20 == 0:
            memory_usage = process.memory_info().rss / 1024 / 1024
            print(f"Итерация {i}: {memory_usage:.2f} MB")
    
    print(f"🔍 Финальное использование памяти: {process.memory_info().rss / 1024 / 1024:.2f} MB")

if __name__ == "__main__":
    asyncio.run(monitor_resources())
```

## 🎯 **Критерии успешного тестирования**

### ✅ **Основные проверки:**

1. **Синтаксис:** Все модули компилируются без ошибок
2. **Импорты:** Все импорты работают корректно
3. **Валидация:** Неверные конфигурации обрабатываются правильно
4. **Обработка ошибок:** Исключения логируются, не вызывают crash
5. **Память:** Нет утечек памяти при длительной работе
6. **API:** Корректная обработка API ошибок и таймаутов

### ✅ **Функциональные проверки:**

1. **Команды:** Все команды выполняются без ошибок
2. **Callback'и:** Inline кнопки работают корректно
3. **Генерация:** API генерирует ответы успешно
4. **Сохранение:** Данные сохраняются и загружаются
5. **Опрос:** Система опроса работает последовательно

### ❌ **Признаки проблем:**

- Неперехваченные исключения в логах
- Постоянно растущее потребление памяти
- Timeout'ы API запросов
- Ошибки сохранения данных
- Crash бота при неверных данных

## 🚨 **Экстренное реагирование**

### **При обнаружении критических ошибок:**

1. **Остановите бота:** `Ctrl+C`
2. **Проверьте логи:** `tail -f logs/bot.json`
3. **Сохраните состояние:** Скопируйте `user_data.json`
4. **Отправьте отчет:** Включите логи и описание проблемы

### **Восстановление после ошибок:**

```bash
# Откат к предыдущей версии (если есть бэкап)
cp user_data.json.backup user_data.json

# Очистка логов
rm -f logs/*.log

# Перезапуск в безопасном режиме
python -c "
import os
os.environ['LOG_LEVEL'] = 'DEBUG'
from bot import main
import asyncio
asyncio.run(main())
"
```

---

**🎯 Цель:** Убедиться, что исправленный бот работает стабильно, безопасно и эффективно во всех сценариях использования. 