#!/usr/bin/env python3
"""
Тестирование импорта основных модулей
"""

import sys

def test_module(module_name):
    """Тестирование импорта модуля"""
    try:
        __import__(module_name)
        print(f"✅ {module_name} - OK")
        return True
    except Exception as e:
        print(f"❌ {module_name} - ERROR: {e}")
        return False

def main():
    """Главная функция тестирования"""
    print("🧪 ТЕСТИРОВАНИЕ МОДУЛЕЙ БОТА")
    print("=" * 40)
    
    modules_to_test = [
        'premium_system',
        'adult_templates', 
        'monetized_bot',
        'admin_commands',
        'response_generator',
        'monetization_config',
        'telegram_payment_system',
        'response_cache',
        'bot_integration',
        'simple_bot_windows'
    ]
    
    success_count = 0
    total_count = len(modules_to_test)
    
    for module in modules_to_test:
        if test_module(module):
            success_count += 1
    
    print("=" * 40)
    print(f"РЕЗУЛЬТАТ: {success_count}/{total_count} модулей работают")
    
    if success_count == total_count:
        print("✅ Все модули в порядке!")
    else:
        print("⚠️ Некоторые модули имеют ошибки")
    
    return success_count == total_count

if __name__ == "__main__":
    main() 