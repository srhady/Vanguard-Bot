import os, asyncio, re
import google.generativeai as genai
from telethon import TelegramClient, events
from telethon.sessions import StringSession

# কনফিগারেশন
api_id = int(os.environ.get("API_ID"))
api_hash = os.environ.get("API_HASH")
session_string = os.environ.get("SESSION_STRING")
gemini_key = "AIzaSyCm0tOOntpKoXYBEKRlxgGcnjdgHlDz-Qc" # আপনার প্রোভাইড করা কি

# Gemini AI সেটআপ
genai.configure(api_key=gemini_key)
model = genai.GenerativeModel('gemini-1.5-flash')

CHANNELS = ['FotrosResistancee', 'IntelRepublic', 'Middle_East_Spectator', 'IRIran_Military', 'hnaftali']
TARGET = '@VanguardalertBD'

async def ai_smart_translate(text):
    if not text: return ""
    
    # অপ্রয়োজনীয় লিঙ্ক ও ইউজারনেম পরিষ্কার করা
    text = re.sub(r'https?://t\.me/\S+', '', text)
    text = re.sub(r'@\w+', '', text).strip()
    
    # AI-কে ইনস্ট্রাকশন দেওয়া (যাতে সে অদ্ভুত অনুবাদ না করে)
    prompt = f"""
    Act as a professional news editor. Translate the following international news into high-quality, 
    natural-sounding Bengali. 
    Rules:
    1. Don't use literal/robotic translation.
    2. Use standard media Bengali (Suddho Bhasha).
    3. Keep the tone serious and informative.
    4. If there's a location or technical term, use its common Bengali equivalent.

    News Text: {text}
    """
    
    try:
        response = model.generate_content(prompt)
        # আউটপুট থেকে বাড়তি টেক্সট বা বোল্ড সাইন থাকলে ঠিক করা
        translated_text = response.text.replace('**', '').strip() 
        return f"{translated_text}\n\n📢 @VanguardalertBD"
    except Exception as e:
        print(f"AI Error: {e}")
        # AI ফেইল করলে যেন অন্তত অরিজিনাল টেক্সট যায় (নিরাপত্তার জন্য)
        return f"{text}\n\n📢 @VanguardalertBD"

async def main():
    async with TelegramClient(StringSession(session_string), api_id, api_hash) as client:
        print("🚀 Vanguard AI-Powered Bot is Running!")
        
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
