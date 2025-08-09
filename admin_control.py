from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes

ADMIN_ID = 5073222820  # Apna admin ID yahan set karo


def is_admin(update: Update):
    return update.effective_user and update.effective_user.id == ADMIN_ID


async def admin_panel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update):
        await update.message.reply_text("⛔ आपके पास अनुमति नहीं है!")
        return

    keyboard = [
        [InlineKeyboardButton("👥 यूजर संख्या देखें", callback_data="admin_users")],
        [InlineKeyboardButton("📢 सभी यूजर को ब्रॉडकास्ट भेजें", callback_data="admin_broadcast")],
        # Aage ka option tum customize kar sakte ho
    ]
    await update.message.reply_text(
        "⚙️ *एडमिन कंट्रोल पैनल*",
        parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup(keyboard),
    )


async def admin_users_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update):
        await update.callback_query.answer("⛔ अनुमति नहीं है!", show_alert=True)
        return

    conn = context.bot_data.get("db_conn")
    if conn is None:
        await update.callback_query.answer("❌ डेटाबेस कनेक्शन नहीं मिला!", show_alert=True)
        return

    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM users")
    count = cursor.fetchone()[0]

    await update.callback_query.edit_message_text(f"👥 कुल यूजर जो बोट ने जोड़े हैं: {count}")


async def admin_broadcast_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update):
        await update.callback_query.answer("⛔ अनुमति नहीं है!", show_alert=True)
        return

    await update.callback_query.edit_message_text(
        "📢 कृपया वह मेसेज भेजें जो आप सभी यूजर को भेजना चाहते हैं।\n\n"
        "(टेक्स्ट, लिंक, फोटो या डॉक्यूमेंट हो सकता है।)"
    )
    context.user_data["broadcast_mode"] = True


async def handle_broadcast_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update):
        return
    if not context.user_data.get("broadcast_mode"):
        return

    context.user_data["broadcast_mode"] = False

    conn = context.bot_data.get("db_conn")
    if conn is None:
        await update.message.reply_text("❌ डेटाबेस कनेक्शन नहीं मिला। ब्रॉडकास्ट नहीं भेजा गया।")
        return

    cursor = conn.cursor()
    cursor.execute("SELECT user_id FROM users")
    users = cursor.fetchall()

    sent_count = 0
    failed_count = 0

    if update.message.photo:
        photo_file_id = update.message.photo[-1].file_id
        caption = update.message.caption or ""
        for (uid,) in users:
            try:
                await context.bot.send_photo(chat_id=uid, photo=photo_file_id, caption=caption)
                sent_count += 1
            except Exception:
                failed_count += 1
    elif update.message.document:
        doc_file_id = update.message.document.file_id
        caption = update.message.caption or ""
        for (uid,) in users:
            try:
                await context.bot.send_document(chat_id=uid, document=doc_file_id, caption=caption)
                sent_count += 1
            except Exception:
                failed_count += 1
    else:
        text = update.message.text
        for (uid,) in users:
            try:
                await context.bot.send_message(chat_id=uid, text=text)
                sent_count += 1
            except Exception:
                failed_count += 1

    await update.message.reply_text(f"📢 ब्रॉडकास्ट पूरा हुआ।\nसेंड: {sent_count}\nफेल: {failed_count}")
