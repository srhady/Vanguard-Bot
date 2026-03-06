import os
import asyncio
import re
import sqlite3
from google import genai
from google.genai import types
from telethon import TelegramClient, events
from telethon.sessions import StringSession

# --- Secrets/Env Variables ---
API_ID = int(os.environ.get("API_ID"))
API_HASH = os.environ.get("API_HASH")
SESSION_STRING = os.environ.get("SESSION_STRING")
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")

# Gemini ক্লায়েন্ট সেটআপ
client_gemini = genai.Client(api_key=GEMINI_API_KEY)

# ডাটাবেস
db = sqlite3.connect("vanguard_gemini.db")
cursor = db.cursor()
cursor.execute("CREATE TABLE IF NOT EXISTS mapping (source_id INTEGER, target_id INTEGER)")
db.commit()

CHANNELS = ['FotrosResistancee', 'IntelRepublic', 'Middle_East_Spectator', 'IRIran_Military', 'hnaftali']
TARGET = '@VanguardalertBD'

async def ai_translate(text):
    if not text: return ""
    
    # ক্লিনআপ (লিঙ্ক ও ইউজারনেম সরানো)
    original_text = text
    text = re.sub(r'https?://\S+', '', text)
    text = re.sub(r'@\w+', '', text).strip()
    
    if len(text) < 5: 
        return f"{original_text}\n\n📢 @VanguardalertBD"

    try:
        # প্রফেশনাল নিউজ এডিটর প্রম্পট
        prompt = (
            "You are a professional Bengali news editor. "
            "Translate the following news into natural, sophisticated journalistic Bengali. "
            "Output ONLY the translated text.\n\n"
            f"News: {text}"
        )
        
        response = client_gemini.models.generate_content(
            model='gemini-1.5-flash',
            contents=prompt,
            config=types.GenerateContentConfig(
                temperature=0.3,
                safety_settings=[
                    types.SafetySetting(category='HARM_CATEGORY_HATE_SPEECH', threshold='BLOCK_NONE'),
                    types.SafetySetting(category='HARM_CATEGORY_HARASSMENT', threshold='BLOCK_NONE'),
                    types.SafetySetting(category='HARM_CATEGORY_DANGEROUS_CONTENT', threshold='BLOCK_NONE'),
                    types.SafetySetting(category='HARM_CATEGORY_SEXUALLY_EXPLICIT', threshold='BLOCK_NONE'),
                ]
            )
        )
        
        if response.text:
            return f"{response.text.strip()}\n\n📢 @VanguardalertBD"
        else:
            print("⚠️ AI Warning: Empty response from Gemini. Posting original.")
            return f"{original_text}\n\n📢 @VanguardalertBD"
            
    except Exception as e:
        # এখানে আপনি টার্মিনালে ডিটেইল এরর দেখতে পাবেন
        print(f"❌ Gemini Translation Failed! Error: {e}")
        # টেলিগ্রামে অরিজিনাল টেক্সটই যাবে
        return f"{original_text}\n\n📢 @VanguardalertBD"

async def main():
    client = TelegramClient(StringSession(SESSION_STRING), API_ID, API_HASH)
    await client.start()
    print("🚀 Vanguard Gemini is Running! (Log tracking active)")

    @client.on(events.NewMessage(chats=CHANNELS))
    async def handle_new(e):
        if not e.message.message: return
        
        # অনুবাদ করার চেষ্টা করবে
        translated_msg = await ai_translate(e.message.message)
        
        try:
            sent_msg = await client.send_message(TARGET, translated_msg, file=e.message.media)
            cursor.execute("INSERT INTO mapping VALUES (?, ?)", (e.id, sent_msg.id))
            db.commit()
        except Exception as ex:
            print(f"Telegram Post Error: {ex}")

    @client.on(events.MessageEdited(chats=CHANNELS))
    async def handle_edit(e):
        cursor.execute("SELECT target_id FROM mapping WHERE source_id = ?", (e.id,))
        result = cursor.fetchone()
        if result:
            new_text = await ai_translate(e.message.message)
            try:
                await client.edit_message(TARGET, result[0], text=new_text)
            except Exception as ex:
                print(f"Edit Sync Error: {ex}")
            
    await client.run_until_disconnected()

if __name__ == "__main__":
    asyncio.run(main())
