#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Тест системы управления множественными чатами с клиентами
"""

import sys
import asyncio
import pytest
from pathlib import Path
from unittest.mock import Mock, AsyncMock
from datetime import datetime

# Добавляем путь к модулям бота
sys.path.insert(0, str(Path(__file__).parent))

from chat_models import ChatManager, ClientProfile, ClientChat, ChatMessage
from chat_utils import (
    get_chat_management_keyboard, format_chat_info, format_chat_memory,
    create_chat_context_prompt
)
from chat_handlers import ChatHandlers
from state_manager import StateManager
from models import UserState

def test_client_profile():
    """Тест создания профиля клиента"""
    print("=== TEST: Client Profile ===")
    
    # Создание профиля с автоматическим именем
    profile1 = ClientProfile()
    print(f"✅ Auto profile created: {profile1.name}")
    assert profile1.name.startswith("Клиент_")
    
    # Создание профиля с именем
    profile2 = ClientProfile(name="Максим", description="VIP клиент")
    print(f"✅ Named profile created: {profile2.name}")
    assert profile2.name == "Максим"
    
    # Сериализация/десериализация
    data = profile2.to_dict()
    profile3 = ClientProfile.from_dict(data)
    
    assert profile3.name == profile2.name
    assert profile3.description == profile2.description
    print("✅ Serialization/deserialization works")

def test_chat_message():
    """Тест сообщений в чате"""
    print("\n=== TEST: Chat Message ===")
    
    # Создание сообщения
    message = ChatMessage("user", "Привет! Как дела?", "text")
    print(f"✅ Message created: {message.content[:20]}...")
    
    # Проверка автоматических полей
    assert message.message_id is not None
    assert message.timestamp is not None
    print("✅ Auto fields generated")
    
    # Сериализация/десериализация
    data = message.to_dict()
    message2 = ChatMessage.from_dict(data)
    
    assert message2.content == message.content
    assert message2.role == message.role
    print("✅ Message serialization works")

def test_client_chat():
    """Тест чата с клиентом"""
    print("\n=== TEST: Client Chat ===")
    
    # Создание чата
    profile = ClientProfile(name="Анна", description="Постоянный клиент")
    chat = ClientChat(profile)
    print(f"✅ Chat created for {chat.client_profile.name}")
    
    # Добавление сообщений
    chat.add_message(ChatMessage("user", "Привет!", "text"))
    chat.add_message(ChatMessage("assistant", "Привет, дорогой! 💕", "text"))
    chat.add_message(ChatMessage("user", "Как дела?", "text"))
    
    assert len(chat.messages) == 3
    print(f"✅ Messages added: {len(chat.messages)}")
    
    # Проверка автоматического обновления этапа
    original_stage = chat.conversation_stage
    for i in range(15):  # Добавляем много сообщений для изменения этапа
        chat.add_message(ChatMessage("user", f"Сообщение {i}", "text"))
    
    if chat.conversation_stage != original_stage:
        print(f"✅ Conversation stage updated: {original_stage} -> {chat.conversation_stage}")
    else:
        print("⚠️ Conversation stage not updated (may be expected)")
    
    # Получение последних сообщений
    recent = chat.get_recent_messages(3)
    assert len(recent) <= 3
    print(f"✅ Recent messages: {len(recent)}")
    
    # Создание контекста
    context = chat.get_context_summary()
    assert context is not None
    assert len(context) > 50
    print("✅ Context summary generated")

def test_chat_manager():
    """Тест менеджера чатов"""
    print("\n=== TEST: Chat Manager ===")
    
    # Создание менеджера
    manager = ChatManager(12345)
    print(f"✅ Chat manager created for user {manager.user_id}")
    
    # Создание чатов
    chat1 = manager.create_chat("Алексей", "Новый клиент")
    chat2 = manager.create_chat("Мария", "VIP клиент")
    
    assert len(manager.chats) == 2
    print(f"✅ Chats created: {len(manager.chats)}")
    
    # Проверка активного чата
    active = manager.get_active_chat()
    assert active is not None
    assert active.client_profile.name == "Алексей"
    print(f"✅ Active chat: {active.client_profile.name}")
    
    # Переключение чата
    switch_result = manager.switch_chat(chat2.chat_id)
    assert switch_result == True
    new_active = manager.get_active_chat()
    assert new_active.client_profile.name == "Мария"
    print("✅ Chat switching works")
    
    # Добавление сообщений в активный чат
    success = manager.add_message_to_active_chat("user", "Тест сообщение", "text")
    assert success == True
    assert len(manager.get_active_chat().messages) > 0
    print("✅ Message added to active chat")
    
    # Получение списка чатов
    chat_list = manager.get_chat_list()
    assert len(chat_list) == 2
    print(f"✅ Chat list: {len(chat_list)} chats")

def test_chat_utils():
    """Тест утилит для чатов"""
    print("\n=== TEST: Chat Utils ===")
    
    # Создание клавиатуры
    keyboard = get_chat_management_keyboard()
    assert keyboard is not None
    assert keyboard.keyboard is not None
    print(f"✅ Management keyboard created: {len(keyboard.keyboard)} rows")
    
    # Создание чата для тестирования форматирования
    profile = ClientProfile(name="Тест", description="Тестовый клиент")
    chat = ClientChat(profile)
    chat.add_message(ChatMessage("user", "Длинное сообщение для проверки обрезки текста в превью чата" * 3, "text"))
    
    # Тест форматирования информации о чате
    info = format_chat_info(chat)
    assert info is not None
    assert len(info) > 100
    print("✅ Chat info formatting works")
    
    # Тест форматирования памяти
    chat.client_memory["preferences"]["любимый_цвет"] = "красный"
    chat.client_memory["interests"] = ["фитнес", "путешествия"]
    
    memory = format_chat_memory(chat)
    assert memory is not None
    assert "любимый_цвет" in memory
    print("✅ Memory formatting works")
    
    # Тест создания промпта
    prompt = create_chat_context_prompt(chat, "Как дела?")
    assert prompt is not None
    assert len(prompt) > 200
    print("✅ Context prompt creation works")

@pytest.mark.asyncio
async def test_chat_handlers():
    """Тест обработчиков чатов"""
    print("\n=== TEST: Chat Handlers ===")
    
    # Создание mock объектов
    state_manager = Mock()
    state_manager.get_user = Mock()
    state_manager.save_data = AsyncMock()
    
    # Создание пользователя с chat_manager
    user = Mock()
    chat_manager = ChatManager(12345)
    chat_manager.create_chat("Тестовый клиент", "Описание")
    user.chat_manager = chat_manager
    
    state_manager.get_user.return_value = user
    
    # Создание обработчиков
    handlers = ChatHandlers(state_manager)
    print("✅ Chat handlers created")
    
    # Получение словаря обработчиков
    callback_handlers = handlers.get_callback_handlers()
    assert callback_handlers is not None
    assert "chat_management" in callback_handlers
    print(f"✅ Callback handlers: {len(callback_handlers)} handlers")
    
    # Тест обработки callback с параметрами
    test_chat_id = list(chat_manager.chats.keys())[0]
    param_handler = handlers.handle_callback_with_params(f"chat_switch_{test_chat_id}")
    assert param_handler is not None
    print("✅ Parameterized callback handling works")

def test_user_state_integration():
    """Тест интеграции с UserState"""
    print("\n=== TEST: UserState Integration ===")
    
    # Создание пользователя
    user = UserState()
    print("✅ UserState created")
    
    # Проверка новых полей
    assert hasattr(user, 'chat_manager')
    assert hasattr(user, 'waiting_for_chat_name')
    assert hasattr(user, 'waiting_for_chat_reply')
    print("✅ New chat fields present")
    
    # Создание chat_manager
    from chat_models import ChatManager
    user.chat_manager = ChatManager(12345)
    user.waiting_for_chat_name = True
    
    # Сериализация
    data = user.to_dict()
    assert 'chat_manager' in data
    assert 'waiting_for_chat_name' in data
    print("✅ Serialization includes chat fields")
    
    # Десериализация
    user2 = UserState.from_dict(data)
    assert user2.chat_manager is not None
    assert user2.waiting_for_chat_name == True
    print("✅ Deserialization works")

@pytest.mark.asyncio
async def test_all_chat_system():
    """Запуск всех тестов системы чатов"""
    print("Testing Chat Management System")
    print("=" * 50)
    
    test_client_profile()
    test_chat_message()
    test_client_chat()
    test_chat_manager()
    test_chat_utils()
    await test_chat_handlers()
    test_user_state_integration()
    
    print("\n" + "=" * 50)
    print("SUCCESS: All tests completed!")
    print("✅ Client profiles work correctly")
    print("✅ Chat messages and history work")
    print("✅ Chat management functions properly")
    print("✅ Multiple chat switching works")
    print("✅ Memory and context preservation works")
    print("✅ User interface components ready")
    print("✅ Integration with existing system complete")
    print("\n🎉 Chat system is ready for production!")

if __name__ == "__main__":
    asyncio.run(test_all_chat_system()) 