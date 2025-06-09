"""
Smoke-тесты для OF Assistant Bot с DeepSeek интеграцией
"""

import pytest
import asyncio
import sys
import os
from pathlib import Path

# Добавляем корневую директорию в путь
root_dir = Path(__file__).parent.parent
sys.path.insert(0, str(root_dir))

# Мокируем переменные окружения для тестов
os.environ['TELEGRAM_BOT_TOKEN'] = 'test_token'
os.environ['DEEPSEEK_API_KEY'] = 'test_key'

# Проверяем возможность импорта всех модулей
def test_import_config():
    """Тест импорта конфигурации"""
    try:
        import config
        assert hasattr(config, 'config')
        assert hasattr(config.config, 'DEEPSEEK_API_KEY')
        print("✅ Config импортируется успешно")
    except Exception as e:
        pytest.fail(f"❌ Ошибка импорта config: {e}")

def test_import_ai_service():
    """Тест импорта AI сервиса"""
    try:
        from services.ai_integration import AIService, ai_service
        assert isinstance(ai_service, AIService)
        print("✅ AI Service импортируется успешно")
    except Exception as e:
        pytest.fail(f"❌ Ошибка импорта AI Service: {e}")

def test_import_handlers():
    """Тест импорта обработчиков"""
    try:
        from handlers import BotHandlers, setup_handlers
        print("✅ Handlers импортируются успешно")
    except Exception as e:
        pytest.fail(f"❌ Ошибка импорта handlers: {e}")

def test_import_main():
    """Тест импорта главного модуля"""
    try:
        import main
        assert hasattr(main, 'OFAssistantBot')
        print("✅ Main импортируется успешно")
    except Exception as e:
        pytest.fail(f"❌ Ошибка импорта main: {e}")

@pytest.mark.asyncio
async def test_ai_service_initialization():
    """Тест инициализации AI сервиса"""
    try:
        from services.ai_integration import AIService
        # Создаем экземпляр с тестовыми данными
        service = AIService()
        
        assert service.api_key == 'test_key'
        assert service.model == 'deepseek-chat'
        assert hasattr(service, 'stats')
        assert hasattr(service, 'response_cache')
        
        print("✅ AI Service инициализируется корректно")
    except ValueError as e:
        if "DEEPSEEK_API_KEY" in str(e):
            print("⚠️ AI Service требует валидный API ключ (ожидаемо)")
        else:
            pytest.fail(f"❌ Неожиданная ошибка AI Service: {e}")
    except Exception as e:
        pytest.fail(f"❌ Ошибка инициализации AI Service: {e}")

@pytest.mark.asyncio 
async def test_ai_service_fallback_response():
    """Тест fallback ответов AI сервиса"""
    try:
        from services.ai_integration import AIService
        service = AIService()
        
        # Тестируем fallback ответы
        flirt_response = service._get_fallback_response("test", {"type": "flirt"})
        ppv_response = service._get_fallback_response("test", {"type": "ppv_promo"})
        default_response = service._get_fallback_response("test", {})
        
        assert isinstance(flirt_response, str)
        assert isinstance(ppv_response, str) 
        assert isinstance(default_response, str)
        
        assert "😘" in flirt_response  # Проверяем флиртовый ответ
        assert "🔥" in ppv_response    # Проверяем PPV ответ
        
        print("✅ Fallback ответы работают корректно")
    except Exception as e:
        pytest.fail(f"❌ Ошибка fallback ответов: {e}")

def test_cache_functionality():
    """Тест функциональности кэша"""
    try:
        from services.ai_integration import AIService
        service = AIService()
        
        # Тестируем генерацию ключа кэша
        key1 = service._get_cache_key("test prompt", {"type": "test"})
        key2 = service._get_cache_key("test prompt", {"type": "test"})
        key3 = service._get_cache_key("different prompt", {"type": "test"})
        
        assert key1 == key2  # Одинаковые промпты = одинаковые ключи
        assert key1 != key3  # Разные промпты = разные ключи
        
        # Тестируем кэширование
        service._cache_response("test_key", "test_response")
        cached = service._get_cached_response("test_key")
        
        assert cached == "test_response"
        
        print("✅ Кэш функционирует корректно")
    except Exception as e:
        pytest.fail(f"❌ Ошибка кэша: {e}")

def test_stats_functionality():
    """Тест статистики"""
    try:
        from services.ai_integration import AIService
        service = AIService()
        
        stats = service.get_stats()
        required_keys = ["total_requests", "successful_requests", "failed_requests", 
                        "cache_hits", "cache_size", "success_rate"]
        
        for key in required_keys:
            assert key in stats
        
        assert isinstance(stats["success_rate"], (int, float))
        assert 0 <= stats["success_rate"] <= 100
        
        print("✅ Статистика работает корректно")
    except Exception as e:
        pytest.fail(f"❌ Ошибка статистики: {e}")

def test_requirements_availability():
    """Тест доступности зависимостей"""
    required_modules = [
        'telebot',
        'aiohttp', 
        'aiofiles',
        'apscheduler',
        'loguru',
        'pydantic',
        'cachetools',
        'dotenv'
    ]
    
    missing_modules = []
    
    for module in required_modules:
        try:
            __import__(module)
            print(f"✅ {module} доступен")
        except ImportError:
            missing_modules.append(module)
            print(f"❌ {module} недоступен")
    
    if missing_modules:
        pytest.fail(f"Отсутствуют модули: {', '.join(missing_modules)}")

def test_file_structure():
    """Тест структуры файлов"""
    required_files = [
        'main.py',
        'config.py', 
        'handlers.py',
        'api_handler.py',
        'services/__init__.py',
        'services/ai_integration.py',
        'core/services/__init__.py',
        'requirements.txt',
        'env_template.txt'
    ]
    
    missing_files = []
    
    for file_path in required_files:
        full_path = root_dir / file_path
        if full_path.exists():
            print(f"✅ {file_path} существует")
        else:
            missing_files.append(file_path)
            print(f"❌ {file_path} отсутствует")
    
    if missing_files:
        pytest.fail(f"Отсутствуют файлы: {', '.join(missing_files)}")

if __name__ == "__main__":
    """Запуск тестов напрямую"""
    print("🧪 Запуск smoke-тестов OF Assistant Bot")
    print("=" * 50)
    
    # Синхронные тесты
    test_import_config()
    test_import_ai_service() 
    test_import_handlers()
    test_import_main()
    test_requirements_availability()
    test_file_structure()
    
    # Асинхронные тесты
    async def run_async_tests():
        await test_ai_service_initialization()
        await test_ai_service_fallback_response()
        
    try:
        asyncio.run(run_async_tests())
    except Exception as e:
        print(f"❌ Ошибка асинхронных тестов: {e}")
    
    # Синхронные тесты 2
    test_cache_functionality()
    test_stats_functionality()
    
    print("=" * 50)
    print("🎉 Все smoke-тесты завершены!") 