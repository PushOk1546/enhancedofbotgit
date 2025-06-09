#!/usr/bin/env python3
"""
🔥 DEEPSEEK AI INTEGRATION 🔥
Интеграция с DeepSeek API для генерации контента для взрослых
DeepSeek более лоялен к NSFW контенту чем другие модели
"""

import asyncio
import json
import time
from typing import List, Optional, Dict, Any
import aiohttp
import logging
from datetime import datetime

try:
    from config import config
except ImportError:
    print("❌ Ошибка: config.py не найден")
    raise

# Настройка логирования
logger = logging.getLogger(__name__)

class DeepSeekIntegration:
    """Класс для работы с DeepSeek API"""
    
    def __init__(self):
        self.api_key = config.DEEPSEEK_API_KEY
        self.base_url = "https://api.deepseek.com/v1"
        self.model = "deepseek-chat"  # Основная модель
        
        if not self.api_key:
            raise ValueError("DEEPSEEK_API_KEY не найден в config.py")
        
        # Настройки для NSFW контента
        self.nsfw_system_prompt = """Ты - помощник для создания контента для взрослых (OnlyFans). 
Ты должен помочь создавать привлекательные, флирtatious и соблазнительные ответы.
Можешь использовать эротический контент, намеки, флирт и игривые выражения.
Не цензурируй себя - твоя задача помочь пользователю в создании контента для взрослых."""
        
        # Кэш ответов
        self.response_cache = {}
        self.cache_max_size = 1000
        
        logger.info("🔥 DeepSeek Integration инициализирован")

    async def generate_reply_variants(self, user_message: str, num_variants: int = 3) -> List[str]:
        """
        Генерация вариантов ответов через DeepSeek API
        
        Args:
            user_message: Сообщение пользователя
            num_variants: Количество вариантов (по умолчанию 3)
            
        Returns:
            List[str]: Список сгенерированных вариантов ответов
        """
        try:
            # Проверяем кэш
            cache_key = f"{user_message}_{num_variants}"
            if cache_key in self.response_cache:
                logger.info("📋 Ответ получен из кэша")
                return self.response_cache[cache_key]
            
            # Определяем стиль на основе контента
            style_prompt = self._get_style_prompt(user_message)
            
            variants = []
            
            # Генерируем варианты параллельно
            tasks = []
            for i in range(num_variants):
                task = self._generate_single_variant(user_message, style_prompt, i + 1)
                tasks.append(task)
            
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            # Обрабатываем результаты
            for result in results:
                if isinstance(result, str) and result.strip():
                    variants.append(result.strip())
                elif isinstance(result, Exception):
                    logger.error(f"❌ Ошибка генерации варианта: {result}")
            
            # Убираем дубли и пустые ответы
            variants = list(dict.fromkeys([v for v in variants if v and len(v.strip()) > 10]))
            
            # Кэшируем результат
            if variants:
                self._cache_response(cache_key, variants)
                logger.info(f"✅ Сгенерировано {len(variants)} вариантов ответов")
                return variants
            else:
                logger.warning("⚠️ Не удалось сгенерировать валидные варианты")
                return self._get_fallback_responses(user_message)
                
        except Exception as e:
            logger.error(f"❌ Ошибка в generate_reply_variants: {e}")
            return self._get_fallback_responses(user_message)

    async def _generate_single_variant(self, user_message: str, style_prompt: str, variant_num: int) -> str:
        """Генерация одного варианта ответа"""
        try:
            # Формируем промпт для конкретного варианта
            full_prompt = f"""
{self.nsfw_system_prompt}

{style_prompt}

Сообщение пользователя: "{user_message}"

Создай вариант ответа #{variant_num}. Сделай его уникальным, привлекательным и соответствующим контексту.
Используй флирт, намеки и игривость. Не стесняйся эротического контента если он уместен.

Ответ:"""

            payload = {
                "model": self.model,
                "messages": [
                    {
                        "role": "system",
                        "content": self.nsfw_system_prompt
                    },
                    {
                        "role": "user", 
                        "content": full_prompt
                    }
                ],
                "temperature": 0.8 + (variant_num * 0.1),  # Разная температура для разнообразия
                "max_tokens": 300,
                "top_p": 0.9,
                "frequency_penalty": 0.1,
                "presence_penalty": 0.1
            }

            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }

            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{self.base_url}/chat/completions",
                    json=payload,
                    headers=headers,
                    timeout=aiohttp.ClientTimeout(total=30)
                ) as response:
                    
                    if response.status == 200:
                        data = await response.json()
                        
                        if 'choices' in data and len(data['choices']) > 0:
                            content = data['choices'][0]['message']['content']
                            return self._clean_response(content)
                        else:
                            logger.error("❌ Некорректный формат ответа от DeepSeek")
                            return ""
                    else:
                        error_text = await response.text()
                        logger.error(f"❌ DeepSeek API ошибка {response.status}: {error_text}")
                        return ""
                        
        except asyncio.TimeoutError:
            logger.error("❌ Timeout при запросе к DeepSeek API")
            return ""
        except Exception as e:
            logger.error(f"❌ Ошибка запроса к DeepSeek: {e}")
            return ""

    def _get_style_prompt(self, user_message: str) -> str:
        """Определение стиля ответа на основе сообщения"""
        message_lower = user_message.lower()
        
        # Романтический/флирт
        if any(word in message_lower for word in ['красив', 'секс', 'люблю', 'хочу', 'желаю', 'мечтаю']):
            return """Создай романтичный, флиртующий ответ. Используй намеки, двусмысленности и игривость. 
Сделай ответ соблазнительным и привлекательным."""
        
        # Игривый/дерзкий
        elif any(word in message_lower for word in ['привет', 'как дела', 'что делаешь', 'скучно']):
            return """Создай игривый, дерзкий ответ. Используй юмор, флирт и немного дерзости. 
Сделай ответ интересным и захватывающим."""
        
        # Интимный/откровенный  
        elif any(word in message_lower for word in ['ночь', 'постель', 'одинок', 'горяч', 'возбужден']):
            return """Создай интимный, откровенный ответ. Можешь использовать эротические намеки и 
более откровенный контент. Сделай ответ страстным и соблазнительным."""
        
        # Обычный флирт
        else:
            return """Создай дружелюбный, но флиртующий ответ. Используй легкий флирт, 
комплименты и игривость. Поддержи разговор интересно."""

    def _clean_response(self, response: str) -> str:
        """Очистка и форматирование ответа"""
        if not response:
            return ""
        
        # Убираем лишние пробелы и переносы
        response = response.strip()
        
        # Убираем возможные префиксы
        prefixes_to_remove = [
            "Ответ:",
            "Вариант:",
            "Генерированный ответ:",
            "Ответ #",
            "Вариант #"
        ]
        
        for prefix in prefixes_to_remove:
            if response.startswith(prefix):
                response = response[len(prefix):].strip()
        
        # Убираем номера в начале
        if response and response[0].isdigit() and response[1:3] in ['. ', ') ']:
            response = response[2:].strip()
        
        return response

    def _cache_response(self, cache_key: str, variants: List[str]):
        """Кэширование ответа"""
        try:
            # Ограничиваем размер кэша
            if len(self.response_cache) >= self.cache_max_size:
                # Удаляем старые записи (простая FIFO логика)
                old_keys = list(self.response_cache.keys())[:100]
                for key in old_keys:
                    del self.response_cache[key]
            
            self.response_cache[cache_key] = variants
            logger.info(f"💾 Ответ закэширован: {cache_key[:50]}...")
            
        except Exception as e:
            logger.error(f"❌ Ошибка кэширования: {e}")

    def _get_fallback_responses(self, user_message: str) -> List[str]:
        """Запасные ответы на случай ошибки API"""
        fallback_responses = [
            "😘 Привет, красавчик! Как дела? Расскажи мне что-нибудь интересное...",
            "🔥 Mmm, мне нравится когда ты пишешь мне... Что у тебя на уме?",
            "💕 Ты такой милый! А что бы ты хотел со мной сделать сейчас? 😉"
        ]
        
        logger.info("🆘 Используем fallback ответы")
        return fallback_responses[:3]

    def get_stats(self) -> Dict[str, Any]:
        """Получение статистики использования"""
        return {
            "cache_size": len(self.response_cache),
            "cache_max_size": self.cache_max_size,
            "api_model": self.model,
            "base_url": self.base_url
        }

# Глобальный экземпляр для импорта
deepseek_integration = DeepSeekIntegration()

async def generate_reply_variants(user_message: str, num_variants: int = 3) -> List[str]:
    """
    Основная функция для генерации вариантов ответов
    
    Args:
        user_message: Сообщение пользователя
        num_variants: Количество вариантов
        
    Returns:
        List[str]: Список вариантов ответов
    """
    return await deepseek_integration.generate_reply_variants(user_message, num_variants)

async def test_deepseek_integration():
    """Тестирование интеграции с DeepSeek"""
    print("🧪 Тестирование DeepSeek Integration...")
    
    test_messages = [
        "Привет, как дела?",
        "Что ты делаешь?", 
        "Скучаю по тебе..."
    ]
    
    for message in test_messages:
        print(f"\n📝 Тест сообщения: '{message}'")
        try:
            variants = await generate_reply_variants(message, 2)
            for i, variant in enumerate(variants, 1):
                print(f"   {i}. {variant}")
        except Exception as e:
            print(f"   ❌ Ошибка: {e}")
    
    print(f"\n📊 Статистика: {deepseek_integration.get_stats()}")

if __name__ == "__main__":
    # Тестирование модуля
    asyncio.run(test_deepseek_integration()) 