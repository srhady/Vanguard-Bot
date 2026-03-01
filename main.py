import os, asyncio, re
from google import genai
from telethon import TelegramClient, events
from telethon.sessions import StringSession

# কনফিগারেশন
api_id = int(os.environ.get("API_ID"))
api_hash = os.environ.get("API_HASH")
session_string = os.environ.get("SESSION_STRING")
gemini_key = "AIzaSyCm0tOOntpKoXYBEKRlxgGcnjdgHlDz-Qc"

# নতুন Gemini AI ক্লায়েন্ট সেটআপ
client_ai = genai.Client(api_key=gemini_key)

CHANNELS = ['FotrosResistancee', 'IntelRepublic', 'Middle_East_Spectator', 'IRIran_Military', 'hnaftali']
TARGET = '@VanguardalertBD'

async def ai_smart_translate(text):
    if not text: return ""
    
    # লিঙ্ক ও ইউজারনেম পরিষ্কার করা
    text = re.sub(r'https?://t\.me/\S+', '', text)
    text = re.sub(r'@\w+', '', text).strip()
    
    prompt = f"""
    Act as a professional news editor. Translate the following news into high-quality, 
    natural-sounding Bengali.
    Rules: 1. No robotic translation. 2. Use standard media Bengali. 3. Serious tone.
    News: {text}
    """
    
    try:
        # লেটেস্ট লাইব্রেরি মেথড
        response = client_ai.models.generate_content(
            model="gemini-1.5-flash",
            contents=prompt
        )
        translated_text = response.text.replace('**', '').strip() 
        return f"{translated_text}\n\n📢 @VanguardalertBD"
    except Exception as e:
        print(f"AI Error: {e}")
        return f"{text}\n\n📢 @VanguardalertBD"

async def main():
    async with TelegramClient(StringSession(session_string), api_id, api_hash) as client:
        print("🚀 Vanguard (Latest GenAI) is Running!")
        
        @client.on(events.NewMessage(chats=CHANNELS))
        async def handle_new_message(e):
            if e.grouped_id or not e.message.message: return
            translated = await ai_smart_translate(e.message.message)
            await client.send_message(TARGET, translated, file=e.message.media)

        @client.on(events.Album(chats=CHANNELS))
        async def handle_album(e):
            translated = await ai_smart_translate(e.text)
            await client.send_message(TARGET, file=e.messages, message=translated)
            
        await client.run_until_disconnected()

asyncio.run(main())
