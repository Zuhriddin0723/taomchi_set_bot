import os
import sys
import time
import telebot
from telebot import types
import config
import database

# Bot ish papkasini aniqlash (mutlaq yo'l uchun)
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
IMAGES_DIR = os.path.join(BASE_DIR, "images")

bot = telebot.TeleBot(config.ADMIN_BOT_TOKEN)

# Admin states and data store
admin_steps = {}
admin_data = {}

# State Constants
STATE_ADDING_SET_NAME = "ADDING_SET_NAME"
STATE_ADDING_SET_DESC = "ADDING_SET_DESC"
STATE_ADDING_SET_PRICE = "ADDING_SET_PRICE"
STATE_ADDING_SET_PHOTOS = "ADDING_SET_PHOTOS"

STATE_EDITING_SUB_TEXT = "EDITING_SUB_TEXT"
STATE_EDITING_SUB_PHOTO = "EDITING_SUB_PHOTO"

STATE_BROADCASTING = "BROADCASTING"

STATE_TODAY_DISH_PHOTO = "TODAY_DISH_PHOTO"
STATE_TODAY_DISH_CONFIRM_TEXT = "TODAY_DISH_CONFIRM_TEXT"
STATE_TODAY_DISH_TEXT = "TODAY_DISH_TEXT"


# ─────────────────────────────────────────────
# Keyboard Builders
# ─────────────────────────────────────────────

def get_admin_keyboard():
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.row("📊 Statistika", "📦 Faol buyurtmalar")
    markup.row("👥 Qiziquvchilar", "📦 Setlar ro'yxati")
    markup.row("📦 Set qo'shish", "📅 Obuna ma'lumotini tahrirlash")
    markup.row("📢 Xabar yuborish", "🍽️ Bugungi taom")
    markup.row("👥 Barcha userlarni olish")
    return markup


def get_cancel_keyboard():
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.row("❌ Bekor qilish")
    return markup


def get_yes_no_keyboard():
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.row("✅ Ha", "❌ Yo'q")
    return markup


# ─────────────────────────────────────────────
# Helper: reset admin state
# ─────────────────────────────────────────────

def reset_state(chat_id):
    admin_steps[chat_id] = None
    admin_data.pop(chat_id, None)


# ─────────────────────────────────────────────
# Notify admins about new order
# ─────────────────────────────────────────────

def notify_new_order(order_id):
    order = database.get_order(order_id)
    if not order:
        return

    user_info = database.get_user(order['user_id'])
    if user_info and user_info['username']:
        username_str = f"@{user_info['username']}"
    else:
        username_str = f"[Profil (link)](tg://user?id={order['user_id']})"

    order_type_str = (
        "📅 1 oylik obuna"
        if order['order_type'] == 'subscription'
        else f"🍔 Set: {order['set_name']}"
    )

    address_str = order['address']
    if order['latitude'] and order['longitude']:
        map_url = f"https://www.google.com/maps?q={order['latitude']},{order['longitude']}"
        address_str = f"[Geolokatsiya (Xaritada ko'rish)]({map_url})"

    message_text = (
        f"🚨 *Yangi buyurtma! (ID: {order_id})*\n\n"
        f"👤 *Mijoz:* {order['customer_name']}\n"
        f"🆔 *Telegram ID:* `{order['user_id']}`\n"
        f"🔗 *Telegram Nick:* {username_str}\n"
        f"📞 *Tel:* {order['phone']}\n"
        f"🛍 *Turi:* {order_type_str}\n"
        f"📍 *Manzil:* {address_str}\n"
        f"📅 *Vaqt:* {order['created_at']}"
    )

    markup = types.InlineKeyboardMarkup()
    btn_approve = types.InlineKeyboardButton("✅ Qabul qilish", callback_data=f"approve_{order_id}")
    btn_reject = types.InlineKeyboardButton("❌ Rad etish", callback_data=f"reject_{order_id}")
    markup.row(btn_approve, btn_reject)

    admins = database.get_admins()
    for admin_id in admins:
        try:
            bot.send_message(admin_id, message_text, parse_mode="Markdown", reply_markup=markup)
        except Exception as e:
            print(f"Failed to send order notification to admin {admin_id}: {e}")


# ─────────────────────────────────────────────
# Access control
# ─────────────────────────────────────────────

@bot.message_handler(func=lambda msg: msg.chat.id not in config.ALLOWED_ADMIN_IDS)
def handle_unauthorized(message):
    bot.send_message(message.chat.id, "Kechirasiz, sizga bu botga kirishga ruhsat berilmagan.")


# ─────────────────────────────────────────────
# /start
# ─────────────────────────────────────────────

@bot.message_handler(commands=['start'])
def handle_start(message):
    chat_id = message.chat.id
    user = message.from_user

    database.add_admin(chat_id, user.username)
    reset_state(chat_id)

    welcome_text = (
        "Assalomu aleykum, Taomchi Set admin botiga xush kelibsiz! 🛠️\n\n"
        "Bu yerda buyurtmalarni qabul qilishingiz va sozlamalarni boshqarishingiz mumkin."
    )
    bot.send_message(chat_id, welcome_text, reply_markup=get_admin_keyboard())


# ─────────────────────────────────────────────
# ❌ Bekor qilish — alohida handler
# ─────────────────────────────────────────────

@bot.message_handler(func=lambda msg: msg.text == "❌ Bekor qilish")
def handle_cancel(message):
    chat_id = message.chat.id
    reset_state(chat_id)
    bot.send_message(chat_id, "Amal bekor qilindi.", reply_markup=get_admin_keyboard())


# ─────────────────────────────────────────────
# 📊 Statistika
# ─────────────────────────────────────────────

@bot.message_handler(func=lambda msg: msg.text == "📊 Statistika")
def handle_stats(message):
    stats = database.get_stats()
    stats_text = (
        "📊 *Bot statistikasi:*\n\n"
        f"👤 Jami mijozlar soni: {stats['total_users']} ta\n"
        f"🛍 Jami buyurtmalar soni: {stats['total_orders']} ta\n"
        f"🚨 Kutilayotgan buyurtmalar: {stats['pending_orders']} ta"
    )
    bot.send_message(message.chat.id, stats_text, parse_mode="Markdown")


# ─────────────────────────────────────────────
# 👥 Barcha userlarni olish — TUZATILGAN
# ─────────────────────────────────────────────

@bot.message_handler(func=lambda msg: msg.text == "👥 Barcha userlarni olish")
def handle_get_all_users(message):
    chat_id = message.chat.id
    users = database.get_all_users()

    if not users:
        bot.send_message(chat_id, "Hozircha foydalanuvchilar yo'q.")
        return

    msg_parts = []
    for idx, user in enumerate(users, 1):
        first_name = user['first_name'] or ""
        last_name = user['last_name'] or ""
        full_name = f"{first_name} {last_name}".strip() or "Nomsiz"

        if user['username']:
            username_str = f"@{user['username']}"
        else:
            username_str = f"[Profil](tg://user?id={user['chat_id']})"

        phone = user['phone'] or "Telefon yo'q"

        part = (
            f"{idx}. *{full_name}*\n"
            f"   🔗 {username_str}\n"
            f"   📞 {phone}\n"
            f"   🆔 `{user['chat_id']}`\n"
            f"   📅 {user['registered_at']}\n"
        )
        msg_parts.append(part)

    # 4096 belgidan oshmasligi uchun bo'lib yuborish
    current_msg = f"👥 *Barcha foydalanuvchilar ({len(users)} ta):*\n\n"
    for part in msg_parts:
        if len(current_msg) + len(part) > 4000:
            bot.send_message(chat_id, current_msg, parse_mode="Markdown")
            current_msg = part
        else:
            current_msg += part

    if current_msg:
        bot.send_message(chat_id, current_msg, parse_mode="Markdown")


# ─────────────────────────────────────────────
# 📦 Faol buyurtmalar
# ─────────────────────────────────────────────

@bot.message_handler(func=lambda msg: msg.text == "📦 Faol buyurtmalar")
def handle_active_orders(message):
    chat_id = message.chat.id
    orders = database.get_pending_orders()

    if not orders:
        bot.send_message(chat_id, "Hozircha kutilayotgan faol buyurtmalar yo'q. 🎉")
        return

    bot.send_message(chat_id, f"📦 Jami kutilayotgan buyurtmalar: {len(orders)} ta. Quyida ro'yxat:")

    for order in orders:
        order_id = order['id']
        user_info = database.get_user(order['user_id'])

        if user_info and user_info['username']:
            username_str = f"@{user_info['username']}"
        else:
            username_str = f"[Profil (link)](tg://user?id={order['user_id']})"

        order_type_str = (
            "📅 1 oylik obuna"
            if order['order_type'] == 'subscription'
            else f"🍔 Set: {order['set_name']}"
        )

        address_str = order['address']
        if order['latitude'] and order['longitude']:
            map_url = f"https://www.google.com/maps?q={order['latitude']},{order['longitude']}"
            address_str = f"[Geolokatsiya (Xaritada ko'rish)]({map_url})"

        order_text = (
            f"🆔 ID: {order_id}\n"
            f"👤 Mijoz: {order['customer_name']}\n"
            f"🆔 Telegram ID: `{order['user_id']}`\n"
            f"🔗 Telegram Nick: {username_str}\n"
            f"📞 Tel: {order['phone']}\n"
            f"🛍 Turi: {order_type_str}\n"
            f"📍 Manzil: {address_str}"
        )

        markup = types.InlineKeyboardMarkup()
        btn_approve = types.InlineKeyboardButton("✅ Qabul qilish", callback_data=f"approve_{order_id}")
        btn_reject = types.InlineKeyboardButton("❌ Rad etish", callback_data=f"reject_{order_id}")
        markup.row(btn_approve, btn_reject)

        bot.send_message(chat_id, order_text, parse_mode="Markdown", reply_markup=markup)


# ─────────────────────────────────────────────
# 📢 Xabar yuborish
# ─────────────────────────────────────────────

@bot.message_handler(func=lambda msg: msg.text == "📢 Xabar yuborish")
def start_broadcast(message):
    chat_id = message.chat.id
    admin_steps[chat_id] = STATE_BROADCASTING
    bot.send_message(chat_id, "Barcha foydalanuvchilarga yuboriladigan xabar matnini kiriting:", reply_markup=get_cancel_keyboard())


# ─────────────────────────────────────────────
# 🍽️ Bugungi taom
# ─────────────────────────────────────────────

@bot.message_handler(func=lambda msg: msg.text == "🍽️ Bugungi taom")
def start_today_dish(message):
    chat_id = message.chat.id
    admin_steps[chat_id] = STATE_TODAY_DISH_PHOTO
    admin_data[chat_id] = {}
    bot.send_message(
        chat_id,
        "🍽️ *Bugungi taom rasmini yuboring:*",
        parse_mode="Markdown",
        reply_markup=get_cancel_keyboard()
    )


# ─────────────────────────────────────────────
# 📦 Set qo'shish
# ─────────────────────────────────────────────

@bot.message_handler(func=lambda msg: msg.text == "📦 Set qo'shish")
def start_add_set(message):
    chat_id = message.chat.id
    admin_steps[chat_id] = STATE_ADDING_SET_NAME
    admin_data[chat_id] = {}
    bot.send_message(chat_id, "Set nomini kiriting:", reply_markup=get_cancel_keyboard())


# ─────────────────────────────────────────────
# 📅 Obuna ma'lumotini tahrirlash
# ─────────────────────────────────────────────

@bot.message_handler(func=lambda msg: msg.text == "📅 Obuna ma'lumotini tahrirlash")
def start_edit_sub(message):
    chat_id = message.chat.id
    text, photo = database.get_subscription_info()

    if text or photo:
        preview = "📋 *Joriy obuna ma'lumoti:*\n\n"
        if text:
            preview += f"{text}\n\n"
        if photo:
            preview += "_(Rasm mavjud)_\n\n"
        preview += "Yangi ma'lumot kiriting yoki o'chirishingiz mumkin:"

        inline_markup = types.InlineKeyboardMarkup()
        inline_markup.add(types.InlineKeyboardButton("🗑 Obuna ma'lumotini o'chirish", callback_data="delete_sub_info"))
        bot.send_message(chat_id, preview, parse_mode="Markdown", reply_markup=inline_markup)

    admin_steps[chat_id] = STATE_EDITING_SUB_TEXT
    admin_data[chat_id] = {}
    bot.send_message(chat_id, "Obuna uchun yangi matn (tavsif) kiriting:", reply_markup=get_cancel_keyboard())


# ─────────────────────────────────────────────
# 📦 Setlar ro'yxati
# ─────────────────────────────────────────────

@bot.message_handler(func=lambda msg: msg.text == "📦 Setlar ro'yxati")
def handle_list_sets(message):
    chat_id = message.chat.id
    food_sets = database.get_food_sets()

    if not food_sets:
        bot.send_message(chat_id, "Hozircha menyuda hech qanday set mavjud emas.")
        return

    bot.send_message(chat_id, "📋 *Mavjud setlar ro'yxati:*", parse_mode="Markdown")

    for f_set in food_sets:
        set_id = f_set['id']
        name = f_set['name']
        desc = f_set['description']
        price = f_set['price']
        images_str = f_set['images']

        info_text = f"📦 *{name}*\n\n📝 Tavsif: {desc}\n\n💵 Narxi: {price:,} so'm"

        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton("❌ O'chirish", callback_data=f"delete_set_{set_id}"))

        if images_str:
            file_paths = [fp.strip() for fp in images_str.split(',') if fp.strip()]
            if len(file_paths) == 1:
                try:
                    file_path = file_paths[0]
                    if os.path.exists(file_path):
                        with open(file_path, 'rb') as photo:
                            bot.send_photo(chat_id, photo, caption=info_text, parse_mode="Markdown", reply_markup=markup)
                    else:
                        bot.send_photo(chat_id, file_path, caption=info_text, parse_mode="Markdown", reply_markup=markup)
                except Exception as e:
                    bot.send_message(chat_id, info_text + f"\n\n_(Rasm yuklanmadi: {e})_", parse_mode="Markdown", reply_markup=markup)
            else:
                try:
                    media = []
                    opened_files = []
                    for idx, file_path in enumerate(file_paths):
                        if os.path.exists(file_path):
                            f = open(file_path, 'rb')
                            opened_files.append(f)
                            img_obj = f
                        else:
                            img_obj = file_path

                        if idx == 0:
                            media.append(types.InputMediaPhoto(img_obj, caption=info_text, parse_mode="Markdown"))
                        else:
                            media.append(types.InputMediaPhoto(img_obj))

                    bot.send_media_group(chat_id, media)
                    for f in opened_files:
                        f.close()
                    bot.send_message(chat_id, f"⚙️ *{name}* setini boshqarish:", parse_mode="Markdown", reply_markup=markup)
                except Exception as e:
                    bot.send_message(chat_id, info_text + f"\n\n_(Rasmlar yuklanmadi: {e})_", parse_mode="Markdown", reply_markup=markup)
        else:
            bot.send_message(chat_id, info_text, parse_mode="Markdown", reply_markup=markup)


# ─────────────────────────────────────────────
# 👥 Qiziquvchilar
# ─────────────────────────────────────────────

@bot.message_handler(func=lambda msg: msg.text == "👥 Qiziquvchilar")
def handle_interests(message):
    chat_id = message.chat.id
    interests = database.get_interests()

    if not interests:
        bot.send_message(chat_id, "Hozircha qiziqish bildirgan foydalanuvchilar yo'q. 🤷‍♂️")
        return

    bot.send_message(chat_id, f"👥 *Qiziquvchilar ro'yxati (oxirgi {min(len(interests), 30)} ta qiziqish):*", parse_mode="Markdown")

    msg_parts = []
    for idx, item in enumerate(interests[:30]):
        first_name = item['first_name'] or ""
        last_name = item['last_name'] or ""
        name = f"{first_name} {last_name}".strip() or "Noma'lum"

        username = item['username']
        username_str = f"@{username}" if username else f"[Profil](tg://user?id={item['user_id']})"
        phone = item['phone'] or "Tel yuborilmagan"

        q_type = item['query_type']
        item_name = item['item_name'] or ""

        if q_type == 'sets_info':
            action = "Setlar ro'yxatini ko'rdi"
        elif q_type == 'sub_info':
            action = "Obuna ma'lumotini ko'rdi"
        elif q_type == 'start_order_sub':
            action = "Obuna buyurtma qilishni boshladi"
        elif q_type == 'start_order_set':
            action = f"Set buyurtma qilishni boshladi: {item_name}"
        else:
            action = f"Qiziqdi: {item_name}"

        part = (
            f"{idx+1}. *{name}* ({username_str})\n"
            f"📞 Tel: {phone} | ID: `{item['user_id']}`\n"
            f"🔍 So'ragan narsasi: _{action}_\n"
            f"🕒 Vaqt: {item['created_at']}\n"
        )
        msg_parts.append(part)

    current_msg = ""
    for part in msg_parts:
        if len(current_msg) + len(part) > 4000:
            bot.send_message(chat_id, current_msg, parse_mode="Markdown")
            current_msg = part
        else:
            current_msg += part + "\n"

    if current_msg:
        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton("🗑 Ro'yxatni tozalash", callback_data="clear_interests"))
        bot.send_message(chat_id, current_msg, parse_mode="Markdown", reply_markup=markup)


# ─────────────────────────────────────────────
# Callback queries
# ─────────────────────────────────────────────

@bot.callback_query_handler(func=lambda call: True)
def handle_callbacks(call):
    if call.from_user.id not in config.ALLOWED_ADMIN_IDS:
        bot.answer_callback_query(call.id, "Kechirasiz, sizga ruxsat berilmagan!", show_alert=True)
        return

    chat_id = call.message.chat.id
    data = call.data

    import user_bot

    # 1. Buyurtma qabul / rad etish
    if data.startswith("approve_") or data.startswith("reject_"):
        order_id = int(data.split("_")[1])
        order = database.get_order(order_id)

        if not order:
            bot.answer_callback_query(call.id, "Buyurtma topilmadi.")
            return

        if order['status'] != 'pending':
            bot.answer_callback_query(call.id, f"Buyurtma allaqachon '{order['status']}' holatida!")
            return

        admin_name = call.from_user.username or call.from_user.first_name

        if data.startswith("approve_"):
            database.update_order_status(order_id, 'approved')
            bot.answer_callback_query(call.id, "Buyurtma qabul qilindi.")

            edited_text = call.message.text + f"\n\n✅ *Buyurtma qabul qilindi* (Admin: @{admin_name})"
            bot.edit_message_text(
                chat_id=chat_id,
                message_id=call.message.message_id,
                text=edited_text,
                parse_mode="Markdown",
                reply_markup=None
            )
            try:
                user_bot.bot.send_message(order['user_id'], "Sizning buyurtmangiz qabul qilindi! Tez orada yetkazib beriladi. 🚚")
            except Exception as e:
                print(f"Failed to notify user about approval: {e}")

        else:
            database.update_order_status(order_id, 'rejected')
            bot.answer_callback_query(call.id, "Buyurtma rad etildi.")

            edited_text = call.message.text + f"\n\n❌ *Buyurtma rad etildi* (Admin: @{admin_name})"
            bot.edit_message_text(
                chat_id=chat_id,
                message_id=call.message.message_id,
                text=edited_text,
                parse_mode="Markdown",
                reply_markup=None
            )
            try:
                user_bot.bot.send_message(order['user_id'], "Kechirasiz, sizning buyurtmangiz rad etildi. 😔")
            except Exception as e:
                print(f"Failed to notify user about rejection: {e}")

    # 2. Obuna rasmini o'tkazib yuborish
    elif data == "skip_sub_photo":
        if chat_id in admin_data and 'sub_text' in admin_data[chat_id]:
            sub_text = admin_data[chat_id]['sub_text']
            database.update_subscription_info(sub_text, None)
            bot.answer_callback_query(call.id, "Obuna ma'lumoti saqlandi.")
            bot.send_message(chat_id, "Obuna ma'lumotlari muvaffaqiyatli saqlandi! (Rasmsiz)", reply_markup=get_admin_keyboard())
            reset_state(chat_id)

    # 3. Set o'chirish
    elif data.startswith("delete_set_"):
        set_id = int(data.split("_")[2])
        set_info = database.get_food_set_by_id(set_id)
        if set_info:
            set_name = set_info['name']
            images_to_delete = database.delete_food_set(set_id)
            for img_path in images_to_delete:
                try:
                    if os.path.exists(img_path):
                        os.remove(img_path)
                except Exception as e:
                    print(f"Failed to delete file {img_path}: {e}")

            bot.answer_callback_query(call.id, f"'{set_name}' o'chirildi.")
            try:
                bot.delete_message(chat_id, call.message.message_id)
            except Exception:
                bot.edit_message_text(
                    chat_id=chat_id,
                    message_id=call.message.message_id,
                    text=f"❌ *{set_name}* seti o'chirildi.",
                    parse_mode="Markdown"
                )
        else:
            bot.answer_callback_query(call.id, "Set allaqachon o'chirilgan.")

    # 4. Qiziquvchilar ro'yxatini tozalash
    elif data == "clear_interests":
        database.clear_interests()
        bot.answer_callback_query(call.id, "Ro'yxat tozalandi.")
        bot.edit_message_text(
            chat_id=chat_id,
            message_id=call.message.message_id,
            text="🗑 *Qiziquvchilar ro'yxati tozalandi.*",
            parse_mode="Markdown"
        )

    # 5. Obuna ma'lumotini o'chirish
    elif data == "delete_sub_info":
        database.clear_subscription_info()
        bot.answer_callback_query(call.id, "Obuna ma'lumoti o'chirildi.", show_alert=True)
        try:
            bot.edit_message_text(
                chat_id=chat_id,
                message_id=call.message.message_id,
                text="🗑 *Obuna ma'lumoti muvaffaqiyatli o'chirildi.*",
                parse_mode="Markdown"
            )
        except Exception:
            pass

    # 6. Eski obuna rasmini saqlab qolish
    elif data == "keep_sub_photo":
        if chat_id in admin_data and 'sub_text' in admin_data[chat_id]:
            sub_text = admin_data[chat_id]['sub_text']
            _, old_photo = database.get_subscription_info()
            database.update_subscription_info(sub_text, old_photo)
            bot.answer_callback_query(call.id, "Eski rasm saqlandi.")
            bot.send_message(chat_id, "Obuna ma'lumotlari eski rasm bilan muvaffaqiyatli saqlandi!", reply_markup=get_admin_keyboard())
            reset_state(chat_id)

    # 7. Set rasmlarini yuklashni yakunlash
    elif data == "finish_photos":
        if chat_id in admin_data and admin_steps.get(chat_id) == STATE_ADDING_SET_PHOTOS:
            photos = admin_data[chat_id].get('photos', [])

            if not photos:
                bot.answer_callback_query(call.id, "Kamida 1 ta rasm yuborishingiz kerak!", show_alert=True)
                return

            bot.answer_callback_query(call.id, "Rasmlar yuklandi.")

            name = admin_data[chat_id]['name']
            description = admin_data[chat_id]['desc']
            price = admin_data[chat_id]['price']
            images_str = ",".join(photos)

            success = database.add_food_set(name, description, price, images_str)
            if success:
                bot.send_message(chat_id, f"🎉 *{name}* muvaffaqiyatli qo'shildi!", parse_mode="Markdown", reply_markup=get_admin_keyboard())
            else:
                bot.send_message(chat_id, "Xatolik: Bunday nomli set allaqachon mavjud!", reply_markup=get_admin_keyboard())

            reset_state(chat_id)


# ─────────────────────────────────────────────
# Message routing — admin states
# ─────────────────────────────────────────────

@bot.message_handler(func=lambda msg: True, content_types=['text', 'photo'])
def handle_admin_states(message):
    chat_id = message.chat.id
    state = admin_steps.get(chat_id)

    if not state:
        bot.send_message(chat_id, "Tugmalardan foydalaning.", reply_markup=get_admin_keyboard())
        return

    # ── BROADCASTING ──
    if state == STATE_BROADCASTING:
        # Faqat oddiy matn qabul qilinadi
        if message.content_type != 'text' or not message.text or message.text.startswith('/'):
            bot.send_message(chat_id, "Iltimos, xabar matnini yuboring:")
            return

        import user_bot

        conn = database.get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT chat_id FROM users")
        users = cursor.fetchall()
        conn.close()

        sent_count = 0
        for u in users:
            try:
                user_bot.bot.send_message(u['chat_id'], message.text)
                sent_count += 1
            except Exception:
                pass

        bot.send_message(chat_id, f"📢 Xabar {sent_count} ta foydalanuvchiga yuborildi!", reply_markup=get_admin_keyboard())
        reset_state(chat_id)

    # ── TODAY DISH — rasm kutilmoqda ──
    elif state == STATE_TODAY_DISH_PHOTO:
        if message.content_type == 'photo':
            file_id = message.photo[-1].file_id
            os.makedirs(IMAGES_DIR, exist_ok=True)
            try:
                file_info = bot.get_file(file_id)
                downloaded_file = bot.download_file(file_info.file_path)
                local_path = os.path.join(IMAGES_DIR, f"today_{file_id[:15]}_{int(time.time())}.jpg")
                with open(local_path, 'wb') as new_file:
                    new_file.write(downloaded_file)
                admin_data[chat_id]['today_photo'] = local_path
            except Exception as e:
                bot.send_message(chat_id, f"Rasm yuklashda xatolik: {e}")
                return

            admin_steps[chat_id] = STATE_TODAY_DISH_CONFIRM_TEXT
            bot.send_message(
                chat_id,
                "✅ Rasm qabul qilindi!\n\nQo'shimcha matn qo'shasizmi?",
                reply_markup=get_yes_no_keyboard()
            )
        else:
            bot.send_message(chat_id, "Iltimos, rasm formatida fayl yuboring.")

    # ── TODAY DISH — matn qo'shish tasdiqi ──
    elif state == STATE_TODAY_DISH_CONFIRM_TEXT:
        if message.content_type != 'text':
            bot.send_message(chat_id, "Iltimos, ✅ Ha yoki ❌ Yo'q tugmalaridan birini tanlang.", reply_markup=get_yes_no_keyboard())
            return

        if message.text == "✅ Ha":
            admin_steps[chat_id] = STATE_TODAY_DISH_TEXT
            bot.send_message(chat_id, "📝 Bugungi taom uchun matn kiriting:", reply_markup=get_cancel_keyboard())
        elif message.text == "❌ Yo'q":
            _send_today_dish_to_all(chat_id, photo_path=admin_data[chat_id]['today_photo'], caption=None)
        else:
            bot.send_message(chat_id, "Iltimos, ✅ Ha yoki ❌ Yo'q tugmalaridan birini tanlang.", reply_markup=get_yes_no_keyboard())

    # ── TODAY DISH — matn kirish ──
    elif state == STATE_TODAY_DISH_TEXT:
        if message.content_type != 'text' or not message.text or message.text.startswith('/'):
            bot.send_message(chat_id, "Iltimos, matn kiriting:")
            return
        _send_today_dish_to_all(chat_id, photo_path=admin_data[chat_id]['today_photo'], caption=message.text)

    # ── SET QO'SHISH — nom ──
    elif state == STATE_ADDING_SET_NAME:
        if message.content_type != 'text' or not message.text or message.text.startswith('/'):
            bot.send_message(chat_id, "Set nomini matn shaklida kiriting:")
            return
        admin_data[chat_id]['name'] = message.text
        admin_steps[chat_id] = STATE_ADDING_SET_DESC
        bot.send_message(chat_id, f"'{message.text}' uchun tavsif matnini kiriting:", reply_markup=get_cancel_keyboard())

    # ── SET QO'SHISH — tavsif ──
    elif state == STATE_ADDING_SET_DESC:
        if message.content_type != 'text' or not message.text or message.text.startswith('/'):
            bot.send_message(chat_id, "Set tavsifini matn shaklida kiriting:")
            return
        admin_data[chat_id]['desc'] = message.text
        admin_steps[chat_id] = STATE_ADDING_SET_PRICE
        bot.send_message(chat_id, "Set narxini kiriting (masalan, 35000 — faqat sonlar bilan):", reply_markup=get_cancel_keyboard())

    # ── SET QO'SHISH — narx ──
    elif state == STATE_ADDING_SET_PRICE:
        if message.content_type != 'text':
            bot.send_message(chat_id, "Iltimos, faqat musbat butun son kiriting (masalan, 45000):")
            return
        price_text = message.text or ""
        if not price_text.isdigit():
            bot.send_message(chat_id, "Iltimos, faqat musbat butun son kiriting (masalan, 45000):")
            return
        admin_data[chat_id]['price'] = int(price_text)
        admin_data[chat_id]['photos'] = []
        admin_steps[chat_id] = STATE_ADDING_SET_PHOTOS

        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton("✅ Tugatish", callback_data="finish_photos"))
        bot.send_message(
            chat_id,
            "Set uchun rasmlarni yuboring (kamida 1 ta, ko'pi bilan 3 ta). Rasmlarni yuborib bo'lgach, '✅ Tugatish' tugmasini bosing:",
            reply_markup=markup
        )

    # ── SET QO'SHISH — rasmlar ──
    elif state == STATE_ADDING_SET_PHOTOS:
        if message.content_type == 'photo':
            photos_list = admin_data[chat_id].get('photos', [])
            if len(photos_list) >= 3:
                bot.send_message(chat_id, "Maksimal 3 ta rasm yuklash mumkin. '✅ Tugatish' tugmasini bosing.")
                return

            file_id = message.photo[-1].file_id
            os.makedirs(IMAGES_DIR, exist_ok=True)
            try:
                file_info = bot.get_file(file_id)
                downloaded_file = bot.download_file(file_info.file_path)
                local_path = os.path.join(IMAGES_DIR, f"set_{file_id[:15]}_{int(time.time())}.jpg")
                with open(local_path, 'wb') as new_file:
                    new_file.write(downloaded_file)
                photos_list.append(local_path)
            except Exception as e:
                bot.send_message(chat_id, f"Rasm yuklashda xatolik: {e}")
                return

            admin_data[chat_id]['photos'] = photos_list

            markup = types.InlineKeyboardMarkup()
            markup.add(types.InlineKeyboardButton("✅ Tugatish", callback_data="finish_photos"))
            bot.send_message(
                chat_id,
                f"Rasm qabul qilindi ({len(photos_list)}/3). Yana rasm yuborishingiz yoki yakunlash tugmasini bosishingiz mumkin:",
                reply_markup=markup
            )
        else:
            bot.send_message(chat_id, "Iltimos, rasm formatida fayl yuboring yoki '✅ Tugatish' tugmasini bosing.")

    # ── OBUNA — matn ──
    elif state == STATE_EDITING_SUB_TEXT:
        if message.content_type != 'text' or not message.text or message.text.startswith('/'):
            bot.send_message(chat_id, "Obuna matnini kiriting:")
            return
        admin_data[chat_id]['sub_text'] = message.text
        admin_steps[chat_id] = STATE_EDITING_SUB_PHOTO

        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton("❌ Rasmsiz davom etish", callback_data="skip_sub_photo"))
        _, old_photo = database.get_subscription_info()
        if old_photo:
            markup.add(types.InlineKeyboardButton("💾 Avvalgi rasmni saqlab qolish", callback_data="keep_sub_photo"))

        bot.send_message(
            chat_id,
            "Obuna uchun rasm yuboring yoki pastdagi variantlardan birini tanlang:",
            reply_markup=markup
        )

    # ── OBUNA — rasm ──
    elif state == STATE_EDITING_SUB_PHOTO:
        if message.content_type == 'photo':
            file_id = message.photo[-1].file_id
            os.makedirs(IMAGES_DIR, exist_ok=True)
            try:
                file_info = bot.get_file(file_id)
                downloaded_file = bot.download_file(file_info.file_path)
                local_path = os.path.join(IMAGES_DIR, f"sub_{file_id[:15]}_{int(time.time())}.jpg")
                with open(local_path, 'wb') as new_file:
                    new_file.write(downloaded_file)
            except Exception as e:
                bot.send_message(chat_id, f"Rasm yuklashda xatolik: {e}")
                return

            sub_text = admin_data[chat_id]['sub_text']
            database.update_subscription_info(sub_text, local_path)

            bot.send_message(chat_id, "Obuna ma'lumotlari rasm bilan birga muvaffaqiyatli saqlandi! 📅", reply_markup=get_admin_keyboard())
            reset_state(chat_id)
        else:
            bot.send_message(chat_id, "Iltimos, rasm yuboring yoki quyidagi tugmalardan birini tanlang.")


# ─────────────────────────────────────────────
# Helper: bugungi taomni barcha userlarga yuborish
# ─────────────────────────────────────────────

def _send_today_dish_to_all(admin_chat_id, photo_path, caption):
    """Bugungi taom rasmini (va ixtiyoriy matnni) barcha userlarga yuboradi."""
    import user_bot

    database.update_today_dish(caption, photo_path)

    conn = database.get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT chat_id FROM users")
    users = cursor.fetchall()
    conn.close()

    # Rasmni bir marta o'qib, file_id orqali keyingi yuborimlarda tezlashtirish
    sent_count = 0
    failed_count = 0
    telegram_file_id = None  # Birinchi muvaffaqiyatli yuborishdan olingan file_id

    for u in users:
        try:
            if telegram_file_id:
                # Keyingi yuborimlarda file_id ishlatamiz — tezroq
                if caption:
                    user_bot.bot.send_photo(
                        u['chat_id'], telegram_file_id,
                        caption=f"🍽️ *Bugungi taomimiz:*\n\n{caption}",
                        parse_mode="Markdown"
                    )
                else:
                    user_bot.bot.send_photo(u['chat_id'], telegram_file_id, caption="🍽️ *Bugungi taomimiz!*", parse_mode="Markdown")
            else:
                if os.path.exists(photo_path):
                    with open(photo_path, 'rb') as photo_file:
                        if caption:
                            sent_msg = user_bot.bot.send_photo(
                                u['chat_id'], photo_file,
                                caption=f"🍽️ *Bugungi taomimiz:*\n\n{caption}",
                                parse_mode="Markdown"
                            )
                        else:
                            sent_msg = user_bot.bot.send_photo(u['chat_id'], photo_file, caption="🍽️ *Bugungi taomimiz!*", parse_mode="Markdown")
                    # Birinchi muvaffaqiyatli yuborishdan file_id olamiz
                    if sent_msg and sent_msg.photo:
                        telegram_file_id = sent_msg.photo[-1].file_id
            sent_count += 1
        except Exception:
            failed_count += 1

    reset_state(admin_chat_id)

    result_text = f"🍽️ Bugungi taom {sent_count} ta foydalanuvchiga yuborildi!"
    if failed_count > 0:
        result_text += f" ({failed_count} ta yuborilmadi)"
    bot.send_message(admin_chat_id, result_text, reply_markup=get_admin_keyboard())