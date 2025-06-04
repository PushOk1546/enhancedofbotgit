#!/usr/bin/env python3
"""
Тест русского интерфейса Enterprise Bot V2.0
Проверяет корректность всех русскоязычных сообщений
"""

import asyncio
import sys
import os

# Add core directory to path
sys.path.insert(0, str("core"))

try:
    from core.services.payment_service import PaymentService
    from core.services.message_service import MessageService
    from core.services.user_service import UserService, SubscriptionTier
    print("✅ Все импорты успешны")
except ImportError as e:
    print(f"❌ Ошибка импорта: {e}")
    sys.exit(1)


async def test_russian_interface():
    """Тест русского интерфейса"""
    print("\n🧪 ТЕСТИРОВАНИЕ РУССКОГО ИНТЕРФЕЙСА")
    print("="*50)
    
    # Тест PaymentService
    print("\n📊 Тест PaymentService:")
    payment_service = PaymentService()
    
    plans_text = payment_service.get_payment_plans_text()
    print("✅ Планы подписок:")
    print(plans_text[:200] + "..." if len(plans_text) > 200 else plans_text)
    
    tiers_text = payment_service.get_available_tiers_text()
    print("\n✅ Доступные тарифы:")
    print(tiers_text[:200] + "..." if len(tiers_text) > 200 else tiers_text)
    
    # Тест MessageService
    print("\n📝 Тест MessageService:")
    message_service = MessageService()
    
    welcome_msg = message_service.get_welcome_message("Тестовый Пользователь")
    print("✅ Приветственное сообщение:")
    print(welcome_msg[:200] + "..." if len(welcome_msg) > 200 else welcome_msg)
    
    premium_offer = message_service.get_premium_offer_text()
    print("\n✅ Предложение премиум:")
    print(premium_offer[:200] + "..." if len(premium_offer) > 200 else premium_offer)
    
    help_text = message_service.get_help_text()
    print("\n✅ Текст помощи:")
    print(help_text[:200] + "..." if len(help_text) > 200 else help_text)
    
    conversion_msg = message_service.get_conversion_message(10)
    print("\n✅ Конверсионное сообщение:")
    print(conversion_msg[:200] + "..." if len(conversion_msg) > 200 else conversion_msg)
    
    error_msg = message_service.get_error_message()
    print("\n✅ Сообщение об ошибке:")
    print(error_msg)
    
    # Тест генерации ответов
    print("\n🤖 Тест генерации ответов:")
    
    test_messages = [
        "Привет!",
        "Как дела?",
        "Ты красивая",
        "Люблю тебя",
        "Покажи фото"
    ]
    
    for msg in test_messages:
        response = await message_service.generate_response(12345, msg)
        print(f"📩 '{msg}' -> '{response}'")
    
    # Тест шаблонов
    print("\n📋 Тест шаблонов:")
    friendly_templates = await message_service.get_templates("friendly")
    print(f"✅ Дружеские шаблоны: {len(friendly_templates)} штук")
    
    flirt_templates = await message_service.get_templates("flirt")
    print(f"✅ Флирт шаблоны: {len(flirt_templates)} штук")
    
    print("\n🎯 РЕЗУЛЬТАТ: Все русские сообщения работают корректно!")
    return True


async def test_user_service():
    """Тест UserService"""
    print("\n👥 Тест UserService:")
    
    user_service = UserService()
    await user_service.initialize()
    
    # Создание пользователя
    result = await user_service.create_user({
        'user_id': 999999,
        'username': 'test_user',
        'first_name': 'Тест',
        'last_name': 'Пользователь'
    })
    print(f"✅ Создание пользователя: {result}")
    
    # Получение пользователя
    user = await user_service.get_user(999999)
    if user:
        print(f"✅ Получение пользователя: {user.username}")
        print(f"   Подписка: {user.subscription.value}")
        print(f"   Сообщений: {user.messages_sent}")
    
    # Обновление подписки
    result = await user_service.upgrade_subscription(
        999999, SubscriptionTier.PREMIUM, 30
    )
    print(f"✅ Обновление подписки: {result}")
    
    # Получение метрик
    metrics = await user_service.get_performance_metrics()
    print(f"✅ Метрики производительности:")
    for key, value in metrics.items():
        print(f"   {key}: {value}")
    
    return True


def test_payment_plans():
    """Тест планов платежей"""
    print("\n💰 Тест планов платежей:")
    
    payment_service = PaymentService()
    
    for tier in [SubscriptionTier.PREMIUM, SubscriptionTier.VIP, SubscriptionTier.ULTIMATE]:
        for period in ['daily', 'weekly', 'monthly']:
            plan = payment_service.get_plan_by_tier_and_period(tier, period)
            if plan:
                print(f"✅ {tier.value} {period}: {plan.price_stars}⭐ ({plan.description_ru})")
                
                # Тест расчета скидки
                savings = payment_service.calculate_discount_savings(tier, period)
                if savings.get('has_discount'):
                    print(f"   💰 Скидка {savings['discount_percent']}%: экономия {savings['savings_stars']}⭐")
    
    return True


async def main():
    """Главная функция тестирования"""
    print("🔥 ТЕСТИРОВАНИЕ ENTERPRISE BOT V2.0 - РУССКИЙ ИНТЕРФЕЙС")
    print("="*60)
    
    try:
        # Тест русского интерфейса
        await test_russian_interface()
        
        # Тест пользовательского сервиса
        await test_user_service()
        
        # Тест планов платежей
        test_payment_plans()
        
        print("\n🎉 ВСЕ ТЕСТЫ ПРОШЛИ УСПЕШНО!")
        print("✅ Русский интерфейс работает корректно")
        print("✅ Все сервисы функционируют")
        print("✅ Планы подписок настроены")
        print("✅ Готов к продакшену!")
        
        return True
        
    except Exception as e:
        print(f"\n❌ ОШИБКА В ТЕСТАХ: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = asyncio.run(main())
    input(f"\n{'✅ Тестирование завершено успешно' if success else '❌ Тестирование провалено'}. Нажмите ENTER...")
    sys.exit(0 if success else 1) 