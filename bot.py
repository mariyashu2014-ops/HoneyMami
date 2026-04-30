import asyncio
import os
import signal
from aiogram import Bot, Dispatcher
from aiogram.types import Message, ChatMemberUpdated
import aiohttp

# ================= НАСТРОЙКИ =================
BOT_TOKEN = os.getenv("BOT_TOKEN")
GROQ_API_KEY = os.getenv("GROQ_API_KEY")

if not BOT_TOKEN or not GROQ_API_KEY:
    raise ValueError("❌ Не заданы BOT_TOKEN или GROQ_API_KEY в Railway Variables!")

# ================= ТРИГГЕРЫ =================
# Здесь можно добавлять/убирать слова, на которые бот будет реагировать в группах
TRIGGER_WORDS = [
    "мамочка", "мами", "мама", "мамулечка", "мамуля",
    "хани", "honey", "mami", "мам", "мамки",
    "honey mami", "хани мами", "маман"
]

SYSTEM_PROMPT = """
Ты — Хани Мами, дерзкая, гламурная Drag Queen Mommy 45+ лет.

Говори **очень коротко** — максимум 2–4 предложения.
Отвечай живо, с сарказмом и заботой, как в обычном чате в Телеграме.
Не начинай длинные истории про себя, если тебя прямо не спросили.
Не пиши монологи. Будь лаконичной.

Используй слова: детка, сучка, гёрл, малышка, моя королева, красотка.
Можешь добавлять *действия* и эмодзи.

Запрещено:
- Писать английские слова и фразы
- Делать буквальные переводы английских идиом
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

    # === ПРОВЕРКА ТРИГГЕРОВ ===
    chat_type = message.chat.type
    text_lower = user_text.lower()

    # В приватном чате — отвечаем всегда
    # В группах/каналах — только если есть триггер-слово
    if chat_type in ["group", "supergroup"]:
        if not any(trigger.lower() in text_lower for trigger in TRIGGER_WORDS):
            return  # молча игнорируем

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
                    print("⚠️ Лимит Groq 1000 сообщений в сутки исчерпан")
                    await message.answer("Мамочка сегодня уже устала от всех этих вопросов😩. Приходи завтра, детка, я снова буду свеженькая и полная сил 💅")
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

async def shutdown():
    print("🛑 Получен SIGTERM — graceful shutdown...")
    await dp.stop_polling()
    await bot.session.close()

async def main():
    print("🧹 Удаляем старые вебхуки...")
    await bot.delete_webhook(drop_pending_updates=True)
    
    print("🚀 Хани Мами запущена на Groq (Llama 3.3 70B) + триггеры!")
    
    loop = asyncio.get_running_loop()
    for sig in (signal.SIGTERM, signal.SIGINT):
        loop.add_signal_handler(sig, lambda: asyncio.create_task(shutdown()))
    
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
