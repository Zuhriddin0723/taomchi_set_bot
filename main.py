import threading
import time
import database
import user_bot
import admin_bot

def start_user_bot():
    print("[INIT] User Bot is starting polling...")
    while True:
        try:
            user_bot.bot.polling(none_stop=True, interval=0, timeout=25)
        except Exception as e:
            print(f"[ERROR] User Bot encountered an error: {e}. Reconnecting in 5 seconds...")
            time.sleep(5)

def start_admin_bot():
    print("[INIT] Admin Bot is starting polling...")
    while True:
        try:
            admin_bot.bot.polling(none_stop=True, interval=0, timeout=25)
        except Exception as e:
            print(f"[ERROR] Admin Bot encountered an error: {e}. Reconnecting in 5 seconds...")
            time.sleep(5)

if __name__ == "__main__":
    print("=========================================")
    print("      Taomchi Set Telegram Bots          ")
    print("=========================================")
    
    # 1. Initialize SQLite database schema & seed data
    database.init_db()
    
    # 2. Setup threads
    user_thread = threading.Thread(target=start_user_bot, daemon=True)
    admin_thread = threading.Thread(target=start_admin_bot, daemon=True)
    
    # 3. Launch threads
    user_thread.start()
    admin_thread.start()
    
    print("[SYSTEM] Both bots have been successfully launched!")
    print("[SYSTEM] Press Ctrl+C to terminate the process.")
    
    # 4. Keep main thread active
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("[SYSTEM] Shutting down Taomchi Set Bots...")
        print("Goodbye!")
