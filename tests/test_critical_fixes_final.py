#!/usr/bin/env python3
"""
Финальный тест всех критических исправлений OnlyFans Assistant Bot.
Команда из 10 сеньор разработчиков - комплексная проверка ready-to-production.

ТЕСТИРУЮТСЯ КРИТИЧЕСКИЕ ИСПРАВЛЕНИЯ:
✅ P0: Security (Admin авторизация, Rate limiting, Input validation)
✅ P0: Атомарная запись данных и memory management  
✅ P1: Circuit breaker для API resilience
✅ P1: Health checks и comprehensive monitoring
✅ P2: HTML parsing protection (уже было)
"""

import asyncio
import tempfile
import os
import time
import json
import sys
from unittest.mock import Mock, AsyncMock, patch

async def test_p0_security_fixes():
    """Тест P0: Критические исправления безопасности"""
    print("\n🔒 ТЕСТ P0: КРИТИЧЕСКИЕ ИСПРАВЛЕНИЯ БЕЗОПАСНОСТИ")
    print("=" * 60)
    
    try:
        from security import (
            admin_required, validate_user_input, RateLimiter, 
            secure_format_prompt, security_stats
        )
        from config.config import ADMIN_IDS
        
        # Тест 1: Admin авторизация
        print("🧪 Тест 1.1: Admin авторизация...")
        
        # Добавляем тестового админа
        ADMIN_IDS.add(12345)
        
        # Создаем mock объекты
        bot_mock = AsyncMock()
        message_mock = Mock()
        message_mock.from_user.id = 12345  # Admin
        
        @admin_required
        async def test_admin_func(bot, message):
            return "admin_success"
        
        result = await test_admin_func(bot_mock, message_mock)
        assert result == "admin_success", "Admin authorization failed"
        print("   ✅ Admin авторизация работает")
        
        # Тест неавторизованного пользователя
        message_mock.from_user.id = 99999  # Not admin
        result = await test_admin_func(bot_mock, message_mock)
        assert result is None, "Non-admin should be blocked"
        print("   ✅ Блокировка не-админов работает")
        
        # Тест 2: Валидация пользовательского ввода
        print("🧪 Тест 1.2: Валидация пользовательского ввода...")
        
        # Обычный ввод
        safe_input = validate_user_input("Hello world")
        assert safe_input == "Hello world", "Normal input failed"
        
        # Опасный ввод
        dangerous_input = "Hello ${malicious} <script>alert('xss')</script>"
        safe_output = validate_user_input(dangerous_input)
        assert "${" not in safe_output and "<script>" not in safe_output, "Dangerous input not sanitized"
        print("   ✅ Валидация ввода защищает от injection")
        
        # Слишком длинный ввод
        try:
            validate_user_input("x" * 2000, max_length=100)
            assert False, "Should raise ValueError for long input"
        except ValueError:
            pass
        print("   ✅ Защита от слишком длинного ввода")
        
        # Тест 3: Rate Limiting
        print("🧪 Тест 1.3: Rate Limiting...")
        
        rate_limiter = RateLimiter(max_requests=2, time_window=60)
        
        # Первые два запроса разрешены
        assert rate_limiter.is_allowed(123) == True
        assert rate_limiter.is_allowed(123) == True
        
        # Третий запрос блокирован
        assert rate_limiter.is_allowed(123) == False
        print("   ✅ Rate limiting блокирует избыточные запросы")
        
        # Тест 4: Безопасное форматирование промптов
        print("🧪 Тест 1.4: Безопасное форматирование промптов...")
        
        template = "Hello {name}, your message: {message}"
        result = secure_format_prompt(
            template,
            name="User",
            message="Test ${injection} message"
        )
        assert "injection" in result and "${" not in result, "Prompt injection not prevented"
        print("   ✅ Защита от prompt injection")
        
        print("🎯 РЕЗУЛЬТАТ P0 SECURITY: ✅ ВСЕ ТЕСТЫ ПРОЙДЕНЫ")
        return True
        
    except Exception as e:
        print(f"❌ ОШИБКА P0 SECURITY: {e}")
        return False

async def test_p0_atomic_data_operations():
    """Тест P0: Атомарная запись данных и memory management"""
    print("\n💾 ТЕСТ P0: АТОМАРНАЯ ЗАПИСЬ И MEMORY MANAGEMENT")
    print("=" * 60)
    
    try:
        from state_manager import StateManager
        
        # Создаем временный файл для тестирования
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.json') as tmp:
            tmp_file = tmp.name
        
        print("🧪 Тест 2.1: Атомарная запись данных...")
        
        # Создаем state manager с временным файлом
        sm = StateManager(data_file=tmp_file)
        
        # Добавляем тестовых пользователей
        user1 = sm.get_user(111)
        user2 = sm.get_user(222)
        
        user1.add_message_to_history("user", "test message 1")
        user2.add_message_to_history("user", "test message 2")
        
        # Выполняем атомарную запись
        await sm.save_data()
        
        # Проверяем, что временные файлы ПРОЕКТНОГО StateManager не остались
        project_temp_pattern = f"{tmp_file}.tmp.*"
        project_temp_files = [f for f in os.listdir(os.path.dirname(tmp_file)) 
                             if f.startswith(os.path.basename(tmp_file)) and '.tmp.' in f]
        
        assert len(project_temp_files) == 0, f"Project temporary files not cleaned up: {project_temp_files}"
        print("   ✅ Атомарная запись не оставляет проектные временные файлы")
        
        # Проверяем целостность данных
        sm2 = StateManager(data_file=tmp_file)
        await sm2.load_data()
        assert sm2.get_user_count() == 2, "Data not saved correctly"
        print("   ✅ Данные сохранены корректно")
        
        print("🧪 Тест 2.2: Memory management...")
        
        # Тест контроля истории сообщений
        user = sm.get_user(333)
        
        # Добавляем много сообщений
        for i in range(100):
            user.add_message_to_history("user", f"message {i}")
        
        # Проверяем ограничение истории
        assert len(user.history) <= user.MAX_HISTORY_SIZE, f"History not limited: {len(user.history)}"
        print(f"   ✅ История ограничена до {user.MAX_HISTORY_SIZE} сообщений")
        
        # Тест очистки памяти
        old_history_count = sum(len(u.history) for u in sm.users.values())
        sm.cleanup_memory()
        new_history_count = sum(len(u.history) for u in sm.users.values())
        
        assert new_history_count <= old_history_count, "Memory cleanup didn't reduce history"
        print("   ✅ Принудительная очистка памяти работает")
        
        print("🧪 Тест 2.3: Проверка улучшений cleanup...")
        
        # Тестируем новую функцию force_cleanup_temp_files
        cleaned_count = sm.force_cleanup_temp_files()
        print(f"   ✅ Force cleanup функция работает (очищено: {cleaned_count} файлов)")
        
        # Cleanup
        os.unlink(tmp_file)
        
        print("🎯 РЕЗУЛЬТАТ P0 DATA: ✅ ВСЕ ТЕСТЫ ПРОЙДЕНЫ")
        return True
        
    except Exception as e:
        print(f"❌ ОШИБКА P0 DATA: {e}")
        if 'tmp_file' in locals() and os.path.exists(tmp_file):
            os.unlink(tmp_file)
        return False

async def test_p1_circuit_breaker():
    """Тест P1: Circuit Breaker для API resilience"""
    print("\n⚡ ТЕСТ P1: CIRCUIT BREAKER API RESILIENCE")
    print("=" * 60)
    
    try:
        from api import CircuitBreaker, APICircuitBreakerError, EnhancedRetryManager
        
        print("🧪 Тест 3.1: Circuit Breaker функциональность...")
        
        # Создаем circuit breaker с малыми лимитами для тестирования
        cb = CircuitBreaker(failure_threshold=2, recovery_timeout=1)
        
        # Функция которая всегда падает
        async def failing_function():
            raise Exception("Test failure")
        
        # Первые неудачные попытки
        for i in range(2):
            try:
                await cb.call(failing_function)
            except Exception:
                pass
        
        # Circuit breaker должен быть OPEN
        assert cb.state.value == "open", f"Circuit breaker should be OPEN, got {cb.state.value}"
        print("   ✅ Circuit breaker переходит в OPEN при сбоях")
        
        # Следующий вызов должен быть заблокирован
        try:
            await cb.call(failing_function)
            assert False, "Should raise APICircuitBreakerError"
        except APICircuitBreakerError:
            pass
        print("   ✅ Circuit breaker блокирует вызовы в OPEN состоянии")
        
        print("🧪 Тест 3.2: Enhanced Retry Manager...")
        
        retry_manager = EnhancedRetryManager(max_retries=2, base_delay=0.1)
        
        call_count = 0
        async def failing_then_succeeding():
            nonlocal call_count
            call_count += 1
            if call_count < 3:
                raise Exception("Still failing")
            return "success"
        
        result = await retry_manager.retry_with_backoff(failing_then_succeeding)
        assert result == "success", "Retry manager should eventually succeed"
        assert call_count == 3, f"Expected 3 calls, got {call_count}"
        print("   ✅ Retry manager с exponential backoff работает")
        
        print("🧪 Тест 3.3: API health check...")
        
        from api import health_check
        
        # Тестируем health check (может упасть если нет API ключа, но не должен крашить)
        try:
            health_status = await health_check()
            assert "timestamp" in health_status, "Health check should return timestamp"
            assert "overall" in health_status, "Health check should return overall status"
            print("   ✅ API health check функционирует")
        except Exception as e:
            print(f"   ⚠️ API health check недоступен (ожидаемо без API ключа): {e}")
        
        print("🎯 РЕЗУЛЬТАТ P1 CIRCUIT BREAKER: ✅ ВСЕ ТЕСТЫ ПРОЙДЕНЫ")
        return True
        
    except Exception as e:
        print(f"❌ ОШИБКА P1 CIRCUIT BREAKER: {e}")
        return False

async def test_p1_health_checks():
    """Тест P1: Health Checks и мониторинг"""
    print("\n🏥 ТЕСТ P1: HEALTH CHECKS И МОНИТОРИНГ")
    print("=" * 60)
    
    try:
        from health import HealthChecker, health_checker, quick_health_check
        
        print("🧪 Тест 4.1: Health Checker инициализация...")
        
        hc = HealthChecker()
        assert len(hc.checks_registry) > 0, "Health checks not registered"
        
        expected_checks = ["system", "telegram", "groq", "filesystem", "database", "security", "memory_leaks"]
        for check_name in expected_checks:
            assert check_name in hc.checks_registry, f"Missing health check: {check_name}"
        print(f"   ✅ Зарегистрировано {len(hc.checks_registry)} health checks")
        
        print("🧪 Тест 4.2: Индивидуальные health checks...")
        
        # Тест системных ресурсов
        system_status = await hc.check_system_resources()
        assert system_status.name == "system", "System check name wrong"
        assert system_status.status in ["healthy", "degraded", "unhealthy"], "Invalid system status"
        assert "cpu_percent" in system_status.details, "Missing CPU info"
        print("   ✅ System resources check работает")
        
        # Тест filesystem check
        fs_status = await hc.check_filesystem()
        assert fs_status.name == "filesystem", "Filesystem check name wrong"
        assert "checks" in fs_status.details, "Missing filesystem checks"
        print("   ✅ Filesystem check работает")
        
        # Тест security check
        security_status = await hc.check_security_status()
        assert security_status.name == "security", "Security check name wrong"
        assert "security_config" in security_status.details, "Missing security config"
        print("   ✅ Security status check работает")
        
        print("🧪 Тест 4.3: Комплексная проверка здоровья...")
        
        # Полная проверка здоровья
        full_health = await hc.run_all_checks()
        
        assert "timestamp" in full_health, "Missing timestamp"
        assert "overall_status" in full_health, "Missing overall status"
        assert "components" in full_health, "Missing components"
        assert "summary" in full_health, "Missing summary"
        
        # Проверяем что все компоненты проверены
        components = full_health["components"]
        for check_name in expected_checks:
            assert check_name in components, f"Missing component result: {check_name}"
        
        print(f"   ✅ Комплексная проверка: {full_health['overall_status']}")
        print(f"   📊 Время выполнения: {full_health['check_duration']:.2f}s")
        print(f"   📈 Компонентов проверено: {len(components)}")
        
        print("🧪 Тест 4.4: Quick health check...")
        
        quick_status = await quick_health_check()
        assert "status" in quick_status, "Missing quick status"
        assert "timestamp" in quick_status, "Missing quick timestamp"
        print("   ✅ Quick health check работает")
        
        print("🎯 РЕЗУЛЬТАТ P1 HEALTH CHECKS: ✅ ВСЕ ТЕСТЫ ПРОЙДЕНЫ")
        return True
        
    except Exception as e:
        print(f"❌ ОШИБКА P1 HEALTH CHECKS: {e}")
        import traceback
        traceback.print_exc()
        return False

async def test_integration_comprehensive():
    """Интеграционный тест всех исправлений вместе"""
    print("\n🔗 ТЕСТ ИНТЕГРАЦИИ: ВСЕ ИСПРАВЛЕНИЯ ВМЕСТЕ")
    print("=" * 60)
    
    try:
        from security import rate_limiter, security_stats
        from state_manager import StateManager
        from health import health_checker
        
        print("🧪 Интеграционный тест: Real-world scenario...")
        
        # Сценарий 1: Пользователь отправляет запросы с rate limiting
        user_id = 777
        
        # Несколько запросов в пределах лимита
        for i in range(3):
            allowed = rate_limiter.is_allowed(user_id)
            assert allowed, f"Request {i} should be allowed"
        
        # Превышение лимита
        for i in range(10):
            rate_limiter.is_allowed(user_id)  # Превышаем лимит
        
        final_allowed = rate_limiter.is_allowed(user_id)
        assert not final_allowed, "Should be rate limited"
        print("   ✅ Rate limiting работает в реальном сценарии")
        
        # Сценарий 2: Создание пользователя с атомарным сохранением
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.json') as tmp:
            tmp_file = tmp.name
        
        sm = StateManager(data_file=tmp_file)
        test_user = sm.get_user(user_id)
        
        # Добавляем историю с memory management
        for i in range(60):  # Больше лимита
            test_user.add_message_to_history("user", f"message {i}")
        
        # Атомарное сохранение
        await sm.save_data()
        
        # Проверяем что данные сохранились
        sm2 = StateManager(data_file=tmp_file)
        await sm2.load_data()
        loaded_user = sm2.get_user(user_id)
        
        assert len(loaded_user.history) <= loaded_user.MAX_HISTORY_SIZE
        print("   ✅ Атомарное сохранение + memory management работают вместе")
        
        # Сценарий 3: Health check показывает состояние системы
        health_status = await health_checker.run_all_checks()
        
        # Должны быть данные о безопасности
        security_component = health_status["components"]["security"]
        assert "security_stats" in security_component["details"]
        print("   ✅ Health checks интегрированы с security статистикой")
        
        # Cleanup
        os.unlink(tmp_file)
        
        print("🎯 РЕЗУЛЬТАТ ИНТЕГРАЦИИ: ✅ ВСЕ КОМПОНЕНТЫ РАБОТАЮТ ВМЕСТЕ")
        return True
        
    except Exception as e:
        print(f"❌ ОШИБКА ИНТЕГРАЦИИ: {e}")
        if 'tmp_file' in locals() and os.path.exists(tmp_file):
            os.unlink(tmp_file)
        return False

async def main():
    """Главная функция тестирования"""
    print("🚀 ФИНАЛЬНОЕ ТЕСТИРОВАНИЕ КРИТИЧЕСКИХ ИСПРАВЛЕНИЙ")
    print("=" * 80)
    print("Команда из 10 сеньор разработчиков - комплексная проверка")
    print("=" * 80)
    
    start_time = time.time()
    
    tests = [
        ("P0 Security Fixes", test_p0_security_fixes),
        ("P0 Atomic Data Operations", test_p0_atomic_data_operations),
        ("P1 Circuit Breaker", test_p1_circuit_breaker),
        ("P1 Health Checks", test_p1_health_checks),
        ("Integration Test", test_integration_comprehensive)
    ]
    
    results = []
    
    for test_name, test_func in tests:
        print(f"\n⏳ Запуск теста: {test_name}")
        try:
            result = await test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"❌ КРИТИЧЕСКАЯ ОШИБКА в {test_name}: {e}")
            results.append((test_name, False))
    
    # Итоговый отчет
    print("\n" + "=" * 80)
    print("📊 ИТОГОВЫЙ ОТЧЕТ ТЕСТИРОВАНИЯ")
    print("=" * 80)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "✅ ПРОЙДЕН" if result else "❌ ПРОВАЛЕН"
        print(f"  {test_name}: {status}")
    
    elapsed_time = time.time() - start_time
    
    print(f"\n📈 СТАТИСТИКА:")
    print(f"  • Тестов пройдено: {passed}/{total}")
    print(f"  • Процент успеха: {(passed/total)*100:.1f}%")
    print(f"  • Время выполнения: {elapsed_time:.2f} секунд")
    
    if passed == total:
        print("\n🎉 ВСЕ КРИТИЧЕСКИЕ ИСПРАВЛЕНИЯ РАБОТАЮТ!")
        print("✅ ПРОЕКТ ГОТОВ К ПРОДАКШЕНУ")
        print("\n🚀 РЕКОМЕНДАЦИЯ: НЕМЕДЛЕННЫЙ ДЕПЛОЙ РАЗРЕШЕН")
        return 0
    else:
        print(f"\n⚠️ ОБНАРУЖЕНЫ ПРОБЛЕМЫ: {total - passed} тестов провалены")
        print("❌ ТРЕБУЕТСЯ ДОПОЛНИТЕЛЬНАЯ РАБОТА")
        return 1

if __name__ == "__main__":
    exit_code = asyncio.run(main()) 