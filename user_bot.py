import os

# Bot ish papkasini aniqlash (mutlaq yo'l uchun)
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
IMAGES_DIR = os.path.join(BASE_DIR, "images")

def resolve_image_path(path):
    """Nisbiy yoki mutlaq yo'lni mutlaq yo'lga o'giradi."""
    if not path:
        return path
    if os.path.isabs(path):
        return path
    # Nisbiy yo'l bo'lsa, BASE_DIR ga nisbatan hisoblaymiz
    return os.path.join(BASE_DIR, path)
import telebot
from telebot import types
import config
import database

bot = telebot.TeleBot(config.USER_BOT_TOKEN)

# User states and data store
user_steps = {}
user_data = {}

# State Constants
STATE_SELECTING_ORDER_TYPE = "SELECTING_ORDER_TYPE"
STATE_SELECTING_SET = "SELECTING_SET"
STATE_INPUTTING_NAME = "INPUTTING_NAME"
STATE_INPUTTING_PHONE = "INPUTTING_PHONE"
STATE_INPUTTING_ADDRESS = "INPUTTING_ADDRESS"
STATE_CONFIRMING_ORDER = "CONFIRMING_ORDER"

# Keyboard Builders
def get_main_keyboard():
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.row("📦 Setlar haqida ma'lumot")
    markup.row("🛍️ Buyurtma berish")
    markup.row("📅 1 oylik obuna ma'lumoti")
    return markup

def get_cancel_keyboard():
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.row("❌ Bekor qilish")
    return markup

def get_phone_keyboard():
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    btn_phone = types.KeyboardButton("📱 Telefon raqamini yuborish", request_contact=True)
    markup.add(btn_phone)
    markup.row("❌ Bekor qilish")
    return markup

def get_location_keyboard():
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    btn_loc = types.KeyboardButton("📍 Geolokatsiyani yuborish", request_location=True)
    markup.add(btn_loc)
    markup.row("❌ Bekor qilish")
    return markup

def get_confirmation_keyboard():
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.row("✅ Ha, to'g'ri", "❌ Yo'q, noto'g'ri")
    return markup

# Handlers
@bot.message_handler(commands=['start'])
def handle_start(message):
    chat_id = message.chat.id
    user = message.from_user
    
    # Save user to DB
    database.add_user(
        chat_id=chat_id,
        username=user.username,
        first_name=user.first_name,
        last_name=user.last_name
    )
    
    # Reset user state
    user_steps[chat_id] = None
    if chat_id in user_data:
        del user_data[chat_id]
        
    welcome_text = "Assalomu aleykum taomchi setga hush kelibsiz! 😊\n\nQuyidagi menyudan kerakli bo'limni tanlang:"
    bot.send_message(chat_id, welcome_text, reply_markup=get_main_keyboard())

@bot.message_handler(func=lambda msg: msg.text == "❌ Bekor qilish")
def handle_cancel(message):
    chat_id = message.chat.id
    user_steps[chat_id] = None
    if chat_id in user_data:
        del user_data[chat_id]
    bot.send_message(chat_id, "Buyurtma bekor qilindi. Bosh sahifa:", reply_markup=get_main_keyboard())

@bot.message_handler(func=lambda msg: msg.text == "📦 Setlar haqida ma'lumot")
def handle_set_info(message):
    chat_id = message.chat.id
    database.add_interest(chat_id, 'sets_info', 'Setlar menyusi')
    food_sets = database.get_food_sets()
    
    if not food_sets:
        bot.send_message(chat_id, "Hozircha menyuda hech qanday set mavjud emas. 😔")
        return
        
    bot.send_message(chat_id, "🍽️ *Bizning mazali setlarimiz:*", parse_mode="Markdown")
    
    for f_set in food_sets:
        name = f_set['name']
        desc = f_set['description']
        price = f_set['price']
        images_str = f_set['images']
        
        info_text = f"📦 *{name}*\n\n📝 Tavsif: {desc}\n\n💵 Narxi: {price:,} so'm"
        
        if images_str:
            file_ids = [fid.strip() for fid in images_str.split(',') if fid.strip()]
            if len(file_ids) == 1:
                try:
                    file_path = resolve_image_path(file_ids[0])
                    if os.path.exists(file_path):
                        with open(file_path, 'rb') as photo:
                            bot.send_photo(chat_id, photo, caption=info_text, parse_mode="Markdown")
                    else:
                        bot.send_message(chat_id, info_text + "\n\n_(Rasm topilmadi)_", parse_mode="Markdown")
                except Exception as e:
                    bot.send_message(chat_id, info_text + f"\n\n_(Rasm yuklanmadi: {str(e)})_", parse_mode="Markdown")
            else:
                try:
                    media = []
                    opened_files = []
                    for idx, raw_path in enumerate(file_ids):
                        file_path = resolve_image_path(raw_path)
                        if os.path.exists(file_path):
                            f = open(file_path, 'rb')
                            opened_files.append(f)
                            img_obj = f
                        else:
                            # Fayl topilmasa o'tkazib yuboramiz
                            continue
                            
                        if idx == 0:
                            media.append(types.InputMediaPhoto(img_obj, caption=info_text, parse_mode="Markdown"))
                        else:
                            media.append(types.InputMediaPhoto(img_obj))
                            
                    if media:
                        bot.send_media_group(chat_id, media)
                    else:
                        bot.send_message(chat_id, info_text + "\n\n_(Rasmlar topilmadi)_", parse_mode="Markdown")
                    for f in opened_files:
                        f.close()
                except Exception as e:
                    bot.send_message(chat_id, info_text + f"\n\n_(Rasmlar yuklanmadi: {str(e)})_", parse_mode="Markdown")
        else:
            bot.send_message(chat_id, info_text, parse_mode="Markdown")

@bot.message_handler(func=lambda msg: msg.text == "📅 1 oylik obuna ma'lumoti")
def handle_subscription_info(message):
    chat_id = message.chat.id
    database.add_interest(chat_id, 'sub_info', '1 oylik obuna ma\'lumoti')
    text, photo = database.get_subscription_info()
    
    if not text:
        text = "Obuna haqida ma'lumot mavjud emas."
        
    if photo:
        try:
            photo_path = resolve_image_path(photo)
            if os.path.exists(photo_path):
                with open(photo_path, 'rb') as f:
                    bot.send_photo(chat_id, f, caption=text)
            else:
                bot.send_message(chat_id, text + "\n\n_(Rasm topilmadi)_")
        except Exception as e:
            bot.send_message(chat_id, text + f"\n\n_(Rasm yuklanmadi: {str(e)})_")
    else:
        bot.send_message(chat_id, text)

@bot.message_handler(func=lambda msg: msg.text == "🛍️ Buyurtma berish")
def start_order(message):
    chat_id = message.chat.id
    user_steps[chat_id] = STATE_SELECTING_ORDER_TYPE
    user_data[chat_id] = {}
    
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.row("📅 1 oylik obuna", "🍔 1 martalik set")
    markup.row("❌ Bekor qilish")
    
    bot.send_message(chat_id, "Nima sotib olmoqchisiz? Tanlang:", reply_markup=markup)

# Multi-step order state machine
@bot.message_handler(func=lambda msg: True, content_types=['text', 'contact', 'location'])
def handle_order_steps(message):
    chat_id = message.chat.id
    state = user_steps.get(chat_id)
    
    if not state:
        # User is not in ordering state, ignore or redirect to start
        bot.send_message(chat_id, "Tugmalardan foydalaning yoki /start bosing.", reply_markup=get_main_keyboard())
        return
        
    if state == STATE_SELECTING_ORDER_TYPE:
        choice = message.text
        if choice == "📅 1 oylik obuna":
            user_data[chat_id]['order_type'] = 'subscription'
            user_data[chat_id]['set_name'] = None
            database.add_interest(chat_id, 'start_order_sub', 'Obuna buyurtmasi boshlandi')
            
            # Next state
            user_steps[chat_id] = STATE_INPUTTING_NAME
            bot.send_message(chat_id, "👤 1. Ism va familiyangizni kiriting:", reply_markup=get_cancel_keyboard())
            
        elif choice == "🍔 1 martalik set":
            user_data[chat_id]['order_type'] = 'set'
            
            # Show list of sets
            food_sets = database.get_food_sets()
            if not food_sets:
                bot.send_message(chat_id, "Kechirasiz, hozirda mavjud setlar yo'q.", reply_markup=get_main_keyboard())
                user_steps[chat_id] = None
                del user_data[chat_id]
                return
                
            markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
            for f_set in food_sets:
                markup.row(f_set['name'])
            markup.row("❌ Bekor qilish")
            
            user_steps[chat_id] = STATE_SELECTING_SET
            bot.send_message(chat_id, "🍔 Qaysi setni sotib olmoqchisiz? Tanlang:", reply_markup=markup)
        else:
            bot.send_message(chat_id, "Iltimos, tugmalardan birini tanlang.")
            
    elif state == STATE_SELECTING_SET:
        choice = message.text
        food_sets = database.get_food_sets()
        set_names = [f['name'] for f in food_sets]
        
        if choice in set_names:
            user_data[chat_id]['set_name'] = choice
            database.add_interest(chat_id, 'start_order_set', choice)
            
            # Next state
            user_steps[chat_id] = STATE_INPUTTING_NAME
            bot.send_message(chat_id, "👤 1. Ism va familiyangizni kiriting:", reply_markup=get_cancel_keyboard())
        else:
            bot.send_message(chat_id, "Iltimos, pastdagi ro'yxatdan birini tanlang.")
            
    elif state == STATE_INPUTTING_NAME:
        if not message.text or message.text.startswith('/'):
            bot.send_message(chat_id, "Iltimos, ism va familiyangizni matn shaklida to'g'ri kiriting:")
            return
            
        user_data[chat_id]['customer_name'] = message.text
        
        # Next state
        user_steps[chat_id] = STATE_INPUTTING_PHONE
        bot.send_message(chat_id, "📞 2. Telefon raqamingizni yuboring (Tugmani bosing yoki yozib yuboring):", reply_markup=get_phone_keyboard())
        
    elif state == STATE_INPUTTING_PHONE:
        phone = None
        if message.content_type == 'contact' and message.contact is not None:
            phone = message.contact.phone_number
        elif message.content_type == 'text':
            phone = message.text
            
        if not phone or phone.startswith('/'):
            bot.send_message(chat_id, "Iltimos, telefon raqamingizni yuboring yoki yozing:")
            return
            
        user_data[chat_id]['phone'] = phone
        
        # Next state
        user_steps[chat_id] = STATE_INPUTTING_ADDRESS
        bot.send_message(chat_id, "📍 3. Yetkazib berish manzilingizni kiriting (Manzilni yozing yoki geolokatsiyani yuboring):", reply_markup=get_location_keyboard())
        
    elif state == STATE_INPUTTING_ADDRESS:
        address = "Geolokatsiya ulashildi"
        latitude = None
        longitude = None
        
        if message.content_type == 'location' and message.location is not None:
            latitude = message.location.latitude
            longitude = message.location.longitude
        elif message.content_type == 'text':
            address = message.text
        else:
            bot.send_message(chat_id, "Iltimos, manzilingizni yozing yoki geolokatsiyangizni yuboring:")
            return
            
        user_data[chat_id]['address'] = address
        user_data[chat_id]['latitude'] = latitude
        user_data[chat_id]['longitude'] = longitude
        
        # Prepare summary and confirmation
        data = user_data[chat_id]
        order_type_str = "📅 1 oylik obuna" if data['order_type'] == 'subscription' else f"🍔 Set: {data['set_name']}"
        
        summary_text = (
            "❓ *Kiritilgan ma'lumotlaringiz to'g'rimi?*\n\n"
            f"🛍️ *Buyurtma turi:* {order_type_str}\n"
            f"👤 *Mijoz:* {data['customer_name']}\n"
            f"📞 *Tel:* {data['phone']}\n"
            f"📍 *Manzil:* {data['address']}\n"
        )
        
        user_steps[chat_id] = STATE_CONFIRMING_ORDER
        bot.send_message(chat_id, summary_text, parse_mode="Markdown", reply_markup=get_confirmation_keyboard())
        
    elif state == STATE_CONFIRMING_ORDER:
        choice = message.text
        if choice == "✅ Ha, to'g'ri":
            data = user_data[chat_id]
            
            # Save to Database
            order_id = database.add_order(
                user_id=chat_id,
                order_type=data['order_type'],
                set_name=data['set_name'],
                customer_name=data['customer_name'],
                phone=data['phone'],
                address=data['address'],
                latitude=data['latitude'],
                longitude=data['longitude']
            )
            
            bot.send_message(chat_id, "Tashrifingiz uchun rahmat, sizga aloqaga chiqishadi! 😊", reply_markup=get_main_keyboard())
            
            # Notify admins
            try:
                import admin_bot
                admin_bot.notify_new_order(order_id)
            except Exception as e:
                print(f"Error notifying admin: {str(e)}")
                
            # Clear states
            user_steps[chat_id] = None
            if chat_id in user_data:
                del user_data[chat_id]
                
        elif choice == "❌ Yo'q, noto'g'ri":
            # Restart ordering
            user_steps[chat_id] = STATE_SELECTING_ORDER_TYPE
            user_data[chat_id] = {}
            
            markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
            markup.row("📅 1 oylik obuna", "🍔 1 martalik set")
            markup.row("❌ Bekor qilish")
            
            bot.send_message(chat_id, "Ma'lumotlar bekor qilindi.\n\nNima sotib olmoqchisiz? Boshidan tanlang:", reply_markup=markup)
        else:
            bot.send_message(chat_id, "Iltimos, tugmalardan birini tanlang.")
