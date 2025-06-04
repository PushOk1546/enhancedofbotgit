#!/usr/bin/env python3
"""
🧪 ТЕСТ ФАЗЫ 1: Базовая навигация
Проверяет работу кнопок продолжения диалога
"""

import asyncio
import sys
from unittest.mock import Mock, AsyncMock
from telebot import types

# Импортируем наши модули
try:
    from utils import get_quick_continue_keyboard
    from bot import BotManager
    print("✅ Импорты успешны")
except ImportError as e:
    print(f"❌ Ошибка импорта: {e}")
    sys.exit(1)

def test_quick_continue_keyboard():
    """Тест 1: Проверка создания клавиатуры продолжения"""
    print("\n🧪 Тест 1: Клавиатура продолжения диалога")
    
    try:
        keyboard = get_quick_continue_keyboard("test message")
        
        # Проверяем что это InlineKeyboardMarkup
        assert isinstance(keyboard, types.InlineKeyboardMarkup), "Неверный тип клавиатуры"
        
        # Проверяем количество рядов (должно быть 3)
        assert len(keyboard.keyboard) == 3, f"Ожидалось 3 ряда, получено {len(keyboard.keyboard)}"
        
        # Проверяем первый ряд (2 кнопки)
        first_row = keyboard.keyboard[0]
        assert len(first_row) == 2, f"В первом ряду должно быть 2 кнопки, получено {len(first_row)}"
        
        # Проверяем текст кнопок (используем атрибуты объектов)
        button_texts = [btn.text for btn in first_row]
        expected_texts = ["💬 Еще сообщение", "💝 Добавить флирт"]
        
        for expected in expected_texts:
            assert expected in button_texts, f"Отсутствует кнопка: {expected}"
        
        # Проверяем callback_data (используем атрибуты объектов)
        callback_data = [btn.callback_data for btn in first_row]
        expected_callbacks = ["continue_writing", "add_flirt"]
        
        for expected in expected_callbacks:
            assert expected in callback_data, f"Отсутствует callback: {expected}"
        
        print("   ✅ Клавиатура создается корректно")
        print(f"   📊 Рядов: {len(keyboard.keyboard)}")
        print(f"   🔘 Кнопок в первом ряду: {len(first_row)}")
        print(f"   📝 Тексты кнопок: {button_texts}")
        
        return True
        
    except Exception as e:
        print(f"   ❌ Ошибка: {str(e)}")
        return False

def test_callback_handlers():
    """Тест 2: Проверка наличия обработчиков callback'ов"""
    print("\n🧪 Тест 2: Обработчики callback'ов")
    
    try:
        # Создаем mock объект бота
        bot_manager = BotManager()
        
        # Проверяем наличие новых методов
        required_methods = [
            '_handle_continue_writing',
            '_handle_add_flirt', 
            '_handle_quick_ppv',
            '_handle_quick_tips'
        ]
        
        for method_name in required_methods:
            assert hasattr(bot_manager, method_name), f"Отсутствует метод: {method_name}"
            method = getattr(bot_manager, method_name)
            assert callable(method), f"Метод {method_name} не является callable"
            print(f"   ✅ Метод {method_name} найден")
        
        print(f"   📊 Всего методов проверено: {len(required_methods)}")
        return True
        
    except Exception as e:
        print(f"   ❌ Ошибка: {str(e)}")
        return False

def test_integration():
    """Тест 3: Интеграционный тест навигации"""
    print("\n🧪 Тест 3: Интеграция навигации")
    
    try:
        # Симуляция пользовательского сообщения
        print("   📝 Симуляция отправки сообщения пользователем...")
        
        # Проверяем что функция get_quick_continue_keyboard работает с разными входными данными
        test_messages = ["Привет", "Как дела?", ""]
        
        for msg in test_messages:
            keyboard = get_quick_continue_keyboard(msg)
            assert keyboard is not None, f"Клавиатура не создана для сообщения: '{msg}'"
            assert len(keyboard.keyboard) > 0, f"Пустая клавиатура для сообщения: '{msg}'"
        
        print(f"   ✅ Клавиатуры создаются для всех типов сообщений")
        print(f"   📊 Протестировано сообщений: {len(test_messages)}")
        
        # Проверяем callback data (используем атрибуты объектов)
        keyboard = get_quick_continue_keyboard("test")
        all_callbacks = []
        for row in keyboard.keyboard:
            for button in row:
                if hasattr(button, 'callback_data') and button.callback_data:
                    all_callbacks.append(button.callback_data)
        
        expected_callbacks = ['continue_writing', 'add_flirt', 'quick_ppv', 'quick_tips', 'back_to_main']
        for expected in expected_callbacks:
            assert expected in all_callbacks, f"Отсутствует callback: {expected}"
        
        print(f"   ✅ Все callback'ы присутствуют: {all_callbacks}")
        return True
        
    except Exception as e:
        print(f"   ❌ Ошибка: {str(e)}")
        return False

def main():
    """Главная функция тестирования"""
    print("🚀 ЗАПУСК ТЕСТОВ ФАЗЫ 1: БАЗОВАЯ НАВИГАЦИЯ")
    print("=" * 50)
    
    tests = [
        ("Клавиатура продолжения", test_quick_continue_keyboard),
        ("Обработчики callback'ов", test_callback_handlers),
        ("Интеграция навигации", test_integration)
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        try:
            if test_func():
                passed += 1
        except Exception as e:
            print(f"❌ Критическая ошибка в тесте '{test_name}': {str(e)}")
    
    print("\n" + "=" * 50)
    print(f"📊 РЕЗУЛЬТАТЫ ТЕСТИРОВАНИЯ:")
    print(f"✅ Пройдено: {passed}/{total}")
    print(f"❌ Провалено: {total - passed}/{total}")
    print(f"📈 Успешность: {(passed/total)*100:.1f}%")
    
    if passed == total:
        print("\n🎉 ВСЕ ТЕСТЫ ПРОЙДЕНЫ! ФАЗА 1 ГОТОВА К ИСПОЛЬЗОВАНИЮ!")
        return True
    else:
        print(f"\n⚠️ ЕСТЬ ПРОБЛЕМЫ! Необходимо исправить {total - passed} тест(ов)")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1) 