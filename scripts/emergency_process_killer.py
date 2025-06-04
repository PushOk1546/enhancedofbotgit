#!/usr/bin/env python3
"""
🚨 EMERGENCY PROCESS KILLER 🚨
Senior Team Nuclear Solution для Error 409

Принудительно завершает ВСЕ конфликтующие процессы
"""

import os
import sys
import time
import psutil
import requests
import subprocess
from pathlib import Path

class EmergencyProcessKiller:
    def __init__(self):
        self.bot_token = "7843350631:AAHQ6h_BKAH3J4sNkh9ypNt1jih4yKYM_gs"
        self.killed_processes = []
        
    def print_banner(self):
        print("\n🚨" + "="*60 + "🚨")
        print("🔥            EMERGENCY PROCESS KILLER            🔥")
        print("🚨              NUCLEAR SOLUTION                  🚨")
        print("🔥         ПРИНУДИТЕЛЬНОЕ РЕШЕНИЕ ERROR 409       🔥")
        print("🚨" + "="*60 + "🚨\n")
    
    def find_all_python_processes(self):
        """Найти ВСЕ Python процессы"""
        python_processes = []
        current_pid = os.getpid()
        
        try:
            for proc in psutil.process_iter(['pid', 'name', 'cmdline', 'create_time']):
                try:
                    proc_info = proc.info
                    
                    # Пропускаем текущий процесс
                    if proc_info['pid'] == current_pid:
                        continue
                        
                    # Ищем все Python процессы
                    if proc_info['name'] and 'python' in proc_info['name'].lower():
                        cmdline = proc_info['cmdline'] or []
                        cmdline_str = ' '.join(cmdline)
                        
                        python_processes.append({
                            'pid': proc_info['pid'],
                            'name': proc_info['name'],
                            'cmdline': cmdline_str,
                            'create_time': proc_info['create_time'],
                            'process': proc
                        })
                        
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    continue
                    
        except Exception as e:
            print(f"⚠️ Ошибка поиска процессов: {e}")
            
        return python_processes
    
    def force_kill_all_python(self):
        """ПРИНУДИТЕЛЬНОЕ завершение ВСЕХ Python процессов"""
        print("🔍 Поиск всех Python процессов...")
        
        processes = self.find_all_python_processes()
        
        if not processes:
            print("✅ Python процессы не найдены")
            return True
            
        print(f"🎯 Найдено {len(processes)} Python процессов")
        print("\n📋 Список процессов:")
        
        for i, proc in enumerate(processes, 1):
            pid = proc['pid']
            name = proc['name'] 
            cmdline = proc['cmdline'][:100] + "..." if len(proc['cmdline']) > 100 else proc['cmdline']
            print(f"  {i}. PID {pid} ({name}): {cmdline}")
        
        print(f"\n🚨 ПРИНУДИТЕЛЬНОЕ ЗАВЕРШЕНИЕ ВСЕХ {len(processes)} ПРОЦЕССОВ...")
        
        killed_count = 0
        for proc_info in processes:
            try:
                pid = proc_info['pid']
                name = proc_info['name']
                
                print(f"💀 Убиваем процесс: PID {pid} ({name})")
                
                # Принудительное завершение
                proc = psutil.Process(pid)
                proc.kill()  # Сразу KILL, без TERM
                
                # Ждем завершения
                try:
                    proc.wait(timeout=3)
                    print(f"✅ Процесс {pid} убит")
                    killed_count += 1
                    self.killed_processes.append(f"PID {pid} ({name})")
                except psutil.TimeoutExpired:
                    print(f"⚠️ Процесс {pid} не отвечает")
                    
            except (psutil.NoSuchProcess, psutil.AccessDenied) as e:
                print(f"⚠️ Не удалось убить процесс {pid}: {e}")
                continue
                
        print(f"\n✅ Убито {killed_count}/{len(processes)} процессов")
        return killed_count > 0
    
    def clear_webhook_force(self):
        """Принудительная очистка webhook"""
        print("\n🧹 Принудительная очистка webhook...")
        
        try:
            # Удаляем webhook
            response = requests.post(
                f"https://api.telegram.org/bot{self.bot_token}/deleteWebhook",
                timeout=10
            )
            
            if response.status_code == 200:
                result = response.json()
                if result.get('ok'):
                    print("✅ Webhook успешно очищен")
                    return True
                else:
                    print(f"⚠️ Webhook ответ: {result}")
                    
            print(f"❌ HTTP код: {response.status_code}")
            
        except Exception as e:
            print(f"❌ Ошибка очистки webhook: {e}")
            
        return False
    
    def cleanup_lock_files(self):
        """Очистка всех lock файлов"""
        print("\n🧹 Очистка lock файлов...")
        
        lock_files = [
            "bot.lock",
            "bot.pid", 
            "telegram_bot.lock",
            "monetized_bot.lock",
            "enterprise_bot.lock"
        ]
        
        cleaned = 0
        for lock_file in lock_files:
            try:
                if Path(lock_file).exists():
                    Path(lock_file).unlink()
                    print(f"🗑️ Удален: {lock_file}")
                    cleaned += 1
            except Exception as e:
                print(f"⚠️ Не удалось удалить {lock_file}: {e}")
                
        if cleaned > 0:
            print(f"✅ Очищено {cleaned} lock файлов")
        else:
            print("ℹ️ Lock файлы не найдены")
    
    def test_api_connection(self):
        """Тест подключения к Telegram API"""
        print("\n🔍 Тестирование API подключения...")
        
        try:
            # Проверяем getMe
            response = requests.get(
                f"https://api.telegram.org/bot{self.bot_token}/getMe",
                timeout=10
            )
            
            if response.status_code == 200:
                result = response.json()
                if result.get('ok'):
                    bot_info = result['result']
                    username = bot_info.get('username', 'Unknown')
                    print(f"✅ Бот активен: @{username}")
                    return True
                    
            print(f"❌ getMe ошибка: {response.status_code}")
            
        except Exception as e:
            print(f"❌ Ошибка API: {e}")
            
        return False
    
    def wait_for_api_clear(self, seconds=10):
        """Ожидание очистки API"""
        print(f"\n⏰ Ожидание {seconds} секунд для очистки API...")
        
        for i in range(seconds):
            print(f"⏳ {seconds - i} секунд осталось...", end='\r')
            time.sleep(1)
            
        print("\n✅ Ожидание завершено")
    
    def nuclear_cleanup(self):
        """ПОЛНАЯ ЯДЕРНАЯ ОЧИСТКА"""
        self.print_banner()
        
        print("🎯 ЭТАП 1: Принудительное завершение Python процессов")
        self.force_kill_all_python()
        
        print("\n🎯 ЭТАП 2: Очистка lock файлов")
        self.cleanup_lock_files()
        
        print("\n🎯 ЭТАП 3: Принудительная очистка webhook")
        self.clear_webhook_force()
        
        print("\n🎯 ЭТАП 4: Ожидание очистки API")
        self.wait_for_api_clear(10)
        
        print("\n🎯 ЭТАП 5: Финальная проверка API")
        api_ok = self.test_api_connection()
        
        print("\n" + "="*60)
        print("🔥 EMERGENCY CLEANUP ЗАВЕРШЕН")
        print("="*60)
        
        if self.killed_processes:
            print(f"💀 Убитые процессы ({len(self.killed_processes)}):")
            for proc in self.killed_processes:
                print(f"   - {proc}")
        
        if api_ok:
            print("\n✅ API готов к использованию")
            print("🚀 Теперь можно запускать бота!")
            return True
        else:
            print("\n❌ API всё ещё недоступен")
            print("🔧 Возможно нужно подождать ещё или проверить токен")
            return False

def main():
    """Главная функция emergency cleanup"""
    try:
        killer = EmergencyProcessKiller()
        success = killer.nuclear_cleanup()
        
        if success:
            print("\n🎉 ГОТОВО! Теперь запустите бота:")
            print("   python bot_lifecycle_manager.py")
            print("   или")
            print("   start_full_enterprise_bot.bat")
        else:
            print("\n⚠️ Cleanup выполнен, но могут быть проблемы")
            print("💡 Попробуйте подождать 30 секунд и запустить снова")
            
        return success
        
    except KeyboardInterrupt:
        print("\n🛑 Прервано пользователем")
        return False
    except Exception as e:
        print(f"\n❌ Критическая ошибка: {e}")
        return False

if __name__ == "__main__":
    success = main()
    input("\nНажмите Enter для выхода...")
    sys.exit(0 if success else 1) 