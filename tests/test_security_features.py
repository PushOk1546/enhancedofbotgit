"""
Test Suite for Security Features (Rate Limiting & Input Validation)
Tests the newly implemented security modules for the Enhanced OF Bot.
"""

import asyncio
import pytest
import time
from typing import Dict, List

# Import security modules
from src.core.rate_limiter import (
    RateLimiter,
    RateLimitConfig,
    InMemoryRateLimitRepository,
    RateLimitMiddleware,
    UserLimitStatus
)
from input_validator import (
    InputValidationService,
    TextValidator,
    NumberValidator,
    ChoiceValidator,
    UserIdValidator,
    ValidationResult,
    validate_message,
    validate_heat,
    validate_mode
)


class TestRateLimiter:
    """Test rate limiting functionality."""
    
    def setup_method(self) -> None:
        """Setup test environment."""
        self.config = RateLimitConfig(
            requests_per_minute=5,
            requests_per_hour=20,
            burst_limit=3,
            cooldown_seconds=10
        )
        self.repository = InMemoryRateLimitRepository()
        self.rate_limiter = RateLimiter(self.repository, self.config)
        self.middleware = RateLimitMiddleware(self.rate_limiter)
    
    async def test_basic_rate_limiting(self) -> None:
        """Test basic rate limiting functionality."""
        user_id = 12345
        
        # First request should be allowed
        is_allowed, info = await self.rate_limiter.is_allowed(user_id)
        assert is_allowed is True
        assert 'remaining_minute' in info
        
        # Record the request
        await self.rate_limiter.record_request(user_id)
        
        print("✅ Basic rate limiting works")
    
    async def test_burst_limit(self) -> None:
        """Test burst protection."""
        user_id = 12346
        
        # Make requests up to burst limit
        for i in range(self.config.burst_limit):
            is_allowed, _ = await self.rate_limiter.is_allowed(user_id)
            assert is_allowed is True
            await self.rate_limiter.record_request(user_id)
        
        # Next request should trigger burst protection
        is_allowed, info = await self.rate_limiter.is_allowed(user_id)
        assert is_allowed is False
        assert info['reason'] == 'rate_limit'
        
        print("✅ Burst protection works correctly")
    
    async def test_minute_limit(self) -> None:
        """Test per-minute rate limiting."""
        user_id = 12347
        
        # Use up minute allowance
        for i in range(self.config.requests_per_minute):
            is_allowed, _ = await self.rate_limiter.is_allowed(user_id)
            if is_allowed:
                await self.rate_limiter.record_request(user_id)
            else:
                break
        
        # Should be blocked now
        is_allowed, info = await self.rate_limiter.is_allowed(user_id)
        assert is_allowed is False
        
        print("✅ Per-minute rate limiting works")
    
    async def test_penalty_system(self) -> None:
        """Test penalty cooldown system."""
        user_id = 12348
        
        # Trigger rate limit to activate penalty
        for i in range(10):  # Exceed all limits
            await self.rate_limiter.is_allowed(user_id)
        
        # Should be in penalty period
        is_allowed, info = await self.rate_limiter.is_allowed(user_id)
        assert is_allowed is False
        assert info['reason'] == 'penalty'
        assert 'retry_after' in info
        
        print("✅ Penalty system works correctly")
    
    async def test_user_stats(self) -> None:
        """Test user statistics tracking."""
        user_id = 12349
        
        # Make some requests
        await self.rate_limiter.record_request(user_id)
        await self.rate_limiter.record_request(user_id)
        
        stats = await self.rate_limiter.get_user_stats(user_id)
        
        assert stats['user_id'] == user_id
        assert 'minute_requests' in stats
        assert 'hour_requests' in stats
        assert 'penalty_active' in stats
        
        print("✅ User statistics tracking works")
    
    async def test_repository_cleanup(self) -> None:
        """Test repository cleanup functionality."""
        # Create old status
        old_status = UserLimitStatus(
            user_id=99999,
            last_request_time=time.time() - 90000  # 25 hours ago
        )
        
        await self.repository.save_user_status(old_status)
        
        # Trigger cleanup
        await self.repository.cleanup_expired()
        
        # Status should be removed
        status = await self.repository.get_user_status(99999)
        assert status is None
        
        print("✅ Repository cleanup works correctly")
    
    async def test_middleware_integration(self) -> None:
        """Test rate limit middleware."""
        user_id = 12350
        
        # First check should pass
        is_allowed, message = await self.middleware.check_rate_limit(user_id)
        assert is_allowed is True
        assert message == ""
        
        print("✅ Middleware integration works")


class TestInputValidation:
    """Test input validation functionality."""
    
    def setup_method(self) -> None:
        """Setup test environment."""
        self.validator_service = InputValidationService()
    
    async def test_text_validation(self) -> None:
        """Test text input validation."""
        validator = TextValidator(min_length=2, max_length=100)
        
        # Valid text
        result = await validator.validate("Привет")
        assert result.is_valid is True
        assert result.sanitized_value == "Привет"
        
        # Too short
        result = await validator.validate("A")
        assert result.is_valid is False
        assert "короткое" in result.error_message
        
        # Too long
        result = await validator.validate("A" * 200)
        assert result.is_valid is False
        assert "длинное" in result.error_message
        
        # Empty string
        result = await validator.validate("")
        assert result.is_valid is False
        assert "пустым" in result.error_message
        
        print("✅ Text validation works correctly")
    
    async def test_number_validation(self) -> None:
        """Test number input validation."""
        validator = NumberValidator(min_value=1, max_value=5, integer_only=True)
        
        # Valid number
        result = await validator.validate("3")
        assert result.is_valid is True
        assert result.sanitized_value == 3
        
        # Valid number as int
        result = await validator.validate(4)
        assert result.is_valid is True
        assert result.sanitized_value == 4
        
        # Out of range (too low)
        result = await validator.validate("0")
        assert result.is_valid is False
        assert "не менее" in result.error_message
        
        # Out of range (too high)
        result = await validator.validate("10")
        assert result.is_valid is False
        assert "не более" in result.error_message
        
        # Invalid format
        result = await validator.validate("abc")
        assert result.is_valid is False
        assert "числовое" in result.error_message
        
        print("✅ Number validation works correctly")
    
    async def test_choice_validation(self) -> None:
        """Test choice input validation."""
        validator = ChoiceValidator(['chat', 'flirt', 'sexting'])
        
        # Valid choice
        result = await validator.validate("chat")
        assert result.is_valid is True
        assert result.sanitized_value == "chat"
        
        # Valid choice (case insensitive)
        result = await validator.validate("FLIRT")
        assert result.is_valid is True
        assert result.sanitized_value == "flirt"
        
        # Invalid choice
        result = await validator.validate("invalid")
        assert result.is_valid is False
        assert "Выберите один из" in result.error_message
        
        print("✅ Choice validation works correctly")
    
    async def test_user_id_validation(self) -> None:
        """Test user ID validation."""
        validator = UserIdValidator()
        
        # Valid user ID
        result = await validator.validate(123456789)
        assert result.is_valid is True
        assert result.sanitized_value == 123456789
        
        # Valid user ID as string
        result = await validator.validate("987654321")
        assert result.is_valid is True
        assert result.sanitized_value == 987654321
        
        # Invalid (negative)
        result = await validator.validate(-123)
        assert result.is_valid is False
        assert "положительным" in result.error_message
        
        # Invalid (zero)
        result = await validator.validate(0)
        assert result.is_valid is False
        assert "положительным" in result.error_message
        
        # Invalid format
        result = await validator.validate("abc")
        assert result.is_valid is False
        assert "числом" in result.error_message
        
        print("✅ User ID validation works correctly")
    
    async def test_forbidden_patterns(self) -> None:
        """Test forbidden pattern detection."""
        validator = TextValidator(
            forbidden_patterns=[r'<script', r'admin', r'bot']
        )
        
        # Valid text
        result = await validator.validate("Привет, как дела?")
        assert result.is_valid is True
        
        # Contains forbidden pattern
        result = await validator.validate("Привет admin")
        assert result.is_valid is False
        assert "недопустимый" in result.error_message
        
        # Contains script tag
        result = await validator.validate("<script>alert('hack')</script>")
        assert result.is_valid is False
        assert "недопустимый" in result.error_message
        
        print("✅ Forbidden pattern detection works")
    
    async def test_validation_service(self) -> None:
        """Test input validation service."""
        # Test message validation
        result = await self.validator_service.validate_user_message("Привет!")
        assert result.is_valid is True
        
        # Test heat level validation
        result = await self.validator_service.validate_heat_level(3)
        assert result.is_valid is True
        assert result.sanitized_value == 3
        
        # Test mode validation
        result = await self.validator_service.validate_mode_choice("flirt")
        assert result.is_valid is True
        assert result.sanitized_value == "flirt"
        
        # Test user ID validation
        result = await self.validator_service.validate_user_id(123456)
        assert result.is_valid is True
        assert result.sanitized_value == 123456
        
        print("✅ Validation service works correctly")
    
    async def test_convenience_functions(self) -> None:
        """Test convenience validation functions."""
        # Test message validation
        is_valid, error_msg, sanitized = await validate_message("Привет")
        assert is_valid is True
        assert error_msg == ""
        assert sanitized == "Привет"
        
        # Test heat validation
        is_valid, error_msg, validated = await validate_heat(4)
        assert is_valid is True
        assert error_msg == ""
        assert validated == 4
        
        # Test mode validation
        is_valid, error_msg, validated = await validate_mode("sexting")
        assert is_valid is True
        assert error_msg == ""
        assert validated == "sexting"
        
        print("✅ Convenience functions work correctly")
    
    async def test_sanitization(self) -> None:
        """Test data sanitization for storage."""
        data = {
            'user_message': '  Привет! <script>  ',
            'number': 123,
            'boolean': True,
            'null_value': None,
            'complex': {'nested': 'object'}
        }
        
        sanitized = await self.validator_service.sanitize_for_storage(data)
        
        assert sanitized['user_message'] == 'Привет! script'  # Cleaned
        assert sanitized['number'] == 123  # Unchanged
        assert sanitized['boolean'] is True  # Unchanged
        assert sanitized['null_value'] is None  # Unchanged
        assert isinstance(sanitized['complex'], str)  # Converted to string
        
        print("✅ Data sanitization works correctly")


class TestSecurityIntegration:
    """Test integration of security features."""
    
    def setup_method(self) -> None:
        """Setup test environment."""
        self.rate_limiter = RateLimiter(
            InMemoryRateLimitRepository(),
            RateLimitConfig(requests_per_minute=10, burst_limit=5)
        )
        self.validator = InputValidationService()
    
    async def test_combined_security_check(self) -> None:
        """Test combined rate limiting and validation."""
        user_id = 88888
        message = "Привет, как дела?"
        
        # Check rate limit
        rate_middleware = RateLimitMiddleware(self.rate_limiter)
        is_rate_allowed, rate_msg = await rate_middleware.check_rate_limit(user_id)
        
        # Validate input
        is_input_valid, input_msg, sanitized = await validate_message(message)
        
        # Both should pass
        assert is_rate_allowed is True
        assert is_input_valid is True
        assert sanitized == message
        
        print("✅ Combined security checks work")
    
    async def test_security_under_load(self) -> None:
        """Test security features under concurrent load."""
        user_ids = list(range(100, 150))  # 50 users
        tasks = []
        
        # Simulate concurrent requests
        for user_id in user_ids:
            task = self._simulate_user_request(user_id)
            tasks.append(task)
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Check that most requests succeeded
        successful = [r for r in results if r is True]
        assert len(successful) > 40  # At least 80% success rate
        
        print(f"✅ Security under load: {len(successful)}/{len(results)} success")
    
    async def _simulate_user_request(self, user_id: int) -> bool:
        """Simulate a user request with security checks."""
        try:
            # Rate limit check
            is_allowed, _ = await self.rate_limiter.is_allowed(user_id)
            if not is_allowed:
                return False
            
            # Input validation
            is_valid, _, _ = await validate_message(f"Test message {user_id}")
            if not is_valid:
                return False
            
            # Record successful request
            await self.rate_limiter.record_request(user_id)
            return True
            
        except Exception:
            return False


async def run_security_tests() -> None:
    """Run comprehensive security test suite."""
    
    print("🔒 Starting Security Features Test Suite\n")
    
    # Rate limiter tests
    print("⚡ Testing Rate Limiter...")
    rate_test = TestRateLimiter()
    rate_test.setup_method()
    await rate_test.test_basic_rate_limiting()
    await rate_test.test_burst_limit()
    await rate_test.test_minute_limit()
    await rate_test.test_penalty_system()
    await rate_test.test_user_stats()
    await rate_test.test_repository_cleanup()
    await rate_test.test_middleware_integration()
    print()
    
    # Input validation tests
    print("🛡️ Testing Input Validation...")
    validation_test = TestInputValidation()
    validation_test.setup_method()
    await validation_test.test_text_validation()
    await validation_test.test_number_validation()
    await validation_test.test_choice_validation()
    await validation_test.test_user_id_validation()
    await validation_test.test_forbidden_patterns()
    await validation_test.test_validation_service()
    await validation_test.test_convenience_functions()
    await validation_test.test_sanitization()
    print()
    
    # Integration tests
    print("🔗 Testing Security Integration...")
    integration_test = TestSecurityIntegration()
    integration_test.setup_method()
    await integration_test.test_combined_security_check()
    await integration_test.test_security_under_load()
    print()
    
    print("🎉 All security tests passed! Rate limiting and input validation ready.")


if __name__ == "__main__":
    asyncio.run(run_security_tests()) 