import os, asyncio, re, requests
from telethon import TelegramClient, events
from telethon.sessions import StringSession

# আপনার ডাটা (GitHub Secrets থেকে আসবে)
api_id = int(os.environ.get("API_ID"))
api_hash = os.environ.get("API_HASH")
session_string = os.environ.get("SESSION_STRING")

CHANNELS = ['FotrosResistancee', 'IntelRepublic', 'Middle_East_Spectator', 'IRIran_Military', 'hnaftali']
TARGET = '@VanguardalertBD'

# Hugging Face API URL (যেকোনো ভাষা থেকে বাংলা করার জন্য)
API_URL = "https://api-inference.huggingface.co/models/facebook/mbart-large-50-many-to-many-mmt"

async def ai_translate(text):
    if not text: return ""
    
    # অপ্রয়োজনীয় লিঙ্ক পরিষ্কার করা
    text = re.sub(r'https?://t\.me/\S+', '', text).strip()
    
    # এপিআই-তে পাঠানোর ডাটা (উৎস ভাষা নিজে থেকে চিনে নেবে)
    payload = {
        "inputs": text,
        "parameters": {"src_lang": "en_XX", "tgt_lang": "bn_IN"} 
    }
    
    try:
        # হগিং ফেস সার্ভারে রিকোয়েস্ট পাঠানো
        response = requests.post(API_URL, json=payload, timeout=15)
        result = response.json()
        
        # যদি মডেল লোড হতে সময় নেয় তবে ওয়েট করা
        if isinstance(result, dict) and "estimated_time" in result:
            await asyncio.sleep(result["estimated_time"])
            response = requests.post(API_URL, json=payload, timeout=15)
            result = response.json()

        translated_text = result[0]['translation_text']
        return f"{translated_text}\n\n📢 @VanguardalertBD"
        
    except Exception as e:
        print(f"Translation Error: {e}")
        # যদি এআই ফেল করে তবে অরিজিনাল টেক্সট পাঠানো
        return f"{text}\n\n📢 @VanguardalertBD"

async def main():
    async with TelegramClient(StringSession(session_string), api_id, api_hash) as client:
        print("✅ Vanguard AI (Hugging Face) is Running...")
        
        @client.on(events.NewMessage(chats=CHANNELS))
        async def handle_msg(e):
            if e.grouped_id or not e.message.message: return
            new_text = await ai_translate(e.message.message)
            await client.send_message(TARGET, new_text, file=e.message.media)

        @client.on(events.Album(chats=CHANNELS))
        async def handle_album(e):
            new_text = await ai_translate(e.text)
            await client.send_message(TARGET, file=e.messages, message=new_text)
            
        await client.run_until_disconnected()

asyncio.run(main())
