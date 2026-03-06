import os
import asyncio
import re
import sqlite3
import google.generativeai as genai
from telethon import TelegramClient, events
from telethon.sessions import StringSession

# --- Secrets/Environment Variables থেকে ডেটা নেওয়া ---
API_ID = int(os.environ.get("API_ID"))
API_HASH = os.environ.get("API_HASH")
SESSION_STRING = os.environ.get("SESSION_STRING")
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")

# Gemini AI কনফিগারেশন
genai.configure(api_key=GEMINI_API_KEY)

# সেফটি সেটিংস (যাতে সংঘাত বা যুদ্ধের খবর ব্লক না হয়)
safety_settings = [
    {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_NONE"},
    {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_NONE"},
    {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_NONE"},
    {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_NONE"},
]

model = genai.GenerativeModel(
    model_name='gemini-1.5-flash',
    safety_settings=safety_settings,
    generation_config={
        "temperature": 0.4,
        "top_p": 0.9,
    }
)

# ডাটাবেস সেটআপ
db = sqlite3.connect("vanguard_gemini.db")
cursor = db.cursor()
cursor.execute("CREATE TABLE IF NOT EXISTS mapping (source_id INTEGER, target_id INTEGER)")
db.commit()

# সোর্স চ্যানেল এবং টার্গেট চ্যানেল
CHANNELS = ['FotrosResistancee', 'IntelRepublic', 'Middle_East_Spectator', 'IRIran_Military', 'hnaftali']
TARGET = '@VanguardalertBD'

async def ai_translate(text):
    if not text:
        return ""
    
    # অপ্রয়োজনীয় লিঙ্ক ও ইউজারনেম পরিষ্কার করা
    text = re.sub(r'https?://\S+', '', text)
    text = re.sub(r'@\w+', '', text).strip()
    
    if len(text) < 5:
        return ""

    try:
        # হাই-কোয়ালিটি প্রফেশনাল নিউজ প্রম্পট
        prompt = (
            "You are a professional Bengali journalist. "
            "Translate the following news into natural, sophisticated Bengali. "
            "Rule 1: Don't translate word-for-word like Google Translate. "
            "Rule 2: Use standard journalistic terminology (Shuddho Bhasha). "
            "Rule 3: Ensure the news flows logically in Bengali. "
            "Rule 4: Output ONLY the translated news text.\n\n"
            f"English News: {text}"
        )
        
        response = model.generate_content(prompt)
        
        if response.text:
            translated_text = response.text.strip()
            return f"{translated_text}\n\n📢 @VanguardalertBD"
        else:
            return f"{text}\n\n📢 @VanguardalertBD"
            
    except Exception as e:
        print(f"Gemini AI Error: {e}")
        return f"{text}\n\n📢 @VanguardalertBD"

async def main():
    client = TelegramClient(StringSession(SESSION_STRING), API_ID, API_HASH)
    
    try:
        await client.start()
        print("🚀 Vanguard Gemini AI (Secrets Active) is Running!")

        @client.on(events.NewMessage(chats=CHANNELS))
        async def handle_new(e):
            if not e.message.message:
                return
            
            translated_msg = await ai_translate(e.message.message)
            
            try:
                # মিডিয়া থাকলে মিডিয়াসহ পাঠানো
                sent_msg = await client.send_message(TARGET, translated_msg, file=e.message.media)
                cursor.execute("INSERT INTO mapping VALUES (?, ?)", (e.id, sent_msg.id))
                db.commit()
            except Exception as ex:
                print(f"Post Error: {ex}")

        @client.on(events.MessageEdited(chats=CHANNELS))
        async def handle_edit(e):
            cursor.execute("SELECT target_id FROM mapping WHERE source_id = ?", (e.id,))
            result = cursor.fetchone()
            
            if result:
                target_msg_id = result[0]
                new_text = await ai_translate(e.message.message)
                try:
                    await client.edit_message(TARGET, target_msg_id, text=new_text)
                except:
                    pass
            
        await client.run_until_disconnected()

    except Exception as e:
        print(f"Startup Error: {e}")

if __name__ == "__main__":
    asyncio.run(main())
