"""
Test Suite for Enhanced OF Bot System
Professional testing of adult content templates, caching, and user preferences.
"""

import asyncio
import pytest
import json
import time
from typing import Dict, List

# Import enhanced system modules
from adult_templates import (
    AdultTemplateRepository, 
    ExplicitnessLevel, 
    ContentMode, 
    TemplateCategory,
    ContentTemplate,
    FallbackSystem
)
from response_generator import (
    ResponseGenerator, 
    UserPreferences, 
    InMemoryCache,
    GenerationMethod
)

class TestAdultTemplateSystem:
    """Test adult template repository and categorization"""
    
    def setup_method(self):
        """Setup test environment"""
        self.repo = AdultTemplateRepository()
        self.fallback = FallbackSystem(self.repo)
    
    def test_template_repository_initialization(self):
        """Test template repository loads correctly"""
        assert len(self.repo.templates) > 0
        assert TemplateCategory.GREETING in self.repo.templates
        assert TemplateCategory.FLIRT in self.repo.templates
        assert TemplateCategory.PPV_PROMO in self.repo.templates
        
        print("✅ Template repository initialized correctly")
    
    def test_template_filtering(self):
        """Test template filtering by various criteria"""
        
        # Test by explicitness level
        soft_templates = self.repo.get_templates(explicitness=ExplicitnessLevel.SOFT)
        explicit_templates = self.repo.get_templates(explicitness=ExplicitnessLevel.EXPLICIT)
        
        assert len(soft_templates) > 0
        assert len(explicit_templates) > 0
        assert all(t.explicitness == ExplicitnessLevel.SOFT for t in soft_templates)
        
        # Test by mode
        chat_templates = self.repo.get_templates(mode=ContentMode.CHAT)
        sexting_templates = self.repo.get_templates(mode=ContentMode.SEXTING)
        
        assert len(chat_templates) > 0
        assert len(sexting_templates) > 0
        
        # Test by category
        greeting_templates = self.repo.get_templates(category=TemplateCategory.GREETING)
        ppv_templates = self.repo.get_templates(category=TemplateCategory.PPV_PROMO)
        
        assert len(greeting_templates) > 0
        assert len(ppv_templates) > 0
        
        print("✅ Template filtering works correctly")
    
    def test_template_variables(self):
        """Test template variable processing"""
        
        context = {
            'user_name': 'Алексей',
            'amount': '25',
            'time': '14:30'
        }
        
        # Find template with variables
        ppv_templates = self.repo.get_templates(category=TemplateCategory.PPV_PROMO)
        template_with_vars = next((t for t in ppv_templates if '{amount}' in t.text), None)
        
        if template_with_vars:
            processed = self.fallback._process_template_variables(template_with_vars.text, context)
            assert '{amount}' not in processed
            assert '25' in processed
            
        print("✅ Template variables processed correctly")
    
    async def test_fallback_system(self):
        """Test fallback response system"""
        
        context = {'user_name': 'Тест'}
        
        # Test different explicitness levels
        for level in ExplicitnessLevel:
            response = await self.fallback.get_fallback_response(level, context)
            assert isinstance(response, str)
            assert len(response) > 0
            
        print("✅ Fallback system works for all explicitness levels")

class TestCachingSystem:
    """Test caching and performance optimization"""
    
    def setup_method(self):
        """Setup test environment"""
        self.cache = InMemoryCache(max_size=100)
    
    async def test_cache_basic_operations(self):
        """Test basic cache operations"""
        
        context = {'user_message': 'test', 'explicitness': 'MEDIUM'}
        
        # Test cache miss
        result = await self.cache.get(context)
        assert result is None
        
        # Test cache set
        await self.cache.set(context, "Test response", GenerationMethod.TEMPLATE)
        
        # Test cache hit
        result = await self.cache.get(context)
        assert result == "Test response"
        
        print("✅ Basic cache operations work correctly")
    
    async def test_cache_expiration(self):
        """Test cache TTL and expiration"""
        
        # Create cache with short TTL
        short_cache = InMemoryCache(max_size=100, default_ttl=1)
        
        context = {'user_message': 'expire_test'}
        await short_cache.set(context, "Expiring response", GenerationMethod.TEMPLATE)
        
        # Should be available immediately
        result = await short_cache.get(context)
        assert result == "Expiring response"
        
        # Wait for expiration
        await asyncio.sleep(1.1)
        
        # Should be expired
        result = await short_cache.get(context)
        assert result is None
        
        print("✅ Cache expiration works correctly")
    
    async def test_cache_lru_eviction(self):
        """Test LRU eviction policy"""
        
        small_cache = InMemoryCache(max_size=3)
        
        # Fill cache to capacity
        for i in range(3):
            context = {'user_message': f'test_{i}'}
            await small_cache.set(context, f"Response {i}", GenerationMethod.TEMPLATE)
        
        # Verify all items are cached
        assert len(small_cache.cache) == 3
        
        # Access first item to make it recently used
        context_0 = {'user_message': 'test_0'}
        await small_cache.get(context_0)
        
        # Add new item (should evict test_1, not test_0)
        context_new = {'user_message': 'test_new'}
        await small_cache.set(context_new, "New response", GenerationMethod.TEMPLATE)
        
        # test_1 should be evicted
        context_1 = {'user_message': 'test_1'}
        result = await small_cache.get(context_1)
        assert result is None
        
        # test_0 should still be available
        result = await small_cache.get(context_0)
        assert result is not None
        
        print("✅ LRU eviction works correctly")
    
    def test_cache_stats(self):
        """Test cache statistics"""
        
        stats = self.cache.get_stats()
        
        assert 'size' in stats
        assert 'max_size' in stats
        assert 'total_hits' in stats
        assert 'avg_quality_score' in stats
        assert 'methods' in stats
        
        print("✅ Cache statistics are properly formatted")

class TestResponseGenerator:
    """Test response generation system"""
    
    def setup_method(self):
        """Setup test environment"""
        self.generator = ResponseGenerator()
    
    def test_user_preferences_creation(self):
        """Test user preferences initialization"""
        
        user_id = 12345
        prefs = self.generator.get_user_preferences(user_id)
        
        assert prefs.user_id == user_id
        assert isinstance(prefs.explicitness_level, ExplicitnessLevel)
        assert isinstance(prefs.content_mode, ContentMode)
        assert prefs.ab_test_group in self.generator.ab_test_groups
        
        print("✅ User preferences created correctly")
    
    async def test_preference_updates(self):
        """Test user preference updates"""
        
        user_id = 12346
        
        # Update explicitness level
        await self.generator.update_user_preference(
            user_id, 'explicitness_level', ExplicitnessLevel.EXPLICIT
        )
        
        prefs = self.generator.get_user_preferences(user_id)
        assert prefs.explicitness_level == ExplicitnessLevel.EXPLICIT
        
        # Update content mode
        await self.generator.update_user_preference(
            user_id, 'content_mode', ContentMode.SEXTING
        )
        
        prefs = self.generator.get_user_preferences(user_id)
        assert prefs.content_mode == ContentMode.SEXTING
        
        print("✅ User preference updates work correctly")
    
    async def test_template_response_generation(self):
        """Test template-based response generation"""
        
        user_id = 12347
        context = {
            'user_id': user_id,
            'user_message': 'привет',
            'user_name': 'Тестер'
        }
        
        # Force template generation
        response = await self.generator._generate_template_response("привет", context)
        
        assert isinstance(response, str)
        assert len(response) > 0
        
        print("✅ Template response generation works")
    
    async def test_favorite_system(self):
        """Test favorite responses functionality"""
        
        user_id = 12348
        test_response = "Это тестовый ответ для избранного"
        
        # Add to favorites
        await self.generator.save_favorite_response(user_id, test_response)
        
        prefs = self.generator.get_user_preferences(user_id)
        assert test_response in prefs.favorite_responses
        
        # Test duplicate prevention
        await self.generator.save_favorite_response(user_id, test_response)
        assert prefs.favorite_responses.count(test_response) == 1
        
        print("✅ Favorite system works correctly")
    
    def test_performance_stats(self):
        """Test performance statistics"""
        
        stats = self.generator.get_performance_stats()
        
        # Stats should be available even if empty
        assert isinstance(stats, dict)
        
        # If we have metrics, they should be properly formatted
        if stats:
            assert 'total_responses' in stats
            assert 'template_ratio' in stats
            assert 'cache_stats' in stats
        
        print("✅ Performance statistics are properly formatted")
    
    def test_ab_testing_groups(self):
        """Test A/B testing group assignment"""
        
        # Create multiple users and check group distribution
        group_counts = {}
        
        for i in range(100):
            prefs = self.generator.get_user_preferences(i)
            group = prefs.ab_test_group
            group_counts[group] = group_counts.get(group, 0) + 1
        
        # Should have users in multiple groups
        assert len(group_counts) > 1
        
        # All groups should be valid
        for group in group_counts:
            assert group in self.generator.ab_test_groups
        
        print(f"✅ A/B testing groups distributed: {group_counts}")

class TestIntegrationScenarios:
    """Test real-world integration scenarios"""
    
    def setup_method(self):
        """Setup test environment"""
        self.generator = ResponseGenerator()
    
    async def test_full_conversation_flow(self):
        """Test complete conversation flow"""
        
        user_id = 99999
        
        # 1. User starts conversation
        context = {
            'user_id': user_id,
            'user_message': 'Привет',
            'user_name': 'Максим'
        }
        
        response1 = await self.generator.generate_response("Привет", context)
        assert isinstance(response1, str)
        assert len(response1) > 0
        
        # 2. User continues conversation
        context['user_message'] = 'Как дела?'
        response2 = await self.generator.generate_response("Как дела?", context)
        assert isinstance(response2, str)
        
        # 3. User shows interest in content
        context['user_message'] = 'Покажи свои фото'
        response3 = await self.generator.generate_response("Покажи свои фото", context)
        assert isinstance(response3, str)
        
        # Verify user stats are updated
        prefs = self.generator.get_user_preferences(user_id)
        assert prefs.total_responses == 3
        
        print("✅ Full conversation flow works correctly")
    
    async def test_explicitness_progression(self):
        """Test explicitness level progression"""
        
        user_id = 99998
        
        # Start with soft level
        await self.generator.update_user_preference(
            user_id, 'explicitness_level', ExplicitnessLevel.SOFT
        )
        
        context_soft = {
            'user_id': user_id,
            'user_message': 'ты красивая soft',  # Make messages different to avoid cache
            'user_name': 'Игорь'
        }
        
        response_soft = await self.generator.generate_response("ты красивая soft", context_soft)
        
        # Escalate to explicit
        await self.generator.update_user_preference(
            user_id, 'explicitness_level', ExplicitnessLevel.EXPLICIT
        )
        
        context_explicit = {
            'user_id': user_id,
            'user_message': 'ты красивая explicit',  # Different message to avoid cache
            'user_name': 'Игорь'
        }
        
        response_explicit = await self.generator.generate_response("ты красивая explicit", context_explicit)
        
        # Both responses should be valid strings
        assert isinstance(response_soft, str)
        assert isinstance(response_explicit, str)
        assert len(response_soft) > 0
        assert len(response_explicit) > 0
        
        print("✅ Explicitness progression works correctly")
    
    async def test_performance_under_load(self):
        """Test system performance under load"""
        
        start_time = time.time()
        
        # Generate 50 responses concurrently
        tasks = []
        for i in range(50):
            context = {
                'user_id': i,
                'user_message': f'Тест {i}',
                'user_name': f'User{i}'
            }
            task = self.generator.generate_response(f"Тест {i}", context)
            tasks.append(task)
        
        responses = await asyncio.gather(*tasks, return_exceptions=True)
        
        end_time = time.time()
        total_time = end_time - start_time
        
        # Check that all responses were generated
        successful_responses = [r for r in responses if isinstance(r, str)]
        assert len(successful_responses) == 50
        
        # Performance should be reasonable (less than 10 seconds for 50 responses)
        assert total_time < 10.0
        
        avg_time = total_time / 50
        print(f"✅ Performance test passed: {avg_time:.3f}s per response")
    
    async def test_cache_effectiveness(self):
        """Test cache effectiveness in reducing generation time"""
        
        context = {
            'user_id': 88888,
            'user_message': 'Тест кэша',
            'user_name': 'Кэш'
        }
        
        # First generation (cache miss)
        start_time = time.time()
        response1 = await self.generator.generate_response("Тест кэша", context)
        first_time = time.time() - start_time
        
        # Second generation (cache hit)
        start_time = time.time()
        response2 = await self.generator.generate_response("Тест кэша", context)
        second_time = time.time() - start_time
        
        # Should be same response
        assert response1 == response2
        
        # Second should be faster (cache hit)
        assert second_time < first_time
        
        print(f"✅ Cache effectiveness: {first_time:.3f}s vs {second_time:.3f}s")

async def run_all_tests():
    """Run comprehensive test suite"""
    
    print("🚀 Starting Enhanced OF Bot Test Suite\n")
    
    # Template system tests
    print("📋 Testing Template System...")
    template_test = TestAdultTemplateSystem()
    template_test.setup_method()
    template_test.test_template_repository_initialization()
    template_test.test_template_filtering()
    template_test.test_template_variables()
    await template_test.test_fallback_system()
    print()
    
    # Caching system tests
    print("🗄️ Testing Caching System...")
    cache_test = TestCachingSystem()
    cache_test.setup_method()
    await cache_test.test_cache_basic_operations()
    await cache_test.test_cache_expiration()
    await cache_test.test_cache_lru_eviction()
    cache_test.test_cache_stats()
    print()
    
    # Response generator tests
    print("🤖 Testing Response Generator...")
    generator_test = TestResponseGenerator()
    generator_test.setup_method()
    generator_test.test_user_preferences_creation()
    await generator_test.test_preference_updates()
    await generator_test.test_template_response_generation()
    await generator_test.test_favorite_system()
    generator_test.test_performance_stats()
    generator_test.test_ab_testing_groups()
    print()
    
    # Integration tests
    print("🔗 Testing Integration Scenarios...")
    integration_test = TestIntegrationScenarios()
    integration_test.setup_method()
    await integration_test.test_full_conversation_flow()
    await integration_test.test_explicitness_progression()
    await integration_test.test_performance_under_load()
    await integration_test.test_cache_effectiveness()
    print()
    
    print("🎉 All tests passed! Enhanced OF Bot system is ready for production.")

def test_template_quality_scores():
    """Test template quality scoring"""
    
    repo = AdultTemplateRepository()
    
    # Test initial quality scores
    for category, templates in repo.templates.items():
        for template in templates:
            assert 0.1 <= template.quality_score <= 2.0
    
    # Test quality score updates
    test_template = list(repo.templates.values())[0][0]
    original_score = test_template.quality_score
    
    repo.update_quality_score(test_template.text, 1.5)
    assert test_template.quality_score == 1.5
    assert test_template.quality_score != original_score
    
    print("✅ Template quality scoring works correctly")

def test_serialization():
    """Test user preferences serialization"""
    
    generator = ResponseGenerator()
    user_id = 77777
    
    # Create and modify preferences
    prefs = generator.get_user_preferences(user_id)
    prefs.explicitness_level = ExplicitnessLevel.EXPLICIT
    prefs.content_mode = ContentMode.SEXTING
    prefs.favorite_responses.append("Test favorite")
    
    # Test serialization
    serialized = prefs.to_dict()
    assert isinstance(serialized, dict)
    assert 'user_id' in serialized
    assert 'explicitness_level' in serialized
    
    # Test deserialization
    restored = UserPreferences.from_dict(serialized)
    assert restored.user_id == prefs.user_id
    assert restored.explicitness_level == prefs.explicitness_level
    assert restored.content_mode == prefs.content_mode
    assert restored.favorite_responses == prefs.favorite_responses
    
    print("✅ Serialization/deserialization works correctly")

if __name__ == "__main__":
    # Run synchronous tests
    test_template_quality_scores()
    test_serialization()
    
    # Run asynchronous tests
    asyncio.run(run_all_tests()) 