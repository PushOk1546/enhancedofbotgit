"""
Adult Content Templates - Explicit Version for Maximum Monetization
Explicit templates organized by intensity for premium conversions
"""

import random
from enum import Enum
from dataclasses import dataclass
from typing import List, Dict, Optional

class ExplicitnessLevel(Enum):
    SOFT = 1      # Flirty, suggestive 
    MEDIUM = 2    # Sexual tension, teasing
    EXPLICIT = 3  # Direct sexual content
    INTENSE = 4   # Very explicit, fetish content
    EXTREME = 5   # Maximum explicitness

class ContentMode(Enum):
    CHAT = "chat"
    FLIRT = "flirt" 
    SEXTING = "sexting"

class TemplateCategory(Enum):
    """Template categories for enhanced bot compatibility"""
    GREETING = "greeting"
    COMPLIMENT = "compliment"
    SEDUCTIVE = "seductive"
    EXPLICIT = "explicit"
    CONVERSION = "conversion"
    PREMIUM_PREVIEW = "premium_preview"

@dataclass
class AdultTemplate:
    text: str
    level: ExplicitnessLevel
    mode: ContentMode
    premium_only: bool = False
    conversion_focused: bool = False
    category: TemplateCategory = TemplateCategory.GREETING

class AdultTemplateManager:
    def __init__(self):
        self.templates = self._load_templates()
        
    def _load_templates(self) -> Dict[ExplicitnessLevel, Dict[ContentMode, List[AdultTemplate]]]:
        """Load explicit templates organized by level and mode"""
        
        templates = {
            ExplicitnessLevel.SOFT: {
                ContentMode.CHAT: [
                    AdultTemplate("Hey gorgeous 😘 How's your day treating you?", ExplicitnessLevel.SOFT, ContentMode.CHAT, category=TemplateCategory.GREETING),
                    AdultTemplate("You look absolutely stunning today baby 🔥", ExplicitnessLevel.SOFT, ContentMode.CHAT, category=TemplateCategory.COMPLIMENT),
                    AdultTemplate("Can't stop thinking about your beautiful smile 😍", ExplicitnessLevel.SOFT, ContentMode.CHAT, category=TemplateCategory.COMPLIMENT),
                ],
                ContentMode.FLIRT: [
                    AdultTemplate("You're making me feel things I shouldn't be feeling right now 😈", ExplicitnessLevel.SOFT, ContentMode.FLIRT, category=TemplateCategory.SEDUCTIVE),
                    AdultTemplate("I love how you make my heart race baby 💓", ExplicitnessLevel.SOFT, ContentMode.FLIRT, category=TemplateCategory.SEDUCTIVE),
                    AdultTemplate("Your energy is so intoxicating... I'm drawn to you 🌹", ExplicitnessLevel.SOFT, ContentMode.FLIRT, category=TemplateCategory.SEDUCTIVE),
                ]
            },
            
            ExplicitnessLevel.MEDIUM: {
                ContentMode.FLIRT: [
                    AdultTemplate("I can't help but imagine what you're wearing right now 😏", ExplicitnessLevel.MEDIUM, ContentMode.FLIRT, category=TemplateCategory.SEDUCTIVE),
                    AdultTemplate("You're driving me crazy with those looks... I want more 🔥", ExplicitnessLevel.MEDIUM, ContentMode.FLIRT, category=TemplateCategory.SEDUCTIVE),
                    AdultTemplate("I'm getting distracted thinking about your body against mine 💋", ExplicitnessLevel.MEDIUM, ContentMode.FLIRT, category=TemplateCategory.SEDUCTIVE),
                ],
                ContentMode.SEXTING: [
                    AdultTemplate("I wish I could feel your hands all over me right now... 🔥", ExplicitnessLevel.MEDIUM, ContentMode.SEXTING, category=TemplateCategory.SEDUCTIVE),
                    AdultTemplate("You're making me so hot and bothered baby 😈", ExplicitnessLevel.MEDIUM, ContentMode.SEXTING, category=TemplateCategory.SEDUCTIVE),
                    AdultTemplate("I want to show you exactly what you do to me... 💦", ExplicitnessLevel.MEDIUM, ContentMode.SEXTING, category=TemplateCategory.SEDUCTIVE),
                ]
            },
            
            ExplicitnessLevel.EXPLICIT: {
                ContentMode.SEXTING: [
                    AdultTemplate("I'm touching myself thinking about you right now... wish it was your hands instead 🔥💦", ExplicitnessLevel.EXPLICIT, ContentMode.SEXTING, premium_only=True, category=TemplateCategory.EXPLICIT),
                    AdultTemplate("I want to feel every inch of your body against mine... take me hard baby 😈", ExplicitnessLevel.EXPLICIT, ContentMode.SEXTING, premium_only=True, category=TemplateCategory.EXPLICIT),
                    AdultTemplate("You make me so wet... I need you inside me right now 💦🔥", ExplicitnessLevel.EXPLICIT, ContentMode.SEXTING, premium_only=True, category=TemplateCategory.EXPLICIT),
                    AdultTemplate("I'm imagining your cock sliding deep inside me... fuck me harder 😈💦", ExplicitnessLevel.EXPLICIT, ContentMode.SEXTING, premium_only=True, category=TemplateCategory.EXPLICIT),
                    AdultTemplate("I want to taste every drop of you baby... make me your dirty little slut 👅💦", ExplicitnessLevel.EXPLICIT, ContentMode.SEXTING, premium_only=True, category=TemplateCategory.EXPLICIT),
                ]
            },
            
            ExplicitnessLevel.INTENSE: {
                ContentMode.SEXTING: [
                    AdultTemplate("I want you to pin me down and fuck me like the dirty whore I am 🔥💦", ExplicitnessLevel.INTENSE, ContentMode.SEXTING, premium_only=True, category=TemplateCategory.EXPLICIT),
                    AdultTemplate("Use my holes however you want daddy... I'm your personal fucktoy 😈👅", ExplicitnessLevel.INTENSE, ContentMode.SEXTING, premium_only=True, category=TemplateCategory.EXPLICIT),
                    AdultTemplate("I'm your submissive little slut... punish me for being so naughty 🔥💦", ExplicitnessLevel.INTENSE, ContentMode.SEXTING, premium_only=True, category=TemplateCategory.EXPLICIT),
                    AdultTemplate("Choke me while you pound my tight pussy... I want to be your dirty cumslut 😈💦", ExplicitnessLevel.INTENSE, ContentMode.SEXTING, premium_only=True, category=TemplateCategory.EXPLICIT),
                ]
            },
            
            ExplicitnessLevel.EXTREME: {
                ContentMode.SEXTING: [
                    AdultTemplate("Destroy my holes daddy... use me like the worthless fuckdoll I am 🔥💦", ExplicitnessLevel.EXTREME, ContentMode.SEXTING, premium_only=True, category=TemplateCategory.EXPLICIT),
                    AdultTemplate("I want you and your friends to gangbang me until I'm a cum-covered mess 😈💦", ExplicitnessLevel.EXTREME, ContentMode.SEXTING, premium_only=True, category=TemplateCategory.EXPLICIT),
                    AdultTemplate("Fill all my holes at once... I need to be your personal cumdump 👅💦", ExplicitnessLevel.EXTREME, ContentMode.SEXTING, premium_only=True, category=TemplateCategory.EXPLICIT),
                ]
            }
        }
        
        # Add conversion-focused templates (premium upsells)
        conversion_templates = [
            AdultTemplate("Mmm baby... want to see more? 💋 Upgrade to premium for my exclusive content 🔥", ExplicitnessLevel.SOFT, ContentMode.CHAT, conversion_focused=True, category=TemplateCategory.CONVERSION),
            AdultTemplate("I'm getting so horny talking to you... but my really dirty stuff is premium only 😈💦", ExplicitnessLevel.MEDIUM, ContentMode.FLIRT, conversion_focused=True, category=TemplateCategory.CONVERSION),
            AdultTemplate("This is just a taste baby... upgrade now to unlock my nastiest fantasies 🔥💎", ExplicitnessLevel.EXPLICIT, ContentMode.SEXTING, conversion_focused=True, category=TemplateCategory.CONVERSION),
            AdultTemplate("Free trial ending soon! Don't miss out on my exclusive XXX content 💦👑", ExplicitnessLevel.MEDIUM, ContentMode.CHAT, conversion_focused=True, category=TemplateCategory.CONVERSION),
        ]
        
        # Add conversion templates to appropriate levels
        for template in conversion_templates:
            if template.level not in templates:
                templates[template.level] = {}
            if template.mode not in templates[template.level]:
                templates[template.level][template.mode] = []
            templates[template.level][template.mode].append(template)
            
        return templates

    def get_template(self, level: ExplicitnessLevel, mode: ContentMode, 
                    is_premium: bool = False, force_conversion: bool = False) -> str:
        """Get template based on user's level and premium status"""
        
        # Force conversion template if user approaching limit
        if force_conversion:
            conversion_templates = []
            for lvl_templates in self.templates.values():
                for mode_templates in lvl_templates.values():
                    conversion_templates.extend([t for t in mode_templates if t.conversion_focused])
            if conversion_templates:
                return random.choice(conversion_templates).text
        
        # Get templates for specified level and mode
        if level in self.templates and mode in self.templates[level]:
            available_templates = self.templates[level][mode]
            
            # Filter by premium status
            if not is_premium:
                available_templates = [t for t in available_templates if not t.premium_only]
            
            if available_templates:
                return random.choice(available_templates).text
        
        # Fallback to conversion message if no templates available
        return "Want more exclusive content? 💎 Upgrade to premium for unlimited access! 🔥"

    def get_template_by_category(self, category: TemplateCategory) -> str:
        """Get template by specific category"""
        category_templates = []
        for lvl_templates in self.templates.values():
            for mode_templates in lvl_templates.values():
                category_templates.extend([t for t in mode_templates if t.category == category])
        
        if category_templates:
            return random.choice(category_templates).text
        return "Hey there! 😘"

    def get_premium_preview(self) -> str:
        """Get a preview of premium content to entice upgrades"""
        previews = [
            "🔥 PREMIUM PREVIEW 🔥\n'I want you to...' [Content locked] 💎\n\nUpgrade now to unlock my dirtiest fantasies!",
            "💦 VIP EXCLUSIVE 💦\n'Fuck me like...' [Premium only] 👑\n\nJoin VIP for unlimited explicit chat!",
            "😈 ULTIMATE ACCESS 😈\n'I'm your dirty...' [Ultimate tier] 🔥\n\nGet Ultimate for my nastiest roleplay!"
        ]
        return random.choice(previews)

    def get_upsell_message(self, current_tier: str) -> str:
        """Get targeted upsell message based on current tier"""
        upsells = {
            "free_trial": "🔥 Your trial is almost over! Upgrade to PREMIUM for unlimited dirty talk - only ⭐150 Stars! 💎",
            "premium": "💎 Want even dirtier content? Upgrade to VIP for exclusive fetish chat - ⭐250 Stars! 👑", 
            "vip": "👑 Ready for the ultimate experience? ULTIMATE tier has my nastiest content - ⭐500 Stars! 🔥",
        }
        return upsells.get(current_tier, "💰 Upgrade now for exclusive adult content! 🔥")

# Global template manager
template_manager = AdultTemplateManager() 