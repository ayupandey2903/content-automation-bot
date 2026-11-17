import os
from dotenv import load_dotenv
from google import genai

load_dotenv()

client = genai.Client(api_key=os.environ["GEMINI_API_KEY"])

response = client.models.generate_content(
    model="gemini-3.8-flash",
    contents="Write one short, engaging tweet about staying productive while working from home. Keep it under 250 characters, no hashtags."
)

print(response.text)