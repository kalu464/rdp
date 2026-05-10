from telethon import TelegramClient, events
from telethon.tl.functions.users import GetFullUserRequest
from telethon.tl.functions.photos import GetUserPhotosRequest
import asyncio
import os
import re

# API Details
API_ID = os.getenv("27595157")
API_HASH = os.getenv("080aeea5174851d44c3609844363bb25")

if not API_ID or not API_HASH:
    API_ID = 12345
    API_HASH = "dummy_hash"

# Session name rebranded to dev_power_session
client = TelegramClient('dev_power_session', int(API_ID), API_HASH)

# Global states
AUTOREACT = False
STOP_TASKS = False
LAST_MENU_MSG = None
RAID_TARGETS = {} # {chat_id: user_id}
SLIDEALL_CHATS = set() # {chat_id}

# Embedded Raid Text directly in the script
RAID_LINES = [
    "[ ]--- 𝙍𝘼𝙉𝘿𝘼𝙇 𝙆𝘼 𝘽𝘾𝘾𝘼 𝙃𝘼𝙄 ~ 🐣",
    "[ ]  चुद गया -!",
    "Aʟᴏᴏ Kʜᴀᴋᴇ [ ]  Kɪ Mᴀ Cʜᴏᴅ Dᴜɴɢᴀ!",
    "[ ]  Cʜᴜᴅᴀ🦖🪽",
    "[ ]  Bᴏʟᴇ ɴᴏʙɪ ᴘᴀᴘᴀ पिताश्री  Mᴇʀɪ Mᴀ Cʜᴏᴅ Dᴏ",
    "[ ]  Kɪ Mᴀ Bᴏʟᴇ ɴᴏʙɪ ᴘᴀᴘᴀ Sᴇ Cʜᴜᴅᴜɴɢɪ",
    "[ ]  Kɪ Bᴇʜɴ Kɪ Cʜᴜᴛ Kᴀʟɪ Kᴀʟɪ - Dᴇᴋʜᴋʀ Aʏᴇ Mᴜʜ Mᴇ Pᴀɴɪ",
    "[ ]  Kɪ Cʜᴀᴄʜɪ Kɪ Bᴜʀ Mᴇ Mᴀʀᴀ ɴᴏʙɪ ᴘᴀᴘᴀ Nᴇ Pᴀᴛʜᴀʀ",
    "[ ]  Bᴏʟᴇ ɴᴏʙɪ ᴘᴀᴘᴀ Pᴀᴘᴀ Mᴜᴊʜᴇ Mᴀᴀғ Kᴀʀᴅᴏ",
    "[ ]  Kɪ Mᴀ Kᴀʀᴇ Bʜᴀᴡ Bʜᴀᴡ",
    "Aʟᴏᴏ Kʜᴀᴋᴇ [ ]  Kɪ Mᴀ Cʜᴏᴅ Dᴜɴɢᴀ 🙊",
    "[ ]  मर गया",
    "[ ]  दफ़न",
    "[ ]  ᴋɪ ʙᴇʜɴ ᴄʜᴜᴅᴇ Tᴀʟɪʙᴀɴ ᴍᴇ",
    "[ ]  ᴋɪ ᴍᴀ Jᴀᴘᴀɴɪ",
    "[ ]  ᴋɪ ʙᴇʜɴ ᴋɪ ᴄʜᴜᴛ ᴋᴀʟɪ ᴋᴀʟɪ",
    "[ ]  ᴋɪ ʙᴜᴀ ʀᴀɴᴅɪ ʜᴀɪɪ ᴏᴋᴋᴋ",
    "[ ]  Cʜᴜᴅᴀ Usᴋɪ Mᴀ Cʜᴜᴅᴇ",
    "[ ]  Kɪ Mᴀᴀ Lᴀɴɢᴅɪ",
    "[ ]  Kᴀ ʙᴀᴀᴘ Bʜɪᴋʜᴀʀɪ",
    "[ ]  Kɪ Mᴀ Rᴀɴᴅɪ",
    "[ ]  ɢᴀʀᴇᴇʙ ᴋᴀ ʙᴀᴄʜʜᴀ",
    "[ ]  ᴋɪ ᴍᴀᴀ ᴄʜᴏᴅᴜ",
    "[ ]  ᴄʜᴀʟ ʙʜᴇᴇᴋʜ ᴍᴀɴɢ",
    "[ ]  ᴄʜᴜᴅ ᴋᴇ ᴘᴀɢᴀʟ ʜᴏɢᴀʏᴀ",
    "[ ]  ᴘᴀɢᴀʟ sᴀʟᴇ ʜᴀᴡᴀʙᴀᴢɪ ᴋᴀʀᴇɢᴀ",
    "[ ]  ᴋɪ ʙᴇʜɴ ᴄʜᴏᴅᴜ",
    "[ ]  ʟᴜɴᴅ ᴄʜᴜsᴇɢᴀ sᴀʙᴋᴀ",
    "[ ]  ʜᴇʟʟᴏ ᴍᴀʀɴᴀ ɴᴀʜɪ ʜᴀɪ ᴍᴀᴅʀᴄʜᴏᴅ!",
    "[ ]  ᴋɪ ʙᴇʜɴ ᴋɪ ᴄʜᴜᴛ ᴘᴇ ɴᴀɴɢᴀ ᴅᴀɴᴄᴇ ᴋᴀʀᴜ!",
    "[ ]  Kɪ ʙᴇʜɴ ᴄʜᴜᴅɪ!",
    "[ ]  ᴄʜᴜᴘ ᴄʜᴀᴘ ᴄʜᴜᴅ ɴᴏ sᴏᴜɴᴅ!",
    "[ ]  ᴋᴜᴛᴛɪʏᴀ ᴋʜɪᴋʜɪᴋʜɪ!",
    "[ ]  ʙʜᴀɢᴀ ᴋʏᴜ!",
    "[ ]  ɢᴜʟᴀᴍ ᴋɪ ɢᴀɴᴅ ғᴀᴛɪ!",
    "[ ]  ᴋɪ ᴍᴀ ᴋɪ ɢᴀɴᴅ ғᴀᴛɪ!",
    "[ ]  ᴋᴀ ʙᴀᴀᴘ ᴄʜᴜᴅᴀ!",
    "[ ]  ᴍᴄ ᴅᴀʀᴛᴀ ᴋʏᴜ ʜᴀɪ ɪᴛɴᴀ!",
    "[ ]  ʙᴇᴛᴇ ɢᴜᴅ ɴʏᴛ!",
    "[ ]  ᴋɪ ᴍᴏᴍ ᴋᴏ ɢᴜᴅ ᴍᴏʀɴɪɴɢ ʙᴏʟᴋʀ ᴄʜᴏᴅᴜ!",
    "[ ]  ᴋɪ ʙᴇʜɴ ʜᴜʟᴜʟᴜʟᴜʟᴜ!",
    "[ ]  ᴋɪ ʙᴀɴᴅɪ ʜɪᴊᴅɪ!",
    "[ ]  sᴀʟᴇ ᴀᴅɪᴠᴀsɪ ᴋᴇ ʟᴀᴅᴋᴇ!",
    "[ ]  sᴀʟᴇ ᴊᴜɴɢʟᴇ ᴍᴇ ᴄʜᴜᴅɴᴇ ᴡᴀʟᴇ ᴛᴍᴋᴄ!",
    "[ ]  ᴋɪ ᴍᴀ ɢᴜʟᴀʙᴊᴀᴍᴜɴ!",
    "[ ]  ᴋɪ ᴍᴀ sᴀʙ ᴄʜᴏᴅᴇɴɢᴇ!",
    "[ ]  ᴋɪ ᴄʜᴀᴄʜɪ ᴋʜᴀʟɪsᴛᴀɴɪ!",
    "[ ]  ᴋɪ ᴅᴀᴅɪ ᴄʜᴜᴅ ɢᴀʏɪ!",
    "[ ]  ᴄʜᴜᴅᴀɪ ᴘᴏʟɪᴄʏ ᴍᴇ sʜᴀᴍɪʟ ʜᴏɴɢᴇ sᴀʙ!",
    "[ ]  ʀᴏ ᴅɪʏᴀᴀᴀ!",
    "[ ]  ᴋɪ ᴍᴀ ᴍᴀʀ ɢʏɪ!",
    "[ ]  ᴋɪ ᴍᴀ ᴋᴇ ᴛᴇᴅʜᴇ ᴍᴇᴅʜᴇ ʙᴏᴏʙs!",
    "[ ]  ᴋɪ ʙᴜʀ ᴍᴇ ʟᴏᴅᴀ ɢʜᴜsᴀᴜɴɢᴀ!",
    "[ ]  ᴋᴀ ᴊɪᴊᴀ ɴᴏʙɪ ᴘᴀᴘᴀ ʜᴀɪ!",
    "[ ]  ᴄʜᴜᴅ ᴊᴀᴛᴀ ʜᴀɪ sᴀʙsᴇ!",
    "[ ]  ᴋɪ ᴄʜᴜᴅᴀɪ ᴅᴀʏ 1#!",
]

# Set of clean strings (no brackets) for matching
CLEAN_RAID_LINES = {line.replace("[ ]", "").replace("[target]", "").strip() for line in RAID_LINES}

MENU_TEXT = """
╭━━━━━━━━━━━━━━━━━━━━╮
│   ⚡ ɴᴏʙɪ ᴘᴏᴡᴇʀ ʙᴏᴛ ⚡
│   ᴀᴜʀᴀ ᴇᴅɪᴛɪᴏɴ 🎀
╰━━━━━━━━━━━━━━━━━━━━╯
📌 ɪɴᴛᴇʟ & ᴏsɪɴᴛ:
├ ✧ .info    ➲ sᴄᴀɴ ᴇɴᴛɪᴛʏ
├ ✧ .history ➲ ᴛʀᴀᴄᴇ ʟᴏɢs
└ ✧ .search  ➲ ᴅʙ ʟᴏᴏᴋᴜᴘ

🔥 ᴀᴛᴛᴀᴄᴋ ᴍᴏᴅᴇ:
├ ✧ .slide   ➲ ᴀᴜʀᴀ ʀᴀɪᴅ
├ ✧ .slideall➲ ɢʟᴏʙᴀʟ ʀᴀɪᴅ
├ ✧ .bomb    ➲ ғᴏʀᴄᴇ ʀᴀɪᴅ
├ ✧ .spam    ➲ ʀᴀᴘɪᴅ sᴘᴀᴍ
└ ✧ .ghost   ➲ ʀᴀɪᴅ ᴡɪᴘᴇ

⚡ ᴀᴜᴛᴏ-ᴍᴏᴅᴇ:
├ ✧ .autoreact ➲ ᴏɴ/ᴏғғ
└ ✧ .stop      ➲ ᴋɪʟʟ ᴀʟʟ

✨ ᴘᴏᴡᴇʀᴇᴅ ʙʏ ᴀᴜʀᴀ ~ ❤️‍🔥🫧
╰━━━━━━━━━━━━━━━━━━━━╯
"""

async def close_menu():
    global LAST_MENU_MSG
    if LAST_MENU_MSG:
        try:
            await LAST_MENU_MSG.delete()
        except: pass
        LAST_MENU_MSG = None

@client.on(events.NewMessage(pattern=r'^\.(help|menu)'))
async def help_menu(event):
    if event.out:
        global LAST_MENU_MSG
        if LAST_MENU_MSG and LAST_MENU_MSG.id == event.id:
            return
        await close_menu()
        LAST_MENU_MSG = await event.edit(f"<code>{MENU_TEXT}</code>", parse_mode='html')

@client.on(events.NewMessage)
async def auto_closer(event):
    if event.out and event.text and event.text.startswith('.') and not re.match(r'^\.(help|menu)', event.text):
        await close_menu()

@client.on(events.NewMessage(pattern=r'^\.info'))
async def info_cmd(event):
    if not event.out: return
    reply = await event.get_reply_message()
    user = await client.get_entity(reply.sender_id if reply else 'me')
    full = await client(GetFullUserRequest(user.id))
    photos = await client(GetUserPhotosRequest(user_id=user.id, offset=0, max_id=0, limit=0))
    dc_id = getattr(user.photo, 'dc_id', 'Unknown') if user.photo else 'N/A'
    status = "🟢 ʀᴇᴄᴇɴᴛʟʏ ᴀᴄᴛɪᴠᴇ"
    if hasattr(user.status, 'was_online'):
        status = "🔴 ᴏғғʟɪɴᴇ"
    elif hasattr(user.status, 'online'):
        status = "🟢 ᴏɴʟɪɴᴇ"
    info = f"╭━━━━━━━━━━━━━━━━━╮\n│  👤 ᴜsᴇʀ ɪɴғᴏʀᴍᴀᴛɪᴏɴ\n╰━━━━━━━━━━━━━━━━━╯\n\n"
    info += f"📌 ʙᴀsɪᴄ ᴅᴇᴛᴀɪʟs:\n├ 🆔 ɪᴅ: <code>{user.id}</code>\n├ 👨‍💻 ɴᴀᴍᴇ: {user.first_name} {user.last_name or ''}\n├ 🏷 ᴜsᴇʀɴᴀᴍᴇ: @{user.username or 'N/A'}\n└ 🔗 ᴍᴇɴᴛɪᴏɴ: <a href='tg://user?id={user.id}'>{user.first_name}</a>\n\n"
    info += f"🌐 ᴀᴄᴄᴏᴜɴᴛ ɪɴғᴏ:\n├ 📡 ᴅᴄ ɪᴅ: {dc_id}\n├ 💎 ᴘʀᴇᴍɪᴜᴍ: {'✅ ʏᴇs' if user.premium else '❌ ɴᴏ'}\n├ 🤖 ʙᴏᴛ: {'✅ ʏᴇs' if user.bot else '❌ ɴᴏ'}\n├ ✅ ᴠᴇʀɪғɪᴇᴅ: {'✅ ʏᴇs' if user.verified else '❌ ɴᴏ'}\n├ ⭐ ғᴀᴋᴇ: {'✅ ʏᴇs' if getattr(user, 'fake', False) else '❌ ɴᴏ'}\n└ 🚫 sᴄᴀᴍ: {'✅ ʏᴇs' if getattr(user, 'scam', False) else '❌ ɴᴏ'}\n\n"
    info += f"📊 ᴘʀᴏғɪʟᴇ sᴛᴀᴛs:\n├ 📸 ᴘʀᴏғɪʟᴇ ᴘʜᴏᴛᴏs: {photos.count}\n├ 💬 ʙɪᴏ: {full.full_user.about or 'N/A'}\n└ 👥 ᴍᴜᴛᴜᴀʟ ɢʀᴏᴜᴘs: ᴜɴᴀᴠᴀɪʟᴀʙʟᴇ\n\n"
    info += f"⏰ ᴛɪᴍᴇsᴛᴀᴍᴘs:\n├ 📅 ᴊᴏɪɴᴇᴅ ᴛᴇʟᴇɢʀᴀᴍ: ᴜɴᴀᴠᴀɪʟᴀʙʟᴇ\n└ 📶 ᴄᴜʀʀᴇɴᴛ sᴛᴀᴛᴜs: {status}\n╰━━━━━━━━━━━━━━━━━╯"
    await event.edit(info, parse_mode='html', link_preview=False)

@client.on(events.NewMessage(pattern=r'^\.slide(?:\s+(.+))?'))
async def slide_cmd(event):
    if not event.out: return
    global RAID_TARGETS
    reply = await event.get_reply_message()
    if not reply:
        await event.edit("❌ Reply to a message to target for auto-raid.")
        return
    RAID_TARGETS[event.chat_id] = reply.sender_id
    await event.edit(f"🔥 <b>Auto-Raid Target Locked.</b> Waiting for message...")
    await asyncio.sleep(2)
    await event.delete()

@client.on(events.NewMessage(pattern=r'^\.slideall'))
async def slideall_cmd(event):
    if not event.out: return
    global SLIDEALL_CHATS
    if event.chat_id in SLIDEALL_CHATS:
        SLIDEALL_CHATS.remove(event.chat_id)
        await event.edit("🔥 <b>Global Raid: Disabled.</b>")
    else:
        SLIDEALL_CHATS.add(event.chat_id)
        await event.edit("🔥 <b>Global Raid: Enabled.</b> Sliding every message.")
    await asyncio.sleep(2)
    await event.delete()

@client.on(events.NewMessage(pattern=r'^\.bomb(?:\s+(.+))?'))
async def bomb_cmd(event):
    if not event.out: return
    global STOP_TASKS
    STOP_TASKS = False
    target_name = event.pattern_match.group(1)
    reply = await event.get_reply_message()
    if not target_name and reply:
        user = await client.get_entity(reply.sender_id)
        target_name = user.first_name
    if not target_name:
        await event.edit("❌ Provide a target name or reply.")
        return
    await event.delete()
    for line in RAID_LINES:
        if STOP_TASKS: break
        msg = line.replace("[ ]", target_name).replace("[target]", target_name)
        if reply: await client.send_message(event.chat_id, msg, reply_to=reply.id)
        else: await client.send_message(event.chat_id, msg)
        await asyncio.sleep(0.3)

@client.on(events.NewMessage(pattern=r'^\.spam(?:\s+(.+))?'))
async def spam_cmd(event):
    if not event.out: return
    global STOP_TASKS
    STOP_TASKS = False
    text = event.pattern_match.group(1)
    if not text:
        await event.edit("❌ Usage: .spam {text}")
        return
    await event.delete()
    while not STOP_TASKS:
        try:
            await client.send_message(event.chat_id, text)
            await asyncio.sleep(0.1) # Rapid spam
        except Exception as e:
            print(f"Spam error: {e}")
            break

@client.on(events.NewMessage)
async def slide_handler(event):
    if event.out: return
    if event.chat_id in SLIDEALL_CHATS or (event.chat_id in RAID_TARGETS and event.sender_id == RAID_TARGETS[event.chat_id]):
        target_name = (await event.get_sender()).first_name
        for line in RAID_LINES:
            if STOP_TASKS: break
            msg = line.replace("[ ]", target_name).replace("[target]", target_name)
            await event.reply(msg)
            await asyncio.sleep(0.3)
        if event.chat_id in RAID_TARGETS and event.sender_id == RAID_TARGETS[event.chat_id]:
            del RAID_TARGETS[event.chat_id]

@client.on(events.NewMessage(pattern=r'^\.ghost'))
async def ghost_cmd(event):
    if not event.out: return
    try:
        # Scan last 100 messages from self and delete only those that match raid patterns
        async for msg in client.iter_messages(event.chat_id, limit=100, from_user='me'):
            if msg.text:
                # Check if message content (stripped of target name) matches any raid line
                # We do a basic check: if a significant portion of the msg text is in our raid list
                msg_content = msg.text
                is_raid = False
                for clean_line in CLEAN_RAID_LINES:
                    if clean_line and clean_line in msg_content:
                        is_raid = True
                        break
                if is_raid:
                    await msg.delete()
                    await asyncio.sleep(0.1)
        # Delete the trigger command itself if it still exists
        try: await event.delete()
        except: pass
    except Exception as e:
        print(f"Error in ghost_cmd: {e}")

@client.on(events.NewMessage(pattern=r'^\.autoreact (on|off)'))
async def autoreact_toggle(event):
    if not event.out: return
    global AUTOREACT
    state = event.pattern_match.group(1).lower()
    AUTOREACT = (state == 'on')
    await event.edit(f"⚡ <b>Aura React: {'Enabled' if AUTOREACT else 'Disabled'}</b>", parse_mode='html')

@client.on(events.NewMessage)
async def react_handler(event):
    if AUTOREACT and not event.out:
        try: await event.react('❤️‍🔥')
        except: pass

@client.on(events.NewMessage(pattern=r'^\.stop'))
async def stop_cmd(event):
    if not event.out: return
    global STOP_TASKS, RAID_TARGETS, SLIDEALL_CHATS
    STOP_TASKS = True
    RAID_TARGETS = {}
    SLIDEALL_CHATS.clear()
    await event.edit("🛑 <b>Protocols terminated. All tasks killed.</b>", parse_mode='html')

async def main():
    try:
        await client.start()
        print("⚡ 𝐃𝐄𝐕 𝐏𝐎𝐖𝐄𝐑 𝐁𝐎𝐓 ⚡ is online.")
        await client.run_until_disconnected()
    except Exception as e: print(f"Error: {e}")

if __name__ == "__main__":
    client.loop.run_until_complete(main())
