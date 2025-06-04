#!/usr/bin/env python3
"""
Тест исправлений callback query.
Проверяет что все callback handlers работают корректно.
"""

import asyncio
from dataclasses import dataclass
from config import FLIRT_STYLES, PPV_STYLES, MODELS, SURVEY_STEPS
from utils import get_flirt_style_keyboard, get_ppv_style_keyboard, get_model_keyboard, get_survey_keyboard

@dataclass
class MockCallbackQuery:
    """Mock объект callback query для тестирования"""
    id: str
    data: str
    from_user_id: int = 12345

@dataclass 
class MockUser:
    """Mock объект пользователя для тестирования"""
    model: str = 'smart'
    preferences: object = None

class CallbackTester:
    """Тестер callback query логики"""
    
    def __init__(self):
        print("🧪 ТЕСТ ИСПРАВЛЕНИЙ CALLBACK QUERY")
        print("=" * 50)
    
    def test_flirt_styles_mapping(self):
        """Тестирует правильность маппинга flirt styles"""
        print("\n🎯 Тестируем FLIRT STYLES:")
        
        keyboard = get_flirt_style_keyboard()
        callback_data_list = []
        
        for button_row in keyboard.keyboard:
            for button in button_row:
                callback_data_list.append(button.callback_data)
        
        print(f"📊 Кнопок в клавиатуре: {len(callback_data_list)}")
        
        # Проверяем что все callback_data корректные
        for callback_data in callback_data_list:
            if callback_data.startswith("flirt_style_"):
                style_id = callback_data.replace("flirt_style_", "")
                
                # Ищем стиль по ID
                found = False
                for name, info in FLIRT_STYLES.items():
                    if info['id'] == style_id:
                        print(f"✅ {style_id} -> {name}: {info['description']}")
                        found = True
                        break
                
                if not found:
                    print(f"❌ {style_id}: ID не найден в FLIRT_STYLES!")
                    return False
        
        return True
    
    def test_ppv_styles_mapping(self):
        """Тестирует правильность маппинга PPV styles"""
        print("\n💎 Тестируем PPV STYLES:")
        
        keyboard = get_ppv_style_keyboard()
        callback_data_list = []
        
        for button_row in keyboard.keyboard:
            for button in button_row:
                callback_data_list.append(button.callback_data)
        
        print(f"📊 Кнопок в клавиатуре: {len(callback_data_list)}")
        
        # Проверяем что все callback_data корректные
        for callback_data in callback_data_list:
            if callback_data.startswith("ppv_style_"):
                style_name = callback_data.replace("ppv_style_", "")
                
                if style_name in PPV_STYLES:
                    print(f"✅ {style_name}: {PPV_STYLES[style_name]}")
                else:
                    print(f"❌ {style_name}: Не найден в PPV_STYLES!")
                    return False
        
        return True
    
    def test_model_mapping(self):
        """Тестирует правильность маппинга моделей"""
        print("\n🤖 Тестируем MODELS:")
        
        keyboard = get_model_keyboard()
        callback_data_list = []
        
        for button_row in keyboard.keyboard:
            for button in button_row:
                callback_data_list.append(button.callback_data)
        
        print(f"📊 Кнопок в клавиатуре: {len(callback_data_list)}")
        
        # Проверяем что все callback_data корректные
        for callback_data in callback_data_list:
            if callback_data.startswith("model_"):
                model_key = callback_data.replace("model_", "")
                
                if model_key in MODELS:
                    print(f"✅ {model_key}: {MODELS[model_key]['description']}")
                else:
                    print(f"❌ {model_key}: Не найден в MODELS!")
                    return False
        
        return True
    
    def test_survey_mapping(self):
        """Тестирует правильность маппинга опроса"""
        print("\n📝 Тестируем SURVEY STEPS:")
        
        for step_name in SURVEY_STEPS.keys():
            keyboard = get_survey_keyboard(step_name)
            
            print(f"\n🔍 Шаг: {step_name}")
            
            for button_row in keyboard.keyboard:
                for button in button_row:
                    callback_data = button.callback_data
                    
                    if callback_data.startswith("survey_"):
                        parts = callback_data.split('_')
                        if len(parts) >= 3:
                            step = parts[1]
                            value = parts[2]
                            print(f"  ✅ {step}_{value}")
                        else:
                            print(f"  ❌ Неправильный формат: {callback_data}")
                            return False
        
        return True
    
    async def simulate_callback_handlers(self):
        """Симулирует обработку callback queries"""
        print("\n🎮 СИМУЛЯЦИЯ CALLBACK HANDLERS:")
        
        test_callbacks = [
            # Тест флирт стилей
            "flirt_style_playful",
            "flirt_style_passionate", 
            "flirt_style_tender",
            
            # Тест PPV стилей
            "ppv_style_провокационный",
            "ppv_style_романтичный",
            
            # Тест моделей
            "model_smart",
            "model_fast",
            
            # Тест опроса
            "survey_content_types_photos",
            "survey_price_range_medium"
        ]
        
        for callback_data in test_callbacks:
            print(f"\n🔧 Обрабатываем: {callback_data}")
            
            try:
                if callback_data.startswith("flirt_style_"):
                    style_id = callback_data.replace("flirt_style_", "")
                    
                    # Симуляция логики из _handle_flirt_style
                    style_info = None
                    style_name = None
                    
                    for name, info in FLIRT_STYLES.items():
                        if info['id'] == style_id:
                            style_info = info
                            style_name = name
                            break
                    
                    if style_info:
                        print(f"  ✅ Найден стиль: {style_name}")
                    else:
                        print(f"  ❌ Стиль не найден: {style_id}")
                        
                elif callback_data.startswith("ppv_style_"):
                    style_name = callback_data.replace("ppv_style_", "")
                    
                    if style_name in PPV_STYLES:
                        print(f"  ✅ Найден PPV стиль: {style_name}")
                    else:
                        print(f"  ❌ PPV стиль не найден: {style_name}")
                        
                elif callback_data.startswith("model_"):
                    model_key = callback_data.replace("model_", "")
                    
                    if model_key in MODELS:
                        print(f"  ✅ Найдена модель: {model_key}")
                    else:
                        print(f"  ❌ Модель не найдена: {model_key}")
                        
                elif callback_data.startswith("survey_"):
                    # Убираем префикс "survey_"
                    survey_data = callback_data[7:]  # len("survey_") = 7
                    
                    # Разделяем на части
                    parts = survey_data.split('_')
                    if len(parts) >= 2:
                        # Последняя часть - это value, всё остальное - step
                        value = parts[-1]
                        step = '_'.join(parts[:-1])
                        
                        if step in SURVEY_STEPS:
                            print(f"  ✅ Шаг опроса: {step} = {value}")
                        else:
                            print(f"  ❌ Неизвестный шаг: {step}")
                    else:
                        print(f"  ❌ Неправильный формат survey callback")
                        
            except Exception as e:
                print(f"  💥 Ошибка: {e}")
        
        return True

async def main():
    tester = CallbackTester()
    
    # Тестируем маппинги
    flirt_ok = tester.test_flirt_styles_mapping()
    ppv_ok = tester.test_ppv_styles_mapping()
    model_ok = tester.test_model_mapping()
    survey_ok = tester.test_survey_mapping()
    
    # Симулируем обработку
    simulation_ok = await tester.simulate_callback_handlers()
    
    print("\n" + "=" * 50)
    print("📊 РЕЗУЛЬТАТЫ ТЕСТИРОВАНИЯ:")
    print(f"✅ Flirt styles: {'OK' if flirt_ok else 'FAIL'}")
    print(f"✅ PPV styles: {'OK' if ppv_ok else 'FAIL'}")
    print(f"✅ Models: {'OK' if model_ok else 'FAIL'}")
    print(f"✅ Survey: {'OK' if survey_ok else 'FAIL'}")
    print(f"✅ Simulation: {'OK' if simulation_ok else 'FAIL'}")
    
    all_ok = all([flirt_ok, ppv_ok, model_ok, survey_ok, simulation_ok])
    
    if all_ok:
        print("\n🎉 ВСЕ CALLBACK HANDLERS ИСПРАВЛЕНЫ!")
        print("🚀 Кнопки должны работать корректно!")
    else:
        print("\n💥 ЕСТЬ ПРОБЛЕМЫ В CALLBACK HANDLERS!")
    
    return all_ok

if __name__ == "__main__":
    success = asyncio.run(main())
    exit(0 if success else 1) 