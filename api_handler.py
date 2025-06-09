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

# Глобальный экземпляр
deepseek_handler = DeepSeekAPIHandler() 