"""
Groq API интеграция для OF Assistant Bot
Обеспечивает AI-генерацию контента с использованием Llama модели
"""

import os
import asyncio
from typing import List, Optional, Dict, Any
import logging
from groq import AsyncGroq
from cachetools import TTLCache
import ujson as json

# Импорт кастомных исключений
from app.core.error_handler import (
    GroqApiError, 
    InvalidUserInputError, 
    InputValidator,
    ErrorHandler
)

# Импорт логгера
try:
    from enhanced_logging import bot_logger
except ImportError:
    import logging
    bot_logger = logging.getLogger(__name__)

# Инициализация обработчика ошибок
error_handler = ErrorHandler(bot_logger)

class GroqContentGenerator:
    """Генератор контента на базе Groq API"""
    
    def __init__(self, api_key: str = None):
        try:
            self.api_key = api_key or os.getenv('GROQ_KEY') or os.getenv('GROQ_API_KEY')
            if not self.api_key:
                raise GroqApiError(
                    "GROQ_API_KEY не найден в переменных окружения",
                    status_code=None,
                    api_response="Missing API key"
                )
            
            # Инициализация клиента с обработкой ошибок
            try:
                self.client = AsyncGroq(api_key=self.api_key)
                self.model = "llama3-70b-8192"  # Основная модель
            except Exception as e:
                raise GroqApiError(
                    f"Ошибка инициализации Groq клиента: {str(e)}",
                    api_response=str(e)
                )
            
            # Кэш для ответов (TTL = 1 час)
            self.reply_cache = TTLCache(maxsize=1000, ttl=3600)
            self.ppv_cache = TTLCache(maxsize=500, ttl=3600)
            self.hot_cache = TTLCache(maxsize=500, ttl=3600)
            
            bot_logger.log_info("Groq Content Generator успешно инициализирован")
            
        except Exception as e:
            bot_logger.log_error(f"Ошибка инициализации GroqContentGenerator: {e}")
            if not isinstance(e, GroqApiError):
                raise GroqApiError(f"Неожиданная ошибка инициализации: {str(e)}")
            raise
    
    def _get_cache_key(self, text: str, style: str = None) -> str:
        """Генерация ключа для кэша"""
        try:
            import hashlib
            content = f"{text}:{style}" if style else text
            return hashlib.md5(content.encode()).hexdigest()[:16]
        except Exception as e:
            bot_logger.log_warning(f"Ошибка генерации ключа кэша: {e}")
            return f"{text}:{style}" if style else text
    
    async def generate_reply_variants(self, user_text: str, style: str = 'friendly') -> List[str]:
        """Генерация 3 вариантов ответа на сообщение клиента с обработкой ошибок"""
        
        try:
            # Валидация входных данных
            InputValidator.validate_message_length(user_text, max_length=500)
            InputValidator.validate_style(style)
            
            bot_logger.log_api_call(f"Groq API вызов для генерации ответов", {
                "style": style,
                "text_length": len(user_text)
            })
            
            # Проверяем кэш
            cache_key = self._get_cache_key(user_text, style)
            if cache_key in self.reply_cache:
                bot_logger.log_info("Использование кэшированных вариантов ответов")
                return self.reply_cache[cache_key]
            
            # Генерация промптов
            style_prompts = {
                'friendly': "Дружелюбный и теплый тон, как подруга",
                'flirty': "Легкий флирт, игривый и привлекательный тон",
                'passionate': "Страстный и эмоциональный тон с намеками",
                'romantic': "Романтичный и нежный тон",
                'professional': "Вежливый и профессиональный тон"
            }
            
            system_prompt = f"""Ты - привлекательная OnlyFans модель, которая отвечает на сообщения клиентов.

ЗАДАЧА: Создай 3 разных варианта ответа на сообщение клиента.

СТИЛЬ: {style_prompts.get(style, style_prompts['friendly'])}

ТРЕБОВАНИЯ:
- Каждый вариант должен быть уникальным
- Используй эмодзи умеренно (1-2 на вариант)
- Длина: 1-2 предложения
- Будь естественной и живой
- Поощряй дальнейшее общение

ФОРМАТ ОТВЕТА:
Вариант 1: [текст]
Вариант 2: [текст]  
Вариант 3: [текст]"""

            user_prompt = f"Сообщение клиента: {user_text}"
            
            # API вызов с обработкой ошибок
            try:
                response = await self.client.chat.completions.create(
                    model=self.model,
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_prompt}
                    ],
                    max_tokens=200,
                    temperature=0.8
                )
                
                if not response or not response.choices:
                    raise GroqApiError(
                        "Пустой ответ от Groq API", 
                        api_response="Empty response"
                    )
                
                content = response.choices[0].message.content.strip()
                variants = self._parse_variants(content)
                
                if len(variants) < 3:
                    bot_logger.log_warning("Парсинг не дал 3 варианта, используем fallback")
                    variants = self._fallback_variants(user_text, style)
                
                # Сохраняем в кэш
                self.reply_cache[cache_key] = variants
                bot_logger.log_info(f"Сгенерировано {len(variants)} вариантов ответов")
                return variants
                
            except Exception as api_error:
                if "rate_limit" in str(api_error).lower():
                    raise GroqApiError(
                        "Превышен лимит запросов к API",
                        api_response=str(api_error)
                    )
                elif "unauthorized" in str(api_error).lower():
                    raise GroqApiError(
                        "Неверный API ключ",
                        status_code=401,
                        api_response=str(api_error)
                    )
                else:
                    raise GroqApiError(
                        f"Ошибка Groq API: {str(api_error)}",
                        api_response=str(api_error)
                    )
                
        except InvalidUserInputError:
            # Пробрасываем ошибки валидации как есть
            raise
        except GroqApiError:
            # Пробрасываем ошибки API как есть
            raise
        except Exception as e:
            # Все остальные ошибки обрабатываем
            result = error_handler.handle_error(e, {
                'function': 'generate_reply_variants',
                'user_text_length': len(user_text),
                'style': style
            })
            
            # Возвращаем fallback варианты
            variants = self._fallback_variants(user_text, style)
            bot_logger.log_warning("Использование fallback вариантов из-за ошибки")
            return variants
    
    async def generate_ppv_description(self, price: int) -> str:
        """Генерация описания PPV контента с обработкой ошибок"""
        
        try:
            # Валидация цены
            if not isinstance(price, int) or price <= 0:
                raise InvalidUserInputError(
                    "Цена должна быть положительным числом",
                    user_input=str(price),
                    validation_rule="positive_price"
                )
            
            if price > 1000:
                raise InvalidUserInputError(
                    "Цена слишком высокая (максимум $1000)",
                    user_input=str(price),
                    validation_rule="max_price_1000"
                )
            
            bot_logger.log_api_call(f"Groq API вызов для PPV описания", {"price": price})
            
            # Проверяем кэш
            cache_key = self._get_cache_key(str(price))
            if cache_key in self.ppv_cache:
                bot_logger.log_info("Использование кэшированного PPV описания")
                return self.ppv_cache[cache_key]
            
            system_prompt = f"""Ты - OnlyFans модель, создающая описание платного контента (PPV).

ЗАДАЧА: Создай привлекательное описание эксклюзивного контента за ${price}

ТРЕБОВАНИЯ:
- Интригующее описание без конкретных деталей
- Подчеркни эксклюзивность и ценность
- Создай желание купить
- Используй эмодзи для привлечения внимания
- Длина: 2-3 предложения
- Цена: ${price}

СТИЛЬ: Соблазнительный, но элегантный"""

            try:
                response = await self.client.chat.completions.create(
                    model=self.model,
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": f"Создай описание PPV контента за ${price}"}
                    ],
                    max_tokens=150,
                    temperature=0.9
                )
                
                if not response or not response.choices:
                    raise GroqApiError("Пустой ответ от Groq API для PPV")
                
                description = response.choices[0].message.content.strip()
                
                # Сохраняем в кэш
                self.ppv_cache[cache_key] = description
                bot_logger.log_info("PPV описание успешно сгенерировано")
                return description
                
            except Exception as api_error:
                raise GroqApiError(f"Ошибка API при генерации PPV: {str(api_error)}")
                
        except (InvalidUserInputError, GroqApiError):
            raise
        except Exception as e:
            result = error_handler.handle_error(e, {
                'function': 'generate_ppv_description',
                'price': price
            })
            
            # Возвращаем fallback описание
            description = self._fallback_ppv_description(price)
            bot_logger.log_warning("Использование fallback PPV описания")
            return description
    
    async def generate_hot_content(self, level: str) -> str:
        """Генерация откровенного контента с обработкой ошибок"""
        
        try:
            # Валидация уровня
            valid_levels = ['light', 'passionate', 'explicit']
            if level not in valid_levels:
                raise InvalidUserInputError(
                    f"Недопустимый уровень. Доступные: {', '.join(valid_levels)}",
                    user_input=level,
                    validation_rule="valid_content_level"
                )
            
            bot_logger.log_api_call(f"Groq API вызов для hot контента", {"level": level})
            
            # Проверяем кэш
            cache_key = self._get_cache_key(level)
            if cache_key in self.hot_cache:
                bot_logger.log_info("Использование кэшированного hot контента")
                return self.hot_cache[cache_key]
            
            level_prompts = {
                'light': "Легкий флирт, намеки без откровенности",
                'passionate': "Страстные намеки, эмоциональный тон",
                'explicit': "Более откровенный контент, но в рамках приличия"
            }
            
            system_prompt = f"""Ты - OnlyFans модель, создающая {level_prompts.get(level)} контент.

ЗАДАЧА: Создай привлекательное сообщение с соответствующим уровнем откровенности

ТРЕБОВАНИЯ:
- Соответствуй выбранному уровню: {level}
- Будь соблазнительной, но элегантной
- Используй намеки вместо прямых выражений
- 1-2 предложения
- Подходящие эмодзи

ВАЖНО: Контент должен быть привлекательным, но не вульгарным"""

            try:
                response = await self.client.chat.completions.create(
                    model=self.model,
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": f"Создай {level} контент"}
                    ],
                    max_tokens=100,
                    temperature=0.8
                )
                
                if not response or not response.choices:
                    raise GroqApiError("Пустой ответ от Groq API для hot контента")
                
                content = response.choices[0].message.content.strip()
                
                # Сохраняем в кэш
                self.hot_cache[cache_key] = content
                bot_logger.log_info("Hot контент успешно сгенерирован")
                return content
                
            except Exception as api_error:
                raise GroqApiError(f"Ошибка API при генерации hot контента: {str(api_error)}")
                
        except (InvalidUserInputError, GroqApiError):
            raise
        except Exception as e:
            result = error_handler.handle_error(e, {
                'function': 'generate_hot_content',
                'level': level
            })
            
            # Возвращаем fallback контент
            content = self._fallback_hot_content(level)
            bot_logger.log_warning("Использование fallback hot контента")
            return content
    
    def _parse_variants(self, content: str) -> List[str]:
        """Парсинг вариантов из ответа API с обработкой ошибок"""
        try:
            variants = []
            lines = content.split('\n')
            
            for line in lines:
                line = line.strip()
                if line.startswith('Вариант') and ':' in line:
                    # Извлекаем текст после ":"
                    variant_text = line.split(':', 1)[1].strip()
                    if variant_text:
                        variants.append(variant_text)
            
            # Если не нашли варианты в стандартном формате, пробуем другие форматы
            if not variants and content:
                # Разбиваем по точкам или переносам
                potential_variants = [
                    line.strip() for line in content.replace('.', '\n').split('\n')
                    if line.strip() and len(line.strip()) > 10
                ]
                variants = potential_variants[:3]
            
            return variants[:3]  # Максимум 3 варианта
            
        except Exception as e:
            bot_logger.log_warning(f"Ошибка парсинга вариантов: {e}")
            return []
    
    def _fallback_variants(self, user_text: str, style: str) -> List[str]:
        """Резервные варианты ответов при ошибке API"""
        try:
            fallback_map = {
                'friendly': [
                    "Привет! Спасибо за сообщение! 😊",
                    "Как дела? Рада тебя видеть! 💕",
                    "Отличное сообщение! Расскажи больше 🌟"
                ],
                'flirty': [
                    "Мм, интересно... расскажи мне больше 😏",
                    "Ты такой милый! Что еще у тебя на уме? 😘",
                    "Обожаю с тобой общаться! Продолжай 💋"
                ],
                'passionate': [
                    "Ты меня заводишь своими словами... 🔥",
                    "Мм, я чувствую страсть в твоем сообщении 💫",
                    "Продолжай, мне нравится твоя энергия! ⚡"
                ],
                'romantic': [
                    "Какой ты романтичный... мое сердце тает 💝",
                    "Твои слова такие нежные и красивые 🌹",
                    "Ты знаешь, как растопить мое сердце 💖"
                ],
                'professional': [
                    "Спасибо за ваше сообщение! Рада общению.",
                    "Благодарю за интерес! Что вас интересует?",
                    "Приятно познакомиться! Как дела?"
                ]
            }
            
            variants = fallback_map.get(style, fallback_map['friendly'])
            bot_logger.log_warning(f"Использование fallback вариантов для стиля: {style}")
            return variants
            
        except Exception as e:
            bot_logger.log_error(f"Ошибка в fallback вариантах: {e}")
            return [
                "Спасибо за сообщение! 😊",
                "Рада с тобой общаться! 💕", 
                "Расскажи мне больше! 🌟"
            ]
    
    def _fallback_ppv_description(self, price: int) -> str:
        """Резервное описание PPV при ошибке API"""
        try:
            descriptions = [
                f"🔥 Эксклюзивный контент только для тебя! Не пропусти возможность увидеть что-то особенное 💫 ${price}",
                f"💝 Специальный сюрприз ждет тебя! Этот контент создан с особой страстью 🌹 ${price}",
                f"✨ Секретный контент, который ты больше нигде не увидишь! Только для избранных 💎 ${price}"
            ]
            
            import random
            selected = random.choice(descriptions)
            bot_logger.log_warning(f"Использование fallback PPV описания для ${price}")
            return selected
            
        except Exception as e:
            bot_logger.log_error(f"Ошибка в fallback PPV описании: {e}")
            return f"🔥 Эксклюзивный контент для тебя! ${price} 💫"
    
    def _fallback_hot_content(self, level: str) -> str:
        """Резервный hot контент при ошибке API"""
        try:
            content_map = {
                'light': "Думаю о тебе... что ты сейчас делаешь? 😉💕",
                'passionate': "Ты меня так заводишь... не могу перестать думать о нас 🔥💫",
                'explicit': "Хочу поделиться с тобой чем-то особенным... готов? 😏🔥"
            }
            
            content = content_map.get(level, content_map['light'])
            bot_logger.log_warning(f"Использование fallback hot контента для уровня: {level}")
            return content
            
        except Exception as e:
            bot_logger.log_error(f"Ошибка в fallback hot контенте: {e}")
            return "Думаю о тебе... 😘💕"

# Глобальный экземпляр генератора
_generator_instance = None

def get_content_generator() -> GroqContentGenerator:
    """Получение глобального экземпляра генератора с обработкой ошибок"""
    global _generator_instance
    
    try:
        if _generator_instance is None:
            _generator_instance = GroqContentGenerator()
        return _generator_instance
    except Exception as e:
        bot_logger.log_error(f"Ошибка получения генератора контента: {e}")
        raise GroqApiError(f"Не удалось инициализировать генератор: {str(e)}")

# Удобные функции для использования в боте
async def generate_reply_variants(user_text: str, style: str = 'friendly') -> List[str]:
    """Глобальная функция для генерации вариантов ответов с обработкой ошибок"""
    try:
        generator = get_content_generator()
        return await generator.generate_reply_variants(user_text, style)
    except Exception as e:
        bot_logger.log_error(f"Ошибка в глобальной функции generate_reply_variants: {e}")
        # Возвращаем базовые fallback варианты
        return [
            "Спасибо за сообщение! 😊",
            "Рада с тобой общаться! 💕",
            "Расскажи мне больше! 🌟"
        ]

async def generate_ppv_description(price: int) -> str:
    """Глобальная функция для генерации PPV описания с обработкой ошибок"""
    try:
        generator = get_content_generator()
        return await generator.generate_ppv_description(price)
    except Exception as e:
        bot_logger.log_error(f"Ошибка в глобальной функции generate_ppv_description: {e}")
        return f"🔥 Эксклюзивный контент для тебя! ${price} 💫"

async def generate_hot_content(level: str) -> str:
    """Глобальная функция для генерации hot контента с обработкой ошибок"""
    try:
        generator = get_content_generator()
        return await generator.generate_hot_content(level)
    except Exception as e:
        bot_logger.log_error(f"Ошибка в глобальной функции generate_hot_content: {e}")
        return "Думаю о тебе... 😘💕" 