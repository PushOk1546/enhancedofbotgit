#!/usr/bin/env python3
"""
🚨 EMERGENCY INSTALLER 🚨
Emergency dependency installer without requirements.txt
"""

import sys
import subprocess
import os

def install_package(package):
    """Install single package"""
    try:
        print(f"Installing {package}...")
        subprocess.run([sys.executable, "-m", "pip", "install", package], 
                      check=True, capture_output=True)
        print(f"✅ {package} installed successfully")
        return True
    except Exception as e:
        print(f"❌ Failed to install {package}: {e}")
        return False

def main():
    print("🚨 EMERGENCY DEPENDENCY INSTALLER 🚨")
    print("=" * 50)
    
    # Critical packages list (hardcoded to avoid file encoding issues)
    packages = [
        "pyTelegramBotAPI",
        "requests", 
        "psutil",
        "python-dotenv"
    ]
    
    # Optional packages
    optional_packages = [
        "groq",
        "cryptography"
    ]
    
    print("📦 Installing critical packages...")
    success_count = 0
    
    for package in packages:
        if install_package(package):
            success_count += 1
    
    print(f"\n📊 Critical packages: {success_count}/{len(packages)}")
    
    # Install optional packages
    print("\n📦 Installing optional packages...")
    optional_success = 0
    
    for package in optional_packages:
        if install_package(package):
            optional_success += 1
    
    print(f"📊 Optional packages: {optional_success}/{len(optional_packages)}")
    
    # Test imports
    print("\n🔍 Testing imports...")
    try:
        import telebot
        print("✅ telebot: OK")
    except:
        print("❌ telebot: FAILED")
        
    try:
        import requests
        print("✅ requests: OK")
    except:
        print("❌ requests: FAILED")
    
    if success_count >= 2:  # At least telebot and requests
        print("\n🎉 EMERGENCY INSTALL SUCCESSFUL!")
        print("🚀 You can now run the bot with:")
        print("   python simple_start.py")
        print("   python quick_start.py")
    else:
        print("\n❌ EMERGENCY INSTALL FAILED")
        print("💡 Try manual installation:")
        print("   pip install pyTelegramBotAPI")
        print("   pip install requests")

if __name__ == "__main__":
    main() 