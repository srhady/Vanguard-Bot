import os, asyncio, re
import google.generativeai as genai
from telethon import TelegramClient, events
from telethon.sessions import StringSession

# কনফিগারেশন
api_id = int(os.environ.get("API_ID"))
api_hash = os.environ.get("API_HASH")
session_string = os.environ.get("SESSION_STRING")
gemini_key = "AIzaSyCm0tOOntpKoXYBEKRlxgGcnjdgHlDz-Qc"

# Gemini AI সেটআপ
genai.configure(api_key=gemini_key)
model = genai.GenerativeModel('gemini-1.5-flash')

CHANNELS = ['FotrosResistancee', 'IntelRepublic', 'Middle_East_Spectator', 'IRIran_Military', 'hnaftali']
TARGET = '@VanguardalertBD'

async def ai_smart_translate(text):
    if not text: return ""
    
    # লিঙ্ক ও ইউজারনেম পরিষ্কার করা
    text = re.sub(r'https?://t\.me/\S+', '', text)
    text = re.sub(r'@\w+', '', text).strip()
    
    # মাল্টি-ল্যাঙ্গুয়েজ প্রম্পট
    prompt = f"Translate the following news into professional Bengali from any language. Keep the meaning exact. News: {text}"
    
    try:
        # জেনারেশন কনফিগ
        response = model.generate_content(
            prompt,
            safety_settings={
                "HARM_CATEGORY_HARASSMENT": "BLOCK_NONE",
                "HARM_CATEGORY_HATE_SPEECH": "BLOCK_NONE",
                "HARM_CATEGORY_SEXUALLY_EXPLICIT": "BLOCK_NONE",
                "HARM_CATEGORY_DANGEROUS_CONTENT": "BLOCK_NONE",
            }
        )
        
        if response.text:
            translated_text = response.text.replace('**', '').strip()
            return f"{translated_text}\n\n📢 @VanguardalertBD"
        else:
            return f"{text}\n\n📢 @VanguardalertBD"
            
    except Exception as e:
        print(f"AI Error: {e}")
        return f"{text}\n\n📢 @VanguardalertBD"

async def main():
    async with TelegramClient(StringSession(session_string), api_id, api_hash) as client:
        print("🚀 Vanguard AI is back to basics & working!")
        
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
