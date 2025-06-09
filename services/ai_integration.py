"""
AI Integration Service с официальным DeepSeek SDK
Продвинутая интеграция для OF Assistant Bot
"""

import asyncio
import logging
from typing import Optional, Dict, Any, List
from datetime import datetime
import json

try:
    from deepseek import DeepSeek
    DEEPSEEK_AVAILABLE = True
except ImportError:
    DEEPSEEK_AVAILABLE = False
    logging.warning("⚠️ deepseek-sdk не установлен. Использую fallback через aiohttp")

import aiohttp
from config import config
from enhanced_logging import BotLogger

logger = BotLogger(
    log_dir="logs",
    log_file="ai_integration.log",
    logger_name="AIIntegration"
)

class AIService:
    """Продвинутый AI сервис с DeepSeek SDK"""
    
    def __init__(self):
        """Инициализация AI сервиса"""
        self.api_key = config.DEEPSEEK_API_KEY
        self.model = "deepseek-chat"
        self.client = None
        
        if not self.api_key:
            logger.log_error("❌ DEEPSEEK_API_KEY не найден!")
            raise ValueError("DEEPSEEK_API_KEY обязателен для работы")
        
        # Инициализация клиента
        if DEEPSEEK_AVAILABLE:
            try:
                self.client = DeepSeek(api_key=self.api_key)
                logger.log_info("✅ DeepSeek SDK клиент инициализирован")
            except Exception as e:
                logger.log_error(f"❌ Ошибка инициализации DeepSeek SDK: {e}")
                self.client = None
        
        if not self.client:
            logger.log_info("🔄 Использую HTTP API fallback")
        
        # Кэш ответов
        self.response_cache = {}
        self.cache_ttl = 300  # 5 минут
        
        # Статистика
        self.stats = {
            "total_requests": 0,
            "successful_requests": 0,
            "failed_requests": 0,
            "cache_hits": 0
        }
    
    async def get_response(self, prompt: str, context: Optional[Dict] = None) -> str:
        """
        Получение ответа от DeepSeek AI
        
        Args:
            prompt: Запрос пользователя
            context: Дополнительный контекст
            
        Returns:
            Ответ от AI
        """
        self.stats["total_requests"] += 1
        
        # Проверка кэша
        cache_key = self._get_cache_key(prompt, context)
        cached_response = self._get_cached_response(cache_key)
        if cached_response:
            self.stats["cache_hits"] += 1
            logger.log_info(f"💾 Возвращен кэшированный ответ")
            return cached_response
        
        try:
            # Построение сообщений
            messages = self._build_messages(prompt, context)
            
            # Получение ответа
            if self.client and DEEPSEEK_AVAILABLE:
                response = await self._get_sdk_response(messages)
            else:
                response = await self._get_http_response(messages)
            
            # Кэширование
            self._cache_response(cache_key, response)
            
            self.stats["successful_requests"] += 1
            logger.log_info(f"✅ AI ответ получен (длина: {len(response)})")
            return response
            
        except Exception as e:
            self.stats["failed_requests"] += 1
            logger.log_error(f"💥 Ошибка AI запроса: {e}")
            return self._get_fallback_response(prompt, context)
    
    async def generate_flirt_response(self, user_message: str, user_context: Dict[str, Any] = None) -> str:
        """Специализированный метод для флирта"""
        
        system_prompt = """Ты - соблазнительная модель OnlyFans. 
        Отвечай кокетливо, игриво и сексуально. Поддерживай интерес к эксклюзивному контенту.
        Используй эмодзи, будь дерзкой но элегантной."""
        
        context = {
            "type": "flirt",
            "system_prompt": system_prompt,
            "user_context": user_context or {}
        }
        
        enhanced_prompt = f"""
        Сообщение: "{user_message}"
        
        Создай соблазнительный ответ:
        - Отвечающий на сообщение
        - Поддерживающий флирт  
        - Мотивирующий на покупку контента
        - Естественный и сексуальный
        """
        
        return await self.get_response(enhanced_prompt, context)
    
    async def generate_ppv_content(self, content_type: str, price: int, description: str) -> str:
        """Генерация промо для PPV контента"""
        
        prompt = f"""
        Создай соблазнительное описание для PPV контента:
        Тип: {content_type}
        Цена: ${price}
        Описание: {description}
        
        Сделай текст максимально возбуждающим и продающим!
        """
        
        context = {"type": "ppv_promo", "content_type": content_type, "price": price}
        return await self.get_response(prompt, context)
    
    def _build_messages(self, prompt: str, context: Optional[Dict] = None) -> List[Dict]:
        """Построение сообщений для API"""
        messages = []
        
        # Системный промпт
        if context and context.get("system_prompt"):
            messages.append({
                "role": "system",
                "content": context["system_prompt"]
            })
        else:
            # Базовый системный промпт
            messages.append({
                "role": "system", 
                "content": "Ты умный ассистент для OnlyFans модели. Отвечай живо и интересно."
            })
        
        # Пользовательское сообщение
        messages.append({
            "role": "user",
            "content": prompt
        })
        
        return messages
    
    async def _get_sdk_response(self, messages: List[Dict]) -> str:
        """Получение ответа через SDK"""
        try:
            response = await asyncio.to_thread(
                self.client.chat,
                model=self.model,
                messages=messages,
                temperature=0.8,
                max_tokens=500
            )
            return response.choices[0].message.content
            
        except Exception as e:
            logger.log_error(f"❌ SDK ошибка: {e}")
            raise
    
    async def _get_http_response(self, messages: List[Dict]) -> str:
        """Fallback через HTTP API"""
        url = "https://api.deepseek.com/v1/chat/completions"
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "model": self.model,
            "messages": messages,
            "temperature": 0.8,
            "max_tokens": 500
        }
        
        async with aiohttp.ClientSession() as session:
            async with session.post(url, json=payload, headers=headers) as response:
                if response.status != 200:
                    error_text = await response.text()
                    raise Exception(f"HTTP {response.status}: {error_text}")
                
                result = await response.json()
                return result["choices"][0]["message"]["content"]
    
    def _get_cache_key(self, prompt: str, context: Optional[Dict] = None) -> str:
        """Генерация ключа кэша"""
        context_str = json.dumps(context, sort_keys=True) if context else ""
        return f"{hash(prompt + context_str)}"
    
    def _get_cached_response(self, cache_key: str) -> Optional[str]:
        """Получение из кэша"""
        if cache_key in self.response_cache:
            cached_time, response = self.response_cache[cache_key]
            if (datetime.now().timestamp() - cached_time) < self.cache_ttl:
                return response
            else:
                del self.response_cache[cache_key]
        return None
    
    def _cache_response(self, cache_key: str, response: str):
        """Кэширование ответа"""
        self.response_cache[cache_key] = (datetime.now().timestamp(), response)
        
        # Очистка старого кэша
        current_time = datetime.now().timestamp()
        expired_keys = [
            key for key, (cached_time, _) in self.response_cache.items()
            if (current_time - cached_time) > self.cache_ttl
        ]
        for key in expired_keys:
            del self.response_cache[key]
    
    def _get_fallback_response(self, prompt: str, context: Optional[Dict] = None) -> str:
        """Fallback ответ при ошибках"""
        if context and context.get("type") == "flirt":
            return "😘 Извини, малыш, что-то я задумалась... Напиши мне еще раз?"
        elif context and context.get("type") == "ppv_promo":
            return "🔥 Горячий контент скоро будет готов! Следи за обновлениями! 💕"
        else:
            return "Извини, произошла техническая ошибка. Попробуй еще раз!"
    
    def get_stats(self) -> Dict[str, Any]:
        """Получение статистики работы"""
        return {
            **self.stats,
            "cache_size": len(self.response_cache),
            "success_rate": round(
                (self.stats["successful_requests"] / max(self.stats["total_requests"], 1)) * 100, 
                2
            )
        }
    
    def clear_cache(self):
        """Очистка кэша"""
        self.response_cache.clear()
        logger.log_info("🗑️ Кэш очищен")

# Глобальный экземпляр
ai_service = AIService() 