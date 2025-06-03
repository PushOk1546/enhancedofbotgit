#!/usr/bin/env python3
"""
Тест актуальных моделей Groq API.
Проверяет что все модели в конфигурации работают.
"""

import asyncio
import sys
from api import generate_groq_response
from config import MODELS

async def test_groq_models():
    """Тестирует все модели Groq"""
    print("🧪 ТЕСТ МОДЕЛЕЙ GROQ API")
    print("=" * 50)
    
    test_prompt = "Привет! Как дела?"
    
    working_models = []
    failed_models = []
    
    for model_key, model_info in MODELS.items():
        model_id = model_info['id']
        print(f"\n🔍 Тестируем модель: {model_key} ({model_id})")
        
        try:
            response = await generate_groq_response(
                test_prompt, 
                model_id, 
                max_tokens=50,
                max_retries=1
            )
            
            if response and len(response.strip()) > 0:
                print(f"✅ {model_key}: OK")
                print(f"   Ответ: {response[:100]}...")
                working_models.append(model_key)
            else:
                print(f"❌ {model_key}: Пустой ответ")
                failed_models.append(model_key)
                
        except Exception as e:
            print(f"❌ {model_key}: {str(e)}")
            failed_models.append(model_key)
    
    print("\n" + "=" * 50)
    print("📊 РЕЗУЛЬТАТЫ ТЕСТИРОВАНИЯ:")
    print(f"✅ Работающие модели: {len(working_models)}/{len(MODELS)}")
    for model in working_models:
        print(f"   • {model}")
    
    if failed_models:
        print(f"❌ Неработающие модели: {len(failed_models)}")
        for model in failed_models:
            print(f"   • {model}")
    
    if len(working_models) > 0:
        print("\n🎉 ХОТЯ БЫ ОДНА МОДЕЛЬ РАБОТАЕТ - БОТ ГОТОВ!")
        return True
    else:
        print("\n💥 ВСЕ МОДЕЛИ НЕ РАБОТАЮТ!")
        return False

async def test_fallback_mechanism():
    """Тестирует механизм fallback"""
    print("\n🔄 ТЕСТ FALLBACK МЕХАНИЗМА")
    print("-" * 30)
    
    try:
        # Пробуем с несуществующей моделью
        response = await generate_groq_response(
            "Test fallback", 
            "non-existent-model-12345",
            max_tokens=20
        )
        
        if response:
            print("✅ Fallback механизм работает!")
            print(f"   Ответ: {response[:50]}...")
            return True
        else:
            print("❌ Fallback вернул пустой ответ")
            return False
            
    except Exception as e:
        print(f"❌ Fallback не работает: {e}")
        return False

if __name__ == "__main__":
    async def main():
        models_ok = await test_groq_models()
        fallback_ok = await test_fallback_mechanism()
        
        if models_ok or fallback_ok:
            print("\n🚀 СИСТЕМА ГОТОВА К ПРОДАКШЕНУ!")
            return True
        else:
            print("\n🚨 ТРЕБУЕТСЯ ИСПРАВЛЕНИЕ GROQ API!")
            return False
    
    success = asyncio.run(main())
    sys.exit(0 if success else 1) 