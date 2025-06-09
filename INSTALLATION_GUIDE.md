# 🚀 Руководство по установке зависимостей

## 📋 Системные требования

- **Python 3.11+** (протестировано на 3.11.9)
- **pip** (последняя версия)
- **Windows 10/11** (для других ОС команды могут отличаться)

## 🔧 Пошаговая установка

### 1. Проверка версии Python
```bash
python --version
```
**Ожидаемый результат:** Python 3.11.9 или выше

### 2. Создание виртуального окружения
```bash
python -m venv venv
```

### 3. Активация виртуального окружения

**Windows (PowerShell):**
```powershell
.\venv\Scripts\Activate.ps1
```

**Windows (CMD):**
```cmd
venv\Scripts\activate.bat
```

**Linux/MacOS:**
```bash
source venv/bin/activate
```

### 4. Обновление pip
```bash
pip install --upgrade pip
```

### 5. Установка зависимостей
```bash
pip install -r requirements.txt
```

## 📦 Ключевые зависимости

| Пакет | Версия | Назначение |
|-------|--------|------------|
| pyTelegramBotAPI | 4.21.0 | Telegram Bot API |
| groq | 0.9.0 | ИИ-интеграция |
| aiofiles | 23.2.1 | Асинхронная работа с файлами |
| asyncio-throttle | 1.0.2 | Rate limiting |
| psutil | 5.9.8 | Мониторинг системы |
| pytest | 8.1.1 | Тестирование |

## ✅ Проверка установки

Запустите тест совместимости:
```bash
python test_dependencies.py
```

**Ожидаемый результат:**
```
🎉 Все зависимости совместимы с Python 3.11+!
```

## 🚨 Возможные проблемы

### Проблема с aioredis
Если возникает ошибка `TypeError: duplicate base class TimeoutError`:
- **Решение:** aioredis закомментирован в requirements.txt из-за несовместимости с Python 3.11+
- **Альтернатива:** Используется файловое кэширование вместо Redis

### Конфликт зависимостей
Если pip сообщает о конфликтах:
```bash
pip install --force-reinstall -r requirements.txt
```

### Проблемы с правами доступа
На Windows может потребоваться:
```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

## 🔧 Переменные окружения

Создайте файл `.env` с необходимыми переменными:
```env
TELEGRAM_BOT_TOKEN=your_bot_token_here
GROQ_API_KEY=your_groq_api_key_here
LOG_LEVEL=INFO
CACHE_TTL=3600
MAX_MESSAGE_LENGTH=1000
```

## 🏃‍♂️ Быстрый старт

После установки зависимостей:
```bash
# Активация окружения (если не активировано)
.\venv\Scripts\Activate.ps1

# Проверка зависимостей
python test_dependencies.py

# Запуск тестов
pytest

# Запуск бота
python main_bot.py
```

## 📚 Дополнительная информация

- [SETUP_GUIDE.md](SETUP_GUIDE.md) - Подробное руководство по настройке
- [QUICK_START.md](QUICK_START.md) - Быстрый старт проекта
- [README.md](README.md) - Общая информация о проекте

---
✨ **Готово!** Окружение настроено и готово к работе. 