import os
import asyncio
from html import escape

from aiogram import Bot, Dispatcher, types, F
from aiogram.types import Message
from aiogram.filters import Command

# Імпортуємо get_connection ТА функцію init_db для автоматичного створення таблиць
from database import get_connection, init_db

TOKEN = os.getenv("BOT_TOKEN")  # Переконайтеся, що BOT_TOKEN встановлено в оточенні

bot = Bot(token=TOKEN)
dp = Dispatcher()

@dp.message(Command("start"))
async def start_command(message: Message):
    await message.answer(
        "Привіт! Я PriceWatcher - бот для відстеження цін на товари. \n\n"
        "/list - Показати перші 10 оголошень\n"
        "/all - Показати першу сторінку оголошень\n"
        "/page [номер] - Перейти на конкретну сторінку (наприклад: /page 2)"
    )

@dp.message(Command("list"))
async def list_command(message: Message):
    with get_connection() as conn:
        listings = conn.execute("""
            SELECT title, price, url
            FROM listings
            ORDER BY last_seen DESC 
            LIMIT 10
        """).fetchall()

    if not listings:
        await message.answer("База даних порожня. Парсер ще не зібрав жодного оголошення.")
        return

    for item in listings:
        title = escape(item["title"])
        url = escape(item["url"], quote=True)
        price = f"{item['price']} грн" if item["price"] is not None else "Ціна не вказана"

        text = (
            f"<b>{title}</b>\n"
            f"Ціна: {price}\n"
            f"<a href='{url}'>Перейти до оголошення</a>"
        )
        await message.answer(text, parse_mode="HTML", disable_web_page_preview=True)


PAGE_SIZE = 25

async def show_page(message: Message, page_number: int):
    if page_number < 1:
        await message.answer("Номер сторінки повинен бути більшим за 0.")
        return

    offset = (page_number - 1) * PAGE_SIZE

    with get_connection() as conn:
        # Безпечний підрахунок кількості рядків для sqlite3.Row
        total_row = conn.execute("SELECT COUNT(*) AS total_count FROM listings").fetchone()
        total = total_row["total_count"] if total_row else 0

        listings = conn.execute("""
            SELECT title, price, url
            FROM listings
            ORDER BY last_seen DESC
            LIMIT ? OFFSET ?
        """, (PAGE_SIZE, offset)).fetchall()

    if not listings or total == 0:
        await message.answer(f"Сторінка {page_number} порожня або ще не створена. У базі поки немає даних.")
        return

    await message.answer(f"📖 Сторінка {page_number}.\nУсього оголошень у базі: {total}.")

    for item in listings:
        title = escape(item["title"])
        url = escape(item["url"], quote=True)
        price = f"{item['price']} грн" if item["price"] is not None else "Ціна не вказана"
        
        text = (
            f"<b>{title}</b>\n"
            f"Ціна: {price}\n"
            f"<a href='{url}'>Перейти до оголошення</a>"
        )
        await message.answer(text, parse_mode="HTML", disable_web_page_preview=True)


@dp.message(Command("all"))
async def all_command(message: Message):
    await show_page(message, 1)  


@dp.message(Command("page"))
async def page_command(message: Message):
    parts = (message.text or "").split(maxsplit=1)    

    if len(parts) < 2 or not parts[1].isdigit():
        await message.answer("Будь ласка, вкажіть номер сторінки після команди. Приклад: `/page 2`", parse_mode="Markdown")
        return

    await show_page(message, int(parts[1]))                                    


async def main():
    if not TOKEN:
        raise RuntimeError("BOT_TOKEN environment variable is not set.")

    # КРИТИЧНО НАДВАТЛИВО: Автоматично створюємо базу/таблиці при запуску бота, якщо файл видалили
    init_db()
    print("Базу даних перевірено та ініціалізовано.")

    print("Бот запускається...")
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())    
