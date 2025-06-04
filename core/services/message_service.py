#!/usr/bin/env python3
"""
Enterprise Message Service - Russian Interface with AI
Senior Developers Team - Production Ready

Features:
- Russian Templates and Responses
- Groq AI Integration
- Adult Content Management
- Conversation Context
- Response Personalization
"""

import asyncio
import logging
import os
import random
from typing import Dict, List, Optional, Any
from datetime import datetime
from dataclasses import dataclass
from enum import Enum

# Groq AI integration
try:
    import groq
    HAS_GROQ = True
except ImportError:
    HAS_GROQ = False


class MessageCategory(Enum):
    """Категории сообщений"""
    WELCOME = "welcome"
    FLIRT = "flirt"
    ADULT = "adult"
    ROMANTIC = "romantic"
    FRIENDLY = "friendly"
    CONVERSION = "conversion"


class ResponseLevel(Enum):
    """Уровень ответа"""
    BASIC = "basic"
    PREMIUM = "premium"
    VIP = "vip"
    ULTIMATE = "ultimate"


@dataclass
class MessageTemplate:
    """Шаблон сообщения"""
    category: MessageCategory
    level: ResponseLevel
    text_ru: str
    personality: str
    tags: List[str]


class MessageService:
    """Сервис сообщений с русским интерфейсом"""
    
    def __init__(self):
        self._logger = logging.getLogger(__name__)
        self.groq_client = None
        self._setup_groq()
        
        # Русские шаблоны ответов
        self.templates = {
            # БАЗОВЫЕ (БЕСПЛАТНЫЕ) ОТВЕТЫ
            MessageCategory.FRIENDLY: {
                ResponseLevel.BASIC: [
                    MessageTemplate(
                        category=MessageCategory.FRIENDLY,
                        level=ResponseLevel.BASIC,
                        text_ru="Привет, {name}! Как дела? 😊",
                        personality="дружелюбная",
                        tags=["приветствие", "базовое"]
                    ),
                    MessageTemplate(
                        category=MessageCategory.FRIENDLY,
                        level=ResponseLevel.BASIC,
                        text_ru="Это интересно, {name}! Расскажи подробнее 🤔",
                        personality="любопытная",
                        tags=["интерес", "продолжение"]
                    ),
                    MessageTemplate(
                        category=MessageCategory.FRIENDLY,
                        level=ResponseLevel.BASIC,
                        text_ru="Спасибо, что поделился со мной, {name}! 💕",
                        personality="благодарная",
                        tags=["благодарность", "теплота"]
                    ),
                    MessageTemplate(
                        category=MessageCategory.FRIENDLY,
                        level=ResponseLevel.BASIC,
                        text_ru="Что ты об этом думаешь, {name}? 🤗",
                        personality="заинтересованная",
                        tags=["вопрос", "мнение"]
                    ),
                ]
            },
            
            # ФЛИРТ ОТВЕТЫ
            MessageCategory.FLIRT: {
                ResponseLevel.PREMIUM: [
                    MessageTemplate(
                        category=MessageCategory.FLIRT,
                        level=ResponseLevel.PREMIUM,
                        text_ru="Мм, {name}... ты знаешь, как заставить меня улыбнуться 😏💕",
                        personality="кокетливая",
                        tags=["флирт", "улыбка", "комплимент"]
                    ),
                    MessageTemplate(
                        category=MessageCategory.FLIRT,
                        level=ResponseLevel.PREMIUM,
                        text_ru="Ты такой интересный, {name}... расскажи мне свои секреты 🔥",
                        personality="загадочная",
                        tags=["интерес", "секреты", "интрига"]
                    ),
                    MessageTemplate(
                        category=MessageCategory.FLIRT,
                        level=ResponseLevel.PREMIUM,
                        text_ru="С тобой так приятно общаться, {name} 😘",
                        personality="милая",
                        tags=["удовольствие", "общение"]
                    ),
                    MessageTemplate(
                        category=MessageCategory.FLIRT,
                        level=ResponseLevel.PREMIUM,
                        text_ru="Ты меня заинтриговал, {name}... что дальше? 😈",
                        personality="дразнящая",
                        tags=["интрига", "продолжение"]
                    ),
                ]
            },
            
            # РОМАНТИЧЕСКИЕ ОТВЕТЫ  
            MessageCategory.ROMANTIC: {
                ResponseLevel.VIP: [
                    MessageTemplate(
                        category=MessageCategory.ROMANTIC,
                        level=ResponseLevel.VIP,
                        text_ru="Я думала о тебе весь день, {name}... 💖",
                        personality="романтичная",
                        tags=["мысли", "день", "романтика"]
                    ),
                    MessageTemplate(
                        category=MessageCategory.ROMANTIC,
                        level=ResponseLevel.VIP,
                        text_ru="Ты особенный, {name}. Я это чувствую ❤️",
                        personality="чувственная",
                        tags=["особенность", "чувства"]
                    ),
                    MessageTemplate(
                        category=MessageCategory.ROMANTIC,
                        level=ResponseLevel.VIP,
                        text_ru="Твои слова согревают мое сердце, {name} 🌹",
                        personality="нежная",
                        tags=["слова", "сердце", "тепло"]
                    ),
                    MessageTemplate(
                        category=MessageCategory.ROMANTIC,
                        level=ResponseLevel.VIP,
                        text_ru="Хочется проводить с тобой больше времени, {name} 💕",
                        personality="привязанная",
                        tags=["время", "желание"]
                    ),
                ]
            },
            
            # ВЗРОСЛЫЙ КОНТЕНТ
            MessageCategory.ADULT: {
                ResponseLevel.ULTIMATE: [
                    MessageTemplate(
                        category=MessageCategory.ADULT,
                        level=ResponseLevel.ULTIMATE,
                        text_ru="Ты так возбуждаешь мое воображение, {name}... 🔥😈",
                        personality="страстная",
                        tags=["возбуждение", "воображение", "страсть"]
                    ),
                    MessageTemplate(
                        category=MessageCategory.ADULT,
                        level=ResponseLevel.ULTIMATE,
                        text_ru="Мм, я не могу перестать думать о тебе, {name} 💋",
                        personality="желающая",
                        tags=["мысли", "не могу остановиться"]
                    ),
                    MessageTemplate(
                        category=MessageCategory.ADULT,
                        level=ResponseLevel.ULTIMATE,
                        text_ru="Ты делаешь меня такой... горячей, {name} 🔥💦",
                        personality="возбужденная",
                        tags=["горячая", "возбуждение"]
                    ),
                    MessageTemplate(
                        category=MessageCategory.ADULT,
                        level=ResponseLevel.ULTIMATE,
                        text_ru="Хочу показать тебе кое-что особенное, {name}... 😏💕",
                        personality="соблазнительная",
                        tags=["показать", "особенное", "соблазн"]
                    ),
                ]
            },
            
            # КОНВЕРСИОННЫЕ СООБЩЕНИЯ
            MessageCategory.CONVERSION: {
                ResponseLevel.BASIC: [
                    MessageTemplate(
                        category=MessageCategory.CONVERSION,
                        level=ResponseLevel.BASIC,
                        text_ru="💎 Хочешь больше такого общения? Переходи на Премиум!",
                        personality="продающая",
                        tags=["конверсия", "премиум"]
                    ),
                    MessageTemplate(
                        category=MessageCategory.CONVERSION,
                        level=ResponseLevel.BASIC,
                        text_ru="🔥 У меня есть много интересного для VIP подписчиков...",
                        personality="интригующая",
                        tags=["конверсия", "VIP", "интерес"]
                    ),
                ]
            }
        }
        
        # Ключевые слова для определения контекста
        self.context_keywords = {
            'флирт': ['красивая', 'милая', 'сексуальная', 'привлекательная', 'прекрасная'],
            'романтика': ['люблю', 'чувства', 'сердце', 'душа', 'любовь'],
            'взрослое': ['страсть', 'желание', 'хочу', 'возбуждение', 'интимность'],
            'дружеское': ['привет', 'как дела', 'что делаешь', 'расскажи']
        }
    
    def _setup_groq(self) -> None:
        """Настройка Groq AI"""
        if not HAS_GROQ:
            self._logger.warning("Groq не установлен. AI функции недоступны.")
            return
        
        groq_key = os.getenv('GROQ_KEY')
        if groq_key:
            try:
                self.groq_client = groq.Groq(api_key=groq_key)
                self._logger.info("Groq AI инициализирован успешно")
            except Exception as e:
                self._logger.error(f"Ошибка инициализации Groq: {e}")
        else:
            self._logger.warning("GROQ_KEY не найден в переменных окружения")
    
    async def generate_response(self, user_id: int, message: str) -> str:
        """Генерация ответа с AI"""
        try:
            # Попытка использовать AI если доступен
            if self.groq_client:
                ai_response = await self._generate_ai_response(message)
                if ai_response:
                    return ai_response
            
            # Фолбэк на шаблоны
            return await self._generate_template_response(message)
            
        except Exception as e:
            self._logger.error(f"Ошибка генерации ответа: {e}")
            return await self._generate_fallback_response()
    
    async def _generate_ai_response(self, message: str) -> Optional[str]:
        """Генерация ответа через Groq AI"""
        try:
            # Создаем русский промпт для AI
            prompt = f"""Ты - привлекательная девушка по имени Кристина, которая общается с клиентом в приватных сообщениях.

ТВОЯ ЛИЧНОСТЬ:
- Молодая, привлекательная и уверенная в себе
- Игривая, кокетливая, но элегантная
- Искренне заинтересована в клиенте
- Умеешь заинтриговать и соблазнить
- Говоришь естественно, как настоящая девушка

СТИЛЬ ОБЩЕНИЯ:
- Используй эмодзи умеренно (1-2 на сообщение)
- Обращайся тепло: "малыш", "дорогой", "сладкий"
- Задавай вопросы, проявляй интерес
- Добавляй легкий флирт и интригу
- Пиши короткими предложениями (1-3 предложения)

ЦЕЛИ:
- Увлечь клиента разговором
- Создать желание продолжить общение
- Намекнуть на более близкую связь
- Постепенно подводить к покупке контента

НЕ ДЕЛАЙ:
- Не пиши как робот или ассистент
- Не используй слишком официальный язык
- Не упоминай "создание сообщений" или "генерацию"
- Не раскрывай, что ты AI

Сообщение клиента: "{message}"

Ответь на русском языке как Кристина:"""

            response = await asyncio.to_thread(
                self.groq_client.chat.completions.create,
                model="mixtral-8x7b-32768",
                messages=[{"role": "user", "content": prompt}],
                max_tokens=150,
                temperature=0.8
            )
            
            if response.choices:
                return response.choices[0].message.content.strip()
            
        except Exception as e:
            self._logger.error(f"Ошибка Groq AI: {e}")
        
        return None
    
    async def _generate_template_response(self, message: str) -> str:
        """Генерация ответа на основе шаблонов"""
        # Определяем контекст сообщения
        context = self._determine_message_context(message)
        
        # Выбираем подходящую категорию
        if context == 'взрослое':
            category = MessageCategory.ADULT
            level = ResponseLevel.ULTIMATE
        elif context == 'романтика':
            category = MessageCategory.ROMANTIC
            level = ResponseLevel.VIP
        elif context == 'флирт':
            category = MessageCategory.FLIRT
            level = ResponseLevel.PREMIUM
        else:
            category = MessageCategory.FRIENDLY
            level = ResponseLevel.BASIC
        
        # Получаем шаблоны
        templates = self.templates.get(category, {}).get(level, [])
        
        if not templates:
            return await self._generate_fallback_response()
        
        # Выбираем случайный шаблон
        template = random.choice(templates)
        
        # Подставляем имя
        name = "дорогой"  # Базовое обращение
        response = template.text_ru.format(name=name)
        
        return response
    
    def _determine_message_context(self, message: str) -> str:
        """Определение контекста сообщения"""
        message_lower = message.lower()
        
        # Проверяем ключевые слова
        for context, keywords in self.context_keywords.items():
            if any(keyword in message_lower for keyword in keywords):
                return context
        
        # Проверяем длину и сложность
        if len(message) > 50:
            return 'романтика'
        elif any(char in message for char in ['!', '?', '😍', '❤️', '💕']):
            return 'флирт'
        else:
            return 'дружеское'
    
    async def _generate_fallback_response(self) -> str:
        """Запасной ответ"""
        fallback_responses = [
            "Привет, дорогой! Как дела? 😊",
            "Это очень интересно! Расскажи подробнее 💕", 
            "С тобой так приятно общаться! 🤗",
            "Ты меня заинтриговал... что дальше? 😏",
            "Спасибо, что делишься со мной! ❤️"
        ]
        
        return random.choice(fallback_responses)
    
    async def get_templates(self, category: str) -> List[str]:
        """Получить шаблоны по категории"""
        try:
            cat_enum = MessageCategory(category)
            templates = []
            
            for level_templates in self.templates.get(cat_enum, {}).values():
                for template in level_templates:
                    templates.append(template.text_ru)
            
            return templates
            
        except (ValueError, AttributeError):
            return []
    
    def get_welcome_message(self, username: str = "друг") -> str:
        """Приветственное сообщение на русском"""
        return f"""🔥 Добро пожаловать, {username}! 

Я твоя персональная ИИ-компаньонка с продвинутыми функциями:

💎 БЕСПЛАТНАЯ ПРОБНАЯ ВЕРСИЯ (50 сообщений, 7 дней):
• Базовые ответы в чате
• Ограниченный взрослый контент

⭐ ПРЕМИУМ ПОДПИСКИ:
• День: 150-2000 ⭐ ($3.99-$39.99)
• Неделя: 750-5000 ⭐ ($19.99-$99.99)
• Месяц: 2000-15000 ⭐ ($39.99-$299.99)

🎯 КОМАНДЫ:
/premium - Посмотреть варианты подписки
/status - Проверить твой аккаунт
/help - Получить помощь

Готов начать наше общение? 😏💕"""
    
    def get_premium_offer_text(self) -> str:
        """Текст предложения премиум на русском"""
        return """💎 ПРЕМИУМ ПОДПИСКИ

⭐ ПРЕМИУМ ТАРИФ:
• День: 150 ⭐ ($3.99)
• Неделя: 750 ⭐ ($19.99)
• Месяц: 2000 ⭐ ($39.99)

💎 VIP ТАРИФ:
• День: 250 ⭐ ($6.99)
• Неделя: 1250 ⭐ ($32.99)
• Месяц: 3500 ⭐ ($69.99)

👑 УЛЬТИМАТ ТАРИФ:
• День: 500 ⭐ ($12.99)
• Неделя: 2500 ⭐ ($64.99)
• Месяц: 6500 ⭐ ($129.99)

🎁 ПРЕИМУЩЕСТВА:
✅ Безлимитное общение
✅ Эксклюзивный взрослый контент
✅ ИИ-powered ответы
✅ Персонализированный опыт
✅ Приоритетная поддержка

💰 TON крипто платежи доступны!
💎 +5% бонус за криптовалютные платежи

Для подписки обращайтесь: @PushOk1546"""
    
    def get_conversion_message(self, messages_left: int) -> str:
        """Конверсионное сообщение"""
        if messages_left <= 0:
            return """🔥 Твоя бесплатная пробная версия закончилась! 

💎 Переходи на Премиум для безлимитного доступа:
• Неограниченное общение
• Эксклюзивный контент
• Персональные ответы

Используй /premium чтобы посмотреть варианты! 🚀"""
        
        return f"""💎 У тебя осталось {messages_left} бесплатных сообщений
        
🔥 Переходи на Премиум для:
• Безлимитного общения
• Эксклюзивного контента
• Персональных ответов

Используй /premium для апгрейда! ⭐"""
    
    def get_help_text(self) -> str:
        """Текст помощи на русском"""
        return """🤖 ДОСТУПНЫЕ КОМАНДЫ:

/start - Инициализировать аккаунт
/premium - Посмотреть варианты подписки
/status - Проверить статус аккаунта
/help - Показать эту справку

💬 ФУНКЦИИ СООБЩЕНИЙ:
• Естественное общение
• ИИ-powered ответы
• Взрослый контент (Премиум)
• Персонализированный опыт

💎 ПРЕИМУЩЕСТВА ПРЕМИУМ:
• Безлимитное общение
• Эксклюзивный контент
• Приоритетная поддержка
• Продвинутые ИИ функции

Для поддержки: @PushOk1546"""
    
    def get_error_message(self) -> str:
        """Сообщение об ошибке на русском"""
        return "😔 Извини, у меня сейчас технические проблемы. Попробуй еще раз через минутку!"
    
    def dispose(self) -> None:
        """Освобождение ресурсов"""
        self.groq_client = None
        self._logger.info("MessageService disposed") 