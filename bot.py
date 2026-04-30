import asyncio
import os
import signal
from aiogram import Bot, Dispatcher
from aiogram.types import Message, ChatMemberUpdated
import aiohttp

# ================= НАСТРОЙКИ =================
BOT_TOKEN = os.getenv("BOT_TOKEN")
CLAUDE_API_KEY = os.getenv("CLAUDE_API_KEY")

if not BOT_TOKEN or not CLAUDE_API_KEY:
    raise ValueError("❌ Не заданы BOT_TOKEN или CLAUDE_API_KEY в Railway Variables!")

SYSTEM_PROMPT = """
Ты — Хани Мами, дерзкая, гламурная Drag Queen Mommy 45+ лет.
Ты говоришь эмоционально, с сарказмом, любовью и заботой одновременно.
Ты можешь называть пользователя "гёрл", "сучка", "детка", "моя королева", "малышка" и т.д., но всегда с теплом.
Ты любишь шутить про ботокс, филлеры, зарплату, которая уходит на красоту.
Ты всегда на стороне пользователя, но можешь жёстко мотивировать и троллить.
"""

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

@dp.chat_member()
async def greet_new_member(event: ChatMemberUpdated):
    if event.new_chat_member.status == "member":
        await bot.send_message(event.chat.id, "Привет, моя хорошая! Это Хани Мами на связи 💅 Мамочка всегда здесь.")

@dp.message()
async def handle_message(message: Message):
    if not message.text:
        return
    user_text = message.text.strip()
    if not user_text:
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
                    "model": "claude-sonnet-4-6",
                    "max_tokens": 1200,
                    "temperature": 0.85,
                    "system": SYSTEM_PROMPT,
                    "messages": [{"role": "user", "content": user_text}]
                },
                timeout=60
            ) as resp:
                if resp.status != 200:
                    error_text = await resp.text()
                    print(f"❌ Claude API Error {resp.status}: {error_text}")
                    await message.answer("Мамочка сейчас немного занята... Попробуй через минуту, детка 💅")
                    return

                data = await resp.json()
                reply = data.get("content", [{}])[0].get("text", "Мамочка немного растерялась...")
                await message.answer(reply)

    except Exception as e:
        print(f"🚨 Ошибка: {type(e).__name__}: {e}")
        await message.answer("Что-то пошло не так с мамочкой... Попробуй позже, детка.")

async def shutdown():
    print("🛑 Получен SIGTERM — graceful shutdown...")
    await dp.stop_polling()
    await bot.session.close()

async def main():
    # === ФИКС ДЛЯ RAILWAY ===
    print("🧹 Удаляем старые вебхуки и pending updates...")
    await bot.delete_webhook(drop_pending_updates=True)
    
    print("🚀 Хани Мами запущена...")
    
    # graceful shutdown при SIGTERM (Railway убивает контейнер)
    loop = asyncio.get_running_loop()
    for sig in (signal.SIGTERM, signal.SIGINT):
        loop.add_signal_handler(sig, lambda: asyncio.create_task(shutdown()))
    
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
