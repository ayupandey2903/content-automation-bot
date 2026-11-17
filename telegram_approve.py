import os
import asyncio
import mysql.connector
from dotenv import load_dotenv
from telegram import Bot, InlineKeyboardButton, InlineKeyboardMarkup

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


async def send_draft_for_approval():
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)

    cursor.execute("SELECT id, content FROM posts WHERE status = 'draft' LIMIT 1")
    draft = cursor.fetchone()

    if not draft:
        print("No drafts waiting for approval.")
        return

    post_id = draft["id"]
    content = draft["content"]

    bot = Bot(token=BOT_TOKEN)

    keyboard = InlineKeyboardMarkup([
    [
        InlineKeyboardButton("✅ Approve", callback_data=f"approve_{post_id}"),
        InlineKeyboardButton("❌ Reject", callback_data=f"reject_{post_id}")
    ],
    [
        InlineKeyboardButton("🔁 Request Changes", callback_data=f"changes_{post_id}")
    ]

    ])

    message = await bot.send_message(
        chat_id=CHAT_ID,
        text=f"📝 Draft #{post_id}\n\n{content}",
        reply_markup=keyboard
    )

    cursor.execute(
        "UPDATE posts SET telegram_message_id = %s WHERE id = %s",
        (str(message.message_id), post_id)
    )
    conn.commit()

    print(f"Draft #{post_id} sent to Telegram for approval.")

    cursor.close()
    conn.close()


if __name__ == "__main__":
    asyncio.run(send_draft_for_approval())