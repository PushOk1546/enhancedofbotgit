"""
DeepSeek-R1 API Handler
Интеграция с DeepSeek AI для OF Assistant Bot
"""

import aiohttp
import asyncio
import json
from typing import Optional, Dict, Any
from config import config
from enhanced_logging import BotLogger

logger = BotLogger(
    log_dir="logs",
    log_file="deepseek_api.log",
    logger_name="DeepSeekAPI"
)

class DeepSeekAPIHandler:
    """Обработчик DeepSeek-R1 API"""
    
    def __init__(self):
        deepseek_config = config.get_deepseek_config()
        self.api_key = deepseek_config.get('api_key')
        self.base_url = deepseek_config.get('base_url', 'https://api.deepseek.com')
        self.model = deepseek_config.get('model', 'deepseek-chat')
        
        if not self.api_key:
            logger.log_error("❌ DEEPSEEK_API_KEY не найден в конфигурации!")
            raise ValueError("DEEPSEEK_API_KEY обязателен для работы с DeepSeek")
        
        logger.log_info("✅ DeepSeek API Handler инициализирован")

    async def ask_deepseek(self, prompt: str, system_prompt: str = None) -> str:
        """
        Отправка запроса к DeepSeek-R1
        
        Args:
            prompt: Пользовательский запрос
            system_prompt: Системный промпт (опционально)
            
        Returns:
            Ответ от DeepSeek-R1
        """
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})
        
        payload = {
            "model": self.model,
            "messages": messages,
            "temperature": 0.7,
            "max_tokens": 1000
        }
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{self.base_url}/chat/completions",
                    json=payload,
                    headers=headers,
                    timeout=aiohttp.ClientTimeout(total=30)
                ) as response:
                    
                    if response.status != 200:
                        error_text = await response.text()
                        logger.log_error(f"❌ DeepSeek API ошибка {response.status}: {error_text}")
                        return "Извините, произошла ошибка при обращении к AI"
                    
                    result = await response.json()
                    content = result['choices'][0]['message']['content']
                    
                    logger.log_info(f"✅ DeepSeek ответил успешно (длина: {len(content)} символов)")
                    return content
                    
        except asyncio.TimeoutError:
            logger.log_error("⏰ Таймаут запроса к DeepSeek API")
            return "Извините, AI не отвечает. Попробуйте позже."
        except Exception as e:
            logger.log_error(f"💥 Ошибка DeepSeek API: {str(e)}")
            return "Произошла техническая ошибка"

    async def generate_flirt_response(self, user_message: str, context: Dict[str, Any] = None) -> str:
        """Генерация флиртового ответа для OF модели"""
        
        system_prompt = """Ты - профессиональная модель OnlyFans. Отвечай кокетливо, 
        игриво и соблазнительно. Поддерживай интерес подписчика, намекай на эксклюзивный 
        контент. Будь дерзкой, но элегантной. Используй эмодзи."""
        
        enhanced_prompt = f"""
        Сообщение подписчика: "{user_message}"
        
        Контекст: {json.dumps(context, ensure_ascii=False) if context else "Новый диалог"}
        
        Создай соблазнительный ответ, который:
        1. Отвечает на сообщение 
        2. Поддерживает флирт
        3. Мотивирует на покупку контента
        4. Звучит естественно и сексуально
        """
        
        return await self.ask_deepseek(enhanced_prompt, system_prompt)

    async def generate_response_with_style(self, user_message: str, style: str, context: Dict[str, Any] = None, variant_number: int = 1) -> str:
        """Генерация ответа в определенном стиле"""
        
        style_prompts = {
            'friendly': {
                'system': 'Ты дружелюбная и позитивная девушка. Отвечай тепло, с улыбкой, поддерживающе.',
                'tone': 'дружелюбно и позитивно'
            },
            'flirty': {
                'system': 'Ты кокетливая и игривая девушка. Отвечай флиртующе, с легкими намеками и игривостью.',
                'tone': 'кокетливо и игриво'
            },
            'passionate': {
                'system': 'Ты страстная и эмоциональная девушка. Отвечай горячо, с чувствами и желанием.',
                'tone': 'страстно и эмоционально'
            },
            'romantic': {
                'system': 'Ты романтичная и нежная девушка. Отвечай мягко, с романтикой и теплотой.',
                'tone': 'романтично и нежно'
            },
            'professional': {
                'system': 'Ты профессиональная модель OnlyFans. Отвечай уверенно, но вежливо.',
                'tone': 'профессионально и уверенно'
            }
        }
        
        style_config = style_prompts.get(style, style_prompts['friendly'])
        
        enhanced_prompt = f"""
        Сообщение: "{user_message}"
        
        Отвечай {style_config['tone']}. Вариант ответа #{variant_number}.
        
        Требования:
        1. Ответ должен быть естественным
        2. Длина 1-3 предложения
        3. Используй подходящие эмодзи
        4. Поддерживай диалог
        5. Будь {style_config['tone']}
        
        Контекст пользователя: {context.get('first_name', 'Незнакомец')} (@{context.get('username', 'anonymous')})
        """
        
        try:
            response = await self.ask_deepseek(enhanced_prompt, style_config['system'])
            return response.strip()
        except Exception as e:
            logger.log_error(f"💥 Ошибка генерации стиля {style}: {e}")
            # Fallback ответы
            fallback_responses = {
                'friendly': f"Привет! Спасибо за сообщение! 😊",
                'flirty': f"Ой, какой ты интересный... 😘💕",
                'passionate': f"Ммм, мне нравится как ты пишешь! 🔥",
                'romantic': f"Какой ты милый... 💕✨",
                'professional': f"Спасибо за ваше сообщение! 😊"
            }
            return fallback_responses.get(style, "Спасибо за сообщение! 😊")

# Глобальный экземпляр
deepseek_handler = DeepSeekAPIHandler() 