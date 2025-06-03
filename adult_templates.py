"""
Professional Adult Content Templates Module
Handles template-based responses for OF bot with proper categorization.
"""

from typing import Dict, List, Optional, Tuple, Any
from enum import Enum
from dataclasses import dataclass, field
from abc import ABC, abstractmethod
import random
import asyncio
from datetime import datetime

class ExplicitnessLevel(Enum):
    """Levels of content explicitness"""
    SOFT = 1        # Romantic, flirty
    MEDIUM = 2      # Suggestive, teasing
    EXPLICIT = 3    # Direct, sexual
    INTENSE = 4     # Very explicit
    EXTREME = 5     # Maximum intensity

class ContentMode(Enum):
    """Communication modes"""
    CHAT = "chat"           # Casual conversation
    FLIRT = "flirt"         # Flirtatious interaction
    SEXTING = "sexting"     # Explicit messaging

class TemplateCategory(Enum):
    """Template categories for organization"""
    GREETING = "greeting"
    FLIRT = "flirt"
    TEASE = "tease"
    PPV_PROMO = "ppv_promo"
    APPRECIATION = "appreciation"
    ESCALATION = "escalation"
    CONTENT_OFFER = "content_offer"
    PLAYFUL = "playful"
    INTIMATE = "intimate"
    THANK_YOU = "thank_you"

@dataclass
class ContentTemplate:
    """Individual content template with metadata"""
    text: str
    category: TemplateCategory
    explicitness: ExplicitnessLevel
    mode: ContentMode
    tags: List[str] = field(default_factory=list)
    variables: List[str] = field(default_factory=list)  # {name}, {amount}, etc.
    context_keywords: List[str] = field(default_factory=list)
    quality_score: float = 1.0  # User feedback score

class TemplateStrategy(ABC):
    """Abstract strategy for template selection"""
    
    @abstractmethod
    async def select_template(
        self, 
        templates: List[ContentTemplate], 
        context: Dict[str, Any]
    ) -> Optional[ContentTemplate]:
        pass

class RandomStrategy(TemplateStrategy):
    """Random template selection strategy"""
    
    async def select_template(
        self, 
        templates: List[ContentTemplate], 
        context: Dict[str, Any]
    ) -> Optional[ContentTemplate]:
        if not templates:
            return None
        return random.choice(templates)

class QualityBasedStrategy(TemplateStrategy):
    """Quality-weighted template selection"""
    
    async def select_template(
        self, 
        templates: List[ContentTemplate], 
        context: Dict[str, Any]
    ) -> Optional[ContentTemplate]:
        if not templates:
            return None
        
        # Weight by quality score
        weights = [template.quality_score for template in templates]
        return random.choices(templates, weights=weights)[0]

class ContextAwareStrategy(TemplateStrategy):
    """Context-aware template selection"""
    
    async def select_template(
        self, 
        templates: List[ContentTemplate], 
        context: Dict[str, Any]
    ) -> Optional[ContentTemplate]:
        if not templates:
            return None
        
        user_message = context.get('user_message', '').lower()
        scored_templates = []
        
        for template in templates:
            score = template.quality_score
            
            # Boost score for matching context keywords
            for keyword in template.context_keywords:
                if keyword.lower() in user_message:
                    score += 0.5
            
            scored_templates.append((template, score))
        
        # Sort by score and add randomness
        scored_templates.sort(key=lambda x: x[1], reverse=True)
        top_templates = [t[0] for t in scored_templates[:3]]
        
        return random.choice(top_templates)

class AdultTemplateRepository:
    """Repository for managing adult content templates"""
    
    def __init__(self):
        self.templates: Dict[TemplateCategory, List[ContentTemplate]] = {}
        self._load_default_templates()
    
    def _load_default_templates(self):
        """Load default template collection"""
        
        # GREETING templates
        self.templates[TemplateCategory.GREETING] = [
            ContentTemplate(
                "Привет, красавчик! 😘 Как дела?",
                TemplateCategory.GREETING,
                ExplicitnessLevel.SOFT,
                ContentMode.CHAT,
                tags=["casual", "friendly"],
                context_keywords=["привет", "хай", "hello"]
            ),
            ContentTemplate(
                "Ммм, соскучилась по тебе 💋 Что делаешь?",
                TemplateCategory.GREETING,
                ExplicitnessLevel.MEDIUM,
                ContentMode.FLIRT,
                tags=["missing", "intimate"],
                context_keywords=["привет", "дела"]
            ),
            ContentTemplate(
                "Детка, я так хочу тебя прямо сейчас... 🔥",
                TemplateCategory.GREETING,
                ExplicitnessLevel.EXPLICIT,
                ContentMode.SEXTING,
                tags=["desire", "direct"],
                context_keywords=["привет", "хочу"]
            )
        ]
        
        # FLIRT templates
        self.templates[TemplateCategory.FLIRT] = [
            ContentTemplate(
                "Ты такой милый 😊 Расскажи мне что-нибудь интересное",
                TemplateCategory.FLIRT,
                ExplicitnessLevel.SOFT,
                ContentMode.CHAT,
                tags=["compliment", "interest"],
                context_keywords=["расскажи", "интересно"]
            ),
            ContentTemplate(
                "Знаешь, ты мне очень нравишься... 😏 Хочешь увидеть что-то особенное?",
                TemplateCategory.FLIRT,
                ExplicitnessLevel.MEDIUM,
                ContentMode.FLIRT,
                tags=["attraction", "tease"],
                context_keywords=["нравишься", "особенное"]
            ),
            ContentTemplate(
                "Мм, представляю как ты меня трогаешь... 🔥 Хочешь мои фото?",
                TemplateCategory.FLIRT,
                ExplicitnessLevel.EXPLICIT,
                ContentMode.SEXTING,
                tags=["imagination", "photos"],
                context_keywords=["трогаешь", "фото", "хочешь"]
            )
        ]
        
        # PPV_PROMO templates
        self.templates[TemplateCategory.PPV_PROMO] = [
            ContentTemplate(
                "У меня есть кое-что особенное для тебя 💝 Всего за ${amount}",
                TemplateCategory.PPV_PROMO,
                ExplicitnessLevel.SOFT,
                ContentMode.CHAT,
                tags=["special", "offer"],
                variables=["amount"],
                context_keywords=["особенное", "покупка"]
            ),
            ContentTemplate(
                "Детка, хочешь увидеть меня в новом белье? 😈 ${amount} за эксклюзив",
                TemplateCategory.PPV_PROMO,
                ExplicitnessLevel.MEDIUM,
                ContentMode.FLIRT,
                tags=["lingerie", "exclusive"],
                variables=["amount"],
                context_keywords=["белье", "эксклюзив"]
            ),
            ContentTemplate(
                "Мм, сняла для тебя очень горячее видео... 🔥🔥 ${amount} и оно твоё",
                TemplateCategory.PPV_PROMO,
                ExplicitnessLevel.EXPLICIT,
                ContentMode.SEXTING,
                tags=["video", "hot"],
                variables=["amount"],
                context_keywords=["видео", "горячее"]
            )
        ]
        
        # APPRECIATION templates
        self.templates[TemplateCategory.APPRECIATION] = [
            ContentTemplate(
                "Спасибо, милый! 💕 Ты такой щедрый",
                TemplateCategory.APPRECIATION,
                ExplicitnessLevel.SOFT,
                ContentMode.CHAT,
                tags=["thanks", "generous"],
                context_keywords=["спасибо", "щедрый"]
            ),
            ContentTemplate(
                "Ммм, обожаю таких щедрых мужчин... 😘 Хочешь бонус?",
                TemplateCategory.APPRECIATION,
                ExplicitnessLevel.MEDIUM,
                ContentMode.FLIRT,
                tags=["love", "bonus"],
                context_keywords=["обожаю", "бонус"]
            ),
            ContentTemplate(
                "За это ты заслуживаешь особой награды... 🔥 Покажу тебе всё",
                TemplateCategory.APPRECIATION,
                ExplicitnessLevel.EXPLICIT,
                ContentMode.SEXTING,
                tags=["reward", "show"],
                context_keywords=["награда", "покажу"]
            )
        ]
        
        # TEASE templates
        self.templates[TemplateCategory.TEASE] = [
            ContentTemplate(
                "Хм, интересно... 😏 А что ты готов сделать ради этого?",
                TemplateCategory.TEASE,
                ExplicitnessLevel.SOFT,
                ContentMode.FLIRT,
                tags=["curiosity", "challenge"],
                context_keywords=["интересно", "готов"]
            ),
            ContentTemplate(
                "Ой, а ты такой нетерпеливый... 😈 Но сначала покажи мне свою щедрость",
                TemplateCategory.TEASE,
                ExplicitnessLevel.MEDIUM,
                ContentMode.FLIRT,
                tags=["impatient", "generosity"],
                context_keywords=["нетерпеливый", "щедрость"]
            ),
            ContentTemplate(
                "Мм, хочешь меня? 🔥 Докажи насколько сильно...",
                TemplateCategory.TEASE,
                ExplicitnessLevel.EXPLICIT,
                ContentMode.SEXTING,
                tags=["want", "prove"],
                context_keywords=["хочешь", "докажи"]
            )
        ]

    def get_templates(
        self,
        category: Optional[TemplateCategory] = None,
        explicitness: Optional[ExplicitnessLevel] = None,
        mode: Optional[ContentMode] = None,
        tags: Optional[List[str]] = None
    ) -> List[ContentTemplate]:
        """Get filtered templates"""
        
        if category:
            templates = self.templates.get(category, [])
        else:
            templates = []
            for cat_templates in self.templates.values():
                templates.extend(cat_templates)
        
        # Apply filters
        if explicitness:
            templates = [t for t in templates if t.explicitness == explicitness]
        
        if mode:
            templates = [t for t in templates if t.mode == mode]
        
        if tags:
            templates = [t for t in templates if any(tag in t.tags for tag in tags)]
        
        return templates
    
    def add_template(self, template: ContentTemplate):
        """Add new template to repository"""
        if template.category not in self.templates:
            self.templates[template.category] = []
        self.templates[template.category].append(template)
    
    def update_quality_score(self, template_text: str, score: float):
        """Update template quality based on user feedback"""
        for category_templates in self.templates.values():
            for template in category_templates:
                if template.text == template_text:
                    template.quality_score = max(0.1, min(2.0, score))
                    break

class FallbackSystem:
    """Fallback system when AI refuses or fails"""
    
    def __init__(self, repository: AdultTemplateRepository):
        self.repository = repository
        self.safe_fallbacks = {
            ExplicitnessLevel.SOFT: [
                "Давай поговорим о чём-то приятном 😊",
                "Расскажи мне о себе, интересно узнать тебя лучше 💕",
                "Как прошёл твой день? 🌟"
            ],
            ExplicitnessLevel.MEDIUM: [
                "Хочешь узнать мои секреты? 😏",
                "У меня есть кое-что особенное... 💝",
                "Ты мне нравишься, давай общаться 😘"
            ],
            ExplicitnessLevel.EXPLICIT: [
                "Покажи мне свою щедрость, и я удивлю тебя 🔥",
                "Хочешь эксклюзивный контент? Пиши в DM 💋",
                "Для таких как ты у меня особые предложения 😈"
            ]
        }
    
    async def get_fallback_response(
        self,
        explicitness: ExplicitnessLevel,
        context: Dict[str, Any]
    ) -> str:
        """Get safe fallback response"""
        
        # Try template-based fallback first
        templates = self.repository.get_templates(explicitness=explicitness)
        if templates:
            template = random.choice(templates)
            return self._process_template_variables(template.text, context)
        
        # Use hardcoded safe fallbacks
        fallbacks = self.safe_fallbacks.get(explicitness, self.safe_fallbacks[ExplicitnessLevel.SOFT])
        return random.choice(fallbacks)
    
    def _process_template_variables(self, text: str, context: Dict[str, Any]) -> str:
        """Process template variables like {name}, {amount}"""
        
        # Replace common variables
        replacements = {
            'name': context.get('user_name', 'красавчик'),
            'amount': context.get('amount', '10'),
            'time': datetime.now().strftime('%H:%M')
        }
        
        for var, value in replacements.items():
            text = text.replace(f'{{{var}}}', str(value))
        
        return text

# Global repository instance
adult_templates_repo = AdultTemplateRepository()
fallback_system = FallbackSystem(adult_templates_repo) 