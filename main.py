import os
import logging
import sqlite3
import asyncio
from datetime import datetime
from telegram import (
    Update,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    InputMediaPhoto,
    InputMediaVideo,
)
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    CallbackQueryHandler,
    MessageHandler,
    filters,
    ContextTypes,
)

# ===== CONFIGURATION =====
BOT_TOKEN = os.getenv("8464960686:AAEw2ZGxNhsqusz_IgAeNbZENGqaOK-TWfM")
ADMIN_ID = 5073222820  # अपना Telegram ID डालो
DB_PATH = "bot_users.db"

# Plan to Channel Mapping
PLAN_CHANNELS = {
    '99_indian': -1002411835724,    # 👑 Indian L££d Des channel
    '99_tango': -1001733080767,      # 👑 Tang0 & Str!pchat channel
    '199': -1002785323161,           # Ultimate plan channel
    '249_chamet': -1002833081538,    # 👑 Chamet.video.vip channel
}

# Setup logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)

# In-memory user-channel map (if needed)
user_channel = {}

# Database init
def init_db():
    conn = sqlite3.connect(DB_PATH)
    conn.execute("CREATE TABLE IF NOT EXISTS users (user_id INTEGER PRIMARY KEY)")
    conn.commit()
    conn.close()

def add_user_to_db(user_id: int):
    conn = sqlite3.connect(DB_PATH)
    conn.execute("INSERT OR IGNORE INTO users (user_id) VALUES (?)", (user_id,))
    conn.commit()
    conn.close()

def fetch_all_users():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.execute("SELECT user_id FROM users")
    users = [row[0] for row in cursor.fetchall()]
    conn.close()
    return users

# ---- START: Support DB helpers ----
def init_support_table():
    conn = sqlite3.connect(DB_PATH)
    conn.execute("""
    CREATE TABLE IF NOT EXISTS support_map (
        admin_msg_id INTEGER PRIMARY KEY,
        user_id INTEGER NOT NULL,
        user_msg_id INTEGER,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """)
    conn.commit()
    conn.close()

def save_support_mapping(admin_msg_id: int, user_id: int, user_msg_id: int = None):
    conn = sqlite3.connect(DB_PATH)
    conn.execute(
        "INSERT OR REPLACE INTO support_map (admin_msg_id, user_id, user_msg_id, created_at) VALUES (?, ?, ?, ?)",
        (admin_msg_id, user_id, user_msg_id, datetime.utcnow()),
    )
    conn.commit()
    conn.close()

def get_user_by_admin_msg(admin_msg_id: int):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.execute("SELECT user_id, user_msg_id FROM support_map WHERE admin_msg_id = ?", (admin_msg_id,))
    row = cursor.fetchone()
    conn.close()
    if row:
        return {"user_id": row[0], "user_msg_id": row[1]}
    return None

def delete_support_mapping(admin_msg_id: int):
    conn = sqlite3.connect(DB_PATH)
    conn.execute("DELETE FROM support_map WHERE admin_msg_id = ?", (admin_msg_id,))
    conn.commit()
    conn.close()
# ---- END: Support DB helpers ----

# Helper: Send colorful message with inline buttons
async def send_membership_plans(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("👑 Indian L££d Des!:- ₹99 lifetime", callback_data="plan_99_indian")],
        [InlineKeyboardButton("👑 Tang0 & Str!pchat:- ₹99 lifetime", callback_data="plan_99_tango")],
        [InlineKeyboardButton("👑 Chamet.video.vip:- ₹249 lifetime", callback_data="plan_249_chamet")],
        [InlineKeyboardButton("🌟 ₹199 Ultimate Plan", callback_data="plan_199")],
    ]
    text = (
        "✨ <b><u>Welcome to Premium Membership Plans</u></b> ✨\n\n"
        "Choose a plan below to get exclusive access:\n\n"
        "👑 ₹99 - Indian L££d Des Lifetime\n"
        "👑 ₹99 - Tang0 & Str!pchat Lifetime\n"
        "👑 ₹249 - Chamet.video.vip Lifetime\n"
        "🌟 ₹199 - Ultimate Plan\n\n"
        "👉 <i>Select your plan by clicking a button below</i>"
    )
    await update.message.reply_text(
        text, parse_mode="HTML", reply_markup=InlineKeyboardMarkup(keyboard)
    )

# Start command handler
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    if not user:
        return
    uid = user.id
    full_name = user.full_name or "User"

    # Add to DB
    loop = asyncio.get_running_loop()
    await loop.run_in_executor(None, add_user_to_db, uid)

    # Notify admin about new user
    try:
        await context.bot.send_message(
            chat_id=ADMIN_ID,
            text=f"👤 New user started bot:\n\nName: {full_name}\nID: {uid}",
        )
    except Exception as e:
        logger.error(f"Failed to notify admin: {e}")

    # Send welcome + plans
    welcome_text = (
        f"👋 Hello <b>{full_name}</b>!\n\n"
        "Welcome to our exclusive Telegram bot.\n"
        "Please choose a membership plan below to proceed."
    )
    await update.message.reply_text(
        welcome_text, parse_mode="HTML"
    )
    await send_membership_plans(update, context)

# Handle plan selection
async def plan_selected(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    data = q.data  # e.g. plan_99_indian, plan_99_tango, plan_199, plan_249_chamet

    uid = q.from_user.id
    plan_key = data.split("_", 1)[1]  # Get the full plan key after "plan_"
    
    # Store selected plan in user_data
    context.user_data['plan'] = plan_key

    plan_info = {
        "99_indian": {
            "name": "Indian L££d Des",
            "price": "₹99",
            "desc": "Lifetime Access",
            "demo_url": "https://telegra.ph/Premium-sirf-vip-06-03-11",
            "demo_img": "https://freeimage.host/i/FLdvITb",
            "payment_img": "https://freeimage.host/i/FLd3hAX",
            "features": "🔞Daily latest new porn video is uploaded in this channel, currently 10000 plus videos are already present and 3000 plus images are available"
        },
        "99_tango": {
            "name": "Tang0 & Str!pchat",
            "price": "₹99",
            "desc": "Lifetime Access",
            "demo_url": "https://telegra.ph/Premium-sirf-vip-06-03-9",
            "demo_img": "https://freeimage.host/i/FL34o92",
            "payment_img": "https://freeimage.host/i/FLd3hAX",
            "features": "🔞this group daily latest live video tango stripchat latest video is uploaded while already 8000 plus videos uploaded and 3000 plus images"
        },
        "199": {
            "name": "Ultimate Plan",
            "price": "₹199",
            "desc": "Ultimate Access",
            "payment_img": "https://i.ibb.co/7fSB1CQ/qr.png",
        },
        "249_chamet": {
            "name": "Chamet-video-vip",
            "price": "₹249",
            "desc": "Lifetime Access",
            "demo_url": "https://telegra.ph/Premium-sirf-vip-06-03-6",
            "demo_img": "https://freeimage.host/i/FLFlsMg",
            "payment_img": "https://freeimage.host/i/FLFOJxj",
            "features": "🔞this group daily latest live video Chamet vip latest video is uploaded while already 3000 plus videos uploaded and 500 plus images"
        }
    }

    if plan_key not in plan_info:
        await q.edit_message_text("Invalid plan selected.")
        return

    info = plan_info[plan_key]

    # Delete old message
    try:
        await q.message.delete()
    except:
        pass

    # Special handling for ₹99 and ₹249 plans
    if plan_key in ["99_indian", "99_tango", "249_chamet"]:
        # First message for plan
        caption1 = (
            f"🔞Group Name - 👑 {info['name']}\n"
            "━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
            f"💰 price - {info['price']}\n"
            "━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
            f"⌛Duration - {info['desc']}\n"
            "━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
            f"{info['features']}"
        )
        keyboard1 = InlineKeyboardMarkup([
            [InlineKeyboardButton("🔞Live Demo", url=info['demo_url'])]
        ])
        
        await context.bot.send_photo(
            chat_id=uid,
            photo=info['demo_img'],
            caption=caption1,
            reply_markup=keyboard1
        )
        
        # Second message for plan
        caption2 = (
            "Please complete the following payment:\n\n"
            f"💰 Price - {info['price']}\n"
            f"🆔 Order ID - {uid}\n\n"
            "👇Instructions:-\n"
            "1️⃣ Scan QR and pay\n"
            "2️⃣ Send ✅ screenshot\n"
            "3️⃣ Show UTR/Txn ID in screenshot"
        )
        keyboard2 = InlineKeyboardMarkup([
            [
                InlineKeyboardButton("Demo group", url="https://t.me/+JpFMWbFto6wwY2Nl"),
                InlineKeyboardButton("Proof 🧾", url="https://t.me/+x4s1rIAKLxQ1ODFl")
            ],
            [InlineKeyboardButton("✅ Payment Done", callback_data="payment_done")]
        ])
        
        await context.bot.send_photo(
            chat_id=uid,
            photo=info['payment_img'],
            caption=caption2,
            reply_markup=keyboard2
        )
        return

    # For ultimate plan (199)
    caption = (
        f"💰 <b>Price:</b> {info['price']}\n"
        f"⌛ <b>Duration:</b> {info['desc']}\n\n"
        "👇 Please complete payment by scanning QR below and send payment screenshot here.\n"
        "After payment, click the 'Payment Done' button."
    )

    keyboard = InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton("✅ Payment Done", callback_data="payment_done"),
            ]
        ]
    )

    await context.bot.send_photo(
        chat_id=uid,
        photo=info["payment_img"],
        caption=caption,
        parse_mode="HTML",
        reply_markup=keyboard,
    )

# Payment Done callback
async def payment_done_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    uid = q.from_user.id
    context.user_data["waiting_payment_ss"] = True

    await context.bot.send_message(
        chat_id=uid,
        text="✅ धन्यवाद! कृपया अब भुगतान का स्क्रीनशॉट भेजें।"
    )

# Handle payment screenshot
async def handle_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.user_data.get("waiting_payment_ss"):
        return

    uid = update.effective_user.id
    plan_key = context.user_data.get('plan', '99_indian')

    # Forward screenshot to admin
    try:
        await update.message.forward(chat_id=ADMIN_ID)
    except Exception as e:
        logger.error(f"Failed to forward payment screenshot: {e}")
        await update.message.reply_text("कुछ गलती हुई, कृपया पुनः प्रयास करें।")
        context.user_data.clear()
        return

    # Notify admin with approve/reject buttons
    await context.bot.send_message(
        chat_id=ADMIN_ID,
        text=f"💰 Payment screenshot from user ID: {uid}\nPlan: {plan_key}",
        reply_markup=InlineKeyboardMarkup(
            [
                [
                    InlineKeyboardButton("✅ Approve", callback_data=f"approve_{uid}_{plan_key}"),
                    InlineKeyboardButton("❌ Reject", callback_data=f"reject_{uid}_{plan_key}"),
                ]
            ]
        ),
    )

    await update.message.reply_text(
        "📩 Payment received. कृपया कुछ समय प्रतीक्षा करें, एडमिन आपकी पेमेंट वेरीफाई करने के बाद 1 से 5 मिनट के अंदर ग्रुप का लिंक भेज देगा।"
    )
    context.user_data.clear()

# Admin approve/reject callback
async def admin_approval_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()

    data = q.data  # approve_123456_99_indian or reject_123456_99_tango
    parts = data.split("_")
    if len(parts) < 3:
        await q.edit_message_text("Invalid action.")
        return

    action = parts[0]
    try:
        uid = int(parts[1])
        plan_key = "_".join(parts[2:])  # Handle keys with underscores
    except (ValueError, IndexError):
        await q.edit_message_text("Invalid user id or plan.")
        return

    # Get channel ID based on plan
    CHANNEL_ID = PLAN_CHANNELS.get(plan_key, PLAN_CHANNELS['99_indian'])

    try:
        # Create single-use invite link
        invite = await context.bot.create_chat_invite_link(
            chat_id=CHANNEL_ID, 
            member_limit=1,
            creates_join_request=False
        )
        invite_link = invite.invite_link
    except Exception as e:
        logger.error(f"Failed to create invite link: {e}")
        try:
            invite_link = await context.bot.export_chat_invite_link(CHANNEL_ID)
        except Exception as e:
            logger.error(f"Failed to export invite link: {e}")
            invite_link = None

    if action == "approve":
        if invite_link:
            await context.bot.send_message(
                chat_id=uid,
                text=f"🎉 आपकी पेमेंट वेरीफाई हो गई है! इस लिंक से जुड़ें:\n{invite_link}\n\n"
                     "⚠️ ध्यान दें: यह लिंक सिर्फ 1 बार इस्तेमाल होगा। अगर आप ज्वाइन नहीं कर पाए तो दोबारा बॉट स्टार्ट करें।"
            )
            await q.edit_message_text(f"✅ Payment approved for user {uid}. Invite link sent.")
        else:
            await q.edit_message_text(f"✅ Payment approved for user {uid}, लेकिन लिंक नहीं भेजा जा सका।")
            await context.bot.send_message(
                chat_id=uid,
                text="🎉 आपकी पेमेंट वेरीफाई हो गई है! (Admin invite link भेजने में असमर्थ)"
            )
    else:
        await context.bot.send_message(
            chat_id=uid,
            text="❌ आपकी पेमेंट वेरीफाई नहीं हो पाई। कृपया सही स्क्रीनशॉट भेजें या एडमिन से संपर्क करें।"
        )
        await q.edit_message_text(f"❌ Payment rejected for user {uid}.")

# ---- START: Support handlers ----
# Help command: accept inline message or start two-step flow
async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    if not user:
        return
    uid = user.id
    # If command has args: /help Problem here...
    full_text = update.message.text or ""
    parts = full_text.split(" ", 1)
    if len(parts) > 1 and parts[1].strip():
        user_msg = parts[1].strip()
        # send directly to admin (as a sent message for context)
        try:
            sent = await context.bot.send_message(
                chat_id=ADMIN_ID,
                text=f"📩 Help request from <b>{user.full_name or uid}</b> (ID: <code>{uid}</code>):\n\n{user_msg}",
                parse_mode="HTML"
            )
            # save mapping so admin can reply to this sent message
            save_support_mapping(sent.message_id, uid, None)
            await update.message.reply_text("✅ आपकी समस्या एडमिन को भेज दी गई है। वे जल्द ही रिप्लाई करेंगे।")
        except Exception as e:
            logger.error(f"Failed to send help message to admin: {e}")
            await update.message.reply_text("❌ कुछ गलत हुआ, कृपया बाद में पुनः प्रयास करें।")
        return

    # else start two-step flow
    context.user_data["awaiting_help"] = True
    await update.message.reply_text("✍️ कृपया अपनी समस्या यहाँ लिखें — मैं इसे सीधे एडमिन को भेज दूँगा।")

# Handler to catch the user's next message (when awaiting_help flag is set)
async def help_text_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.user_data.get("awaiting_help"):
        return  # not in help flow, ignore
    uid = update.effective_user.id
    user_name = update.effective_user.full_name or uid

    # Forward the user's message to admin to preserve media if any
    msg = update.message
    try:
        # If message has media, forward whole message (keeps original media)
        if msg.photo or msg.video or msg.document or msg.sticker:
            forwarded = await msg.forward(chat_id=ADMIN_ID)
            admin_msg_id = forwarded.message_id
            # Save mapping
            save_support_mapping(admin_msg_id, uid, msg.message_id)
            await update.message.reply_text("✅ आपकी मैसेज एडमिन को भेज दी गई है।")
        else:
            # For plain text, send formatted message to admin
            sent = await context.bot.send_message(
                chat_id=ADMIN_ID,
                text=f"📩 Help request from <b>{user_name}</b> (ID: <code>{uid}</code>):\n\n{msg.text}",
                parse_mode="HTML"
            )
            save_support_mapping(sent.message_id, uid, msg.message_id)
            await update.message.reply_text("✅ आपकी मैसेज एडमिन को भेज दी गई है।")
    except Exception as e:
        logger.error(f"Failed to send help message to admin: {e}")
        await update.message.reply_text("❌ कुछ गलत हुआ, कृपया बाद में पुनः प्रयास करें।")

    # clear flag
    context.user_data.pop("awaiting_help", None)

# Admin reply handler: admin must reply to the forwarded/admin message
async def admin_reply_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # Only allow admin to use this
    if update.effective_user.id != ADMIN_ID:
        return

    msg = update.message
    if not msg.reply_to_message:
        # Not a reply -> ignore
        return

    replied_id = msg.reply_to_message.message_id
    mapping = get_user_by_admin_msg(replied_id)
    if not mapping:
        # Maybe admin replied to a forwarded message that doesn't exist in mapping
        await msg.reply_text("⚠️ यह मैसेज किसी यूज़र के साथ मैपेड नहीं है। कृपया पहले यूज़र का मैसेज फॉरवर्ड/सेंड करें।")
        return

    user_id = mapping["user_id"]

    # Helper to forward/send appropriate content to the user
    try:
        if msg.text:
            await context.bot.send_message(chat_id=user_id, text=f"💬 Admin reply:\n\n{msg.text}")
        elif msg.photo:
            await context.bot.send_photo(chat_id=user_id, photo=msg.photo[-1].file_id, caption=msg.caption)
        elif msg.video:
            await context.bot.send_video(chat_id=user_id, video=msg.video.file_id, caption=msg.caption)
        elif msg.document:
            await context.bot.send_document(chat_id=user_id, document=msg.document.file_id, caption=msg.caption)
        elif msg.sticker:
            await context.bot.send_sticker(chat_id=user_id, sticker=msg.sticker.file_id)
        else:
            # fallback: forward the admin's reply as-is
            await msg.forward(chat_id=user_id)

        # Optional: notify admin that message sent
        await msg.reply_text(f"✅ Reply sent to user {user_id}.")
    except Exception as e:
        logger.error(f"Failed to deliver admin reply to {user_id}: {e}")
        await msg.reply_text(f"❌ Failed to send reply to user (error logged).")
# ---- END: Support handlers ----

# Admin panel command handler
async def admin_panel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    if user.id != ADMIN_ID:
        await update.message.reply_text("❌ You are not authorized to use this command.")
        return

    keyboard = [
        [InlineKeyboardButton("👥 List All Users", callback_data="admin_users")],
        [InlineKeyboardButton("📢 Broadcast Message", callback_data="admin_broadcast")],
    ]
    text = "<b>Admin Panel</b>\n\nChoose an action below:"
    await update.message.reply_text(text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="HTML")

# Admin users list callback
async def admin_users_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    users = fetch_all_users()
    text = f"👥 Total Users: {len(users)}\n\n" + "\n".join(str(u) for u in users[:50])
    if len(users) > 50:
        text += "\n\nand more..."
    await q.edit_message_text(text)

# Admin broadcast start
async def admin_broadcast_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    await q.edit_message_text("📢 कृपया भेजने के लिए मैसेज लिखें (टेक्स्ट, फोटो, वीडियो, डॉक्यूमेंट, या फॉरवर्ड किया हुआ मैसेज):")

    # Set a flag in user_data to accept next message as broadcast
    context.user_data["broadcast_mode"] = True

# Handle broadcast message from admin
async def handle_broadcast_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    if user.id != ADMIN_ID:
        return  # Only admin allowed

    if not context.user_data.get("broadcast_mode"):
        return

    context.user_data["broadcast_mode"] = False

    users = fetch_all_users()
    count = 0
    failed = 0

    # Check message type and prepare broadcast content
    msg = update.message

    # Function to send message to a user
    async def send_to_user(user_id):
        nonlocal count, failed
        try:
            if msg.text:
                await context.bot.send_message(chat_id=user_id, text=msg.text)
            elif msg.photo:
                await context.bot.send_photo(chat_id=user_id, photo=msg.photo[-1].file_id, caption=msg.caption)
            elif msg.video:
                await context.bot.send_video(chat_id=user_id, video=msg.video.file_id, caption=msg.caption)
            elif msg.document:
                await context.bot.send_document(chat_id=user_id, document=msg.document.file_id, caption=msg.caption)
            elif msg.sticker:
                await context.bot.send_sticker(chat_id=user_id, sticker=msg.sticker.file_id)
            else:
                # Unsupported content, try forwarding the whole message
                await msg.forward(chat_id=user_id)
            count += 1
        except Exception as e:
            logger.error(f"Failed to send broadcast to {user_id}: {e}")
            failed += 1

    # Broadcast concurrently (batching for rate-limit can be added later)
    tasks = [send_to_user(u) for u in users]
    await asyncio.gather(*tasks)

    await update.message.reply_text(f"📢 Broadcast sent to {count} users, failed: {failed}.")

# Main function
def main():
    init_db()
    init_support_table()
    if not BOT_TOKEN:
        logger.error("BOT_TOKEN env var missing! Set it in environment variables.")
        import time
        while True:
            time.sleep(60)

    app = ApplicationBuilder().token(BOT_TOKEN).build()

    # Register handlers
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(plan_selected, pattern="^plan_"))
    app.add_handler(CallbackQueryHandler(payment_done_callback, pattern="^payment_done$"))
    app.add_handler(MessageHandler(filters.PHOTO & ~filters.COMMAND, handle_photo))
    app.add_handler(CallbackQueryHandler(admin_approval_callback, pattern="^(approve|reject)_"))

    app.add_handler(CommandHandler("admin", admin_panel))
    app.add_handler(CallbackQueryHandler(admin_users_callback, pattern="^admin_users$"))
    app.add_handler(CallbackQueryHandler(admin_broadcast_callback, pattern="^admin_broadcast$"))

    # ----- Support handlers (add BEFORE generic/broadcast handler) -----
    app.add_handler(CommandHandler("help", help_command))
    # admin replies (admin must reply to forwarded/sent admin message)
    app.add_handler(MessageHandler(filters.ALL & filters.Chat(ADMIN_ID) & filters.REPLY, admin_reply_handler))
    # user's follow-up when in awaiting_help mode
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, help_text_handler))
    # ------------------------------------------------------------------

    # Generic/broadcast catch-all (keep at end)
    app.add_handler(MessageHandler(filters.ALL & ~filters.COMMAND, handle_broadcast_message))

    logger.info("Bot started")
    app.run_polling()

if __name__ == "__main__":
    main()
