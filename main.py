#!/usr/bin/env python3
"""
OF Assistant Bot - Main Entry Point
Clean, optimized single entry point for the bot.
"""

import asyncio
import sys
import os
from pathlib import Path

# Add current directory to path for imports
sys.path.insert(0, str(Path(__file__).parent))

try:
    from bot import BotManager
    from config import BOT_TOKEN, GROQ_KEY
    import logging
except ImportError as e:
    print(f"❌ Import error: {e}")
    print("💡 Make sure all required modules are installed:")
    print("   pip install -r requirements.txt")
    sys.exit(1)

def validate_environment():
    """Validate required environment variables"""
    missing = []
    
    if not BOT_TOKEN:
        missing.append("BOT_TOKEN")
    if not GROQ_KEY:
        missing.append("GROQ_KEY")
    
    if missing:
        print("❌ Missing required environment variables:")
        for var in missing:
            print(f"   - {var}")
        print("\n💡 Create a .env file with these variables or set them in your environment")
        return False
    
    return True

async def main():
    """Main entry point"""
    print("🚀 Starting OF Assistant Bot...")
    
    # Validate environment
    if not validate_environment():
        sys.exit(1)
    
    # Initialize and run bot
    bot_manager = BotManager()
    
    try:
        # Initialize bot
        if not await bot_manager.initialize():
            print("❌ Bot initialization failed")
            sys.exit(1)
        
        print("✅ Bot initialized successfully")
        print("🤖 Bot is running... Press Ctrl+C to stop")
        
        # Run bot
        await bot_manager.run()
        
    except KeyboardInterrupt:
        print("\n🛑 Shutdown signal received")
    except Exception as e:
        print(f"❌ Bot error: {e}")
        logging.exception("Bot crashed")
    finally:
        print("🔄 Shutting down...")
        await bot_manager.shutdown()
        print("✅ Bot stopped")

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n👋 Goodbye!")
    except Exception as e:
        print(f"❌ Fatal error: {e}")
        sys.exit(1) 