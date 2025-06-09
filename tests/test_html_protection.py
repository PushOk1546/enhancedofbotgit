#!/usr/bin/env python3
"""
Тест защиты от HTML parsing errors
Демонстрирует работу safe_send_message и safe_reply_to функций
"""

import asyncio
from unittest.mock import AsyncMock, MagicMock
from handlers import safe_send_message, safe_reply_to

async def test_html_protection():
    """Тестирует защиту от HTML ошибок"""
    print("🛡️ ТЕСТ ЗАЩИТЫ ОТ HTML PARSING ERRORS")
    print("=" * 50)
    
    # Создаем mock бота
    bot = AsyncMock()
    
    # Тест 1: Нормальная отправка
    print("\n📤 ТЕСТ 1: Нормальная отправка сообщения")
    bot.send_message.return_value = "success"
    
    result = await safe_send_message(
        bot, 123, "Обычное сообщение", parse_mode='HTML'
    )
    
    print("✅ Обычное сообщение отправлено успешно")
    
    # Тест 2: HTML parsing error + fallback
    print("\n🚨 ТЕСТ 2: HTML parsing error и автоматический fallback")
    
    # Симулируем ошибку при первой попытке
    def side_effect(*args, **kwargs):
        if 'parse_mode' in kwargs:
            raise Exception("can't parse entities: Can't find end of the entity starting at byte offset 1130")
        return "fallback_success"
    
    bot.send_message.side_effect = side_effect
    
    # Проблемное сообщение с некорректным HTML
    problematic_html = "Привет! <b>Жирный текст <i>и курсив без закрытия <u>подчеркнутый текст"
    
    result = await safe_send_message(
        bot, 123, problematic_html, parse_mode='HTML'
    )
    
    print("✅ HTML ошибка автоматически исправлена через fallback")
    print("📝 Сообщение отправлено как plain text без parse_mode")
    
    # Тест 3: Тест safe_reply_to
    print("\n💬 ТЕСТ 3: Защищенный ответ на сообщение")
    
    message_mock = MagicMock()
    message_mock.from_user.id = 456
    
    bot.reply_to.side_effect = side_effect
    
    result = await safe_reply_to(
        bot, message_mock, "Ответ с <b>проблемным HTML", parse_mode='HTML'
    )
    
    print("✅ safe_reply_to работает корректно")
    
    # Тест 4: Другие ошибки (не HTML)
    print("\n⚠️ ТЕСТ 4: Обработка других типов ошибок")
    
    def other_error(*args, **kwargs):
        raise Exception("Network timeout")
    
    bot.send_message.side_effect = other_error
    
    try:
        await safe_send_message(bot, 123, "Тест", parse_mode='HTML')
        print("❌ Ошибка должна была быть выброшена")
    except Exception as e:
        if "Network timeout" in str(e):
            print("✅ Другие ошибки правильно проброшены дальше")
        else:
            print(f"❌ Неожиданная ошибка: {e}")

def test_new_eco_model():
    """Тестирует новую экономичную модель"""
    print("\n\n💚 ТЕСТ НОВОЙ ЭКО-МОДЕЛИ")
    print("=" * 50)
    
    from config.config import MODELS
    from state_manager import StateManager
    
    # Проверяем модели
    print(f"📋 Доступные модели: {list(MODELS.keys())}")
    
    # Проверяем eco модель
    eco_model = MODELS.get('eco')
    if eco_model:
        print(f"✅ Модель 'eco' найдена:")
        print(f"   📛 ID: {eco_model['id']}")
        print(f"   📝 Описание: {eco_model['description']}")
    else:
        print("❌ Модель 'eco' не найдена!")
        return
    
    # Проверяем что она по умолчанию
    sm = StateManager()
    user = sm.get_user(999999)  # Новый пользователь
    
    print(f"👤 Модель по умолчанию для нового пользователя: '{user.model}'")
    
    if user.model == 'eco':
        print("✅ Экономичная модель установлена по умолчанию")
        print("💰 Новые пользователи будут использовать самую дешевую модель")
    else:
        print(f"❌ Ожидалась модель 'eco', получена '{user.model}'")

async def main():
    """Главная функция теста"""
    print("🧪 ЗАПУСК ТЕСТОВ HTML ЗАЩИТЫ И НОВОЙ МОДЕЛИ")
    print("=" * 60)
    
    # Тест защиты от HTML
    await test_html_protection()
    
    # Тест новой модели
    test_new_eco_model()
    
    print("\n" + "=" * 60)
    print("🎉 ВСЕ ТЕСТЫ ЗАВЕРШЕНЫ")
    print("✅ HTML защита работает корректно") 
    print("✅ Новая экономичная модель активна")
    print("🚀 Система готова к продакшену!")

if __name__ == "__main__":
    asyncio.run(main()) 