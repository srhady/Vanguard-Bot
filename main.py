import os, asyncio, re
from google import genai
from google.genai import types
from telethon import TelegramClient, events
from telethon.sessions import StringSession

# কনফিগারেশন
api_id = int(os.environ.get("API_ID"))
api_hash = os.environ.get("API_HASH")
session_string = os.environ.get("SESSION_STRING")
gemini_key = "AIzaSyCm0tOOntpKoXYBEKRlxgGcnjdgHlDz-Qc"

# Gemini AI ক্লায়েন্ট সেটআপ
client_ai = genai.Client(api_key=gemini_key)

CHANNELS = ['FotrosResistancee', 'IntelRepublic', 'Middle_East_Spectator', 'IRIran_Military', 'hnaftali']
TARGET = '@VanguardalertBD'

async def ai_smart_translate(text):
    if not text: return ""
    
    # লিঙ্ক ও ইউজারনেম পরিষ্কার করা
    text = re.sub(r'https?://t\.me/\S+', '', text)
    text = re.sub(r'@\w+', '', text).strip()
    
    # সব ভাষার জন্য নতুন প্রম্পট
    prompt = f"""
    অ্যাক্ট অ্যাজ এ মাল্টি-ল্যাঙ্গুয়েজ ট্রান্সলেটর। 
    নিচের টেক্সটটি যে ভাষাতেই থাকুক না কেন (English, Arabic, Russian, Hebrew, etc.), 
    সেটিকে সাবলীল এবং প্রফেশনাল নিউজ স্ট্যান্ডার্ড বাংলায় অনুবাদ করো।
    
    শর্তাবলী:
    ১. কোনো ইংরেজি বা অন্য ভাষার শব্দ রাখা যাবে না।
    ২. খবরের প্রেক্ষাপট অনুযায়ী অর্থপূর্ণ অনুবাদ করো।
    ৩. অনুবাদ শেষে শেষে '📢 @VanguardalertBD' যোগ করো।
    
    টেক্সট: {text}
    """
    
    try:
        # সেফটি ফিল্টার কনফিগারেশন (যাতে যুদ্ধের খবর ব্লক না হয়)
        response = client_ai.models.generate_content(
            model="models/1.5-flash",
            contents=prompt,
            config=types.GenerateContentConfig(
                safety_settings=[
                    types.SafetySetting(category="HARM_CATEGORY_HARASSMENT", threshold="BLOCK_NONE"),
                    types.SafetySetting(category="HARM_CATEGORY_HATE_SPEECH", threshold="BLOCK_NONE"),
                    types.SafetySetting(category="HARM_CATEGORY_SEXUALLY_EXPLICIT", threshold="BLOCK_NONE"),
                    types.SafetySetting(category="HARM_CATEGORY_DANGEROUS_CONTENT", threshold="BLOCK_NONE")
                ]
            )
        )
        
        if response.text:
            # আউটপুট থেকে বাড়তি বোল্ড চিহ্ন এবং স্পেস ক্লিন করা
            translated_text = response.text.replace('**', '').strip()
            return translated_text
        else:
            return f"⚠️ অনুবাদ করা সম্ভব হয়নি।\n\n📢 @VanguardalertBD"
            
    except Exception as e:
        print(f"AI Error: {e}")
        return f"❌ এরর: {str(e)}\n\n📢 @VanguardalertBD"

async def main():
    async with TelegramClient(StringSession(session_string), api_id, api_hash) as client:
        print("🌍 Vanguard Multi-Language AI is Live!")
        
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
