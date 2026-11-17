import os
import mysql.connector
from dotenv import load_dotenv
from google import genai
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CallbackQueryHandler, MessageHandler, ContextTypes, filters
from safety_filter import is_safe

load_dotenv()

BOT_TOKEN = os.environ["TELEGRAM_BOT_TOKEN"]
CHAT_ID = os.environ["TELEGRAM_CHAT_ID"]


def get_connection():
    return mysql.connector.connect(
        host="localhost",
        user="root",
        password="508622",
        database="content_bot"
    )


def build_keyboard(post_id):
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton("✅ Approve", callback_data=f"approve_{post_id}"),
            InlineKeyboardButton("❌ Reject", callback_data=f"reject_{post_id}")
        ],
        [
            InlineKeyboardButton("🔁 Request Changes", callback_data=f"changes_{post_id}")
        ]
    ])


async def handle_button_tap(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    action, post_id = query.data.split("_")
    post_id = int(post_id)

    conn = get_connection()
    cursor = conn.cursor()

    if action == "approve":
        cursor.execute("UPDATE posts SET status = 'approved' WHERE id = %s", (post_id,))
        conn.commit()
        await query.edit_message_text(f"✅ Approved — Draft #{post_id} will be posted.")

    elif action == "reject":
        cursor.execute("UPDATE posts SET status = 'rejected' WHERE id = %s", (post_id,))
        conn.commit()
        await query.edit_message_text(f"❌ Rejected — Draft #{post_id} will not be posted.")

    elif action == "changes":
        # Remember which post this user is giving feedback about
        context.user_data["awaiting_feedback_for"] = post_id
        await query.edit_message_text(
            f"🔁 Draft #{post_id} — what would you like changed?\n\nJust type your feedback as a normal message."
        )

    cursor.close()
    conn.close()


async def handle_feedback_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    post_id = context.user_data.get("awaiting_feedback_for")

    if not post_id:
        # No pending feedback request — ignore random messages
        return

    feedback = update.message.text

    conn = get_connection()
    cursor = conn.cursor(dictionary=True)

    cursor.execute("""
        SELECT p.content, t.topic
        FROM posts p
        JOIN topics t ON p.topic_id = t.id
        WHERE p.id = %s
    """, (post_id,))
    row = cursor.fetchone()

    if not row:
        await update.message.reply_text("Couldn't find that draft anymore.")
        cursor.close()
        conn.close()
        return

    original_content = row["content"]
    topic_text = row["topic"]

    await update.message.reply_text("Got it — regenerating with your feedback...")

    client = genai.Client(api_key=os.environ["GEMINI_API_KEY"])
    response = client.models.generate_content(
        model="gemini-3.5-flash-lite",
        contents=(
            f"Original topic: {topic_text}\n"
            f"Previous draft: {original_content}\n"
            f"Feedback from the user: {feedback}\n\n"
            f"Rewrite the tweet applying this feedback. Max 250 characters, no hashtags in the body."
        )
    )
    new_content = response.text.strip()

    if is_safe(new_content):
        cursor.execute(
            "UPDATE posts SET content = %s, safety_passed = TRUE WHERE id = %s",
            (new_content, post_id)
        )
        conn.commit()

        await update.message.reply_text(
            f"📝 Updated Draft #{post_id}\n\n{new_content}",
            reply_markup=build_keyboard(post_id)
        )
    else:
        cursor.execute(
            "UPDATE posts SET status = 'rejected', safety_passed = FALSE WHERE id = %s",
            (post_id,)
        )
        conn.commit()
        await update.message.reply_text("⚠️ The revised version failed the safety check — draft rejected.")

    # Clear the "waiting for feedback" state now that we're done
    context.user_data["awaiting_feedback_for"] = None

    cursor.close()
    conn.close()


def main():
    app = Application.builder().token(BOT_TOKEN).build()
    app.add_handler(CallbackQueryHandler(handle_button_tap))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_feedback_text))
    print("Listening for Telegram button taps and feedback... (press Ctrl+C to stop)")
    app.run_polling()


if __name__ == "__main__":
    main()