# 🚀 Инструкция по установке OF Assistant Bot

## ✅ Проверка готовности системы

### 1. **Синтаксис кода**
Все Python файлы имеют корректный синтаксис:
```bash
python test_syntax.py
# Результат: 33 ✅ | 0 ❌ - все файлы корректны
```

### 2. **Внутренние модули**
Все внутренние модули работают:
```bash
python test_imports.py
# Результат: 15/15 модулей ✅ - все модули доступны
```

## 📋 Требуемые зависимости

### **Основные пакеты (для полного функционала):**
```bash
pip install -r requirements.txt
```

**Содержимое requirements.txt:**
```
aiohttp
aiofiles
python-json-logger
apscheduler
PyTelegramBotAPI
python-dotenv
```

### **Опциональные пакеты (для улучшенной производительности):**
```bash
pip install ujson cachetools
```

## 🔧 Настройка окружения

### 1. **Создание .env файла**
```bash
cp env_template.txt .env
```

### 2. **Заполнение переменных в .env:**
```env
TELEGRAM_BOT_TOKEN=your_telegram_bot_token_here
DEEPSEEK_API_KEY=your_deepseek_api_key_here
```

## 🚦 Запуск бота

### **Способ 1: Через Python**
```bash
python main.py
```

### **Способ 2: Через batch файл (Windows)**
```bash
СТАРТ_БОТА.bat
```

### **Способ 3: Простой лаунчер**
```bash
python simple_launcher.py
```

## 🛠️ Решение проблем

### **Проблема: `No module named 'telebot'`**
**Решение:**
```bash
pip install PyTelegramBotAPI
```

### **Проблема: `No module named 'aiohttp'`**
**Решение:**
```bash
pip install aiohttp aiofiles
```

### **Проблема: `No module named 'apscheduler'`**
**Решение:**
```bash
pip install apscheduler
```

### **Проблема: Git конфликты**
**Решение:** Все конфликты уже исправлены в текущей версии

### **Проблема: Отсутствуют переменные окружения**
**Решение:**
1. Создайте `.env` файл в корне проекта
2. Добавьте необходимые токены
3. Убедитесь что файл не добавлен в git

## 🧪 Тестирование системы

### **Тест синтаксиса:**
```bash
python test_syntax.py
```

### **Тест импортов:**
```bash
python test_imports.py
```

### **Smoke тест (требует зависимости):**
```bash
python tests/smoke_test.py
```

## 📦 Структура проекта

```
of_assistant_bot/
├── main.py              # 🚀 Основная точка входа
├── handlers.py          # 📱 Обработчики команд
├── config.py           # ⚙️ Конфигурация
├── utils.py            # 🛠️ Вспомогательные функции
├── models.py           # 📊 Модели данных
├── api_handler.py      # 🌐 DeepSeek API
├── enhanced_logging.py # 📝 Логирование
├── services/           # 🔧 Сервисы
│   └── ai_integration.py
├── tests/              # 🧪 Тесты
│   └── smoke_test.py
├── requirements.txt    # 📋 Зависимости
├── .env               # 🔐 Переменные окружения
└── СТАРТ_БОТА.bat     # 🖱️ Быстрый запуск
```

## 🎯 Команды бота

После успешного запуска доступны команды:

- `/start` - Запуск бота и приветствие
- `/test_deepseek` - Тест DeepSeek AI
- `/flirt` - Режим флирта
- `/ppv` - PPV контент меню
- `/generate_ppv [тип] [цена] [описание]` - Генерация PPV
- `/stats` - Статистика системы

## ⚡ Fallback режим (без зависимостей)

Система спроектирована с fallback режимом:

- **Без telebot**: Можно тестировать внутренние модули
- **Без ujson**: Использует стандартный json
- **Без cachetools**: Использует простую dict реализацию
- **Без deepseek-sdk**: Использует HTTP API напрямую

## 🔄 Обновление

Для получения последних изменений:
```bash
git pull origin main
python test_syntax.py
python test_imports.py
```

## 📞 Поддержка

При возникновении проблем:
1. Проверьте все зависимости: `pip list`
2. Запустите тесты: `python test_syntax.py`
3. Проверьте .env файл
4. Убедитесь что Python 3.8+

---
*Система готова к работе! 🚀* 