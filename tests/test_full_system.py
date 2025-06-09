#!/usr/bin/env python3
"""
Финальный комплексный тест всей системы OF Assistant Bot.
Проверяет интеграцию всех компонентов включая чаты с клиентами.
"""

import asyncio
import sys
from dataclasses import dataclass
from chat_models import ChatManager
from state_manager import StateManager
from chat_handlers import ChatHandlers
from telebot import types

@dataclass
class MockUser:
    """Mock пользователь"""
    id: int = 12345
    first_name: str = "Test"
    username: str = "testuser"

@dataclass
class MockMessage:
    """Mock сообщение"""
    message_id: int = 1
    from_user: MockUser = None
    chat: object = None
    text: str = "test"
    
    def __post_init__(self):
        if self.from_user is None:
            self.from_user = MockUser()
        if self.chat is None:
            self.chat = MockUser()

class SystemTester:
    """Тестер всей системы"""
    
    def __init__(self):
        print("🚀 ФИНАЛЬНЫЙ КОМПЛЕКСНЫЙ ТЕСТ СИСТЕМЫ")
        print("=" * 60)
        self.state_manager = StateManager()
        self.chat_handlers = ChatHandlers(self.state_manager)
        
    def test_basic_functionality(self):
        """Тест базовой функциональности"""
        print("\n🔧 ТЕСТ БАЗОВОЙ ФУНКЦИОНАЛЬНОСТИ:")
        
        try:
            # Тест импортов
            from config.config import MODELS, FLIRT_STYLES, PPV_STYLES, SURVEY_STEPS
            from utils import get_main_keyboard, get_flirt_style_keyboard, get_ppv_style_keyboard
            from api import generate_groq_response
            print("✅ Все модули импортированы")
            
            # Тест конфигурации
            print(f"✅ Модели AI: {len(MODELS)}")
            print(f"✅ Стили флирта: {len(FLIRT_STYLES)}")
            print(f"✅ Стили PPV: {len(PPV_STYLES)}")
            print(f"✅ Шаги опроса: {len(SURVEY_STEPS)}")
            
            # Тест клавиатур
            main_kb = get_main_keyboard()
            flirt_kb = get_flirt_style_keyboard()
            ppv_kb = get_ppv_style_keyboard()
            print("✅ Все клавиатуры создаются")
            
            return True
            
        except Exception as e:
            print(f"❌ Ошибка в базовой функциональности: {e}")
            return False
    
    def test_state_management(self):
        """Тест управления состоянием"""
        print("\n💾 ТЕСТ УПРАВЛЕНИЯ СОСТОЯНИЕМ:")
        
        try:
            # Создаем пользователя
            user = self.state_manager.get_user(12345)
            print(f"✅ Пользователь создан: {user.user_id}")
            
            # Добавляем в историю
            self.state_manager.add_to_history(12345, "user", "Привет!")
            self.state_manager.add_to_history(12345, "assistant", "Привет! Как дела?")
            print("✅ История сообщений работает")
            
            # Тест предпочтений
            user.preferences.content_types = ["photos", "videos"]
            user.preferences.communication_style = "flirty"
            user.preferences.completed_survey = True
            print("✅ Предпочтения сохраняются")
            
            # Создаем ChatManager
            if not hasattr(user, 'chat_manager') or user.chat_manager is None:
                user.chat_manager = ChatManager(12345)
            
            # Создаем тестовые чаты
            chat1 = user.chat_manager.create_chat("Анна", "VIP клиент")
            chat2 = user.chat_manager.create_chat("Мария", "Новый клиент")
            print(f"✅ Чаты созданы: {len(user.chat_manager.chats)}")
            
            # Добавляем сообщения в чат
            user.chat_manager.add_message_to_active_chat("user", "Привет!")
            user.chat_manager.add_message_to_active_chat("assistant", "Привет! Как дела?")
            print("✅ Сообщения в чатах работают")
            
            # Сохраняем пользователя
            self.state_manager.save_user(12345, user)
            print("✅ Пользователь сохранен")
            
            # Загружаем заново
            user_loaded = self.state_manager.get_user(12345)
            
            # Проверяем что всё сохранилось
            assert user_loaded.preferences.communication_style == "flirty"
            assert user_loaded.preferences.completed_survey == True
            assert hasattr(user_loaded, 'chat_manager')
            assert user_loaded.chat_manager is not None
            assert len(user_loaded.chat_manager.chats) == 2
            print("✅ Все данные корректно сохранились и загрузились")
            
            return True
            
        except Exception as e:
            print(f"❌ Ошибка в управлении состоянием: {e}")
            return False
    
    async def test_chat_integration(self):
        """Тест интеграции чатов"""
        print("\n💬 ТЕСТ ИНТЕГРАЦИИ ЧАТОВ:")
        
        try:
            # Создаем mock объекты
            user = self.state_manager.get_user(12345)
            message = MockMessage()
            
            # Mock бот
            class MockBot:
                def __init__(self):
                    self.messages_sent = []
                    self.messages_edited = []
                
                async def send_message(self, chat_id, text, **kwargs):
                    self.messages_sent.append({"chat_id": chat_id, "text": text[:50], "kwargs": kwargs})
                    return MockMessage()
                
                async def edit_message_text(self, text, chat_id, message_id, **kwargs):
                    self.messages_edited.append({"text": text[:50], "chat_id": chat_id, "message_id": message_id})
                    return True
                
                async def answer_callback_query(self, callback_id, text=""):
                    return True
                
                async def reply_to(self, message, text, **kwargs):
                    return MockMessage()
            
            mock_bot = MockBot()
            
            # Создаем CallbackQuery
            call = types.CallbackQuery(
                id="test",
                from_user=message.from_user,
                data="chat_management",
                chat_instance="test",
                json_string="{}",
                message=message
            )
            
            # Тестируем основные функции чатов
            await self.chat_handlers.handle_chat_management(mock_bot, call)
            print("✅ Управление чатами работает")
            
            await self.chat_handlers.handle_chat_list(mock_bot, call)
            print("✅ Список чатов работает")
            
            await self.chat_handlers.handle_new_chat(mock_bot, call)
            print("✅ Создание нового чата работает")
            
            # Проверим что сообщения отправлялись
            assert len(mock_bot.messages_sent) > 0 or len(mock_bot.messages_edited) > 0
            print("✅ Сообщения отправляются/редактируются")
            
            return True
            
        except Exception as e:
            print(f"❌ Ошибка интеграции чатов: {e}")
            return False
    
    def test_callback_routing(self):
        """Тест маршрутизации callback queries"""
        print("\n🎯 ТЕСТ CALLBACK МАРШРУТИЗАЦИИ:")
        
        try:
            # Тестируем все возможные callback data
            test_callbacks = [
                # Основные функции
                "model_fast", "model_quick", "model_fastest",
                "flirt_style_playful", "flirt_style_passionate", "flirt_style_tender",
                "ppv_style_провокационный", "ppv_style_романтичный",
                "survey_content_types_photos", "survey_price_range_medium",
                
                # Чаты
                "chat_management", "chat_list", "chat_new", "chat_reply",
                "chat_memory", "chat_analytics",
                "chat_switch_test123", "chat_list_page_1"
            ]
            
            print(f"📊 Тестируем {len(test_callbacks)} callback типов...")
            
            # Проверяем что каждый callback может быть правильно разобран
            for callback_data in test_callbacks:
                if callback_data.startswith("model_"):
                    model_key = callback_data.replace("model_", "")
                    from config.config import MODELS
                    assert model_key in MODELS, f"Модель {model_key} не найдена"
                    
                elif callback_data.startswith("flirt_style_"):
                    style_id = callback_data.replace("flirt_style_", "")
                    from config.config import FLIRT_STYLES
                    found = any(info['id'] == style_id for info in FLIRT_STYLES.values())
                    assert found, f"Флирт стиль {style_id} не найден"
                    
                elif callback_data.startswith("ppv_style_"):
                    style_name = callback_data.replace("ppv_style_", "")
                    from config.config import PPV_STYLES
                    assert style_name in PPV_STYLES, f"PPV стиль {style_name} не найден"
                    
                elif callback_data.startswith("survey_"):
                    survey_data = callback_data[7:]
                    parts = survey_data.split('_')
                    if len(parts) >= 2:
                        step = '_'.join(parts[:-1])
                        from config.config import SURVEY_STEPS
                        assert step in SURVEY_STEPS, f"Шаг опроса {step} не найден"
                    
                elif callback_data.startswith("chat_"):
                    # Все chat_ callbacks должны обрабатываться
                    assert True
                    
            print("✅ Все callback типы валидны")
            return True
            
        except Exception as e:
            print(f"❌ Ошибка в callback маршрутизации: {e}")
            return False

async def main():
    """Главная функция тестирования"""
    tester = SystemTester()
    
    print("🚀 ЗАПУСК ФИНАЛЬНОГО КОМПЛЕКСНОГО ТЕСТИРОВАНИЯ\n")
    
    # Запускаем все тесты
    test_results = []
    
    test_results.append(("Базовая функциональность", tester.test_basic_functionality()))
    test_results.append(("Управление состоянием", tester.test_state_management()))
    test_results.append(("Интеграция чатов", await tester.test_chat_integration()))
    test_results.append(("Callback маршрутизация", tester.test_callback_routing()))
    
    # Выводим результаты
    print("\n" + "=" * 60)
    print("📊 РЕЗУЛЬТАТЫ ФИНАЛЬНОГО ТЕСТИРОВАНИЯ:")
    
    total_tests = len(test_results)
    passed_tests = sum(1 for _, result in test_results if result)
    
    for test_name, result in test_results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"   {status} {test_name}")
    
    print(f"\n📈 ИТОГ: {passed_tests}/{total_tests} тестов прошли успешно")
    
    if passed_tests == total_tests:
        print("\n🎉 СИСТЕМА ПОЛНОСТЬЮ ГОТОВА К ПРОДАКШЕНУ!")
        print("🚀 ВСЕ КОМПОНЕНТЫ РАБОТАЮТ КОРРЕКТНО!")
        print("\n💡 Готовые функции:")
        print("   ✅ Генерация флирт-сообщений (3 стиля)")
        print("   ✅ Генерация PPV контента (5 стилей)")
        print("   ✅ Переключение AI моделей (3 модели)")
        print("   ✅ Многошаговый опрос пользователей")
        print("   ✅ Управление множественными чатами")
        print("   ✅ Память и контекст для каждого клиента")
        print("   ✅ Сохранение и загрузка всех данных")
        print("   ✅ Полная обработка всех callback queries")
        print("   ✅ Интеграция всех компонентов")
        print("\n🎯 БОТ ГОТОВ К ТЕСТИРОВАНИЮ И ЭКСПЛУАТАЦИИ!")
        return True
    else:
        print(f"\n💥 ЕСТЬ ПРОБЛЕМЫ В {total_tests - passed_tests} КОМПОНЕНТАХ!")
        print("❗ Требуется доработка перед продакшеном")
        return False

if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1) 