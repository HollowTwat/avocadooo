import asyncio
import aiogram
import os
import logging
from aiogram import Bot, Dispatcher, types
import openai
# from auth import BOT_TOKEN, ASSISTANT_ID, ASSISTANT_ID_2, ANALYSIS_ASS
import asyncio
import logging
import sys
from aiogram import Bot, Dispatcher, html, Router, BaseMiddleware, types
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.filters import CommandStart, Command
from aiogram.filters.state import StateFilter
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, FSInputFile, InlineKeyboardButton, InlineKeyboardMarkup, CallbackQuery, InputMediaPhoto, InputMediaVideo
from openai import AsyncOpenAI, OpenAI
import shelve
import json

from functions import *
BOT_TOKEN = os.getenv("BOT_TOKEN")
OPENAI_KEY = os.getenv("OPENAI_KEY")
ASSISTANT_ID = os.getenv("ASSISTANT_ID")
ASSISTANT_ID_2 = os.getenv("ASSISTANT_ID_2")
ANALYSIS_ASS = os.getenv("ANALYSIS_ASS")
TOKEN = BOT_TOKEN

bot = Bot(token=TOKEN, default=DefaultBotProperties(
    parse_mode=ParseMode.HTML))
storage = MemoryStorage()
router = Router()
dp = Dispatcher(storage=storage)


class StateMiddleware(BaseMiddleware):
    async def __call__(self, handler, event: Message, data: dict):
        state = data['state']
        current_state = await state.get_state()
        data['current_state'] = current_state
        return await handler(event, data)


class UserState(StatesGroup):
    info_coll = State()
    recognition = State()

class Questionnaire(StatesGroup):
    age = State()
    gender = State()
    location = State()
    allergy = State()
    lifestyle = State()
    phototype = State()
    activity = State()
    water_intake = State()
    stress = State()
    habits = State()

@router.message(CommandStart())
async def command_start_handler(message: Message, state: FSMContext) -> None:
    buttons = [[InlineKeyboardButton(
        text="Анализ состава 🔍", callback_data="analysis")], [InlineKeyboardButton(
        text="Опросник", callback_data="questionaire")]]
    keyboard = InlineKeyboardMarkup(inline_keyboard=buttons)
    step0txt = "Привет"
    await message.answer(step0txt, reply_markup=keyboard)

@dp.message_handler(state=Questionnaire.age)
async def process_age(message: types.Message, state: FSMContext):
    await state.update_data(age=message.text)
    await message.answer("Какой у вас пол? (мужской/женский)")
    await Questionnaire.next()

# Step 2: Gender
@dp.message_handler(state=Questionnaire.gender)
async def process_gender(message: types.Message, state: FSMContext):
    await state.update_data(gender=message.text)
    await message.answer("Укажите вашу страну и город проживания:")
    await Questionnaire.next()

# Step 3: Location
@dp.message_handler(state=Questionnaire.location)
async def process_location(message: types.Message, state: FSMContext):
    await state.update_data(location=message.text)
    await message.answer("Есть ли у вас склонность к аллергии? (да/нет)")
    await Questionnaire.next()

# Step 4: Allergy
@dp.message_handler(state=Questionnaire.allergy)
async def process_allergy(message: types.Message, state: FSMContext):
    await state.update_data(allergy=message.text)
    await message.answer(
        "Особенности образа жизни:\n"
        "1. Частое пребывание на солнце\n"
        "2. Работа в сухом помещении\n"
        "3. Частые физические нагрузки\n"
        "Укажите через запятую все, что применимо (например, 1, 2):"
    )
    await Questionnaire.next()

# Step 5: Lifestyle
@dp.message_handler(state=Questionnaire.lifestyle)
async def process_lifestyle(message: types.Message, state: FSMContext):
    await state.update_data(lifestyle=message.text)
    await message.answer("Какой у вас фототип от 1 до 6?")
    await Questionnaire.next()

# Step 6: Phototype
@dp.message_handler(state=Questionnaire.phototype)
async def process_phototype(message: types.Message, state: FSMContext):
    await state.update_data(phototype=message.text)
    await message.answer("Каков ваш уровень физической активности?")
    await Questionnaire.next()

# Step 7: Physical Activity
@dp.message_handler(state=Questionnaire.activity)
async def process_activity(message: types.Message, state: FSMContext):
    await state.update_data(activity=message.text)
    await message.answer("Опишите ваш питьевой режим:")
    await Questionnaire.next()

# Step 8: Water Intake
@dp.message_handler(state=Questionnaire.water_intake)
async def process_water_intake(message: types.Message, state: FSMContext):
    await state.update_data(water_intake=message.text)
    await message.answer("Каков уровень вашего стресса? (низкий/средний/высокий)")
    await Questionnaire.next()

# Step 9: Stress
@dp.message_handler(state=Questionnaire.stress)
async def process_stress(message: types.Message, state: FSMContext):
    await state.update_data(stress=message.text)
    await message.answer("Есть ли у вас вредные привычки? Опишите:")
    await Questionnaire.next()

# Step 10: Habits
@dp.message_handler(state=Questionnaire.habits)
async def process_habits(message: types.Message, state: FSMContext):
    await state.update_data(habits=message.text)

    user_data = await state.get_data()

    await message.answer(
        "Спасибо за участие в опросе! Вот ваши данные:\n"
        f"Возраст: {user_data['age']}\n"
        f"Пол: {user_data['gender']}\n"
        f"Место проживания: {user_data['location']}\n"
        f"Склонность к аллергии: {user_data['allergy']}\n"
        f"Особенности образа жизни: {user_data['lifestyle']}\n"
        f"Фототип: {user_data['phototype']}\n"
        f"Уровень физической активности: {user_data['activity']}\n"
        f"Питьевой режим: {user_data['water_intake']}\n"
        f"Уровень стресса: {user_data['stress']}\n"
        f"Вредные привычки: {user_data['habits']}"
    )

    await state.finish()

@router.message(StateFilter(UserState.recognition))
async def recognition_handler(message: Message, state: FSMContext) -> None:
    us_id = str(message.from_user.id)
    if message.text:
        med_name = await generate_response(message.text, us_id, ASSISTANT_ID)
        await message.answer(f"Я определил продукт как: {med_name}, сейчас найду в базе и дам аналитику")
        response1 = await no_thread_ass(med_name, ASSISTANT_ID_2)
        response = await remove_json_block(response1)

        extracted_list = await extract_list_from_input(response1)
        print(extracted_list)
        if extracted_list:
            buttons = []
            product_messages = []
            for product in extracted_list:
                product_messages.append(f"id: {product.get('Identifier')}, name: {product.get('FullName')}")
                buttons.append(
                    [
                InlineKeyboardButton(
                    text=product.get('FullName'),
                    callback_data=f"item_{product.get('Identifier')}"
                )
            ]
        )
            combined_message = "\n".join(product_messages)
            keyboard = InlineKeyboardMarkup(inline_keyboard=buttons)
            await message.answer(f"Выбери один из товаров \n{combined_message}", reply_markup=keyboard)
    elif message.voice:

        transcribed_text = await audio_file(message.voice.file_id)
        med_name = await generate_response(transcribed_text, us_id, ASSISTANT_ID)
        await message.answer(f"Я определил продукт как: {med_name}, сейчас найду в базе и дам аналитику")
        response1 = await no_thread_ass(med_name, ASSISTANT_ID_2)
        response = await remove_json_block(response1)

        await message.answer(f"Вот информация по продукту в базе: {response}")
        extracted_list = await extract_list_from_input(response1)
        print(extracted_list)
        if extracted_list:
            buttons = []
            product_messages = []
            for product in extracted_list:
                product_messages.append(f"id: {product.get('Identifier')}, name: {product.get('FullName')}")
                buttons.append(
                    [
                InlineKeyboardButton(
                    text=product.get('FullName'),
                    callback_data=f"item_{product.get('Identifier')}"
                )
            ]
        )
            combined_message = "\n".join(product_messages)
            keyboard = InlineKeyboardMarkup(inline_keyboard=buttons)
            await message.answer(f"Выбери один из товаров \n{combined_message}", reply_markup=keyboard)
    elif message.photo:

        file = await bot.get_file(message.photo[-1].file_id)
        file_path = file.file_path
        file_url = f"https://api.telegram.org/file/bot{bot.token}/{file_path}"
        med_name = await process_url(file_url, us_id, ASSISTANT_ID)
        await message.answer(f"Я определил продукт как: {med_name}, сейчас найду в базе и дам аналитику")
        response1 = await no_thread_ass(med_name, ASSISTANT_ID_2)
        response = await remove_json_block(response1)

        await message.answer(f"Вот информация по продукту в базе: {response}")
        extracted_list = await extract_list_from_input(response1)
        print(extracted_list)
        if extracted_list:
            buttons = []
            product_messages = []
            for product in extracted_list:
                product_messages.append(f"id: {product.get('Identifier')}, name: {product.get('FullName')}")
                buttons.append(
                    [
                InlineKeyboardButton(
                    text=product.get('FullName'),
                    callback_data=f"item_{product.get('Identifier')}"
                )
            ]
        )
            # await message.answer(f"Прогоним первый из продуктов по анализу. Имя продукта: {extracted_list[0].get('FullName')}")
            combined_message = "\n".join(product_messages)
            keyboard = InlineKeyboardMarkup(inline_keyboard=buttons)
            await message.answer(f"Выбери один из товаров \n{combined_message}", reply_markup=keyboard)
            # db_info = await fetch_product_details(extracted_list[0].get('Identifier'))
            # analysys = await no_thread_ass(str(db_info), ANALYSIS_ASS)
            # await message.answer(analysys)
    else:
        await message.answer("Я принимаю только текст голосовое или фото")


@router.callback_query(lambda c: c.data == 'analysis')
async def process_analysis(callback_query: CallbackQuery, state: FSMContext):
    us_id = callback_query.from_user.id
    text = "Скинь мне фото или ссылку твоего средства и я проанализирую? \nИли напиши или надиктуй название"
    await state.set_state(UserState.recognition)
    await bot.send_message(us_id, text)
    await callback_query.answer()

@router.callback_query(lambda c: c.data == 'analysis')
async def process_analysis(callback_query: CallbackQuery, state: FSMContext):
    us_id = callback_query.from_user.id
    text = "Привет! Давайте начнем наш опрос. Сколько вам лет?"
    await bot.send_message(us_id, text)
    await Questionnaire.age.set()
    await callback_query.answer()

@router.callback_query(lambda c: c.data.startswith('item_'))
async def process_analysis(callback_query: CallbackQuery, state: FSMContext):
    buttons = [
        InlineKeyboardButton(text="yep", callback_data='yep'),
        InlineKeyboardButton(text="nope", callback_data='nope')
    ]
    keyboard = InlineKeyboardMarkup(inline_keyboard=[buttons])
    item_id = callback_query.data.split('_')[1]                                    #RECHECK THIS ONE
    db_info = await fetch_product_details(item_id)
    analysys = await no_thread_ass(str(db_info), ANALYSIS_ASS)
    us_id = callback_query.from_user.id
    await bot.send_message(us_id, analysys, reply_markup=keyboard)
    await callback_query.answer()

@router.message()
async def default_handler(message: Message, state: FSMContext, current_state: str) -> None:
    if current_state is not ['redact', 'new_food', 'out_of_uses']:
        await message.answer('Нету стейта')


async def main() -> None:
    logging.basicConfig(level=logging.INFO, stream=sys.stdout)
    dp.include_router(router)
    dp.message.middleware(StateMiddleware())
    bot = Bot(token=TOKEN, default=DefaultBotProperties(
        parse_mode=ParseMode.HTML))
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
