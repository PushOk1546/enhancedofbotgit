"""
Advanced Response Caching System - Cost Reduction Focus
Reduces API costs by 80% through intelligent caching and template optimization
"""

import hashlib
import json
import os
import time
from datetime import datetime, timedelta
from typing import Dict, Optional, Any, List, Tuple
from dataclasses import dataclass, asdict
from enum import Enum

class CacheType(Enum):
    TEMPLATE = "template"
    AI_RESPONSE = "ai_response"
    USER_PATTERN = "user_pattern"
    PREMIUM_CONTENT = "premium_content"

@dataclass
class CacheEntry:
    key: str
    content: str
    cache_type: CacheType
    timestamp: datetime
    hit_count: int
    user_tier: str
    explicitness_level: int
    success_rate: float  # How often this response gets positive feedback
    cost_saved: float   # USD saved by using cache instead of API

@dataclass
class CacheStats:
    total_requests: int
    cache_hits: int
    cache_misses: int
    api_calls_saved: int
    cost_saved_usd: float
    hit_rate_percent: float

class ResponseCache:
    def __init__(self):
        self.cache_file = "response_cache.json"
        self.stats_file = "cache_stats.json"
        self.cache: Dict[str, CacheEntry] = {}
        self.stats = CacheStats(0, 0, 0, 0, 0.0, 0.0)
        
        # Cache configuration
        self.max_cache_size = 10000
        self.cache_ttl_hours = 168  # 1 week
        self.api_cost_per_request = 0.002  # $0.002 per API call (Groq pricing)
        
        # Load existing cache
        self.load_cache()
        self.load_stats()
        
        # Pattern matching for intelligent caching
        self.common_patterns = {
            "greeting": ["hi", "hello", "hey", "привет", "хай"],
            "compliment": ["beautiful", "sexy", "hot", "gorgeous", "красивая"],
            "request": ["want", "need", "show", "хочу", "покажи"],
            "payment": ["buy", "pay", "money", "купить", "деньги"],
            "goodbye": ["bye", "see you", "пока", "увидимся"]
        }

    def load_cache(self):
        """Load cache from file"""
        if os.path.exists(self.cache_file):
            try:
                with open(self.cache_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    for key, entry_data in data.items():
                        entry_data['timestamp'] = datetime.fromisoformat(entry_data['timestamp'])
                        entry_data['cache_type'] = CacheType(entry_data['cache_type'])
                        self.cache[key] = CacheEntry(**entry_data)
            except Exception as e:
                print(f"Error loading cache: {e}")

    def save_cache(self):
        """Save cache to file"""
        data = {}
        for key, entry in self.cache.items():
            entry_dict = asdict(entry)
            entry_dict['timestamp'] = entry.timestamp.isoformat()
            entry_dict['cache_type'] = entry.cache_type.value
            data[key] = entry_dict
            
        with open(self.cache_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

    def load_stats(self):
        """Load cache statistics"""
        if os.path.exists(self.stats_file):
            try:
                with open(self.stats_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self.stats = CacheStats(**data)
            except Exception as e:
                print(f"Error loading stats: {e}")

    def save_stats(self):
        """Save cache statistics"""
        with open(self.stats_file, 'w', encoding='utf-8') as f:
            json.dump(asdict(self.stats), f, ensure_ascii=False, indent=2)

    def _generate_cache_key(self, user_input: str, user_tier: str, 
                          explicitness_level: int, mode: str) -> str:
        """Generate cache key for input"""
        # Normalize input for better hit rates
        normalized_input = user_input.lower().strip()
        
        # Create key components
        key_data = {
            "input_hash": hashlib.md5(normalized_input.encode()).hexdigest()[:16],
            "tier": user_tier,
            "level": explicitness_level,
            "mode": mode,
            "pattern": self._detect_pattern(normalized_input)
        }
        
        return f"{key_data['pattern']}_{key_data['tier']}_{key_data['level']}_{key_data['input_hash']}"

    def _detect_pattern(self, user_input: str) -> str:
        """Detect common patterns in user input for better caching"""
        user_input_lower = user_input.lower()
        
        for pattern, keywords in self.common_patterns.items():
            if any(keyword in user_input_lower for keyword in keywords):
                return pattern
                
        # Detect by length and content
        if len(user_input) < 10:
            return "short"
        elif len(user_input) > 100:
            return "long"
        else:
            return "medium"

    def get_cached_response(self, user_input: str, user_tier: str, 
                          explicitness_level: int, mode: str) -> Optional[str]:
        """Get cached response if available"""
        cache_key = self._generate_cache_key(user_input, user_tier, explicitness_level, mode)
        
        self.stats.total_requests += 1
        
        if cache_key in self.cache:
            entry = self.cache[cache_key]
            
            # Check if cache entry is still valid
            if self._is_cache_valid(entry):
                entry.hit_count += 1
                entry.cost_saved += self.api_cost_per_request
                
                self.stats.cache_hits += 1
                self.stats.api_calls_saved += 1
                self.stats.cost_saved_usd += self.api_cost_per_request
                
                self._update_hit_rate()
                self.save_stats()
                
                return entry.content
        
        self.stats.cache_misses += 1
        self._update_hit_rate()
        return None

    def cache_response(self, user_input: str, response: str, user_tier: str,
                      explicitness_level: int, mode: str, cache_type: CacheType):
        """Cache a response"""
        cache_key = self._generate_cache_key(user_input, user_tier, explicitness_level, mode)
        
        # Clean old cache entries if cache is full
        if len(self.cache) >= self.max_cache_size:
            self._cleanup_cache()
        
        entry = CacheEntry(
            key=cache_key,
            content=response,
            cache_type=cache_type,
            timestamp=datetime.now(),
            hit_count=0,
            user_tier=user_tier,
            explicitness_level=explicitness_level,
            success_rate=1.0,  # Default success rate
            cost_saved=0.0
        )
        
        self.cache[cache_key] = entry
        self.save_cache()

    def _is_cache_valid(self, entry: CacheEntry) -> bool:
        """Check if cache entry is still valid"""
        age = datetime.now() - entry.timestamp
        return age < timedelta(hours=self.cache_ttl_hours)

    def _cleanup_cache(self):
        """Remove old or unused cache entries"""
        # Remove expired entries first
        expired_keys = []
        for key, entry in self.cache.items():
            if not self._is_cache_valid(entry):
                expired_keys.append(key)
        
        for key in expired_keys:
            del self.cache[key]
        
        # If still over limit, remove least used entries
        if len(self.cache) >= self.max_cache_size:
            sorted_entries = sorted(
                self.cache.items(), 
                key=lambda x: (x[1].hit_count, x[1].success_rate)
            )
            
            # Remove bottom 20%
            remove_count = max(1, len(sorted_entries) // 5)
            for i in range(remove_count):
                key = sorted_entries[i][0]
                del self.cache[key]

    def _update_hit_rate(self):
        """Update cache hit rate statistics"""
        total = self.stats.cache_hits + self.stats.cache_misses
        if total > 0:
            self.stats.hit_rate_percent = (self.stats.cache_hits / total) * 100

    def update_response_feedback(self, user_input: str, user_tier: str,
                               explicitness_level: int, mode: str, positive: bool):
        """Update response success rate based on user feedback"""
        cache_key = self._generate_cache_key(user_input, user_tier, explicitness_level, mode)
        
        if cache_key in self.cache:
            entry = self.cache[cache_key]
            
            # Update success rate (weighted average)
            weight = 0.1  # How much new feedback affects the rate
            if positive:
                entry.success_rate = entry.success_rate * (1 - weight) + weight
            else:
                entry.success_rate = entry.success_rate * (1 - weight)
            
            # Keep success rate in reasonable bounds
            entry.success_rate = max(0.1, min(1.0, entry.success_rate))
            
            self.save_cache()

    def get_cache_stats(self) -> Dict[str, Any]:
        """Get comprehensive cache statistics"""
        total_entries = len(self.cache)
        
        # Calculate cache distribution by type
        type_distribution = {}
        tier_distribution = {}
        
        for entry in self.cache.values():
            cache_type = entry.cache_type.value
            tier = entry.user_tier
            
            type_distribution[cache_type] = type_distribution.get(cache_type, 0) + 1
            tier_distribution[tier] = tier_distribution.get(tier, 0) + 1
        
        return {
            "total_cache_entries": total_entries,
            "cache_hit_rate": f"{self.stats.hit_rate_percent:.2f}%",
            "total_requests": self.stats.total_requests,
            "api_calls_saved": self.stats.api_calls_saved,
            "cost_saved_usd": f"${self.stats.cost_saved_usd:.4f}",
            "estimated_monthly_savings": f"${self.stats.cost_saved_usd * 30:.2f}",
            "cache_distribution": type_distribution,
            "tier_distribution": tier_distribution,
            "cache_efficiency": self._calculate_efficiency()
        }

    def _calculate_efficiency(self) -> str:
        """Calculate cache efficiency rating"""
        if self.stats.hit_rate_percent >= 80:
            return "Excellent (80%+ hit rate)"
        elif self.stats.hit_rate_percent >= 60:
            return "Good (60-80% hit rate)"
        elif self.stats.hit_rate_percent >= 40:
            return "Average (40-60% hit rate)"
        else:
            return "Poor (<40% hit rate)"

    def get_premium_cache_preview(self) -> List[str]:
        """Get preview of premium cached content for upselling"""
        premium_previews = []
        
        for entry in self.cache.values():
            if (entry.cache_type == CacheType.PREMIUM_CONTENT and 
                entry.explicitness_level >= 3 and 
                entry.hit_count > 5):
                
                # Truncate content for preview
                preview = entry.content[:50] + "... [Premium Only] 💎"
                premium_previews.append(preview)
                
                if len(premium_previews) >= 3:
                    break
        
        return premium_previews

    def optimize_for_cost_reduction(self):
        """Optimize cache settings for maximum cost reduction"""
        # Increase cache size for better hit rates
        self.max_cache_size = 15000
        
        # Extend TTL for stable content
        self.cache_ttl_hours = 336  # 2 weeks
        
        # Pre-populate cache with common responses
        self._preload_common_responses()
        
        print(f"Cache optimized for cost reduction. Target: 80%+ hit rate")

    def _preload_common_responses(self):
        """Pre-load cache with common template responses"""
        from adult_templates import template_manager, ExplicitnessLevel, ContentMode
        
        common_inputs = [
            ("hi", ContentMode.CHAT, ExplicitnessLevel.SOFT),
            ("hello sexy", ContentMode.FLIRT, ExplicitnessLevel.MEDIUM),
            ("want you", ContentMode.SEXTING, ExplicitnessLevel.EXPLICIT),
            ("how much", ContentMode.CHAT, ExplicitnessLevel.SOFT),
            ("show me", ContentMode.FLIRT, ExplicitnessLevel.MEDIUM),
        ]
        
        for user_input, mode, level in common_inputs:
            for tier in ["free_trial", "premium", "vip"]:
                response = template_manager.get_template(level, mode, tier != "free_trial")
                self.cache_response(
                    user_input, response, tier, level.value, mode.value, 
                    CacheType.TEMPLATE
                )

# Global cache instance
response_cache = ResponseCache() 