import sqlite3
import datetime
from config import DB_NAME

def get_connection():
    """Returns a connection to the SQLite database. check_same_thread is False to allow thread safety."""
    conn = sqlite3.connect(DB_NAME, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    """Initializes the database schema and seeds initial data."""
    conn = get_connection()
    cursor = conn.cursor()
    
    # Users table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS users (
        chat_id INTEGER PRIMARY KEY,
        username TEXT,
        first_name TEXT,
        last_name TEXT,
        phone TEXT,
        registered_at TEXT
    )
    """)
    
    # Admins table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS admins (
        chat_id INTEGER PRIMARY KEY,
        username TEXT,
        registered_at TEXT
    )
    """)
    
    # Orders table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS orders (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        order_type TEXT, -- 'subscription' or 'set'
        set_name TEXT,
        customer_name TEXT,
        phone TEXT,
        address TEXT,
        latitude REAL,
        longitude REAL,
        status TEXT DEFAULT 'pending', -- 'pending', 'approved', 'rejected'
        created_at TEXT
    )
    """)
    
    # Food Sets table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS food_sets (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT UNIQUE,
        description TEXT,
        price INTEGER,
        images TEXT -- Comma-separated file IDs for images (max 3)
    )
    """)
    
    # Settings table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS settings (
        key TEXT PRIMARY KEY,
        value TEXT,
        value_photo TEXT
    )
    """)
    
    # Interests table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS interests (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        query_type TEXT,
        item_name TEXT,
        created_at TEXT
    )
    """)
    
    conn.commit()
    
    # Seed default settings
    cursor.execute("SELECT COUNT(*) as count FROM settings WHERE key = 'subscription'")
    if cursor.fetchone()['count'] == 0:
        cursor.execute(
            "INSERT INTO settings (key, value, value_photo) VALUES (?, ?, ?)",
            ("subscription", "📅 Taomchi Set 1 oylik obunasi orqali har kuni mazali taomlar bepul yetkazib beriladi va 20% chegirmaga ega bo'lasiz!\n\nObuna narxi: 1,500,000 so'm/oy.\n\nHoziroq buyurtma bering!", None)
        )
        
    conn.commit()
    conn.close()
    print("Database initialized successfully.")

# User DB functions
def add_user(chat_id, username, first_name, last_name):
    conn = get_connection()
    cursor = conn.cursor()
    now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    cursor.execute(
        "INSERT OR IGNORE INTO users (chat_id, username, first_name, last_name, registered_at) VALUES (?, ?, ?, ?, ?)",
        (chat_id, username, first_name, last_name, now)
    )
    conn.commit()
    conn.close()

def update_user_phone(chat_id, phone):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("UPDATE users SET phone = ? WHERE chat_id = ?", (phone, chat_id))
    conn.commit()
    conn.close()

def get_users_count():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) as count FROM users")
    count = cursor.fetchone()['count']
    conn.close()
    return count

# Admin DB functions
def add_admin(chat_id, username):
    conn = get_connection()
    cursor = conn.cursor()
    now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    cursor.execute(
        "INSERT OR IGNORE INTO admins (chat_id, username, registered_at) VALUES (?, ?, ?)",
        (chat_id, username, now)
    )
    conn.commit()
    conn.close()

def is_admin(chat_id):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT 1 FROM admins WHERE chat_id = ?", (chat_id,))
    row = cursor.fetchone()
    conn.close()
    return row is not None

def get_admins():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT chat_id FROM admins")
    rows = cursor.fetchall()
    conn.close()
    return [row['chat_id'] for row in rows]

# Order DB functions
def add_order(user_id, order_type, set_name, customer_name, phone, address, latitude=None, longitude=None):
    conn = get_connection()
    cursor = conn.cursor()
    now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    cursor.execute(
        """INSERT INTO orders (user_id, order_type, set_name, customer_name, phone, address, latitude, longitude, status, created_at) 
           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        (user_id, order_type, set_name, customer_name, phone, address, latitude, longitude, 'pending', now)
    )
    order_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return order_id

def update_order_status(order_id, status):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("UPDATE orders SET status = ? WHERE id = ?", (status, order_id))
    conn.commit()
    conn.close()

def get_order(order_id):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM orders WHERE id = ?", (order_id,))
    row = cursor.fetchone()
    conn.close()
    return row

def get_pending_orders():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM orders WHERE status = 'pending' ORDER BY id DESC")
    rows = cursor.fetchall()
    conn.close()
    return rows

def get_orders_count():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) as count FROM orders")
    count = cursor.fetchone()['count']
    conn.close()
    return count

# Food sets DB functions
def add_food_set(name, description, price, images_str):
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute(
            "INSERT INTO food_sets (name, description, price, images) VALUES (?, ?, ?, ?)",
            (name, description, price, images_str)
        )
        conn.commit()
        success = True
    except sqlite3.IntegrityError:
        success = False
    conn.close()
    return success

def get_food_sets():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM food_sets ORDER BY id ASC")
    rows = cursor.fetchall()
    conn.close()
    return rows

def get_food_set_by_id(set_id):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM food_sets WHERE id = ?", (set_id,))
    row = cursor.fetchone()
    conn.close()
    return row

def delete_food_set(set_id):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT images FROM food_sets WHERE id = ?", (set_id,))
    row = cursor.fetchone()
    images_to_delete = []
    if row and row['images']:
        images_to_delete = [img.strip() for img in row['images'].split(',') if img.strip()]
    
    cursor.execute("DELETE FROM food_sets WHERE id = ?", (set_id,))
    conn.commit()
    conn.close()
    return images_to_delete

# Settings / Subscription DB functions
def get_subscription_info():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT value, value_photo FROM settings WHERE key = 'subscription'")
    row = cursor.fetchone()
    conn.close()
    if row:
        return row['value'], row['value_photo']
    return None, None

def update_subscription_info(value, value_photo):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "UPDATE settings SET value = ?, value_photo = ? WHERE key = 'subscription'",
        (value, value_photo)
    )
    conn.commit()
    conn.close()

def clear_subscription_info():
    """Obuna matni va rasmini tozalaydi (bo'sh qilib qo'yadi)."""
    conn = get_connection()
    cursor = conn.cursor()
    # Oldingi rasmni topib, diskdan o'chiramiz
    cursor.execute("SELECT value_photo FROM settings WHERE key = 'subscription'")
    row = cursor.fetchone()
    if row and row['value_photo']:
        old_photo = row['value_photo']
        try:
            import os
            if os.path.exists(old_photo):
                os.remove(old_photo)
        except Exception:
            pass
    cursor.execute(
        "UPDATE settings SET value = NULL, value_photo = NULL WHERE key = 'subscription'"
    )
    conn.commit()
    conn.close()

def get_stats():
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute("SELECT COUNT(*) as total_users FROM users")
    total_users = cursor.fetchone()['total_users']
    
    cursor.execute("SELECT COUNT(*) as total_orders FROM orders")
    total_orders = cursor.fetchone()['total_orders']
    
    cursor.execute("SELECT COUNT(*) as pending_orders FROM orders WHERE status = 'pending'")
    pending_orders = cursor.fetchone()['pending_orders']
    
    conn.close()
    return {
        "total_users": total_users,
        "total_orders": total_orders,
        "pending_orders": pending_orders
    }

def get_user(chat_id):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users WHERE chat_id = ?", (chat_id,))
    row = cursor.fetchone()
    conn.close()
    return row

def add_interest(user_id, query_type, item_name=None):
    conn = get_connection()
    cursor = conn.cursor()
    now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    cursor.execute(
        "INSERT INTO interests (user_id, query_type, item_name, created_at) VALUES (?, ?, ?, ?)",
        (user_id, query_type, item_name, now)
    )
    conn.commit()
    conn.close()

def get_interests():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT i.*, u.first_name, u.last_name, u.username, u.phone 
        FROM interests i
        JOIN users u ON i.user_id = u.chat_id
        ORDER BY i.id DESC
    """)
    rows = cursor.fetchall()
    conn.close()
    return rows

def clear_interests():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM interests")
    conn.commit()
    conn.close()

def get_today_dish():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT value FROM settings WHERE key = 'today_dish_text'")
    row_text = cursor.fetchone()
    cursor.execute("SELECT value FROM settings WHERE key = 'today_dish_photo'")
    row_photo = cursor.fetchone()
    conn.close()
    
    text = row_text['value'] if row_text else None
    photo = row_photo['value'] if row_photo else None
    return text, photo

def update_today_dish(text, photo):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("INSERT OR REPLACE INTO settings (key, value) VALUES ('today_dish_text', ?)", (text,))
    cursor.execute("INSERT OR REPLACE INTO settings (key, value) VALUES ('today_dish_photo', ?)", (photo,))
    conn.commit()
    conn.close()


