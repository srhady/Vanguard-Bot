import os, asyncio, re
from telethon import TelegramClient, events
from telethon.sessions import StringSession
from googletrans import Translator

# GitHub Secrets থেকে ডাটা নিচ্ছে
api_id = int(os.environ.get("API_ID"))
api_hash = os.environ.get("API_HASH")
session_string = os.environ.get("SESSION_STRING")

CHANNELS = ['FotrosResistancee', 'IntelRepublic', 'Middle_East_Spectator']
TARGET = '@VanguardalertBD'

translator = Translator()

# বিজ্ঞাপন এবং লিংক মোছার ফাংশন
async def clean_and_translate(text):
    if not text: return ""
    
    # ১. অদরকারি ইউজারনেম বা শব্দ মোছা
    bad_words = ['@Middle_East_Spectator', '@FotrosResistancee', '@IntelRepublic', 'Subscribe', 'Join us']
    for word in bad_words:
        text = text.replace(word, "")
    
    # ২. সব ধরনের টেলিগ্রাম লিংক (t.me/...) মুছে ফেলা
    text = re.sub(r'https?://t\.me/\S+', '', text).strip()
    
    # ৩. বাংলায় অনুবাদ করা
    try:
        translation = translator.translate(text, dest='bn')
        return f"{translation.text}\n\n📢 @VanguardalertBD"
    except:
        return f"{text}\n\n📢 @VanguardalertBD"

async def main():
    async with TelegramClient(StringSession(session_string), api_id, api_hash) as client:
        print("🛡 Vanguard Clean & Translate Bot is Live!")
        
        @client.on(events.NewMessage(chats=CHANNELS))
        async def h(e):
            if e.grouped_id: return
            new_text = await clean_and_translate(e.message.message)
            await client.send_message(TARGET, new_text, file=e.message.media)

        @client.on(events.Album(chats=CHANNELS))
        async def a(e):
            new_text = await clean_and_translate(e.text)
            await client.send_message(TARGET, file=e.messages, message=new_text)
            
        await client.run_until_disconnected()

asyncio.run(main())
