"""
Input Validation Module for Enhanced OF Bot
Provides comprehensive validation for user inputs and bot data.
"""

import re
import logging
from typing import Optional, Dict, List, Any, Union, Tuple
from dataclasses import dataclass
from abc import ABC, abstractmethod

logger = logging.getLogger(__name__)


@dataclass
class ValidationResult:
    """Result of input validation with details."""
    
    is_valid: bool
    value: Any = None
    error_message: Optional[str] = None
    sanitized_value: Optional[Any] = None
    
    @property
    def safe_value(self) -> Any:
        """Get sanitized value or original if sanitization failed."""
        return self.sanitized_value if self.sanitized_value is not None else self.value


class BaseValidator(ABC):
    """Abstract base validator for all input types."""
    
    @abstractmethod
    async def validate(self, value: Any) -> ValidationResult:
        """Validate input value and return result."""
        pass


class TextValidator(BaseValidator):
    """Validator for text inputs with length and content checks."""
    
    def __init__(
        self,
        min_length: int = 1,
        max_length: int = 4000,
        allow_empty: bool = False,
        strip_whitespace: bool = True,
        forbidden_patterns: Optional[List[str]] = None
    ) -> None:
        """Initialize text validator with configuration."""
        self.min_length = min_length
        self.max_length = max_length
        self.allow_empty = allow_empty
        self.strip_whitespace = strip_whitespace
        self.forbidden_patterns = forbidden_patterns or []
    
    async def validate(self, value: Any) -> ValidationResult:
        """Validate text input."""
        # Type check
        if not isinstance(value, str):
            return ValidationResult(
                is_valid=False,
                value=value,
                error_message="Ожидается текстовое сообщение"
            )
        
        # Sanitize
        sanitized = value.strip() if self.strip_whitespace else value
        
        # Empty check
        if not sanitized and not self.allow_empty:
            return ValidationResult(
                is_valid=False,
                value=value,
                error_message="Сообщение не может быть пустым"
            )
        
        # Length checks
        if len(sanitized) < self.min_length:
            return ValidationResult(
                is_valid=False,
                value=value,
                error_message=f"Сообщение слишком короткое (мин. {self.min_length})"
            )
        
        if len(sanitized) > self.max_length:
            return ValidationResult(
                is_valid=False,
                value=value,
                error_message=f"Сообщение слишком длинное (макс. {self.max_length})"
            )
        
        # Pattern checks
        for pattern in self.forbidden_patterns:
            if re.search(pattern, sanitized, re.IGNORECASE):
                return ValidationResult(
                    is_valid=False,
                    value=value,
                    error_message="Сообщение содержит недопустимый контент"
                )
        
        return ValidationResult(
            is_valid=True,
            value=value,
            sanitized_value=sanitized
        )


class NumberValidator(BaseValidator):
    """Validator for numeric inputs with range checks."""
    
    def __init__(
        self,
        min_value: Optional[Union[int, float]] = None,
        max_value: Optional[Union[int, float]] = None,
        integer_only: bool = False
    ) -> None:
        """Initialize number validator with range constraints."""
        self.min_value = min_value
        self.max_value = max_value
        self.integer_only = integer_only
    
    async def validate(self, value: Any) -> ValidationResult:
        """Validate numeric input."""
        # Try to convert to number
        try:
            if isinstance(value, str):
                num_value = int(value) if self.integer_only else float(value)
            elif isinstance(value, (int, float)):
                num_value = int(value) if self.integer_only else value
            else:
                return ValidationResult(
                    is_valid=False,
                    value=value,
                    error_message="Ожидается числовое значение"
                )
        except ValueError:
            return ValidationResult(
                is_valid=False,
                value=value,
                error_message="Некорректное числовое значение"
            )
        
        # Range checks
        if self.min_value is not None and num_value < self.min_value:
            return ValidationResult(
                is_valid=False,
                value=value,
                error_message=f"Значение должно быть не менее {self.min_value}"
            )
        
        if self.max_value is not None and num_value > self.max_value:
            return ValidationResult(
                is_valid=False,
                value=value,
                error_message=f"Значение должно быть не более {self.max_value}"
            )
        
        return ValidationResult(
            is_valid=True,
            value=value,
            sanitized_value=num_value
        )


class ChoiceValidator(BaseValidator):
    """Validator for choice-based inputs."""
    
    def __init__(
        self,
        valid_choices: List[Any],
        case_sensitive: bool = False
    ) -> None:
        """Initialize choice validator with valid options."""
        self.valid_choices = valid_choices
        self.case_sensitive = case_sensitive
    
    async def validate(self, value: Any) -> ValidationResult:
        """Validate choice input."""
        if self.case_sensitive:
            is_valid = value in self.valid_choices
            matched_choice = value if is_valid else None
        else:
            # Case-insensitive string comparison
            if isinstance(value, str):
                for choice in self.valid_choices:
                    if isinstance(choice, str) and value.lower() == choice.lower():
                        is_valid = True
                        matched_choice = choice
                        break
                else:
                    is_valid = False
                    matched_choice = None
            else:
                is_valid = value in self.valid_choices
                matched_choice = value if is_valid else None
        
        if not is_valid:
            choices_str = ", ".join(str(c) for c in self.valid_choices)
            return ValidationResult(
                is_valid=False,
                value=value,
                error_message=f"Выберите один из: {choices_str}"
            )
        
        return ValidationResult(
            is_valid=True,
            value=value,
            sanitized_value=matched_choice
        )


class UserIdValidator(BaseValidator):
    """Validator for Telegram user IDs."""
    
    async def validate(self, value: Any) -> ValidationResult:
        """Validate Telegram user ID."""
        # Convert to int if possible
        try:
            if isinstance(value, str):
                user_id = int(value)
            elif isinstance(value, int):
                user_id = value
            else:
                return ValidationResult(
                    is_valid=False,
                    value=value,
                    error_message="Некорректный ID пользователя"
                )
        except ValueError:
            return ValidationResult(
                is_valid=False,
                value=value,
                error_message="ID пользователя должен быть числом"
            )
        
        # Telegram user IDs are positive integers
        if user_id <= 0:
            return ValidationResult(
                is_valid=False,
                value=value,
                error_message="ID пользователя должен быть положительным"
            )
        
        # Reasonable range for Telegram user IDs
        if user_id > 2**63 - 1:  # Max int64
            return ValidationResult(
                is_valid=False,
                value=value,
                error_message="Слишком большой ID пользователя"
            )
        
        return ValidationResult(
            is_valid=True,
            value=value,
            sanitized_value=user_id
        )


class CompositeValidator(BaseValidator):
    """Validator that combines multiple validators."""
    
    def __init__(self, validators: List[BaseValidator]) -> None:
        """Initialize with list of validators to apply."""
        self.validators = validators
    
    async def validate(self, value: Any) -> ValidationResult:
        """Apply all validators in sequence."""
        current_value = value
        
        for validator in self.validators:
            result = await validator.validate(current_value)
            
            if not result.is_valid:
                return result
            
            # Use sanitized value for next validator
            current_value = result.safe_value
        
        return ValidationResult(
            is_valid=True,
            value=value,
            sanitized_value=current_value
        )


class InputValidationService:
    """Service for common bot input validation scenarios."""
    
    def __init__(self) -> None:
        """Initialize validation service with predefined validators."""
        # Common forbidden patterns for OF bot
        self.forbidden_patterns = [
            r'\b(admin|moderator|bot|система)\b',  # System-related
            r'<script|javascript:|data:',           # XSS attempts
            r'[<>{}\\]',                           # Suspicious chars
        ]
        
        # Predefined validators
        self.validators = {
            'user_message': TextValidator(
                min_length=1,
                max_length=4000,
                forbidden_patterns=self.forbidden_patterns
            ),
            'chat_name': TextValidator(
                min_length=1,
                max_length=100,
                forbidden_patterns=self.forbidden_patterns
            ),
            'heat_level': CompositeValidator([
                NumberValidator(min_value=1, max_value=5, integer_only=True)
            ]),
            'mode_choice': ChoiceValidator(
                valid_choices=['chat', 'flirt', 'sexting'],
                case_sensitive=False
            ),
            'user_id': UserIdValidator(),
            'rating': NumberValidator(
                min_value=1, max_value=5, integer_only=True
            ),
            'amount': NumberValidator(
                min_value=1, max_value=1000, integer_only=True
            )
        }
    
    async def validate_user_message(self, message: str) -> ValidationResult:
        """Validate user chat message."""
        return await self.validators['user_message'].validate(message)
    
    async def validate_heat_level(self, level: Any) -> ValidationResult:
        """Validate explicitness heat level (1-5)."""
        return await self.validators['heat_level'].validate(level)
    
    async def validate_mode_choice(self, mode: str) -> ValidationResult:
        """Validate communication mode choice."""
        return await self.validators['mode_choice'].validate(mode)
    
    async def validate_user_id(self, user_id: Any) -> ValidationResult:
        """Validate Telegram user ID."""
        return await self.validators['user_id'].validate(user_id)
    
    async def validate_rating(self, rating: Any) -> ValidationResult:
        """Validate response rating (1-5 stars)."""
        return await self.validators['rating'].validate(rating)
    
    async def validate_custom(
        self, 
        value: Any, 
        validator_key: str
    ) -> ValidationResult:
        """Validate using custom validator by key."""
        if validator_key not in self.validators:
            return ValidationResult(
                is_valid=False,
                value=value,
                error_message=f"Неизвестный тип валидации: {validator_key}"
            )
        
        return await self.validators[validator_key].validate(value)
    
    def add_validator(self, key: str, validator: BaseValidator) -> None:
        """Add custom validator to the service."""
        self.validators[key] = validator
    
    async def sanitize_for_storage(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Sanitize data dictionary for safe storage."""
        sanitized = {}
        
        for key, value in data.items():
            if isinstance(value, str):
                # Basic HTML/JS sanitization
                sanitized_value = re.sub(r'[<>{}\\]', '', value)
                sanitized_value = sanitized_value.strip()
                sanitized[key] = sanitized_value
            elif isinstance(value, (int, float, bool)):
                sanitized[key] = value
            elif value is None:
                sanitized[key] = None
            else:
                # Convert complex types to string
                sanitized[key] = str(value)
        
        return sanitized


# Global instance for easy import
input_validator = InputValidationService()


# Convenience functions
async def validate_message(message: str) -> Tuple[bool, str, str]:
    """
    Quick validation for chat messages.
    
    Returns:
        Tuple of (is_valid, error_message, sanitized_message)
    """
    result = await input_validator.validate_user_message(message)
    return result.is_valid, result.error_message or "", result.safe_value


async def validate_heat(level: Any) -> Tuple[bool, str, int]:
    """
    Quick validation for heat level.
    
    Returns:
        Tuple of (is_valid, error_message, validated_level)
    """
    result = await input_validator.validate_heat_level(level)
    return result.is_valid, result.error_message or "", result.safe_value


async def validate_mode(mode: str) -> Tuple[bool, str, str]:
    """
    Quick validation for mode choice.
    
    Returns:
        Tuple of (is_valid, error_message, validated_mode)
    """
    result = await input_validator.validate_mode_choice(mode)
    return result.is_valid, result.error_message or "", result.safe_value 