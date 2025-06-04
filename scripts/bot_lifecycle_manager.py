#!/usr/bin/env python3
"""
🔥 ENTERPRISE BOT LIFECYCLE MANAGER 🔥
Senior Python Developers Team Solution

РЕШАЕТ КРИТИЧЕСКИЕ ПРОБЛЕМЫ:
- Error 409: Multiple bot instances conflict
- Webhook conflicts
- Process management
- Graceful shutdown
- Health checks
- Auto recovery
"""

import os
import sys
import time
import signal
import psutil
import requests
import threading
import atexit
from pathlib import Path
from datetime import datetime
from typing import Optional, List, Dict, Any
import subprocess
import json

class BotLifecycleManager:
    """Enterprise Bot Lifecycle Management"""
    
    def __init__(self, bot_token: str, admin_id: int):
        self.bot_token = bot_token
        self.admin_id = admin_id
        self.lock_file = Path("bot.lock")
        self.pid_file = Path("bot.pid")
        self.webhook_cleared = False
        self.shutdown_event = threading.Event()
        self.current_process = None
        
        # Setup signal handlers
        self.setup_signal_handlers()
        
        # Register cleanup on exit
        atexit.register(self.cleanup_on_exit)
    
    def setup_signal_handlers(self):
        """Setup graceful shutdown handlers"""
        def signal_handler(signum, frame):
            print(f"\n🛑 Received signal {signum}, shutting down gracefully...")
            self.shutdown_event.set()
            self.cleanup_all()
            sys.exit(0)
        
        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)
    
    def check_bot_token_validity(self) -> bool:
        """Validate bot token with Telegram API"""
        try:
            print("🔍 Проверка валидности токена...")
            response = requests.get(
                f"https://api.telegram.org/bot{self.bot_token}/getMe",
                timeout=10
            )
            
            if response.status_code == 200:
                bot_info = response.json()
                if bot_info.get('ok'):
                    username = bot_info['result']['username']
                    print(f"✅ Токен валиден. Бот: @{username}")
                    return True
            
            print(f"❌ Невалидный токен: {response.status_code}")
            return False
            
        except Exception as e:
            print(f"❌ Ошибка проверки токена: {e}")
            return False
    
    def clear_webhook(self) -> bool:
        """Clear existing webhooks to prevent conflicts"""
        try:
            print("🧹 Очистка webhook...")
            
            # Delete webhook
            response = requests.post(
                f"https://api.telegram.org/bot{self.bot_token}/deleteWebhook",
                timeout=10
            )
            
            if response.status_code == 200:
                print("✅ Webhook очищен")
                self.webhook_cleared = True
                return True
            else:
                print(f"⚠️ Ошибка очистки webhook: {response.status_code}")
                return False
                
        except Exception as e:
            print(f"❌ Ошибка при очистке webhook: {e}")
            return False
    
    def find_conflicting_processes(self) -> List[Dict[str, Any]]:
        """Find all Python processes that might be running bot"""
        conflicting = []
        current_pid = os.getpid()
        
        try:
            for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
                try:
                    proc_info = proc.info
                    
                    # Skip current process
                    if proc_info['pid'] == current_pid:
                        continue
                    
                    # Check if it's Python process
                    if proc_info['name'] and 'python' in proc_info['name'].lower():
                        cmdline = proc_info['cmdline'] or []
                        cmdline_str = ' '.join(cmdline).lower()
                        
                        # Check for bot-related keywords
                        bot_keywords = [
                            'bot.py', 'monetized_bot.py', 'minimal_start.py',
                            'quick_start.py', 'ultimate_enterprise_launcher.py',
                            'telebot', 'telegram', self.bot_token[:10]
                        ]
                        
                        if any(keyword in cmdline_str for keyword in bot_keywords):
                            conflicting.append({
                                'pid': proc_info['pid'],
                                'name': proc_info['name'],
                                'cmdline': cmdline_str,
                                'process': proc
                            })
                            
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    continue
                    
        except Exception as e:
            print(f"⚠️ Ошибка поиска процессов: {e}")
        
        return conflicting
    
    def terminate_conflicting_processes(self) -> bool:
        """Terminate conflicting bot processes"""
        conflicts = self.find_conflicting_processes()
        
        if not conflicts:
            print("✅ Конфликтующих процессов не найдено")
            return True
        
        print(f"🔍 Найдено {len(conflicts)} конфликтующих процессов:")
        
        terminated = 0
        for proc_info in conflicts:
            try:
                pid = proc_info['pid']
                name = proc_info['name']
                print(f"🔄 Завершение процесса: PID {pid} ({name})")
                
                # Try graceful termination first
                proc = psutil.Process(pid)
                proc.terminate()
                
                # Wait for graceful shutdown
                try:
                    proc.wait(timeout=5)
                    print(f"✅ Процесс {pid} завершен gracefully")
                    terminated += 1
                except psutil.TimeoutExpired:
                    # Force kill if needed
                    print(f"⚠️ Принудительное завершение процесса {pid}")
                    proc.kill()
                    terminated += 1
                    
            except (psutil.NoSuchProcess, psutil.AccessDenied) as e:
                print(f"⚠️ Не удалось завершить процесс {pid}: {e}")
                continue
        
        print(f"✅ Завершено {terminated}/{len(conflicts)} процессов")
        
        # Wait a bit for cleanup
        time.sleep(2)
        return terminated > 0
    
    def create_lock_file(self) -> bool:
        """Create process lock file"""
        try:
            if self.lock_file.exists():
                # Check if process is still running
                try:
                    with open(self.lock_file, 'r') as f:
                        old_pid = int(f.read().strip())
                    
                    if psutil.pid_exists(old_pid):
                        print(f"❌ Бот уже запущен (PID: {old_pid})")
                        return False
                    else:
                        # Remove stale lock file
                        self.lock_file.unlink()
                        print("🧹 Удален устаревший lock файл")
                        
                except (ValueError, FileNotFoundError):
                    self.lock_file.unlink()
            
            # Create new lock file
            with open(self.lock_file, 'w') as f:
                f.write(str(os.getpid()))
            
            print(f"🔒 Lock файл создан: PID {os.getpid()}")
            return True
            
        except Exception as e:
            print(f"❌ Ошибка создания lock файла: {e}")
            return False
    
    def remove_lock_file(self):
        """Remove process lock file"""
        try:
            if self.lock_file.exists():
                self.lock_file.unlink()
                print("🔓 Lock файл удален")
        except Exception as e:
            print(f"⚠️ Ошибка удаления lock файла: {e}")
    
    def test_telegram_connection(self) -> bool:
        """Test connection to Telegram API"""
        try:
            print("🔄 Тестирование подключения к Telegram API...")
            
            response = requests.get(
                f"https://api.telegram.org/bot{self.bot_token}/getUpdates?limit=1",
                timeout=10
            )
            
            if response.status_code == 200:
                result = response.json()
                if result.get('ok'):
                    print("✅ Подключение к Telegram API успешно")
                    return True
                else:
                    print(f"❌ Telegram API error: {result.get('description', 'Unknown')}")
                    return False
            else:
                print(f"❌ HTTP error: {response.status_code}")
                return False
                
        except Exception as e:
            print(f"❌ Ошибка подключения к Telegram API: {e}")
            return False
    
    def cleanup_all(self):
        """Complete cleanup"""
        print("\n🧹 Выполнение полной очистки...")
        
        # Stop any running processes
        if hasattr(self, 'current_process') and self.current_process:
            try:
                self.current_process.terminate()
                self.current_process.wait(timeout=5)
            except:
                try:
                    self.current_process.kill()
                except:
                    pass
        
        # Remove lock file
        self.remove_lock_file()
        
        # Clear webhook if we set it
        if self.webhook_cleared:
            try:
                self.clear_webhook()
            except:
                pass
        
        print("✅ Очистка завершена")
    
    def cleanup_on_exit(self):
        """Cleanup function for atexit"""
        if not self.shutdown_event.is_set():
            self.cleanup_all()
    
    def start_bot_process(self, script_name: str) -> bool:
        """Start bot process with monitoring"""
        try:
            print(f"🚀 Запуск {script_name}...")
            
            # Set environment variables
            env = os.environ.copy()
            env.update({
                'BOT_TOKEN': self.bot_token,
                'ADMIN_USER_IDS': str(self.admin_id),
                'PYTHONUNBUFFERED': '1'
            })
            
            # Start process
            self.current_process = subprocess.Popen(
                [sys.executable, script_name],
                env=env,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                universal_newlines=True,
                bufsize=1
            )
            
            print(f"✅ Процесс запущен: PID {self.current_process.pid}")
            
            # Monitor process output in separate thread
            def monitor_output():
                while not self.shutdown_event.is_set():
                    try:
                        line = self.current_process.stdout.readline()
                        if line:
                            print(line.strip())
                        elif self.current_process.poll() is not None:
                            break
                    except:
                        break
            
            monitor_thread = threading.Thread(target=monitor_output, daemon=True)
            monitor_thread.start()
            
            # Wait for process
            try:
                self.current_process.wait()
                return_code = self.current_process.returncode
                
                if return_code == 0:
                    print("✅ Процесс завершился успешно")
                    return True
                else:
                    print(f"❌ Процесс завершился с кодом {return_code}")
                    return False
                    
            except KeyboardInterrupt:
                print("\n🛑 Прерывание пользователем")
                self.current_process.terminate()
                return False
                
        except Exception as e:
            print(f"❌ Ошибка запуска процесса: {e}")
            return False
    
    def enterprise_bot_startup(self) -> bool:
        """Complete enterprise bot startup sequence"""
        print("\n🔥 ENTERPRISE BOT STARTUP SEQUENCE 🔥")
        print("=" * 60)
        
        # Step 1: Validate token
        if not self.check_bot_token_validity():
            print("❌ КРИТИЧЕСКАЯ ОШИБКА: Невалидный токен бота")
            return False
        
        # Step 2: Terminate conflicting processes
        print("\n🔍 Поиск и завершение конфликтующих процессов...")
        self.terminate_conflicting_processes()
        
        # Step 3: Clear webhooks
        if not self.clear_webhook():
            print("⚠️ Предупреждение: Не удалось очистить webhook")
        
        # Step 4: Test API connection
        if not self.test_telegram_connection():
            print("❌ КРИТИЧЕСКАЯ ОШИБКА: Нет подключения к Telegram API")
            return False
        
        # Step 5: Create lock file
        if not self.create_lock_file():
            print("❌ КРИТИЧЕСКАЯ ОШИБКА: Не удалось создать lock файл")
            return False
        
        print("\n✅ Все проверки пройдены! Бот готов к запуску")
        return True

def main():
    """Main startup function"""
    print("🔥 ENTERPRISE BOT LIFECYCLE MANAGER 🔥")
    
    # Get configuration
    bot_token = os.getenv('BOT_TOKEN', '7843350631:AAHQ6h_BKAH3J4sNkh9ypNt1jih4yKYM_gs')
    admin_id = int(os.getenv('ADMIN_USER_IDS', '377917978'))
    
    if not bot_token or bot_token == 'YOUR_BOT_TOKEN_HERE':
        print("❌ BOT_TOKEN не настроен!")
        return False
    
    # Initialize lifecycle manager
    manager = BotLifecycleManager(bot_token, admin_id)
    
    # Run startup sequence
    if not manager.enterprise_bot_startup():
        print("❌ Startup sequence failed!")
        return False
    
    # Determine which bot script to run
    bot_scripts = [
        'ultimate_enterprise_launcher.py',
        'monetized_bot.py', 
        'quick_start.py',
        'minimal_start.py'
    ]
    
    for script in bot_scripts:
        if Path(script).exists():
            print(f"\n🚀 Запуск {script}...")
            success = manager.start_bot_process(script)
            
            if success:
                print(f"✅ {script} завершился успешно")
                return True
            else:
                print(f"❌ {script} завершился с ошибкой, пробуем следующий...")
                continue
    
    print("❌ Не удалось запустить ни один bot script!")
    return False

if __name__ == "__main__":
    try:
        success = main()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n🛑 Завершение по Ctrl+C")
        sys.exit(0)
    except Exception as e:
        print(f"\n❌ Критическая ошибка: {e}")
        sys.exit(1) 