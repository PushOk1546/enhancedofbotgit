#!/usr/bin/env python3
"""
Simple launcher for OF Assistant Bot
"""

import os
import sys
import subprocess
from pathlib import Path

def main():
    """Simple launcher for the bot"""
    print("🚀 OF Assistant Bot Launcher")
    print("=" * 40)
    
    # Change to project root
    project_root = Path(__file__).parent.parent
    os.chdir(project_root)
    
    # Check if main.py exists
    if not (project_root / "main.py").exists():
        print("❌ main.py not found!")
        print("💡 Make sure you're in the correct directory")
        return 1
    
    try:
        # Run the bot
        print("🤖 Starting bot...")
        result = subprocess.run([sys.executable, "main.py"], 
                              cwd=project_root)
        return result.returncode
        
    except KeyboardInterrupt:
        print("\n🛑 Bot stopped by user")
        return 0
    except Exception as e:
        print(f"❌ Error: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main()) 