import os, asyncio
from telethon import TelegramClient, events
from telethon.sessions import StringSession # এই লাইনটি নিশ্চিত করুন

api_id = int(os.environ.get("API_ID"))
api_hash = os.environ.get("API_HASH")
session_string = os.environ.get("SESSION_STRING")

CHANNELS = ['FotrosResistancee', 'IntelRepublic', 'Middle_East_Spectator']
TARGET = '@VanguardalertBD'

async def main():
    # এখানে সেশন স্ট্রিং ব্যবহার করে ক্লায়েন্ট শুরু হচ্ছে
    async with TelegramClient(StringSession(session_string), api_id, api_hash) as client:
        print("🛡 Vanguard Bot is successfully running on GitHub!")
        @client.on(events.NewMessage(chats=CHANNELS))
        async def h(e):
            if not e.grouped_id: await client.send_message(TARGET, e.message)
        @client.on(events.Album(chats=CHANNELS))
        async def a(e):
            await client.send_message(TARGET, file=e.messages, message=e.text)
        await client.run_until_disconnected()

if __name__ == '__main__':
    asyncio.run(main())
