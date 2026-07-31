import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
import sqlite3

BOT_TOKEN = '8021399146:AAF4advl-a3ZoSNrM_DzpqbRbLkImF9JkfQ' 
ADMIN_CHAT_ID = 8457000157

bot = telebot.TeleBot(BOT_TOKEN)

# ================= PAYMENT DETAILS =================
PAYMENT_TEXT = (
    "⚠️ **Note: Please Check Name, Number & ID before sending payment** ⚠️\n\n"
    "🟢 📱 **1. EasyPaisa**\n"
    "🔹 Number: `03215150976`\n"
    "🔹 Name: Ahmed Iftikhar\n\n"
    "🟡 💱 **2. Binance**\n"
    "🔸 Pay ID: `991923035`\n"
    "🔸 Name: ahmad819"
)
# ===================================================

# ----------------- DATABASE SETUP -----------------
def init_db():
    conn = sqlite3.connect('store.db', check_same_thread=False)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS products (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT,
            validity TEXT,
            price_pkr TEXT,
            price_usd TEXT
        )
    ''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS stock (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            product_id INTEGER,
            account_details TEXT
        )
    ''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            chat_id INTEGER PRIMARY KEY
        )
    ''')
    conn.commit()
    conn.close()

init_db()
# --------------------------------------------------

user_states = {}
admin_states = {}

def register_user(chat_id):
    conn = sqlite3.connect('store.db', check_same_thread=False)
    cursor = conn.cursor()
    cursor.execute("INSERT OR IGNORE INTO users (chat_id) VALUES (?)", (chat_id,))
    conn.commit()
    conn.close()

def broadcast_to_users(message_text, parse_mode="Markdown"):
    conn = sqlite3.connect('store.db', check_same_thread=False)
    cursor = conn.cursor()
    cursor.execute("SELECT chat_id FROM users")
    users = cursor.fetchall()
    conn.close()
    
    success_count = 0
    for user in users:
        try:
            bot.send_message(user[0], message_text, parse_mode=parse_mode)
            success_count += 1
        except:
            pass
    return success_count

# ================= 1. ADMIN PANEL (MANAGE PRODUCTS) =================

@bot.message_handler(commands=['catalog'])
def manage_catalog(message):
    if message.chat.id != ADMIN_CHAT_ID: return
    
    conn = sqlite3.connect('store.db', check_same_thread=False)
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM products")
    products = cursor.fetchall()
    conn.close()

    text = "🛍️ 📊 **Apna Product Catalog:**\n\n"
    if not products:
        text += "🚫 Abhi koi product add nahi kiya gaya.\n"
    else:
        for p in products:
            text += f"🆔 `{p[0]}` : 📦 [{p[1]}] ⏳ [{p[2]}] 💵 [{p[3]} PKR] 💲 [${p[4]}]\n"

    markup = InlineKeyboardMarkup()
    markup.row(
        InlineKeyboardButton("➕ ✨ Add Product", callback_data="catalog_add"),
        InlineKeyboardButton("✏️ 📝 Edit Product", callback_data="catalog_edit")
    )
    markup.row(
        InlineKeyboardButton("🗑️ ❌ Delete Product", callback_data="catalog_del")
    )
    bot.send_message(message.chat.id, text, reply_markup=markup, parse_mode="Markdown")

@bot.callback_query_handler(func=lambda call: call.data.startswith('catalog_'))
def handle_catalog_action(call):
    if call.message.chat.id != ADMIN_CHAT_ID: return
    action = call.data.split('_')[1]

    if action == "add":
        admin_states[ADMIN_CHAT_ID] = {"step": "waiting_for_new_product"}
        msg = (
            "📝 ✨ **Naya Product is format mein type kar ke bhejein:**\n\n"
            "📦 `Product Name, Validity, Price in PKR, Price in $`\n\n"
            "💡 **Example:**\n`🛡️ Nord VPN, 1 Month, 1500, 5`"
        )
        bot.send_message(ADMIN_CHAT_ID, msg, parse_mode="Markdown")

    elif action == "edit":
        admin_states[ADMIN_CHAT_ID] = {"step": "waiting_for_edit_product_id"}
        bot.send_message(ADMIN_CHAT_ID, "✏️ 📝 **Edit Product:**\nJo product edit karna hai uska sirf **Number (ID)** type kar ke bhejein. (e.g. `1`)", parse_mode="Markdown")
        
    elif action == "del":
        admin_states[ADMIN_CHAT_ID] = {"step": "waiting_for_del_product"}
        bot.send_message(ADMIN_CHAT_ID, "🗑️ ⚠️ **Delete Product:**\nJo product delete karna hai uska sirf **Number (ID)** type kar ke bhejein. (e.g. `1`)", parse_mode="Markdown")

# ================= 2. ADMIN TEXT HANDLER =================

@bot.message_handler(func=lambda message: message.chat.id == ADMIN_CHAT_ID and ADMIN_CHAT_ID in admin_states)
def handle_admin_text_input(message):
    state = admin_states[ADMIN_CHAT_ID].get("step")

    if state == "waiting_for_new_product":
        try:
            parts = message.text.split(',')
            name = parts[0].strip()
            validity = parts[1].strip()
            price_pkr = parts[2].strip()
            price_usd = parts[3].strip()

            conn = sqlite3.connect('store.db', check_same_thread=False)
            cursor = conn.cursor()
            cursor.execute("INSERT INTO products (name, validity, price_pkr, price_usd) VALUES (?, ?, ?, ?)", (name, validity, price_pkr, price_usd))
            conn.commit()
            conn.close()

            bot.send_message(ADMIN_CHAT_ID, f"✅ 🎊 **Product Successfully Added:**\n📦 [{name}] ⏳ [{validity}] 💵 [{price_pkr} PKR] 💲 [${price_usd}]", parse_mode="Markdown")
            
            broadcast_msg = (
                f"🎉 **NEW PRODUCT ADDED!** 🎉\n\n"
                f"Hamare store mein ek naya product shamil kiya gaya hai:\n\n"
                f"🛍️ **{name}** ({validity})\n"
                f"💵 **Price:** {price_pkr} PKR / ${price_usd}\n\n"
                f"Kharidne ke liye abhi `/start` dabayen aur 'Refresh Menu' par click karein! 🛒"
            )
            success = broadcast_to_users(broadcast_msg)
            bot.send_message(ADMIN_CHAT_ID, f"📢 Yeh update {success} users ko bhej di gayi hai.")
            
            del admin_states[ADMIN_CHAT_ID]
        except:
            bot.send_message(ADMIN_CHAT_ID, "❌ ⚠️ Format galat hai! Kripya comma (,) laga kar exact example jaisa bhejein:\n`🛡️ Nord VPN, 1 Month, 1500, 5`", parse_mode="Markdown")

    elif state == "waiting_for_edit_product_id":
        try:
            prod_id = int(message.text.strip())
            conn = sqlite3.connect('store.db', check_same_thread=False)
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM products WHERE id = ?", (prod_id,))
            prod = cursor.fetchone()
            conn.close()

            if prod:
                admin_states[ADMIN_CHAT_ID] = {"step": "waiting_for_edit_product_details", "product_id": prod_id}
                current_details = f"📦 Name: {prod[1]}\n⏳ Validity: {prod[2]}\n💵 PKR: {prod[3]}\n💲 USD: {prod[4]}"
                msg = (
                    f"✅ **Product Found (ID: {prod_id}):**\n\n{current_details}\n\n"
                    "📝 ✨ **Ab naye details is format mein bhejein:**\n"
                    "`Product Name, Validity, Price in PKR, Price in $`\n\n"
                    f"💡 **Asani ke liye isay copy kar ke edit karein:**\n`{prod[1]}, {prod[2]}, {prod[3]}, {prod[4]}`"
                )
                bot.send_message(ADMIN_CHAT_ID, msg, parse_mode="Markdown")
            else:
                bot.send_message(ADMIN_CHAT_ID, "❌ ⚠️ Is ID ka koi product nahi mila.")
                del admin_states[ADMIN_CHAT_ID]
        except:
            bot.send_message(ADMIN_CHAT_ID, "❌ ⚠️ Sirf number (ID) bhejein!")

    elif state == "waiting_for_edit_product_details":
        try:
            parts = message.text.split(',')
            name = parts[0].strip()
            validity = parts[1].strip()
            price_pkr = parts[2].strip()
            price_usd = parts[3].strip()
            prod_id = admin_states[ADMIN_CHAT_ID]["product_id"]

            conn = sqlite3.connect('store.db', check_same_thread=False)
            cursor = conn.cursor()
            cursor.execute("UPDATE products SET name=?, validity=?, price_pkr=?, price_usd=? WHERE id=?", (name, validity, price_pkr, price_usd, prod_id))
            conn.commit()
            conn.close()

            bot.send_message(ADMIN_CHAT_ID, f"✅ 🎊 **Product Successfully Updated!**", parse_mode="Markdown")
            del admin_states[ADMIN_CHAT_ID]
        except:
            bot.send_message(ADMIN_CHAT_ID, "❌ ⚠️ Format galat hai!", parse_mode="Markdown")

    elif state == "waiting_for_del_product":
        try:
            prod_id = int(message.text.strip())
            conn = sqlite3.connect('store.db', check_same_thread=False)
            cursor = conn.cursor()
            cursor.execute("DELETE FROM products WHERE id = ?", (prod_id,))
            cursor.execute("DELETE FROM stock WHERE product_id = ?", (prod_id,))
            conn.commit()
            conn.close()

            bot.send_message(ADMIN_CHAT_ID, f"🗑️ ✅ Product (ID: `{prod_id}`) Delete kar diya gaya hai.", parse_mode="Markdown")
            del admin_states[ADMIN_CHAT_ID]
        except:
            bot.send_message(ADMIN_CHAT_ID, "❌ ⚠️ Sirf number (ID) bhejein!")

    elif state == "waiting_for_stock_details":
        product_id = admin_states[ADMIN_CHAT_ID]["product_id"]
        account_details = message.text
        
        conn = sqlite3.connect('store.db', check_same_thread=False)
        cursor = conn.cursor()
        cursor.execute("INSERT INTO stock (product_id, account_details) VALUES (?, ?)", (product_id, account_details))
        conn.commit()
        conn.close()
        
        bot.send_message(ADMIN_CHAT_ID, "🎉 🔐 Stock successfully save ho gaya hai!")
        del admin_states[ADMIN_CHAT_ID]

    elif state == "waiting_for_broadcast_msg":
        broadcast_msg = message.text
        bot.send_message(ADMIN_CHAT_ID, "⏳ Broadcasting start ho rahi hai... Kripya intezar karein.")
        success = broadcast_to_users(f"📢 **Admin Update:**\n\n{broadcast_msg}")
        bot.send_message(ADMIN_CHAT_ID, f"✅ **Broadcast Complete!**\nMessage {success} users ko successfully bhej diya gaya hai.")
        del admin_states[ADMIN_CHAT_ID]

# ================= 3. USER MENU & BUTTONS =================

def get_menu_markup():
    conn = sqlite3.connect('store.db', check_same_thread=False)
    cursor = conn.cursor()
    cursor.execute("SELECT id, name, price_usd FROM products")
    products = cursor.fetchall()
    conn.close()

    markup = InlineKeyboardMarkup()
    markup.row_width = 1
    
    if products:
        for p in products:
            prod_id = p[0]
            name = p[1]
            price_usd = p[2]
            markup.add(InlineKeyboardButton(f"🛒 {name}  |  ${price_usd}", callback_data=f"buy_{prod_id}"))
    
    markup.row(
        InlineKeyboardButton("💳 Payment Methods", callback_data="show_payments"),
        InlineKeyboardButton("📞 Contact Support", callback_data="contact_support")
    )
    markup.row(
        InlineKeyboardButton("🔄 Refresh Menu", callback_data="refresh_menu")
    )
    return markup, bool(products)

@bot.message_handler(commands=['start'])
def send_welcome(message):
    register_user(message.chat.id)
    markup, has_products = get_menu_markup()
    
    if not has_products:
        text = "👋 🌟 **Welcome to our Premium Digital Store!** 🌟\n\n🚫 Store me abhi products add ho rahe hain. Kripya 'Refresh Menu' par click kar ke thori der baad check karein."
    else:
        text = (
            "👋 🌟 **Welcome to our Premium Digital Store!** 🌟\n\n"
            "🔥 Hamare paas best digital subscriptions available hain.\n"
            "👇 **Neeche diye gaye menu se apna product select karein:**"
        )
        
    bot.send_message(message.chat.id, text, reply_markup=markup, parse_mode="Markdown")

@bot.callback_query_handler(func=lambda call: call.data == 'refresh_menu')
def handle_refresh(call):
    markup, has_products = get_menu_markup()
    
    if not has_products:
        text = "👋 🌟 **Welcome to our Premium Digital Store!** 🌟\n\n🚫 Store me abhi products add ho rahe hain. Kripya 'Refresh Menu' par click kar ke thori der baad check karein."
    else:
        text = (
            "👋 🌟 **Welcome to our Premium Digital Store!** 🌟\n\n"
            "🔥 Hamare paas best digital subscriptions available hain.\n"
            "👇 **Neeche diye gaye menu se apna product select karein (Menu Updated ✅):**"
        )
        
    try:
        bot.edit_message_text(
            chat_id=call.message.chat.id,
            message_id=call.message.message_id,
            text=text,
            reply_markup=markup,
            parse_mode="Markdown"
        )
        bot.answer_callback_query(call.id, "Menu Refreshed Successfully! 🔄✅")
    except:
        bot.answer_callback_query(call.id, "Menu is already up to date! ✅")

@bot.callback_query_handler(func=lambda call: call.data == 'show_payments')
def show_payments_menu(call):
    bot.send_message(call.message.chat.id, PAYMENT_TEXT, parse_mode="Markdown")
    bot.answer_callback_query(call.id)

@bot.callback_query_handler(func=lambda call: call.data == 'contact_support')
def show_support_menu(call):
    support_text = (
        "📞 **Contact Support:**\n\n"
        "Agar aapko koi masla darpesh hai ya koi sawal pochna chahte hain, toh neeche diye gaye buttons par click kar ke hamari support team se rabta karein. 👇"
    )
    
    markup = InlineKeyboardMarkup()
    markup.add(InlineKeyboardButton("💬 WhatsApp Support", url="https://wa.me/923215150976"))
    markup.add(InlineKeyboardButton("✈️ Telegram Support", url="https://t.me/MRAScontact_bot"))
    
    bot.send_message(call.message.chat.id, support_text, reply_markup=markup, parse_mode="Markdown")
    bot.answer_callback_query(call.id)

# ================= 4. BUY PRODUCT (USER) =================

@bot.callback_query_handler(func=lambda call: call.data.startswith('buy_'))
def handle_product_selection(call):
    chat_id = call.message.chat.id
    product_id = int(call.data.split('_')[1])
    
    conn = sqlite3.connect('store.db', check_same_thread=False)
    cursor = conn.cursor()
    cursor.execute("SELECT name, validity, price_pkr, price_usd FROM products WHERE id = ?", (product_id,))
    prod = cursor.fetchone()
    conn.close()

    if not prod:
        bot.send_message(chat_id, "❌ ⚠️ Product not found.")
        return

    name, validity, price_pkr, price_usd = prod
    
    user_states[chat_id] = {"step": "waiting_for_screenshot", "product_id": product_id, "product_name": name}

    checkout_message = (
        f"✅ **Aapne select kiya hai:**\n\n"
        f"🛍️ **Product:** {name} ({validity})\n"
        f"💵 **Price:** {price_pkr} PKR / ${price_usd}\n\n"
        f"👇 **Send Payment Here:** 👇\n\n"
        f"{PAYMENT_TEXT}\n\n"
        "📸 📲 **After Payment send Screen shot in this Whatsapp number:** `+923215150976`\n\n"
        "✅ **After payment done you Got Product Successful**"
    )
    
    markup = InlineKeyboardMarkup()
    whatsapp_button = InlineKeyboardButton("💬 Send Screenshot on WhatsApp", url="https://wa.me/923215150976")
    markup.add(whatsapp_button)
    
    bot.send_message(chat_id, checkout_message, reply_markup=markup, parse_mode="Markdown")

# ================= 5. SCREENSHOT RECEIVER =================

@bot.message_handler(content_types=['photo'])
def handle_screenshot(message):
    chat_id = message.chat.id
    
    if chat_id in user_states and user_states[chat_id].get("step") == "waiting_for_screenshot":
        user_data = user_states[chat_id]
        bot.send_message(chat_id, "✅ ⏳ **Screenshot Received!**\nAdmin verify kar ke aapko details bhej denge. Kripya intezar karein.")
        
        photo_id = message.photo[-1].file_id
        caption = (
            f"🚨 🛍️ **NEW ORDER REQUEST!** 🚨\n\n"
            f"👤 **User ID:** `{chat_id}`\n"
            f"📧 **Username:** @{message.from_user.username}\n"
            f"📦 **Product:** {user_data['product_name']}"
        )
        
        markup = InlineKeyboardMarkup()
        btn_approve = InlineKeyboardButton("✅ Approve & Send", callback_data=f"admin_app_{chat_id}_{user_data['product_id']}")
        btn_reject = InlineKeyboardButton("❌ Reject", callback_data=f"admin_rej_{chat_id}")
        markup.add(btn_approve, btn_reject)
        
        bot.send_photo(ADMIN_CHAT_ID, photo_id, caption=caption, parse_mode="Markdown", reply_markup=markup)
        del user_states[chat_id]

# ================= 6. EMERGENCY BROADCAST (ADMIN) =================

@bot.message_handler(commands=['broadcast'])
def start_broadcast(message):
    if message.chat.id != ADMIN_CHAT_ID: return
    
    admin_states[ADMIN_CHAT_ID] = {"step": "waiting_for_broadcast_msg"}
    msg = (
        "📢 **Emergency Broadcast System**\n\n"
        "Jo message aap yahan type karenge, wo bot ke **tamam users** ko chala jayega.\n\n"
        "Ab apna message type kar ke bhejein:"
    )
    bot.send_message(ADMIN_CHAT_ID, msg, parse_mode="Markdown")

# ================= 7. ADD STOCK (ADMIN) =================

@bot.message_handler(commands=['addstock'])
def add_stock_start(message):
    if message.chat.id != ADMIN_CHAT_ID: return
    
    conn = sqlite3.connect('store.db', check_same_thread=False)
    cursor = conn.cursor()
    cursor.execute("SELECT id, name FROM products")
    products = cursor.fetchall()
    conn.close()
    
    if not products:
        bot.send_message(message.chat.id, "❌ ⚠️ Pehle /catalog command use kar ke koi product add karein.")
        return

    markup = InlineKeyboardMarkup()
    for p in products:
        markup.add(InlineKeyboardButton(f"📦 Add Stock: {p[1]}", callback_data=f"addstock_{p[0]}"))
        
    bot.send_message(message.chat.id, "👇 Kis product ka stock add karna chahte hain?", reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data.startswith('addstock_'))
def ask_stock_details(call):
    if call.message.chat.id != ADMIN_CHAT_ID: return
    product_id = int(call.data.split('_')[1])
    
    admin_states[ADMIN_CHAT_ID] = {"step": "waiting_for_stock_details", "product_id": product_id}
    bot.send_message(ADMIN_CHAT_ID, "✅ ✨ Ab account details (Email/Password) send karein jo user ko bhejni hai.")

# ================= 8. APPROVE / REJECT =================

@bot.callback_query_handler(func=lambda call: call.data.startswith('admin_'))
def handle_admin_action(call):
    if call.message.chat.id != ADMIN_CHAT_ID: return

    data = call.data.split('_')
    action = data[1]
    user_id = int(data[2])

    if action == 'app':
        product_id = int(data[3])
        
        conn = sqlite3.connect('store.db', check_same_thread=False)
        cursor = conn.cursor()
        cursor.execute("SELECT id, account_details FROM stock WHERE product_id = ? LIMIT 1", (product_id,))
        item = cursor.fetchone()
        
        if item:
            item_id = item[0]
            account_details = item[1]
            
            cursor.execute("DELETE FROM stock WHERE id = ?", (item_id,))
            conn.commit()
            conn.close()
            
            success_msg = (
                f"🎉 ✅ **Payment Verified Successfully!**\n\n"
                f"🎁 Yeh rahay aapke account ki details:\n\n"
                f"🔐 `{account_details}`\n\n"
                f"🙏 **Purchase karne ka shukriya! Enjoy your premium service!** 🌟"
            )
            try:
                bot.send_message(user_id, success_msg, parse_mode="Markdown")
                bot.edit_message_caption("✅ 📦 **Approved & Delivered**", chat_id=ADMIN_CHAT_ID, message_id=call.message.message_id, parse_mode="Markdown")
            except:
                bot.answer_callback_query(call.id, "⚠️ Error sending message.")
        else:
            conn.close()
            bot.answer_callback_query(call.id, "❌ OUT OF STOCK!")
            bot.send_message(ADMIN_CHAT_ID, "⚠️ 🚫 **OUT OF STOCK!** Is product ka stock khatam hai. Pehle /addstock karein.")

    elif action == 'rej':
        reject_msg = "❌ ⚠️ **Payment Rejected!**\n\nAapka screenshot verify nahi ho saka. Dobara check karein ya admin se rabta karein."
        try:
            bot.send_message(user_id, reject_msg, parse_mode="Markdown")
            bot.edit_message_caption("❌ 🚫 **Rejected**", chat_id=ADMIN_CHAT_ID, message_id=call.message.message_id, parse_mode="Markdown")
        except:
            pass

print("🚀 Store Bot with Broadcasting and Notifications is running...")
bot.infinity_polling()