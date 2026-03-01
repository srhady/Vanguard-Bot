import os, asyncio, re, sqlite3
from groq import Groq
from telethon import TelegramClient, events
from telethon.sessions import StringSession

# কনফিগারেশন
api_id = int(os.environ.get("API_ID"))
api_hash = os.environ.get("API_HASH")
session_string = os.environ.get("SESSION_STRING")

# আপনার দেওয়া Groq API Key
GROQ_API_KEY = "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"

client_ai = Groq(api_key=GROQ_API_KEY)

# ডাটাবেস (Auto-Edit এর জন্য)
db = sqlite3.connect("vanguard_groq.db")
cursor = db.cursor()
cursor.execute("CREATE TABLE IF NOT EXISTS mapping (source_id INTEGER, target_id INTEGER)")
db.commit()

CHANNELS = ['FotrosResistancee', 'IntelRepublic', 'Middle_East_Spectator', 'IRIran_Military', 'hnaftali']
TARGET = '@VanguardalertBD'

async def ai_translate(text):
    if not text: return ""
    # লিঙ্ক ও ইউজারনেম পরিষ্কার করা
    text = re.sub(r'https?://\S+', '', text)
    text = re.sub(r'@\w+', '', text).strip()
    if not text: return ""

    try:
        # Llama 3.3-70b মডেল (খুবই শক্তিশালী এবং ফাস্ট)
        completion = client_ai.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {"role": "system", "content": "You are a professional news translator. Translate the text to Bengali naturally. Use formal news language. Only provide the translated text."},
                {"role": "user", "content": text}
            ]
        )
        translated_text = completion.choices[0].message.content.strip()
        return f"{translated_text}\n\n📢 @VanguardalertBD"
    except Exception as e:
        print(f"Groq Error: {e}")
        return f"{text}\n\n📢 @VanguardalertBD"

async def main():
    async with TelegramClient(StringSession(session_string), api_id, api_hash) as client:
        print("🚀 Vanguard Groq AI is Running!")

        @client.on(events.NewMessage(chats=CHANNELS))
        async def handle_new(e):
            if e.grouped_id or not e.message.message: return
            new_text = await ai_translate(e.message.message)
            sent_msg = await client.send_message(TARGET, new_text, file=e.message.media)
            cursor.execute("INSERT INTO mapping VALUES (?, ?)", (e.id, sent_msg.id))
            db.commit()

        @client.on(events.MessageEdited(chats=CHANNELS))
        async def handle_edit(e):
            cursor.execute("SELECT target_id FROM mapping WHERE source_id = ?", (e.id,))
            result = cursor.fetchone()
            if result:
                target_msg_id = result[0]
                new_text = await ai_translate(e.message.message)
                try:
                    await client.edit_message(TARGET, target_msg_id, text=new_text)
                except: pass
            
        await client.run_until_disconnected()

asyncio.run(main())
