import logging
import asyncio
import json
import os
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.utils.keyboard import ReplyKeyboardBuilder, InlineKeyboardBuilder

API_TOKEN = '8366675375:AAGIO_sT7pSowUlI4_-5xmCZV5_YAoNVa-Q'
ADMIN_ID = 6712617550  # <-- замените на свой Telegram ID

DATA_FILE = 'data.json'

logging.basicConfig(level=logging.INFO)

class AddCategory(StatesGroup):
    waiting_for_category_name = State()
    waiting_for_script_category = State()
    waiting_for_script_name = State()
    waiting_for_script_file = State()
    waiting_for_script_description = State()

storage = MemoryStorage()
bot = Bot(token=API_TOKEN, parse_mode='HTML')
dp = Dispatcher(storage=storage)

def load_data():
    if not os.path.exists(DATA_FILE):
        return {'categories': {}}
    with open(DATA_FILE, 'r', encoding='utf-8') as f:
        return json.load(f)

def save_data(data):
    with open(DATA_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def main_menu_keyboard(is_admin=False):
    builder = ReplyKeyboardBuilder()
    builder.button(text='📜 Скрипты')
    builder.button(text='💬 Связь с разработчиком')
    if is_admin:
        builder.button(text='🛠 Админ-панель')
    builder.adjust(1)
    return builder.as_markup(resize_keyboard=True)

def admin_panel_keyboard():
    builder = ReplyKeyboardBuilder()
    builder.button(text='➕ Добавить категорию')
    builder.button(text='➕ Добавить скрипт')
    builder.button(text='⬅️ В меню')
    builder.adjust(1)
    return builder.as_markup(resize_keyboard=True)

def categories_keyboard(data):
    builder = InlineKeyboardBuilder()
    for cat in data['categories']:
        builder.button(text=f"📂 {cat}", callback_data=f"category:{cat}")
    builder.adjust(1)
    return builder.as_markup()

def scripts_keyboard(category, data):
    builder = InlineKeyboardBuilder()
    for script in data['categories'][category]['scripts']:
        builder.button(text=f"📝 [{script}]", callback_data=f"script:{category}:{script}")
    builder.adjust(1)
    return builder.as_markup()

@dp.message(CommandStart())
async def start(message: types.Message, state: FSMContext):
    is_admin = message.from_user.id == ADMIN_ID
    text = (
        "👋 <b>Привет, {0}!</b>\n"
        "Добро пожаловать в <b>ScriptHub</b> — ваш помощник для быстрого поиска лучших скриптов по категориям!\n\n"
        "📜 <b>Выберите кнопку ниже для продолжения</b>\n"
        "⬇️\n"
        "<i>Чат поддержки находится ниже</i>"
    ).format(message.from_user.first_name)
    await message.answer(text, reply_markup=main_menu_keyboard(is_admin))
    await message.answer("https://t.me/cleodis")
    await state.clear()

@dp.message()
async def debug_and_scripts(message: types.Message):
    # Всегда показываем что реально пришло
    await message.answer(f"DEBUG: [{message.text}]")
    # Если текст содержит "Скрипт" (с эмодзи или без, сработает на все варианты)
    if message.text and "Скрипт" in message.text:
        data = load_data()
        if not data['categories']:
            await message.answer("Категории пока не добавлены.")
        else:
            await message.answer("Выберите категорию:", reply_markup=categories_keyboard(data))
            
@dp.message(F.text == "💬 Связь с разработчиком")
async def contact_dev(message: types.Message):
    await message.answer(
        "📬 <b>Связь с разработчиком:</b>\n"
        "Пишите в Telegram: <a href='https://t.me/bunkoc'>@bunkoc</a>"
    )

@dp.message(F.text == "🛠 Админ-панель")
async def admin_panel(message: types.Message):
    if message.from_user.id == ADMIN_ID:
        await message.answer("⚙️ <b>Админ-панель</b>", reply_markup=admin_panel_keyboard())
    else:
        await message.answer("У вас нет доступа к этой функции.")

@dp.message(F.text == "➕ Добавить категорию")
async def add_category_start(message: types.Message, state: FSMContext):
    if message.from_user.id != ADMIN_ID:
        return
    await message.answer("Введите название новой категории:")
    await state.set_state(AddCategory.waiting_for_category_name)

@dp.message(AddCategory.waiting_for_category_name)
async def add_category_receive_name(message: types.Message, state: FSMContext):
    category_name = message.text.strip()
    data = load_data()
    if category_name in data['categories']:
        await message.answer("Такая категория уже существует.")
        await state.clear()
        return
    data['categories'][category_name] = {"scripts": {}}
    save_data(data)
    await message.answer(f"Категория <b>{category_name}</b> успешно добавлена!", reply_markup=admin_panel_keyboard())
    await state.clear()

@dp.message(F.text == "➕ Добавить скрипт")
async def add_script_start(message: types.Message, state: FSMContext):
    if message.from_user.id != ADMIN_ID:
        return
    data = load_data()
    if not data['categories']:
        await message.answer("Нет ни одной категории. Сначала добавьте категорию.")
        return
    builder = ReplyKeyboardBuilder()
    for cat in data['categories']:
        builder.button(text=cat)
    builder.button(text="⬅️ В меню")
    builder.adjust(1)
    await message.answer("В какую категорию добавить скрипт?", reply_markup=builder.as_markup(resize_keyboard=True))
    await state.set_state(AddCategory.waiting_for_script_category)

@dp.message(AddCategory.waiting_for_script_category)
async def add_script_receive_category(message: types.Message, state: FSMContext):
    category = message.text.strip()
    data = load_data()
    if category not in data['categories']:
        await message.answer("Такой категории нет. Попробуйте снова.")
        await state.clear()
        return
    await state.update_data(category=category)
    await message.answer("Введите название скрипта (оно будет отображаться в квадратных скобках):")
    await state.set_state(AddCategory.waiting_for_script_name)

@dp.message(AddCategory.waiting_for_script_name)
async def add_script_receive_name(message: types.Message, state: FSMContext):
    script_name = message.text.strip()
    user_data = await state.get_data()
    category = user_data['category']
    data = load_data()
    if script_name in data['categories'][category]['scripts']:
        await message.answer("Скрипт с таким именем уже существует в этой категории.")
        await state.clear()
        return
    await state.update_data(script_name=script_name)
    await message.answer("Отправьте файл скрипта (документом, не как сообщение):")
    await state.set_state(AddCategory.waiting_for_script_file)

@dp.message(AddCategory.waiting_for_script_file)
async def add_script_receive_file(message: types.Message, state: FSMContext):
    # Проверяем, что файл есть
    if not message.document:
        await message.answer("Пожалуйста, отправьте файл скрипта документом.")
        return
    file_id = message.document.file_id
    file_name = message.document.file_name
    user_data = await state.get_data()
    await state.update_data(script_file_id=file_id, script_file_name=file_name)
    await message.answer("Теперь отправьте описание для скрипта (можно отправить как цитату на своё сообщение с файлом):")
    await state.set_state(AddCategory.waiting_for_script_description)

@dp.message(AddCategory.waiting_for_script_description)
async def add_script_receive_description(message: types.Message, state: FSMContext):
    script_description = message.text.strip()
    user_data = await state.get_data()
    category = user_data['category']
    script_name = user_data['script_name']
    script_file_id = user_data['script_file_id']
    script_file_name = user_data['script_file_name']
    data = load_data()
    data['categories'][category]['scripts'][script_name] = {
        "file_id": script_file_id,
        "file_name": script_file_name,
        "description": script_description
    }
    save_data(data)
    await message.answer("Скрипт успешно добавлен!", reply_markup=admin_panel_keyboard())
    await state.clear()

@dp.message(F.text == "⬅️ В меню")
async def back_to_menu(message: types.Message):
    is_admin = message.from_user.id == ADMIN_ID
    await message.answer("Главное меню:", reply_markup=main_menu_keyboard(is_admin))

@dp.callback_query(F.data.startswith("category:"))
async def show_scripts_in_category(callback: types.CallbackQuery):
    category = callback.data.split(":", 1)[1]
    data = load_data()
    if category not in data['categories']:
        await callback.answer("Категория не найдена.")
        return
    scripts = data['categories'][category]['scripts']
    if not scripts:
        await callback.message.answer("В этой категории пока нет скриптов.")
        return
    await callback.message.answer(
        f"<b>Категория: {category}</b>\n\nВыберите скрипт:",
        reply_markup=scripts_keyboard(category, data)
    )

@dp.callback_query(F.data.startswith("script:"))
async def show_script(callback: types.CallbackQuery):
    _, category, script_name = callback.data.split(":", 2)
    data = load_data()
    script = data['categories'][category]['scripts'][script_name]
    desc = script['description']
    file_id = script['file_id']
    file_name = script['file_name']
    text = (
        f"<b>📝 [{script_name}]</b>\n"
        f"<i>{desc}</i>\n\n"
        f"<b>Файл скрипта:</b>"
    )
    await callback.message.answer(text)
    await callback.message.answer_document(file_id, caption=f"[{script_name}]")

async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
