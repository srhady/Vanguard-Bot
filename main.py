import os
import asyncio
import re
import sqlite3
from google import genai
from google.genai import types
from telethon import TelegramClient, events
from telethon.sessions import StringSession

# --- Secrets ---
API_ID = int(os.environ.get("API_ID"))
API_HASH = os.environ.get("API_HASH")
SESSION_STRING = os.environ.get("SESSION_STRING")
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")

client_gemini = genai.Client(api_key=GEMINI_API_KEY)

db = sqlite3.connect("vanguard_gemini.db")
cursor = db.cursor()
cursor.execute("CREATE TABLE IF NOT EXISTS mapping (source_id INTEGER, target_id INTEGER)")
db.commit()

CHANNELS = ['FotrosResistancee', 'IntelRepublic', 'Middle_East_Spectator', 'IRIran_Military', 'hnaftali']
TARGET = '@VanguardalertBD'

async def ai_translate(text):
    if not text: return ""
    
    # --- টেক্সট ক্লিনআপ (যাতে সোর্স চ্যানেলের নাম/লিঙ্ক না যায়) ---
    clean_text = text
    # t.me/username স্টাইলের লিঙ্ক মোছা
    clean_text = re.sub(r'(https?://)?t\.me/\S+', '', clean_text, flags=re.IGNORECASE)
    # সাধারণ http/https লিঙ্ক মোছা
    clean_text = re.sub(r'https?://\S+', '', clean_text)
    # @username স্টাইলের মেনশন মোছা
    clean_text = re.sub(r'@\w+', '', clean_text).strip()
    
    if len(clean_text) < 5: 
        return f"{clean_text}\n\n📢 @VanguardalertBD"

    try:
        prompt = (
            "You are a professional Bengali news editor. "
            "Translate the following news into natural, sophisticated journalistic Bengali. "
            "Output ONLY the translated text. Do not add any extra comments.\n\n"
            f"News: {clean_text}"
        )
        
        # লেটেস্ট জিমিনি ২.০ মডেল ব্যবহার করা হচ্ছে (404 Error বাইপাস করতে)
        response = client_gemini.models.generate_content(
            model='gemini-2.0-flash',
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
            print("✅ Translation successful!", flush=True)
            return f"{response.text.strip()}\n\n📢 @VanguardalertBD"
        else:
            print("⚠️ AI Warning: Empty response from Gemini.", flush=True)
            # অনুবাদ না হলেও ক্লিন করা টেক্সট যাবে (সোর্স নাম থাকবে না)
            return f"{clean_text}\n\n📢 @VanguardalertBD"
            
    except Exception as e:
        print(f"❌ Gemini Error: {e}", flush=True)
        # এরর হলেও ক্লিন করা টেক্সট যাবে (সোর্স নাম থাকবে না)
        return f"{clean_text}\n\n📢 @VanguardalertBD"

async def main():
    client = TelegramClient(StringSession(SESSION_STRING), API_ID, API_HASH)
    await client.start()
    print("🚀 Vanguard Gemini is Running! (Model: Gemini 2.0 Flash)", flush=True)

    @client.on(events.NewMessage(chats=CHANNELS))
    async def handle_new(e):
        if not e.message.message: return
        print(f"📥 New message received from {e.chat_id}", flush=True)
        
        translated_msg = await ai_translate(e.message.message)
        
        try:
            sent_msg = await client.send_message(TARGET, translated_msg, file=e.message.media)
            cursor.execute("INSERT INTO mapping VALUES (?, ?)", (e.id, sent_msg.id))
            db.commit()
            print("📤 Successfully posted to Target Channel.", flush=True)
        except Exception as ex:
            print(f"Post Error: {ex}", flush=True)

    @client.on(events.MessageEdited(chats=CHANNELS))
    async def handle_edit(e):
        cursor.execute("SELECT target_id FROM mapping WHERE source_id = ?", (e.id,))
        result = cursor.fetchone()
        if result:
            new_text = await ai_translate(e.message.message)
            try:
                await client.edit_message(TARGET, result[0], text=new_text)
                print("📝 Edit synced successfully.", flush=True)
            except: pass
            
    await client.run_until_disconnected()

if __name__ == "__main__":
    asyncio.run(main())
