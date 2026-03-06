import os
import asyncio
import re
import sqlite3
from openai import AsyncOpenAI
from telethon import TelegramClient, events
from telethon.sessions import StringSession

# --- Secrets ---
API_ID = int(os.environ.get("API_ID"))
API_HASH = os.environ.get("API_HASH")
SESSION_STRING = os.environ.get("SESSION_STRING")
OPENROUTER_API_KEY = os.environ.get("OPENROUTER_API_KEY")

# OpenRouter (Free AI) ক্লায়েন্ট সেটআপ
client_ai = AsyncOpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=OPENROUTER_API_KEY,
)

# ডাটাবেস
db = sqlite3.connect("vanguard_ai.db")
cursor = db.cursor()
cursor.execute("CREATE TABLE IF NOT EXISTS mapping (source_id INTEGER, target_id INTEGER)")
db.commit()

CHANNELS = ['FotrosResistancee', 'IntelRepublic', 'Middle_East_Spectator', 'IRIran_Military', 'hnaftali']
TARGET = '@VanguardalertBD'

async def ai_translate(text):
    if not text: return ""
    
    # --- টেক্সট ক্লিনআপ ---
    clean_text = text
    clean_text = re.sub(r'(https?://)?t\.me/\S+', '', clean_text, flags=re.IGNORECASE)
    clean_text = re.sub(r'https?://\S+', '', clean_text)
    clean_text = re.sub(r'@\w+', '', clean_text).strip()
    
    if len(clean_text) < 5: 
        return f"{clean_text}\n\n📢 @VanguardalertBD"

    try:
        # OpenRouter এর সম্পূর্ণ ফ্রি Llama 3 মডেল
        response = await client_ai.chat.completions.create(
            model="meta-llama/llama-3-8b-instruct:free",
            messages=[
                {
                    "role": "system", 
                    "content": "You are a professional Bengali news editor. Translate the following English news into natural, sophisticated journalistic Bengali. Output ONLY the translated Bengali text. Do not add any extra comments, intros, or english words."
                },
                {
                    "role": "user", 
                    "content": clean_text
                }
            ],
            temperature=0.3,
        )
        
        translated_text = response.choices[0].message.content.strip()
        
        if translated_text:
            print("✅ Free AI Translation successful!", flush=True)
            return f"{translated_text}\n\n📢 @VanguardalertBD"
        else:
            print("⚠️ AI Warning: Empty response.", flush=True)
            return f"{clean_text}\n\n📢 @VanguardalertBD"
            
    except Exception as e:
        print(f"❌ AI Error: {e}", flush=True)
        return f"{clean_text}\n\n📢 @VanguardalertBD"

async def main():
    client = TelegramClient(StringSession(SESSION_STRING), API_ID, API_HASH)
    await client.start()
    print("🚀 Vanguard Bot is Running! (AI: OpenRouter Llama 3 Free)", flush=True)

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
