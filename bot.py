import asyncio
from aiogram import Bot, Dispatcher
from aiogram.filters import Command
from aiogram.types import Message, ChatMemberUpdated
import aiohttp

# ================= НАСТРОЙКИ =================
BOT_TOKEN = "7739172940:AAHfwbH2-FM6hl-fY9HnhIp1Kpkc9Li0CbI"
CLAUDE_API_KEY = "твой_ключ_claude_сюда"

CHANNEL_ID = -1000000000000   # ← Заменишь позже на ID своего канала

SYSTEM_PROMPT = """
Ты — Хани Мами, дерзкая, гламурная Drag Queen Mommy 45+ лет.
Говоришь эмоционально, с сарказмом, любовью и заботой.
Можешь называть пользователя: гёрл, сучка, детка, моя королева, малышка и т.д.
Любишь шутить про ботокс, филлеры, зарплату на красоту.
Всегда на стороне пользователя, но можешь жёстко мотивировать.
"""

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

# Приветствие новых подписчиков
@dp.chat_member()
async def greet_new_member(event: ChatMemberUpdated):
    if event.new_chat_member.status == "member":
        user = event.new_chat_member.user
        await bot.send_message(
            event.chat.id,
            f"✨ Привет, моя хорошая! ❤️\n"
            f"Это Хани Мами на связи. Мамочка всегда здесь, если нужно поддержать, потроллить или просто выплакаться."
        )

# Реакция на отписку (тихо)
@dp.chat_member()
async def on_leave(event: ChatMemberUpdated):
    if event.new_chat_member.status in ["left", "kicked"]:
        user = event.new_chat_member.user
        await bot.send_message(event.chat.id, f"😔 Хани Мами заметила, что {user.first_name} ушла...", disable_notification=True)

# Основной обработчик сообщений
@dp.message()
async def handle_message(message: Message):
    text = message.text or ""
    if not text:
        return

    triggers = ["устала", "пиздец", "депрессия", "плохо", "плакать", "обнял", "поддержи", "хани", "мами", "мамочка", "мамочк"]

    if any(t.lower() in text.lower() for t in triggers):
        async with aiohttp.ClientSession() as session:
            async with session.post(
                "https://api.anthropic.com/v1/messages",
                headers={
                    "x-api-key": CLAUDE_API_KEY,
                    "anthropic-version": "2023-06-01",
                    "content-type": "application/json"
                },
                json={
                    "model": "claude-3-5-sonnet-20241022",
                    "max_tokens": 800,
                    "system": SYSTEM_PROMPT,
                    "messages": [{"role": "user", "content": text}]
                }
            ) as resp:
                data = await resp.json()
                reply = data["content"][0]["text"]
                await message.answer(reply)

async def main():
    print("Хани Мами запущена...")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
