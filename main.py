import asyncio
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import CommandStart
from aiogram.utils.keyboard import ReplyKeyboardBuilder

API_TOKEN = '8366675375:AAGIO_sT7pSowUlI4_-5xmCZV5_YAoNVa-Q'

bot = Bot(token=API_TOKEN, parse_mode='HTML')
dp = Dispatcher()

def main_menu_keyboard():
    builder = ReplyKeyboardBuilder()
    builder.button(text='📜 Скрипты')
    builder.button(text='💬 Связь с разработчиком')
    builder.adjust(1)
    return builder.as_markup(resize_keyboard=True)

@dp.message(CommandStart())
async def start(message: types.Message):
    await message.answer(
        "👋 Привет! Выберите действие из меню ниже:",
        reply_markup=main_menu_keyboard()
    )

@dp.message(F.text == "📜 Скрипты")
async def scripts_handler(message: types.Message):
    await message.answer("Скрипты работают!")

@dp.message(F.text == "💬 Связь с разработчиком")
async def contact_handler(message: types.Message):
    await message.answer("Контакт с разработчиком!")

async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
