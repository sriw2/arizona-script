import logging
from aiogram import Bot, Dispatcher, types, F
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton, Message, CallbackQuery
from aiogram.filters import CommandStart, Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.fsm.state import State, StatesGroup
import asyncio
import json
import os

API_TOKEN = '8366675375:AAGIO_sT7pSowUlI4_-5xmCZV5_YAoNVa-Q'
ADMIN_ID = 6712617550  # <-- замените на свой Telegram ID

DATA_FILE = 'data.json'

# Логирование
logging.basicConfig(level=logging.INFO)

# FSM States
class AddCategory(StatesGroup):
    waiting_for_category_name = State()
    waiting_for_script_name = State()
    waiting_for_script_content = State()
    waiting_for_script_description = State()

# Storage and Dispatcher
storage = MemoryStorage()
bot = Bot(token=API_TOKEN, parse_mode='HTML')
dp = Dispatcher(storage=storage)

# --- Data Management ---

def load_data():
    if not os.path.exists(DATA_FILE):
        return {'categories': {}}
    with open(DATA_FILE, 'r', encoding='utf-8') as f:
        return json.load(f)

def save_data(data):
    with open(DATA_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

# --- Keyboards ---

def main_menu_keyboard(is_admin=False):
    kb = [
        [KeyboardButton('📜 Скрипты')],
        [KeyboardButton('💬 Связь с разработчиком')],
    ]
    if is_admin:
        kb.append([KeyboardButton('🛠 Админ-панель')])
    return ReplyKeyboardMarkup(keyboard=kb, resize_keyboard=True)

def categories_keyboard(data):
    kb = []
    for cat in data['categories']:
        kb.append([InlineKeyboardButton(f"📂 {cat}", callback_data=f"category:{cat}")])
    return InlineKeyboardMarkup(inline_keyboard=kb)

def scripts_keyboard(category, data):
    kb = []
    for script in data['categories'][category]['scripts']:
        kb.append([InlineKeyboardButton(f"📝 {script}", callback_data=f"script:{category}:{script}")])
    return InlineKeyboardMarkup(inline_keyboard=kb)

def admin_panel_keyboard():
    kb = [
        [KeyboardButton("➕ Добавить категорию")],
        [KeyboardButton("➕ Добавить скрипт")],
        [KeyboardButton("⬅️ В меню")]
    ]
    return ReplyKeyboardMarkup(keyboard=kb, resize_keyboard=True)

# --- Handlers ---

@dp.message(CommandStart())
async def start(message: Message, state: FSMContext):
    is_admin = message.from_user.id == ADMIN_ID
    text = (
        "👋 <b>Привет, {0}!</b>\n"
        "Добро пожаловать в <b>ScriptHub</b> — ваш помощник для быстрого поиска лучших скриптов по категориям!\n\n"
        "📜 <b>Что умеет бот?</b>\n"
        "— Удобно выбирать и просматривать скрипты по категориям\n"
        "— Оставлять обратную связь\n"
        "— Всегда быть на связи с разработчиком\n\n"
        "Ссылка на чат: <a href='https://t.me/cleodis'>https://t.me/cleodis</a>\n\n"
        "Выберите действие из меню ниже 👇"
    ).format(message.from_user.first_name)
    await message.answer(text, reply_markup=main_menu_keyboard(is_admin))
    await state.clear()

@dp.message(F.text == "📜 Скрипты")
async def list_categories(message: Message):
    data = load_data()
    if not data['categories']:
        await message.answer("Категории пока не добавлены.")
    else:
        await message.answer("Выберите категорию:", reply_markup=categories_keyboard(data))

@dp.message(F.text == "💬 Связь с разработчиком")
async def contact_dev(message: Message):
    await message.answer(
        "📬 <b>Связь с разработчиком:</b>\n"
        "Пишите в Telegram: <a href='https://t.me/bunkoc'>@bunkoc</a>"
    )

@dp.message(F.text == "🛠 Админ-панель")
async def admin_panel(message: Message):
    if message.from_user.id == ADMIN_ID:
        await message.answer("⚙️ <b>Админ-панель</b>", reply_markup=admin_panel_keyboard())
    else:
        await message.answer("У вас нет доступа к этой функции.")

@dp.message(F.text == "➕ Добавить категорию")
async def add_category_start(message: Message, state: FSMContext):
    if message.from_user.id != ADMIN_ID:
        return
    await message.answer("Введите название новой категории:")
    await state.set_state(AddCategory.waiting_for_category_name)

@dp.message(AddCategory.waiting_for_category_name)
async def add_category_receive_name(message: Message, state: FSMContext):
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
async def add_script_start(message: Message, state: FSMContext):
    if message.from_user.id != ADMIN_ID:
        return
    data = load_data()
    if not data['categories']:
        await message.answer("Нет ни одной категории. Сначала добавьте категорию.")
        return
    kb = []
    for cat in data['categories']:
        kb.append([KeyboardButton(cat)])
    await message.answer("В какую категорию добавить скрипт?", reply_markup=ReplyKeyboardMarkup(keyboard=kb, resize_keyboard=True))
    await state.set_state(AddCategory.waiting_for_script_name)

@dp.message(AddCategory.waiting_for_script_name)
async def add_script_receive_category(message: Message, state: FSMContext):
    category = message.text.strip()
    data = load_data()
    if category not in data['categories']:
        await message.answer("Такой категории нет. Попробуйте снова.")
        await state.clear()
        return
    await state.update_data(category=category)
    await message.answer("Введите название скрипта:")
    await state.set_state(AddCategory.waiting_for_script_content)

@dp.message(AddCategory.waiting_for_script_content)
async def add_script_receive_name(message: Message, state: FSMContext):
    script_name = message.text.strip()
    user_data = await state.get_data()
    category = user_data['category']
    data = load_data()
    if script_name in data['categories'][category]['scripts']:
        await message.answer("Скрипт с таким именем уже существует в этой категории.")
        await state.clear()
        return
    await state.update_data(script_name=script_name)
    await message.answer("Отправьте сам скрипт (текст):")
    await state.set_state(AddCategory.waiting_for_script_description)

@dp.message(AddCategory.waiting_for_script_description)
async def add_script_receive_content(message: Message, state: FSMContext):
    script_content = message.text.strip()
    user_data = await state.get_data()
    category = user_data['category']
    script_name = user_data['script_name']
    await state.update_data(script_content=script_content)
    await message.answer("Теперь отправьте описание для скрипта (можно прислать цитатой):")
    await state.set_state(None)  # ожидание обычного сообщения

    # Сохраняем без описания, дополнение ниже
    data = load_data()
    data['categories'][category]['scripts'][script_name] = {
        "content": script_content,
        "description": ""
    }
    save_data(data)
    await state.update_data(last_added_script=(category, script_name))

@dp.message()
async def handle_script_description(message: Message, state: FSMContext):
    user_data = await state.get_data()
    if not user_data.get("last_added_script"):
        return
    category, script_name = user_data['last_added_script']
    data = load_data()
    if category in data['categories'] and script_name in data['categories'][category]['scripts']:
        data['categories'][category]['scripts'][script_name]['description'] = message.text
        save_data(data)
        await message.answer("Описание добавлено!")
        await state.clear()
    else:
        await state.clear()

@dp.message(F.text == "⬅️ В меню")
async def back_to_menu(message: Message):
    is_admin = message.from_user.id == ADMIN_ID
    await message.answer("Главное меню:", reply_markup=main_menu_keyboard(is_admin))

# --- Inline Handlers ---

@dp.callback_query(F.data.startswith("category:"))
async def show_scripts_in_category(callback: CallbackQuery):
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
async def show_script(callback: CallbackQuery):
    _, category, script_name = callback.data.split(":", 2)
    data = load_data()
    script = data['categories'][category]['scripts'][script_name]
    desc = script['description']
    script_content = script['content']
    text = (
        f"<b>📝 {script_name}</b>\n"
        f"<i>{desc}</i>\n\n"
        f"<code>{script_content}</code>"
    )
    await callback.message.answer(text)

# --- Entry point ---

async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
