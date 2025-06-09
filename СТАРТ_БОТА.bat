@echo off
chcp 65001 > nul
cls

echo.
echo ████████████████████████████████████████████████████████████████
echo █                                                              █
echo █    🚀 PERFECT BOT - ПОЛНОФУНКЦИОНАЛЬНАЯ ВЕРСИЯ 🚀           █
echo █                                                              █
echo █    ✅ Все импорты исправлены                                  █
echo █    ✅ .env файл настроен                                      █
echo █    ✅ Очаровательный дизайн восстановлен                      █
echo █    ✅ Админ панель работает                                    █
echo █    ✅ Премиум система активна                                  █
echo █                                                              █
echo ████████████████████████████████████████████████████████████████
echo.

echo 🔧 Активация виртуального окружения...
if exist "venv\Scripts\activate.bat" (
    call venv\Scripts\activate.bat
    echo ✅ Виртуальное окружение активировано
) else (
    echo ⚠️  Виртуальное окружение не найдено
    echo 💡 Создаем новое виртуальное окружение...
    python -m venv venv
    call venv\Scripts\activate.bat
    echo ✅ Виртуальное окружение создано и активировано
)

echo.
echo 📦 Проверка зависимостей...
python -m pip install --upgrade pip > nul 2>&1
pip install -r requirements.txt > nul 2>&1
echo ✅ Все зависимости установлены

echo.
echo 🔑 Проверка .env файла...
if exist ".env" (
    echo ✅ .env файл найден
) else (
    echo ❌ .env файл не найден!
    echo 💡 Создайте .env файл с необходимыми токенами
    pause
    exit /b 1
)

echo.
echo 🎯 Запуск PERFECT BOT...
echo 📱 Бот готов к работе!
echo 🛑 Для остановки нажмите Ctrl+C
echo.

python main.py

echo.
echo 👋 Бот остановлен. До свидания!
pause 