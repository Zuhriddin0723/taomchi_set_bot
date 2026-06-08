import os
from dotenv import load_dotenv

# .env faylini yuklash (agar mavjud bo'lsa)
load_dotenv()

# Telegram Bot API Tokenlar
USER_BOT_TOKEN = os.getenv("USER_BOT_TOKEN", "8940547653:AAGGB0aZ9VORt9xFvjFfltVXYCzWTZl6Yk0")
ADMIN_BOT_TOKEN = os.getenv("ADMIN_BOT_TOKEN", "8642922312:AAGoWTs6HHdHhN_f8d5L63MOw9uNhyQs2NE")

# Database Configuration
DB_NAME = os.getenv("DB_NAME", "database.db")

# Allowed Administrator Telegram IDs
_admin_ids_str = os.getenv("ALLOWED_ADMIN_IDS", "1621989960,8529862654")
ALLOWED_ADMIN_IDS = [int(x.strip()) for x in _admin_ids_str.split(",") if x.strip()]
