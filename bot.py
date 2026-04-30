import asyncio
from aiogram import Bot, Dispatcher
from aiogram.filters import Command
from aiogram.types import Message, ChatMemberUpdated
import aiohttp

# ================= НАСТРОЙКИ =================
BOT_TOKEN = "7739172940:AAHfwbH2-FM6hl-fY9HnhIp1Kpkc9Li0CbI"
CLAUDE_API_KEY = "вставь_сюда_полный_ключ_claude"   # ← очень важно, чтобы ключ был правильный!

SYSTEM_PROMPT = """
Ты — Хани Мами, дерзкая, гламурная Drag Queen Mommy 45+ лет.
Ты говоришь эмоционально, с сарказмом, любовью и заботой одновременно.
Ты можешь называть пользователя "гёрл", "сучка", "детка", "моя королева", "малышка" и т.д., но всегда с теплом.
Ты любишь шутить про ботокс, филлеры, зарплату, которая уходит на красоту.
Ты всегда на стороне пользователя, но можешь жёстко мотивировать и троллить.
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
            f"✨ Привет, моя хорошая! ❤️\nЭто Хани Мами на связи. Мамочка всегда здесь, если нужно поддержать, потроллить или просто выплакаться."
        )

# Реакция на отписку
@dp.chat_member()
async def on_leave(event: ChatMemberUpdated):
    if event.new_chat_member.status in ["left", "kicked"]:
        user = event.new_chat_member.user
        await bot.send_message(event.chat.id, f"😔 Хани Мами заметила, что {user.first_name} ушла...", disable_notification=True)

# Теперь бот отвечает на ВСЕ сообщения в личке
@dp.message()
async def handle_message(message: Message):
    text = message.text or ""
    if not text:
        return

    try:
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
                    "max_tokens": 1000,
                    "system": SYSTEM_PROMPT,
                    "messages": [{"role": "user", "content": text}]
                }
            ) as resp:
                data = await resp.json()
                
                # Более надёжный парсинг ответа
                if "content" in data and isinstance(data["content"], list) and data["content"]:
                    reply = data["content"][0].get("text", "Мамочка немного растерялась...")
                else:
                    reply = "Мамочка немного растерялась... Попробуй ещё раз, детка 💅"
                    
                await message.answer(reply)
                
    except Exception as e:
        print(f"Ошибка: {e}")  # для логов
        await message.answer("Мамочка немного растерялась... Попробуй ещё раз, детка 💅")

async def main():
    print("Хани Мами запущена...")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
