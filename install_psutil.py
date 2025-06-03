#!/usr/bin/env python3
"""
Установка psutil для управления процессами
"""

import subprocess
import sys

def install_psutil():
    """Установить psutil для управления процессами"""
    print("📦 Установка psutil для управления процессами...")
    
    try:
        subprocess.run([sys.executable, "-m", "pip", "install", "psutil"], 
                      check=True, capture_output=True, text=True)
        print("✅ psutil установлен успешно")
        
        # Тестируем импорт
        import psutil
        print(f"✅ psutil версия: {psutil.__version__}")
        return True
        
    except subprocess.CalledProcessError as e:
        print(f"❌ Ошибка установки psutil: {e}")
        print("⚠️ Продолжим без управления процессами")
        return False
    except ImportError:
        print("❌ psutil установлен, но не импортируется")
        return False

if __name__ == "__main__":
    install_psutil() 