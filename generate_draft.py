import os
import mysql.connector
from dotenv import load_dotenv
from google import genai
from safety_filter import is_safe

load_dotenv()

conn = mysql.connector.connect(
    host="localhost",
    user="root",
    password="508622",
    database="content_bot"
)
cursor = conn.cursor(dictionary=True)

cursor.execute("""
    SELECT t.id, t.topic
    FROM topics t
    LEFT JOIN posts p ON p.topic_id = t.id
    WHERE p.id IS NULL
    LIMIT 1
""")
topic_row = cursor.fetchone()

if not topic_row:
    print("No new topics to generate drafts for.")
else:
    topic_id = topic_row["id"]
    topic_text = topic_row["topic"]
    print(f"Generating draft for topic: {topic_text}")

    client = genai.Client(api_key=os.environ["GEMINI_API_KEY"])
    response = client.models.generate_content(
        model="gemini-3.5-flash-lite",
        contents=f"Write one short, engaging tweet about: {topic_text}. Max 250 characters, no hashtags in the body."
    )
    tweet_text = response.text.strip()

    if is_safe(tweet_text):
        cursor.execute(
            "INSERT INTO posts (topic_id, content, status, safety_passed) VALUES (%s, %s, 'draft', TRUE)",
            (topic_id, tweet_text)
        )
        conn.commit()
        print("Draft saved (passed safety check):")
        print(tweet_text)
    else:
        cursor.execute(
            "INSERT INTO posts (topic_id, content, status, safety_passed) VALUES (%s, %s, 'rejected', FALSE)",
            (topic_id, tweet_text)
        )
        conn.commit()
        print("⚠️ Content blocked by safety filter — saved as rejected, not sent for approval.")

cursor.close()
conn.close()