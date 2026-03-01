import os, asyncio, re
from googletrans import Translator
from telethon import TelegramClient, events
from telethon.sessions import StringSession

# কনফিগারেশন
api_id = int(os.environ.get("API_ID"))
api_hash = os.environ.get("API_HASH")
session_string = os.environ.get("SESSION_STRING")

# ৫টি সোর্স চ্যানেল এবং টার্গেট চ্যানেল
CHANNELS = ['FotrosResistancee', 'IntelRepublic', 'Middle_East_Spectator', 'IRIran_Military', 'hnaftali']
TARGET = '@VanguardalertBD'

# লেটেস্ট ট্রান্সলেটর অবজেক্ট
translator = Translator()

async def clean_and_translate(text):
    if not text: return ""
    
    # লিঙ্ক এবং সব চ্যানেলের @ইউজারনেম মুছে ফেলা
    text = re.sub(r'https?://\S+', '', text)
    text = re.sub(r'@\w+', '', text)
    text = text.strip()
    
    if not text: return "" 
    
    try:
        # যেকোনো ভাষা থেকে অটোমেটিক শনাক্ত করে বাংলায় অনুবাদ
        translated = translator.translate(text, dest='bn')
        return f"{translated.text}\n\n📢 @VanguardalertBD"
    except Exception as e:
        print(f"Translation Error: {e}")
        return f"{text}\n\n📢 @VanguardalertBD"

async def main():
    async with TelegramClient(StringSession(session_string), api_id, api_hash) as client:
        print("🚀 Vanguard Bot (Latest Google Engine) is Active!")
        
        @client.on(events.NewMessage(chats=CHANNELS))
        async def handle_msg(e):
            if e.grouped_id or not e.message.message: return
            new_text = await clean_and_translate(e.message.message)
            await client.send_message(TARGET, new_text, file=e.message.media)

        @client.on(events.Album(chats=CHANNELS))
        async def handle_album(e):
            new_text = await clean_and_translate(e.text)
            await client.send_message(TARGET, file=e.messages, message=new_text)
            
        await client.run_until_disconnected()

asyncio.run(main())
