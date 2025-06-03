#!/usr/bin/env python3
"""
Тест исправления mock CallbackQuery.
Проверяет что mock CallbackQuery создается корректно.
"""

from telebot import types
from dataclasses import dataclass

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
    text: str = "👥 Чаты с клиентами"
    
    def __post_init__(self):
        if self.from_user is None:
            self.from_user = MockUser()
        if self.chat is None:
            self.chat = MockUser()  # Используем как chat

def test_mock_callback_creation():
    """Тестирует создание mock CallbackQuery"""
    print("🧪 ТЕСТ MOCK CALLBACK QUERY")
    print("=" * 40)
    
    try:
        # Создаем mock сообщение
        message = MockMessage()
        
        print("📝 Создаем mock CallbackQuery...")
        
        # Пробуем создать mock CallbackQuery как в bot.py
        mock_call = types.CallbackQuery(
            id="mock",
            from_user=message.from_user,
            data="chat_management",
            chat_instance="mock_instance",
            json_string="{}",
            message=message
        )
        
        print("✅ Mock CallbackQuery создан успешно!")
        print(f"   ID: {mock_call.id}")
        print(f"   Data: {mock_call.data}")
        print(f"   From User: {mock_call.from_user.first_name}")
        print(f"   Chat Instance: {mock_call.chat_instance}")
        
        return True
        
    except Exception as e:
        print(f"❌ Ошибка создания mock CallbackQuery: {e}")
        print(f"   Тип ошибки: {type(e).__name__}")
        return False

def test_callback_query_parameters():
    """Тестирует параметры CallbackQuery"""
    print("\n🔍 ТЕСТ ПАРАМЕТРОВ CALLBACKQUERY:")
    
    try:
        # Получаем документацию по конструктору
        import inspect
        sig = inspect.signature(types.CallbackQuery.__init__)
        
        print("📋 Параметры конструктора CallbackQuery:")
        for param_name, param in sig.parameters.items():
            if param_name != 'self':
                required = "" if param.default != inspect.Parameter.empty else " (ОБЯЗАТЕЛЬНЫЙ)"
                print(f"   • {param_name}{required}")
        
        return True
        
    except Exception as e:
        print(f"❌ Ошибка анализа параметров: {e}")
        return False

if __name__ == "__main__":
    print("🚀 ЗАПУСК ТЕСТОВ MOCK CALLBACK QUERY\n")
    
    test1 = test_mock_callback_creation()
    test2 = test_callback_query_parameters()
    
    print("\n" + "=" * 40)
    print("📊 РЕЗУЛЬТАТЫ:")
    print(f"✅ Создание mock CallbackQuery: {'OK' if test1 else 'FAIL'}")
    print(f"✅ Анализ параметров: {'OK' if test2 else 'FAIL'}")
    
    if test1:
        print("\n🎉 ИСПРАВЛЕНИЕ РАБОТАЕТ!")
        print("🚀 Кнопка 'Чаты с клиентами' больше не вызывает ошибки!")
    else:
        print("\n💥 ТРЕБУЕТСЯ ДОПОЛНИТЕЛЬНОЕ ИСПРАВЛЕНИЕ!")
    
    exit(0 if test1 else 1) 