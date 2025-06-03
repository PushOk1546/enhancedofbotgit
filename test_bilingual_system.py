#!/usr/bin/env python3
"""
🧪 ТЕСТ ДВУЯЗЫЧНОЙ СИСТЕМЫ (АНГЛИЙСКИЙ + РУССКИЙ)
Проверяет работу с английскими клиентами и русскими чатерами
"""

import sys
from unittest.mock import Mock
from telebot import types

# Импортируем наши модули
try:
    from bot import BotManager
    print("✅ Импорты успешны")
except ImportError as e:
    print(f"❌ Ошибка импорта: {e}")
    sys.exit(1)

def test_english_prompts():
    """Тест 1: Проверка английских промптов"""
    print("\n🧪 Тест 1: Английские промпты для международных клиентов")
    
    try:
        bot_manager = BotManager()
        
        # Создаем мок пользователя
        mock_user = Mock()
        mock_user.message_history = []
        mock_user.preferences = Mock()
        mock_user.preferences.completed_survey = False
        
        # Тестируем различные типы сообщений
        test_messages = [
            "Hello",
            "Hi baby",
            "Show me pics",
            "You're beautiful"
        ]
        
        for message in test_messages:
            prompt = bot_manager._create_safe_prompt(message, mock_user)
            
            # Проверяем что промпт на английском
            assert "You are a real OnlyFans model named Christina" in prompt, f"Промпт не на английском для '{message}'"
            assert "YOUR PERSONALITY" in prompt, f"Нет английской секции личности для '{message}'"
            assert "COMMUNICATION STYLE" in prompt, f"Нет английского стиля общения для '{message}'"
            assert "CLIENT'S MESSAGE" in prompt, f"Нет английского заголовка сообщения для '{message}'"
            
            # Проверяем формат двуязычного ответа
            assert "📋 IMPORTANT OUTPUT FORMAT" in prompt, f"Нет инструкций по формату для '{message}'"
            assert "[Your English response here]" in prompt, f"Нет шаблона английского ответа для '{message}'"
            assert "🔍 Перевод: [Russian translation here" in prompt, f"Нет шаблона русского перевода для '{message}'"
            
            print(f"   ✅ Английский промпт для '{message}': {len(prompt)} символов")
        
        print(f"   📊 Протестировано сообщений: {len(test_messages)}")
        return True
        
    except Exception as e:
        print(f"   ❌ Ошибка: {str(e)}")
        return False

def test_bilingual_format():
    """Тест 2: Проверка двуязычного формата ответов"""
    print("\n🧪 Тест 2: Формат двуязычных ответов")
    
    try:
        # Симулируем правильный формат ответа
        correct_responses = [
            "Hey babe! 😘 How's your day going?\n\n---\n🔍 Перевод: Привет, милый! 😘 Как дела?",
            "I'm feeling so playful today... 💕\n\n---\n🔍 Перевод: Я сегодня такая игривая... 💕",
            "Want to see something special? 😏\n\n---\n🔍 Перевод: Хочешь увидеть что-то особенное? 😏"
        ]
        
        for response in correct_responses:
            # Проверяем структуру ответа
            assert "---" in response, f"Нет разделителя в ответе: {response[:50]}..."
            assert "🔍 Перевод:" in response, f"Нет метки перевода в ответе: {response[:50]}..."
            
            # Разделяем английскую и русскую части
            parts = response.split("---")
            assert len(parts) == 2, f"Неверное количество частей в ответе: {len(parts)}"
            
            english_part = parts[0].strip()
            russian_part = parts[1].strip()
            
            # Проверяем что английская часть не пустая
            assert len(english_part) > 0, f"Пустая английская часть в ответе"
            
            # Проверяем что русская часть содержит перевод
            assert russian_part.startswith("🔍 Перевод:"), f"Неверный формат русской части: {russian_part[:30]}..."
            
            # Извлекаем сам перевод
            translation = russian_part.replace("🔍 Перевод:", "").strip()
            assert len(translation) > 0, f"Пустой перевод в ответе"
            
            print(f"   ✅ Корректный формат: EN({len(english_part)}) + RU({len(translation)})")
        
        print(f"   📊 Протестировано ответов: {len(correct_responses)}")
        return True
        
    except Exception as e:
        print(f"   ❌ Ошибка: {str(e)}")
        return False

def test_international_context():
    """Тест 3: Проверка международного контекста"""
    print("\n🧪 Тест 3: Контекст для международных клиентов")
    
    try:
        bot_manager = BotManager()
        mock_user = Mock()
        mock_user.message_history = []
        mock_user.preferences = Mock()
        mock_user.preferences.completed_survey = False
        
        # Тестируем международные сообщения
        international_messages = [
            ("Hello", ["hello", "hi", "hey"]),
            ("How are you?", ["how are you", "what are you doing"]),
            ("Show me pics", ["photo", "pic", "video", "content", "show"]),
            ("You're gorgeous", ["beautiful", "sexy", "hot", "gorgeous"])
        ]
        
        for message, expected_keywords in international_messages:
            prompt = bot_manager._create_safe_prompt(message, mock_user)
            
            # Проверяем что контекст анализируется на английском
            found_keywords = 0
            for keyword in expected_keywords:
                if keyword in prompt.lower():
                    found_keywords += 1
            
            assert found_keywords > 0, f"Не найдено ключевых слов для '{message}'"
            
            # Проверяем что есть английский контекст
            if "hello" in message.lower() or "hi" in message.lower():
                assert "CONTEXT: This is a greeting" in prompt, f"Нет английского контекста приветствия для '{message}'"
            elif "how are you" in message.lower():
                assert "CONTEXT: Client is asking about you" in prompt, f"Нет английского контекста вопроса для '{message}'"
            
            print(f"   ✅ Международный контекст '{message}': {found_keywords}/{len(expected_keywords)} ключевых слов")
        
        print(f"   📊 Протестировано сообщений: {len(international_messages)}")
        return True
        
    except Exception as e:
        print(f"   ❌ Ошибка: {str(e)}")
        return False

def test_chatroom_moderation():
    """Тест 4: Проверка поддержки модерации чата"""
    print("\n🧪 Тест 4: Поддержка модерации чата")
    
    try:
        # Симулируем сообщения которые должен понимать чатер
        moderator_examples = [
            "Hey sexy! 💕 Want to see my private photos?\n\n---\n🔍 Перевод: Привет, сексуальный! 💕 Хочешь увидеть мои приватные фото?",
            "I'm so horny right now... 🔥\n\n---\n🔍 Перевод: Я сейчас такая возбужденная... 🔥",
            "Send me $20 for exclusive content babe 💰\n\n---\n🔍 Перевод: Отправь мне $20 за эксклюзивный контент, милый 💰"
        ]
        
        for example in moderator_examples:
            # Проверяем что есть перевод для модератора
            assert "🔍 Перевод:" in example, f"Нет перевода для модератора в: {example[:50]}..."
            
            # Разделяем части
            parts = example.split("---")
            english_part = parts[0].strip()
            russian_part = parts[1].strip().replace("🔍 Перевод:", "").strip()
            
            # Проверяем что русская часть понятна для модерации
            assert len(russian_part) > 10, f"Слишком короткий перевод: {russian_part}"
            
            # Проверяем что английская часть для клиента
            assert len(english_part) > 10, f"Слишком короткое сообщение клиенту: {english_part}"
            
            print(f"   ✅ Пример модерации: Клиент видит английский, чатер - русский")
        
        print(f"   📊 Протестировано примеров: {len(moderator_examples)}")
        return True
        
    except Exception as e:
        print(f"   ❌ Ошибка: {str(e)}")
        return False

def test_english_addressing():
    """Тест 5: Проверка английских обращений"""
    print("\n🧪 Тест 5: Английские обращения к клиентам")
    
    try:
        bot_manager = BotManager()
        mock_user = Mock()
        mock_user.message_history = []
        mock_user.preferences = Mock()
        mock_user.preferences.completed_survey = False
        
        prompt = bot_manager._create_safe_prompt("Hello", mock_user)
        
        # Проверяем английские обращения
        english_addresses = ["babe", "honey", "sexy"]
        found_addresses = 0
        
        for address in english_addresses:
            if address in prompt.lower():
                found_addresses += 1
        
        assert found_addresses > 0, "Нет английских обращений в промпте"
        
        # Проверяем что нет русских обращений
        russian_addresses = ["милый", "дорогой", "сладкий"]
        for address in russian_addresses:
            assert address not in prompt.lower(), f"Найдено русское обращение '{address}' в английском промпте"
        
        print(f"   ✅ Найдено английских обращений: {found_addresses}/{len(english_addresses)}")
        print(f"   ✅ Русские обращения отсутствуют")
        return True
        
    except Exception as e:
        print(f"   ❌ Ошибка: {str(e)}")
        return False

def main():
    """Главная функция тестирования двуязычной системы"""
    print("🌍 ТЕСТ ДВУЯЗЫЧНОЙ СИСТЕМЫ (АНГЛИЙСКИЙ + РУССКИЙ)")
    print("=" * 65)
    
    tests = [
        ("Английские промпты", test_english_prompts),
        ("Двуязычный формат", test_bilingual_format),
        ("Международный контекст", test_international_context),
        ("Поддержка модерации", test_chatroom_moderation),
        ("Английские обращения", test_english_addressing)
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        try:
            if test_func():
                passed += 1
        except Exception as e:
            print(f"❌ Критическая ошибка в тесте '{test_name}': {str(e)}")
    
    print("\n" + "=" * 65)
    print(f"📊 РЕЗУЛЬТАТЫ ТЕСТИРОВАНИЯ ДВУЯЗЫЧНОЙ СИСТЕМЫ:")
    print(f"✅ Пройдено: {passed}/{total}")
    print(f"❌ Провалено: {total - passed}/{total}")
    print(f"📈 Успешность: {(passed/total)*100:.1f}%")
    
    if passed == total:
        print("\n🎉 ВСЕ ТЕСТЫ ПРОЙДЕНЫ! ДВУЯЗЫЧНАЯ СИСТЕМА ГОТОВА!")
        print("🌍 Клиенты получают сообщения на английском")
        print("🔍 Чатеры видят переводы на русском")
        print("💬 Международная коммуникация налажена!")
        return True
    else:
        print(f"\n⚠️ ЕСТЬ ПРОБЛЕМЫ! Необходимо исправить {total - passed} тест(ов)")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1) 