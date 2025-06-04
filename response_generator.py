"""
Professional Response Generator with Template/AI Strategy
Optimized for adult content generation with caching and user preferences.
"""

import asyncio
import hashlib
import json
import time
import random
from typing import Dict, List, Optional, Any, Tuple, Union
from dataclasses import dataclass, field, asdict
from enum import Enum
from abc import ABC, abstractmethod
import logging
from datetime import datetime, timedelta

from adult_templates import (
    AdultTemplateRepository, 
    ExplicitnessLevel, 
    ContentMode, 
    TemplateCategory
)

logger = logging.getLogger(__name__)

class GenerationMethod(Enum):
    """Response generation method"""
    TEMPLATE = "template"
    AI = "ai"
    HYBRID = "hybrid"

@dataclass
class UserPreferences:
    """User-specific preferences for content generation"""
    user_id: int
    explicitness_level: ExplicitnessLevel = ExplicitnessLevel.MEDIUM
    content_mode: ContentMode = ContentMode.FLIRT
    favorite_categories: List[TemplateCategory] = field(default_factory=list)
    favorite_responses: List[str] = field(default_factory=list)
    generation_method: GenerationMethod = GenerationMethod.HYBRID
    
    # A/B testing
    ab_test_group: str = "default"
    template_success_rate: float = 0.8
    ai_success_rate: float = 0.6
    
    # Performance tracking
    avg_response_time: float = 2.0
    total_responses: int = 0
    positive_feedback: int = 0
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization"""
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'UserPreferences':
        """Create from dictionary"""
        # Handle enum conversions
        if 'explicitness_level' in data:
            data['explicitness_level'] = ExplicitnessLevel(data['explicitness_level'])
        if 'content_mode' in data:
            data['content_mode'] = ContentMode(data['content_mode'])
        if 'generation_method' in data:
            data['generation_method'] = GenerationMethod(data['generation_method'])
        if 'favorite_categories' in data:
            data['favorite_categories'] = [TemplateCategory(cat) for cat in data['favorite_categories']]
        
        return cls(**data)

@dataclass
class CacheEntry:
    """Cache entry for responses"""
    content: str
    timestamp: float
    hit_count: int = 0
    quality_score: float = 1.0
    generation_method: GenerationMethod = GenerationMethod.TEMPLATE
    
    def is_expired(self, ttl_seconds: int = 3600) -> bool:
        """Check if cache entry is expired"""
        return time.time() - self.timestamp > ttl_seconds
    
    def update_hit(self):
        """Update hit count and timestamp"""
        self.hit_count += 1
        self.timestamp = time.time()

class InMemoryCache:
    """Redis-like in-memory cache with LRU eviction"""
    
    def __init__(self, max_size: int = 1000, default_ttl: int = 3600):
        self.max_size = max_size
        self.default_ttl = default_ttl
        self.cache: Dict[str, CacheEntry] = {}
        self.access_order: List[str] = []
        
    def _make_key(self, context: Dict[str, Any]) -> str:
        """Create cache key from context"""
        key_data = {
            'user_message': context.get('user_message', ''),
            'explicitness': str(context.get('explicitness', '')),
            'mode': str(context.get('mode', '')),
            'category': str(context.get('category', ''))
        }
        
        key_str = json.dumps(key_data, sort_keys=True)
        return hashlib.md5(key_str.encode()).hexdigest()
    
    async def get(self, context: Dict[str, Any]) -> Optional[str]:
        """Get cached response"""
        key = self._make_key(context)
        
        if key in self.cache:
            entry = self.cache[key]
            
            if entry.is_expired(self.default_ttl):
                await self.delete(key)
                return None
            
            # Update LRU order
            if key in self.access_order:
                self.access_order.remove(key)
            self.access_order.append(key)
            
            entry.update_hit()
            logger.debug(f"Cache hit for key: {key[:8]}...")
            return entry.content
        
        return None
    
    async def set(self, context: Dict[str, Any], content: str, method: GenerationMethod):
        """Set cached response"""
        key = self._make_key(context)
        
        # Evict if at capacity
        if len(self.cache) >= self.max_size:
            await self._evict_lru()
        
        entry = CacheEntry(
            content=content,
            timestamp=time.time(),
            generation_method=method
        )
        
        self.cache[key] = entry
        if key in self.access_order:
            self.access_order.remove(key)
        self.access_order.append(key)
        
        logger.debug(f"Cached response for key: {key[:8]}...")
    
    async def delete(self, key: str):
        """Delete cache entry"""
        if key in self.cache:
            del self.cache[key]
        if key in self.access_order:
            self.access_order.remove(key)
    
    async def _evict_lru(self):
        """Evict least recently used entry"""
        if self.access_order:
            lru_key = self.access_order[0]
            await self.delete(lru_key)
    
    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics"""
        total_hits = sum(entry.hit_count for entry in self.cache.values())
        avg_quality = sum(entry.quality_score for entry in self.cache.values()) / len(self.cache) if self.cache else 0
        
        return {
            'size': len(self.cache),
            'max_size': self.max_size,
            'total_hits': total_hits,
            'avg_quality_score': avg_quality,
            'methods': {
                method.value: len([e for e in self.cache.values() if e.generation_method == method])
                for method in GenerationMethod
            }
        }

class CachingDecorator:
    """Decorator for caching API calls"""
    
    def __init__(self, cache: InMemoryCache):
        self.cache = cache
    
    def __call__(self, func):
        """Decorator implementation"""
        async def wrapper(*args, **kwargs):
            # For class methods, skip 'self' argument
            if args and hasattr(args[0], '__class__'):
                method_args = args[1:]
            else:
                method_args = args
            
            # Extract context from arguments
            context = kwargs.get('context', {})
            if not context and len(method_args) > 1:
                context = method_args[1] if isinstance(method_args[1], dict) else {}
            
            # Try cache first
            cached_response = await self.cache.get(context)
            if cached_response:
                return cached_response
            
            # Generate new response
            start_time = time.time()
            response = await func(*args, **kwargs)
            generation_time = time.time() - start_time
            
            # Cache the response
            method = context.get('generation_method', GenerationMethod.TEMPLATE)
            await self.cache.set(context, response, method)
            
            logger.debug(f"Generated response in {generation_time:.2f}s using {method.value}")
            return response
        
        return wrapper

@dataclass
class ResponseMetrics:
    """Metrics for response quality tracking"""
    response_id: str
    generation_method: GenerationMethod
    generation_time: float
    user_feedback: Optional[float] = None
    engagement_score: Optional[float] = None
    template_used: Optional[str] = None
    
    @property
    def quality_score(self) -> float:
        """Calculate overall quality score"""
        base_score = 1.0
        
        if self.user_feedback:
            base_score *= (self.user_feedback / 5.0)  # Normalize to 0-1
        
        if self.engagement_score:
            base_score *= self.engagement_score
        
        # Penalize slow responses
        if self.generation_time > 5.0:
            base_score *= 0.8
        elif self.generation_time > 2.0:
            base_score *= 0.9
        
        return max(0.1, min(2.0, base_score))

class ResponseGenerator:
    """Professional response generator with template/AI hybrid approach"""
    
    def __init__(
        self, 
        template_repo: AdultTemplateRepository = None,
        template_ratio: float = 0.8
    ):
        self.template_repo = template_repo or AdultTemplateRepository()
        self.template_ratio = template_ratio
        
        # User preferences storage
        self.user_preferences: Dict[int, UserPreferences] = {}
        
        # Performance tracking
        self.metrics: List[ResponseMetrics] = []
        
        # Caching system
        self.cache = InMemoryCache()
        
        # A/B testing groups
        self.ab_test_groups = {
            'default': {'template_ratio': 0.8, 'description': 'Default behavior'},
            'template_heavy': {'template_ratio': 0.9, 'description': 'More templates'},
            'ai_heavy': {'template_ratio': 0.5, 'description': 'More AI responses'}
        }
        
        logger.info("✅ ResponseGenerator initialized successfully")
    
    def get_user_preferences(self, user_id: int) -> UserPreferences:
        """Get or create user preferences"""
        if user_id not in self.user_preferences:
            # Assign A/B test group
            ab_group = random.choice(list(self.ab_test_groups.keys()))
            
            self.user_preferences[user_id] = UserPreferences(
                user_id=user_id,
                ab_test_group=ab_group
            )
        
        return self.user_preferences[user_id]
    
    async def update_user_preference(
        self, 
        user_id: int, 
        preference_type: str, 
        value: Any
    ):
        """Update specific user preference"""
        prefs = self.get_user_preferences(user_id)
        
        if hasattr(prefs, preference_type):
            setattr(prefs, preference_type, value)
            logger.info(f"Updated {preference_type} for user {user_id}: {value}")
    
    async def generate_response(
        self, 
        user_message: str, 
        context: Dict[str, Any]
    ) -> str:
        """Generate response using hybrid template/AI approach"""
        
        # Check cache first
        cached_response = await self.cache.get(context)
        if cached_response:
            return cached_response
        
        user_id = context.get('user_id', 0)
        prefs = self.get_user_preferences(user_id)
        
        # Update context with user preferences
        context.update({
            'explicitness': prefs.explicitness_level,
            'mode': prefs.content_mode,
            'user_preferences': prefs
        })
        
        start_time = time.time()
        
        try:
            # Determine generation method based on A/B test group
            ab_config = self.ab_test_groups[prefs.ab_test_group]
            should_use_template = random.random() < ab_config['template_ratio']
            
            if should_use_template or prefs.generation_method == GenerationMethod.TEMPLATE:
                response = await self._generate_template_response(user_message, context)
                method = GenerationMethod.TEMPLATE
                
                # Fallback to AI if template fails
                if not response:
                    response = await self._generate_ai_response(user_message, context)
                    method = GenerationMethod.AI
            else:
                response = await self._generate_ai_response(user_message, context)
                method = GenerationMethod.AI
                
                # Fallback to template if AI fails
                if not response:
                    response = await self._generate_template_response(user_message, context)
                    method = GenerationMethod.TEMPLATE
            
            # Final fallback to simple template
            if not response:
                response = self.template_repo.get_random_template(
                    mode=prefs.content_mode.value, 
                    level=prefs.explicitness_level.value
                )
                method = GenerationMethod.TEMPLATE
            
            # Track metrics
            generation_time = time.time() - start_time
            metric = ResponseMetrics(
                response_id=hashlib.md5(f"{user_id}{time.time()}".encode()).hexdigest()[:8],
                generation_method=method,
                generation_time=generation_time
            )
            self.metrics.append(metric)
            
            # Update user stats
            prefs.total_responses += 1
            prefs.avg_response_time = (
                (prefs.avg_response_time * (prefs.total_responses - 1) + generation_time) 
                / prefs.total_responses
            )
            
            context['generation_method'] = method
            
            # Cache the response
            await self.cache.set(context, response, method)
            
            return response
            
        except Exception as e:
            logger.error(f"Error generating response: {str(e)}", exc_info=True)
            # Simple fallback
            return "Привет, красавчик! 😘 Как дела?"
    
    async def _generate_template_response(
        self, 
        user_message: str, 
        context: Dict[str, Any]
    ) -> Optional[str]:
        """Generate response using templates"""
        
        # Get user preferences safely
        user_id = context.get('user_id', 0)
        prefs = context.get('user_preferences')
        if not prefs:
            prefs = self.get_user_preferences(user_id)
            context['user_preferences'] = prefs
        
        explicitness = context.get('explicitness', prefs.explicitness_level)
        mode = context.get('mode', prefs.content_mode)
        
        # Determine category based on message content
        category = self._classify_message_category(user_message)
        
        # Try to get template by category first
        try:
            response = self.template_repo.get_template_by_category_and_level(
                category.value, explicitness.value
            )
            if response:
                return self._process_template_variables(response, context)
        except:
            pass
        
        # Fallback to random template
        try:
            response = self.template_repo.get_random_template(
                mode=mode.value, 
                level=explicitness.value
            )
            if response:
                return self._process_template_variables(response, context)
        except:
            pass
        
        return None
    
    async def _generate_ai_response(
        self, 
        user_message: str, 
        context: Dict[str, Any]
    ) -> Optional[str]:
        """Generate response using AI (integrate with existing API)"""
        
        try:
            # Import here to avoid circular imports
            from api import generate_groq_response
            
            # Create AI prompt based on context
            prompt = self._create_ai_prompt(user_message, context)
            
            # Call existing AI generation with proper parameters
            response = await generate_groq_response(
                prompt=prompt, 
                model='eco',  # Default model
                max_tokens=120,
                temperature=0.8
            )
            
            return response
            
        except ImportError as e:
            logger.error(f"API module import failed: {str(e)}")
            return None
        except Exception as e:
            logger.error(f"AI generation failed: {str(e)}")
            return None
    
    def _classify_message_category(self, message: str) -> TemplateCategory:
        """Classify message to determine appropriate template category"""
        
        message_lower = message.lower()
        
        # Simple keyword-based classification
        if any(word in message_lower for word in ['привет', 'хай', 'hello', 'здравствуй']):
            return TemplateCategory.GREETING
        elif any(word in message_lower for word in ['спасибо', 'благодарю', 'класс']):
            return TemplateCategory.APPRECIATION
        elif any(word in message_lower for word in ['купить', 'фото', 'видео', 'контент']):
            return TemplateCategory.PPV_PROMO
        elif any(word in message_lower for word in ['красивая', 'секси', 'нравишься']):
            return TemplateCategory.FLIRT
        elif any(word in message_lower for word in ['хочу', 'желаю', 'покажи']):
            return TemplateCategory.TEASE
        else:
            return TemplateCategory.FLIRT  # Default
    
    def _process_template_variables(self, text: str, context: Dict[str, Any]) -> str:
        """Process template variables"""
        
        replacements = {
            'name': context.get('user_name', 'красавчик'),
            'amount': context.get('amount', '10'),
            'time': datetime.now().strftime('%H:%M')
        }
        
        for var, value in replacements.items():
            text = text.replace(f'{{{var}}}', str(value))
        
        return text
    
    def _create_ai_prompt(self, user_message: str, context: Dict[str, Any]) -> str:
        """Create AI prompt based on context"""
        
        prefs = context.get('user_preferences')
        explicitness = prefs.explicitness_level.name.lower()
        mode = prefs.content_mode.value
        
        prompt = f"""
Ответь как привлекательная девушка в стиле {mode}.
Уровень откровенности: {explicitness}.
Сообщение пользователя: {user_message}

Ответ должен быть:
- Естественным и живым
- Соответствовать уровню откровенности
- Поощрять дальнейшее общение
- Содержать emoji
"""
        
        return prompt
    
    async def save_favorite_response(self, user_id: int, response: str):
        """Save response as user favorite"""
        prefs = self.get_user_preferences(user_id)
        
        if response not in prefs.favorite_responses:
            prefs.favorite_responses.append(response)
            
            # Limit favorites to 50
            if len(prefs.favorite_responses) > 50:
                prefs.favorite_responses.pop(0)
            
            logger.info(f"Saved favorite response for user {user_id}")
    
    async def rate_response(self, response_id: str, rating: float):
        """Rate response quality (1-5 stars)"""
        
        for metric in self.metrics:
            if metric.response_id == response_id:
                metric.user_feedback = rating
                
                # Update template quality if it was template-based
                if metric.template_used:
                    self.template_repo.update_quality_score(
                        metric.template_used, 
                        metric.quality_score
                    )
                
                logger.info(f"Rated response {response_id}: {rating}/5")
                break
    
    def get_performance_stats(self) -> Dict[str, Any]:
        """Get generator performance statistics"""
        
        if not self.metrics:
            return {}
        
        template_metrics = [m for m in self.metrics if m.generation_method == GenerationMethod.TEMPLATE]
        ai_metrics = [m for m in self.metrics if m.generation_method == GenerationMethod.AI]
        
        stats = {
            'total_responses': len(self.metrics),
            'template_ratio': len(template_metrics) / len(self.metrics),
            'avg_generation_time': sum(m.generation_time for m in self.metrics) / len(self.metrics),
            'template_avg_time': sum(m.generation_time for m in template_metrics) / len(template_metrics) if template_metrics else 0,
            'ai_avg_time': sum(m.generation_time for m in ai_metrics) / len(ai_metrics) if ai_metrics else 0,
            'cache_stats': self.cache.get_stats(),
            'ab_test_distribution': {
                group: len([p for p in self.user_preferences.values() if p.ab_test_group == group])
                for group in self.ab_test_groups.keys()
            }
        }
        
        return stats

# Global instance
response_generator = ResponseGenerator() 