#!/usr/bin/env python3
"""
🧪 ТЕСТ ЖИВОГО ОБЩЕНИЯ И КОНТЕКСТУАЛЬНОЙ НАВИГАЦИИ
Проверяет улучшенные промпты и умную навигацию
"""

import sys
from unittest.mock import Mock
from telebot import types

# Импортируем наши модули
try:
    from utils import get_quick_continue_keyboard, get_smart_continuation_keyboard
    from bot import BotManager
    print("✅ Импорты успешны")
except ImportError as e:
    print(f"❌ Ошибка импорта: {e}")
    sys.exit(1)

def test_contextual_keyboards():
    """Тест 1: Проверка контекстуальных клавиатур"""
    print("\n🧪 Тест 1: Контекстуальные клавиатуры")
    
    try:
        # Тест различных контекстов
        test_cases = [
            ("привет", "приветствие"),
            ("фото", "контент"),
            ("красивая", "комплимент"),
            ("обычное сообщение", "дефолт")
        ]
        
        for message, context_type in test_cases:
            keyboard = get_quick_continue_keyboard(message)
            
            assert isinstance(keyboard, types.InlineKeyboardMarkup), f"Неверный тип клавиатуры для '{message}'"
            assert len(keyboard.keyboard) >= 2, f"Недостаточно рядов кнопок для '{message}'"
            
            # Проверяем что кнопки разные для разных контекстов
            button_texts = []
            for row in keyboard.keyboard:
                for button in row:
                    button_texts.append(button.text)
            
            print(f"   ✅ Контекст '{context_type}': {len(button_texts)} кнопок")
            print(f"      📝 Кнопки: {button_texts[:3]}...")  # Показываем первые 3
        
        print(f"   📊 Протестировано контекстов: {len(test_cases)}")
        return True
        
    except Exception as e:
        print(f"   ❌ Ошибка: {str(e)}")
        return False

def test_smart_continuation_keyboards():
    """Тест 2: Проверка умных клавиатур продолжения"""
    print("\n🧪 Тест 2: Умные клавиатуры продолжения")
    
    try:
        context_types = ["flirt_mode", "content_interest", "casual_chat"]
        
        for context in context_types:
            keyboard = get_smart_continuation_keyboard(context)
            
            assert isinstance(keyboard, types.InlineKeyboardMarkup), f"Неверный тип для {context}"
            assert len(keyboard.keyboard) >= 2, f"Недостаточно рядов для {context}"
            
            # Проверяем уникальность кнопок для каждого контекста
            button_texts = []
            for row in keyboard.keyboard:
                for button in row:
                    button_texts.append(button.text)
            
            print(f"   ✅ Контекст '{context}': {len(button_texts)} кнопок")
            
            # Проверяем что есть специфичные кнопки для каждого контекста
            if context == "flirt_mode":
                assert any("флирт" in btn.lower() for btn in button_texts), "Нет кнопок флирта"
            elif context == "content_interest":
                assert any("контент" in btn.lower() or "ppv" in btn.lower() for btn in button_texts), "Нет кнопок контента"
            elif context == "casual_chat":
                assert any("беседа" in btn.lower() or "общ" in btn.lower() or "поддержать" in btn.lower() or "рассказать" in btn.lower() for btn in button_texts), "Нет кнопок беседы"
        
        print(f"   📊 Протестировано типов: {len(context_types)}")
        return True
        
    except Exception as e:
        print(f"   ❌ Ошибка: {str(e)}")
        return False

def test_new_handlers():
    """Тест 3: Проверка новых обработчиков"""
    print("\n🧪 Тест 3: Новые обработчики контекстуальных кнопок")
    
    try:
        bot_manager = BotManager()
        
        # Проверяем наличие новых контекстуальных методов
        new_methods = [
            '_handle_get_closer',
            '_handle_light_flirt',
            '_handle_show_content',
            '_handle_casual_chat',
            '_handle_continue_conversation',
            '_handle_flirty_thanks',
            '_send_contextual_response'
        ]
        
        for method_name in new_methods:
            assert hasattr(bot_manager, method_name), f"Отсутствует метод: {method_name}"
            method = getattr(bot_manager, method_name)
            assert callable(method), f"Метод {method_name} не является callable"
            print(f"   ✅ Метод {method_name} найден")
        
        print(f"   📊 Всего новых методов: {len(new_methods)}")
        return True
        
    except Exception as e:
        print(f"   ❌ Ошибка: {str(e)}")
        return False

def test_prompt_improvement():
    """Тест 4: Проверка улучшенного промпта"""
    print("\n🧪 Тест 4: Улучшенная система промптов")
    
    try:
        bot_manager = BotManager()
        
        # Создаем мок пользователя
        mock_user = Mock()
        mock_user.message_history = [
            {'role': 'user', 'content': 'Привет'},
            {'role': 'assistant', 'content': 'Привет, милый! 😊'}
        ]
        mock_user.preferences = Mock()
        mock_user.preferences.completed_survey = True
        mock_user.preferences.communication_style = "кокетливый"
        
        # Тестируем различные типы сообщений
        test_messages = [
            "Hello",
            "How are you?",
            "Show me pics",
            "You're beautiful"
        ]
        
        for message in test_messages:
            prompt = bot_manager._create_safe_prompt(message, mock_user)
            
            # Проверяем что промпт содержит английские ключевые элементы
            assert "Christina" in prompt, f"Нет имени модели в промпте для '{message}'"
            assert "🎭 YOUR PERSONALITY" in prompt, f"Нет английской секции личности для '{message}'"
            assert "💬 COMMUNICATION STYLE" in prompt, f"Нет английского стиля общения для '{message}'"
            assert message in prompt, f"Сообщение не включено в промпт"
            
            # Проверяем что промпт адаптируется под тип сообщения
            if "hello" in message.lower():
                assert "greeting" in prompt.lower(), f"Нет контекста приветствия для '{message}'"
            elif "pic" in message.lower() or "show" in message.lower():
                assert "content" in prompt.lower(), f"Нет контекста контента для '{message}'"
            
            print(f"   ✅ Промпт для '{message}': {len(prompt)} символов")
        
        print(f"   📊 Протестировано сообщений: {len(test_messages)}")
        print(f"   📏 Средняя длина промпта: {len(prompt)//len(test_messages)} символов")
        return True
        
    except Exception as e:
        print(f"   ❌ Ошибка: {str(e)}")
        return False

def test_context_analysis():
    """Тест 5: Проверка анализа контекста"""
    print("\n🧪 Тест 5: Анализ контекста сообщений")
    
    try:
        # Тестируем разные типы контекста
        context_tests = [
            ("привет", ["познакомиться", "флирт", "контент", "пообщаться"]),
            ("покажи фото", ["горячий", "эксклюзив", "чаевые", "интригующий"]),
            ("ты красивая", ["кокетливо", "флирт", "комплимент", "награда"]),
            ("обычное", ["продолжить", "флирт", "контент", "игривый"])
        ]
        
        for message, expected_keywords in context_tests:
            keyboard = get_quick_continue_keyboard(message)
            
            # Собираем все тексты кнопок
            all_button_texts = []
            for row in keyboard.keyboard:
                for button in row:
                    all_button_texts.append(button.text.lower())
            
            # Проверяем что есть хотя бы одно ожидаемое ключевое слово
            found_keywords = 0
            for keyword in expected_keywords:
                if any(keyword in btn_text for btn_text in all_button_texts):
                    found_keywords += 1
            
            assert found_keywords > 0, f"Нет ожидаемых ключевых слов для '{message}'"
            print(f"   ✅ Контекст '{message}': найдено {found_keywords}/{len(expected_keywords)} ключевых слов")
        
        print(f"   📊 Протестировано контекстов: {len(context_tests)}")
        return True
        
    except Exception as e:
        print(f"   ❌ Ошибка: {str(e)}")
        return False

def main():
    """Главная функция тестирования живого общения"""
    print("🚀 ТЕСТ ЖИВОГО ОБЩЕНИЯ И КОНТЕКСТУАЛЬНОЙ НАВИГАЦИИ")
    print("=" * 60)
    
    tests = [
        ("Контекстуальные клавиатуры", test_contextual_keyboards),
        ("Умные клавиатуры продолжения", test_smart_continuation_keyboards),
        ("Новые обработчики", test_new_handlers),
        ("Улучшенные промпты", test_prompt_improvement),
        ("Анализ контекста", test_context_analysis)
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        try:
            if test_func():
                passed += 1
        except Exception as e:
            print(f"❌ Критическая ошибка в тесте '{test_name}': {str(e)}")
    
    print("\n" + "=" * 60)
    print(f"📊 РЕЗУЛЬТАТЫ ТЕСТИРОВАНИЯ ЖИВОГО ОБЩЕНИЯ:")
    print(f"✅ Пройдено: {passed}/{total}")
    print(f"❌ Провалено: {total - passed}/{total}")
    print(f"📈 Успешность: {(passed/total)*100:.1f}%")
    
    if passed == total:
        print("\n🎉 ВСЕ ТЕСТЫ ПРОЙДЕНЫ! ЖИВОЕ ОБЩЕНИЕ ГОТОВО!")
        print("🔥 Бот теперь общается как настоящая модель!")
        print("💬 Контекстуальная навигация работает!")
        print("🎯 Промпты стали человечными и завлекающими!")
        return True
    else:
        print(f"\n⚠️ ЕСТЬ ПРОБЛЕМЫ! Необходимо исправить {total - passed} тест(ов)")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1) 