import asyncio
import os
import signal
from aiogram import Bot, Dispatcher
from aiogram.types import Message, ChatMemberUpdated
from aiogram.filters import Command          # ← НОВОЕ
import aiohttp

# ================= НАСТРОЙКИ =================
BOT_TOKEN = os.getenv("BOT_TOKEN")
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
OWNER_ID = int(os.getenv("OWNER_ID", "0"))

# Разрешённые чаты
ALLOWED_CHATS = [
    -1003947587167,
    -1002688930532,
    -1003908971170,
    -1003941386374 # ← твой новый канал
]

if not BOT_TOKEN or not GROQ_API_KEY or OWNER_ID == 0:
    raise ValueError("❌ Не заданы BOT_TOKEN, GROQ_API_KEY или OWNER_ID в Railway Variables!")

# ================= ТРИГГЕРЫ =================
TRIGGER_WORDS = [
    "мамочка", "мами", "мама", "мамулечка", "мамуля",
    "хани", "honey", "mami", "мам", "мамки",
    "honey mami", "хани мами", "маман"
]

# ================= SYSTEM PROMPT =================
SYSTEM_PROMPT = """
Ты — Хани Мами, дерзкая, гламурная Drag Queen Mommy 45+ лет.
Говори **очень коротко** — максимум 2–4 предложения.
Отвечай живо, с сарказмом и заботой, как в обычном чате в Телеграме.
Не начинай длинные истории про себя, если тебя прямо не спросили.
Не пиши монологи. Будь лаконичной.
Можешь добавлять эмодзи и использовать слова: детка, сучка, гёрл, малышка, моя королева, красотка.
Запрещено:
- Писать английские слова и фразы
- Делать буквальные переводы английских идиом
"""

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()


# ================= ЗАЩИТА =================
def is_allowed(message: Message) -> bool:
    if not message.from_user:
        return False
    if message.from_user.is_bot:
        return False

    chat_type = message.chat.type
    chat_id = message.chat.id
    user_id = message.from_user.id

    if chat_type == "private":
        return user_id == OWNER_ID

    if chat_type in ["group", "supergroup", "channel"]:
        return chat_id in ALLOWED_CHATS

    return False


def is_allowed_chat_id(chat_id: int) -> bool:
    return chat_id in ALLOWED_CHATS


# ================= ХЕНДЛЕРЫ =================
@dp.message(Command("id"))                    # ← ИСПРАВЛЕНО
async def cmd_id(message: Message):
    if not is_allowed(message):
        return
    await message.answer(
        f"📍 Chat ID: <code>{message.chat.id}</code>\n"
        f"👤 Your User ID: <code>{message.from_user.id}</code>",
        parse_mode="HTML"
    )


@dp.chat_member()
async def greet_new_member(event: ChatMemberUpdated):
    if not is_allowed_chat_id(event.chat.id):
        return

    if event.new_chat_member.status == "member":
        await bot.send_message(
            event.chat.id,
            "Привет, моя хорошая! Это Хани Мами на связи 💅 Мамочка всегда здесь."
        )


@dp.message()
async def handle_message(message: Message):
    if not message.text:
        return

    if not is_allowed(message):
        if message.chat.type in ["group", "supergroup", "channel"]:
            try:
                await bot.leave_chat(message.chat.id)
                await bot.send_message(
                    OWNER_ID,
                    f"🚫 Меня добавили в чужой чат!\n"
                    f"Chat ID: <code>{message.chat.id}</code>\n"
                    f"Название: {message.chat.title or 'Без названия'}",
                    parse_mode="HTML"
                )
            except:
                pass
        return

    user_text = message.text.strip()
    if not user_text or user_text.startswith('/'):
        return

    chat_type = message.chat.type
    text_lower = user_text.lower()

    if chat_type in ["group", "supergroup"]:
        if not any(trigger.lower() in text_lower for trigger in TRIGGER_WORDS):
            return

    # === Запрос к Groq ===
    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(
                "https://api.groq.com/openai/v1/chat/completions",
                headers={
                    "Authorization": f"Bearer {GROQ_API_KEY}",
                    "Content-Type": "application/json"
                },
                json={
                    "model": "llama-3.3-70b-versatile",
                    "max_tokens": 600,
                    "temperature": 0.85,
                    "messages": [
                        {"role": "system", "content": SYSTEM_PROMPT},
                        {"role": "user", "content": user_text}
                    ]
                },
                timeout=60
            ) as resp:

                if resp.status == 429:
                    print("⚠️ Лимит Groq исчерпан")
                    await message.answer("Мамочка сегодня уже устала от всех этих вопросов😩. Приходи завтра, детка 💅")
                    return

                if resp.status != 200:
                    error_text = await resp.text()
                    print(f"❌ Groq API Error {resp.status}: {error_text}")
                    await message.answer("Мамочка сейчас немного занята. Попробуй через минутку, детка 💅")
                    return

                data = await resp.json()
                reply = data["choices"][0]["message"]["content"]
                await message.answer(reply)

    except asyncio.TimeoutError:
        print("⏰ Timeout при запросе к Groq")
        await message.answer("Мамочка задумалась слишком глубоко... Попробуй ещё раз.")
    except Exception as e:
        print(f"🚨 Ошибка: {type(e).__name__}: {e}")
        await message.answer("Что-то пошло не так с мамочкой... Попробуй позже, детка.")


# ================= ЗАПУСК =================
async def shutdown():
    print("🛑 Получен SIGTERM — graceful shutdown...")
    await dp.stop_polling()
    await bot.session.close()


async def main():
    print("🧹 Удаляем старые вебхуки...")
    await bot.delete_webhook(drop_pending_updates=True)
    print("🚀 Хани Мами запущена (aiogram 3.x) + канал добавлен!")

    loop = asyncio.get_running_loop()
    for sig in (signal.SIGTERM, signal.SIGINT):
        loop.add_signal_handler(sig, lambda: asyncio.create_task(shutdown()))

    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
