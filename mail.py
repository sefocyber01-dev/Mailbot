import asyncio
import aiohttp
from aiogram import Dispatcher
from aiogram.client.bot import Bot
from aiogram.client.default import DefaultBotProperties
from aiogram.filters import Command
from aiogram.types import Message

# === TELEGRAM TOKEN ===
BOT_TOKEN = "8567370465:AAHMLslV5JjWgxUP373p8ksBc7bQjpCw2hM"

# === BOT OLUŞTURMA (AIROGRAM 3.7+ UYUMLU) ===
bot = Bot(
    token=BOT_TOKEN,
    default=DefaultBotProperties(parse_mode="HTML")
)

dp = Dispatcher()

users = {}

API = "https://www.1secmail.com/api/v1/"

async def api(params):
    async with aiohttp.ClientSession() as session:
        async with session.get(API, params=params) as resp:
            return await resp.json()

async def gen_mail():
    mail = (await api({"action": "genRandomMailbox", "count": 1}))[0]
    login, domain = mail.split("@")
    return login, domain, mail

async def inbox(login, domain):
    return await api({
        "action": "getMessages",
        "login": login,
        "domain": domain
    })

async def read_msg(login, domain, mid):
    return await api({
        "action": "readMessage",
        "login": login,
        "domain": domain,
        "id": mid
    })

async def watcher():
    while True:
        await asyncio.sleep(20)
        for uid, u in list(users.items()):
            msgs = await inbox(u["login"], u["domain"])
            for m in msgs:
                if m["id"] not in u["seen"]:
                    u["seen"].add(m["id"])
                    full = await read_msg(u["login"], u["domain"], m["id"])
                    body = full.get("textBody") or "Boş içerik"

                    await bot.send_message(
                        uid,
                        f"📨 <b>Yeni Mail</b>\n\n"
                        f"<b>From:</b> {full['from']}\n"
                        f"<b>Subject:</b> {full['subject']}\n\n"
                        f"{body[:3500]}"
                    )

@dp.message(Command("start"))
async def start(m: Message):
    login, domain, mail = await gen_mail()
    users[m.from_user.id] = {
        "login": login,
        "domain": domain,
        "seen": set()
    }

    await m.answer(
        f"✅ <b>Geçici Mail</b>\n\n"
        f"<code>{mail}</code>\n\n"
        f"/new → yeni adres"
    )

@dp.message(Command("new"))
async def new(m: Message):
    login, domain, mail = await gen_mail()
    users[m.from_user.id] = {
        "login": login,
        "domain": domain,
        "seen": set()
    }
    await m.answer(f"🆕 <code>{mail}</code>")

async def main():
    asyncio.create_task(watcher())
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
