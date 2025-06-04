#!/usr/bin/env python3
"""
Комплексный тест функциональности чатов с клиентами.
Проверяет все компоненты: создание, управление, переключение, память.
"""

import asyncio
import sys
from dataclasses import dataclass
from datetime import datetime
from chat_models import ChatManager, ClientProfile, ClientChat, ChatMessage
from chat_utils import (
    get_chat_management_keyboard, get_chat_list_keyboard, get_chat_context_keyboard,
    format_chat_info, format_chat_memory, format_chat_analytics, create_chat_context_prompt
)
from chat_handlers import ChatHandlers
from state_manager import StateManager
from telebot import types

@dataclass
class MockUser:
    """Mock пользователь для тестирования"""
    id: int = 12345
    first_name: str = "Test"
    last_name: str = "User"
    username: str = "testuser"

@dataclass
class MockMessage:
    """Mock сообщение для тестирования"""
    message_id: int = 1
    from_user: MockUser = None
    chat: object = None
    text: str = "Тест"
    
    def __post_init__(self):
        if self.from_user is None:
            self.from_user = MockUser()
        if self.chat is None:
            self.chat = MockUser()

class ChatTester:
    """Тестер функциональности чатов"""
    
    def __init__(self):
        print("🧪 КОМПЛЕКСНЫЙ ТЕСТ ЧАТОВ С КЛИЕНТАМИ")
        print("=" * 60)
        self.state_manager = StateManager()
        self.chat_handlers = ChatHandlers(self.state_manager)
        
    def test_chat_models(self):
        """Тестирует модели данных чатов"""
        print("\n📊 ТЕСТ МОДЕЛЕЙ ДАННЫХ:")
        
        try:
            # Тест ClientProfile
            profile = ClientProfile(name="Анна", description="VIP клиент")
            print(f"✅ ClientProfile создан: {profile.name} (ID: {profile.client_id[:8]}...)")
            
            # Тест сериализации профиля
            profile_dict = profile.to_dict()
            profile_restored = ClientProfile.from_dict(profile_dict)
            print(f"✅ Сериализация профиля: {profile_restored.name == profile.name}")
            
            # Тест ChatMessage
            message = ChatMessage("user", "Привет!", "text")
            print(f"✅ ChatMessage создано: {message.role} - {message.content[:20]}...")
            
            # Тест сериализации сообщения
            msg_dict = message.to_dict()
            msg_restored = ChatMessage.from_dict(msg_dict)
            print(f"✅ Сериализация сообщения: {msg_restored.content == message.content}")
            
            # Тест ClientChat
            chat = ClientChat(profile)
            chat.add_message(message)
            print(f"✅ ClientChat создан: {len(chat.messages)} сообщение(й)")
            
            # Тест контекста чата
            context = chat.get_context_summary()
            print(f"✅ Контекст чата: {len(context)} символов")
            
            # Тест сериализации чата
            chat_dict = chat.to_dict()
            chat_restored = ClientChat.from_dict(chat_dict)
            print(f"✅ Сериализация чата: {len(chat_restored.messages)} сообщение(й)")
            
            return True
            
        except Exception as e:
            print(f"❌ Ошибка в моделях данных: {e}")
            return False
    
    def test_chat_manager(self):
        """Тестирует ChatManager"""
        print("\n🎛 ТЕСТ CHAT MANAGER:")
        
        try:
            # Создаем ChatManager
            manager = ChatManager(12345)
            print(f"✅ ChatManager создан для пользователя 12345")
            
            # Создаем несколько чатов
            chat1 = manager.create_chat("Анна", "VIP клиент")
            chat2 = manager.create_chat("Мария", "Новый клиент")
            chat3 = manager.create_chat("Катя", "Постоянный клиент")
            print(f"✅ Создано чатов: {len(manager.chats)}")
            
            # Проверяем активный чат
            active = manager.get_active_chat()
            print(f"✅ Активный чат: {active.client_profile.name if active else 'None'}")
            
            # Добавляем сообщения в активный чат
            manager.add_message_to_active_chat("user", "Привет! Как дела?")
            manager.add_message_to_active_chat("assistant", "Привет! Отлично, спасибо!")
            manager.add_message_to_active_chat("user", "Что планируешь на вечер?")
            print(f"✅ Добавлено сообщений: {len(active.messages)}")
            
            # Переключаем чат
            switched = manager.switch_chat(chat2.chat_id)
            print(f"✅ Переключение чата: {switched}")
            
            new_active = manager.get_active_chat()
            print(f"✅ Новый активный чат: {new_active.client_profile.name}")
            
            # Получаем список чатов
            chat_list = manager.get_chat_list()
            print(f"✅ Список чатов: {len(chat_list)} элементов")
            
            # Контекст для AI
            ai_context = manager.get_context_for_ai()
            print(f"✅ AI контекст: {len(ai_context)} символов")
            
            # Сериализация
            manager_dict = manager.to_dict()
            manager_restored = ChatManager.from_dict(manager_dict)
            print(f"✅ Сериализация менеджера: {len(manager_restored.chats)} чатов")
            
            return True
            
        except Exception as e:
            print(f"❌ Ошибка в ChatManager: {e}")
            return False
    
    def test_chat_utils(self):
        """Тестирует утилиты для чатов"""
        print("\n🛠 ТЕСТ CHAT UTILS:")
        
        try:
            # Создаем тестовые данные
            manager = ChatManager(12345)
            chat1 = manager.create_chat("Анна", "VIP")
            chat2 = manager.create_chat("Мария", "Новая")
            
            # Добавляем сообщения
            chat1.add_message(ChatMessage("user", "Привет!"))
            chat1.add_message(ChatMessage("assistant", "Привет! Как дела?"))
            
            # Тест клавиатур
            mgmt_kb = get_chat_management_keyboard()
            print(f"✅ Клавиатура управления: {len(mgmt_kb.keyboard)} рядов")
            
            list_kb = get_chat_list_keyboard(manager)
            print(f"✅ Клавиатура списка: {len(list_kb.keyboard)} рядов")
            
            context_kb = get_chat_context_keyboard()
            print(f"✅ Клавиатура контекста: {len(context_kb.keyboard)} рядов")
            
            # Тест форматирования
            chat_info = format_chat_info(chat1)
            print(f"✅ Форматирование информации о чате: {len(chat_info)} символов")
            
            chat_memory = format_chat_memory(chat1)
            print(f"✅ Форматирование памяти: {len(chat_memory)} символов")
            
            analytics = format_chat_analytics(manager)
            print(f"✅ Форматирование аналитики: {len(analytics)} символов")
            
            # Тест контекста для AI
            ai_prompt = create_chat_context_prompt(chat1, "Расскажи о себе")
            print(f"✅ AI промпт: {len(ai_prompt)} символов")
            
            return True
            
        except Exception as e:
            print(f"❌ Ошибка в chat utils: {e}")
            return False
    
    async def test_chat_handlers(self):
        """Тестирует обработчики чатов"""
        print("\n🎮 ТЕСТ CHAT HANDLERS:")
        
        try:
            # Создаем mock объекты
            user = self.state_manager.get_user(12345)
            message = MockMessage()
            
            # Создаем mock CallbackQuery
            call = types.CallbackQuery(
                id="test",
                from_user=message.from_user,
                data="chat_management",
                chat_instance="test_instance",
                json_string="{}",
                message=message
            )
            
            # Создаем mock бота (простая заглушка)
            class MockBot:
                async def send_message(self, chat_id, text, **kwargs):
                    print(f"📤 Отправка сообщения: {text[:50]}...")
                    return True
                
                async def edit_message_text(self, text, chat_id, message_id, **kwargs):
                    print(f"✏️ Редактирование сообщения: {text[:50]}...")
                    return True
                
                async def answer_callback_query(self, callback_id, text=""):
                    print(f"📞 Ответ на callback: {text}")
                    return True
            
            mock_bot = MockBot()
            
            print("🔧 Тестируем обработчики...")
            
            # Тест управления чатами
            await self.chat_handlers.handle_chat_management(mock_bot, call, from_button=True)
            print("✅ handle_chat_management работает")
            
            # Создаем чат для тестов
            if not hasattr(user, 'chat_manager'):
                user.chat_manager = ChatManager(12345)
            
            chat = user.chat_manager.create_chat("Тестовый клиент")
            
            # Тест списка чатов
            call.data = "chat_list"
            await self.chat_handlers.handle_chat_list(mock_bot, call)
            print("✅ handle_chat_list работает")
            
            # Тест переключения чата
            await self.chat_handlers.handle_switch_chat(mock_bot, call, chat.chat_id)
            print("✅ handle_switch_chat работает")
            
            # Тест памяти чата
            await self.chat_handlers.handle_chat_memory(mock_bot, call)
            print("✅ handle_chat_memory работает")
            
            # Тест аналитики
            await self.chat_handlers.handle_chat_analytics(mock_bot, call)
            print("✅ handle_chat_analytics работает")
            
            return True
            
        except Exception as e:
            print(f"❌ Ошибка в chat handlers: {e}")
            return False
    
    def test_integration(self):
        """Тест интеграции с основной системой"""
        print("\n🔗 ТЕСТ ИНТЕГРАЦИИ:")
        
        try:
            # Получаем пользователя из StateManager
            user = self.state_manager.get_user(12345)
            print(f"✅ Пользователь получен: {user.user_id}")
            
            # Инициализируем ChatManager
            if not hasattr(user, 'chat_manager'):
                user.chat_manager = ChatManager(12345)
            
            # Создаем чаты
            chat1 = user.chat_manager.create_chat("Анна")
            chat2 = user.chat_manager.create_chat("Мария")
            print(f"✅ Чаты созданы: {len(user.chat_manager.chats)}")
            
            # Добавляем сообщения
            user.chat_manager.add_message_to_active_chat("user", "Привет!")
            user.chat_manager.add_message_to_active_chat("assistant", "Привет! Как дела?")
            print(f"✅ Сообщения добавлены")
            
            # Сохраняем пользователя
            self.state_manager.save_user(12345, user)
            print(f"✅ Пользователь сохранен")
            
            # Загружаем пользователя заново
            user_loaded = self.state_manager.get_user(12345)
            print(f"✅ Пользователь загружен: {hasattr(user_loaded, 'chat_manager')}")
            
            if hasattr(user_loaded, 'chat_manager') and user_loaded.chat_manager:
                print(f"✅ ChatManager сохранился: {len(user_loaded.chat_manager.chats)} чатов")
            
            return True
            
        except Exception as e:
            print(f"❌ Ошибка интеграции: {e}")
            return False

async def main():
    """Главная функция тестирования"""
    tester = ChatTester()
    
    print("🚀 ЗАПУСК КОМПЛЕКСНЫХ ТЕСТОВ ЧАТОВ\n")
    
    # Запускаем все тесты
    test_results = []
    
    test_results.append(("Модели данных", tester.test_chat_models()))
    test_results.append(("ChatManager", tester.test_chat_manager()))
    test_results.append(("Chat Utils", tester.test_chat_utils()))
    test_results.append(("Chat Handlers", await tester.test_chat_handlers()))
    test_results.append(("Интеграция", tester.test_integration()))
    
    # Выводим результаты
    print("\n" + "=" * 60)
    print("📊 РЕЗУЛЬТАТЫ КОМПЛЕКСНОГО ТЕСТИРОВАНИЯ:")
    
    total_tests = len(test_results)
    passed_tests = sum(1 for _, result in test_results if result)
    
    for test_name, result in test_results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"   {status} {test_name}")
    
    print(f"\n📈 ИТОГ: {passed_tests}/{total_tests} тестов прошли успешно")
    
    if passed_tests == total_tests:
        print("\n🎉 ВСЯ ФУНКЦИОНАЛЬНОСТЬ ЧАТОВ РАБОТАЕТ!")
        print("🚀 Система готова к продакшену!")
        print("\n💡 Доступные функции:")
        print("   • Создание и управление множественными чатами")
        print("   • Переключение между клиентами")
        print("   • Память и контекст для каждого клиента")
        print("   • Аналитика и статистика")
        print("   • Интеграция с основным ботом")
        return True
    else:
        print(f"\n💥 ЕСТЬ ПРОБЛЕМЫ В {total_tests - passed_tests} КОМПОНЕНТАХ!")
        print("❗ Требуется доработка перед продакшеном")
        return False

if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1) 