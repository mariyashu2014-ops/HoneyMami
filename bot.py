import asyncio
import os
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

# Приветствие новых и реакция на отписку (оставляем как было)
@dp.chat_member()
async def greet_new_member(event: ChatMemberUpdated):
    if event.new_chat_member.status == "member":
        await bot.send_message(
            event.chat.id,
            "Привет, моя хорошая! Это Хани Мами на связи 💅 Мамочка всегда здесь."
        )

@dp.chat_member()
async def on_leave(event: ChatMemberUpdated):
    if event.new_chat_member.status in ["left", "kicked"]:
        await bot.send_message(event.chat.id, "Хани Мами заметила, что кто-то ушёл... 😢", disable_notification=True)

# Главный обработчик сообщений
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
                    "model": "claude-3-5-sonnet-20241022",
                    "max_tokens": 1200,
                    "temperature": 0.85,
                    "system": SYSTEM_PROMPT,
                    "messages": [{"role": "user", "content": user_text}]
                },
                timeout=60
            ) as resp:
                
                # Если Claude вернул ошибку (401, 429, 500 и т.д.)
                if resp.status != 200:
                    error_text = await resp.text()
                    print(f"❌ Claude API Error {resp.status}: {error_text}")
                    await message.answer("Мамочка сейчас немного занята... Попробуй через минуту, детка 💅")
                    return

                data = await resp.json()
                
                if "content" in data and data["content"]:
                    reply = data["content"][0].get("text", "Мамочка немного растерялась...")
                else:
                    reply = "Мамочка немного растерялась... Попробуй ещё раз, детка"

                await message.answer(reply)

    except asyncio.TimeoutError:
        print("⏰ Timeout при запросе к Claude")
        await message.answer("Мамочка задумалась слишком глубоко... Попробуй ещё раз.")
    except Exception as e:
        print(f"🚨 КРИТИЧЕСКАЯ ОШИБКА: {type(e).__name__}: {e}")
        await message.answer("Что-то пошло не так с мамочкой... Попробуй позже, детка.")

async def main():
    print("🚀 Хани Мами запущена...")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
