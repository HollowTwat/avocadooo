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

ANALYSIS_G_FACE_ASS = os.getenv("ANALYSIS_G_FACE_ASS")
ANALYSIS_G_BODY_ASS = os.getenv("ANALYSIS_G_BODY_ASS")
ANALYSIS_G_HAIR_ASS = os.getenv("ANALYSIS_G_HAIR_ASS")

ANALYSIS_P_FACE_ASS = os.getenv("ANALYSIS_P_FACE_ASS")
ANALYSIS_P_BODY_ASS = os.getenv("ANALYSIS_P_BODY_ASS")
ANALYSIS_P_HAIR_ASS = os.getenv("ANALYSIS_P_HAIR_ASS")

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

@router.message(StateFilter(Questionnaire.age))
async def process_age(message: types.Message, state: FSMContext):
    await state.update_data(age=message.text)
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="Мужской", callback_data="gender_male")],
            [InlineKeyboardButton(text="Женский", callback_data="gender_female")]
        ]
    )
    await state.set_state(Questionnaire.gender)
    await message.answer("Какой у вас пол?", reply_markup=keyboard)

# Step 2: Gender
@router.callback_query(StateFilter(Questionnaire.gender), lambda c: c.data.startswith("gender_"))
async def process_gender(callback_query: types.CallbackQuery, state: FSMContext):
    gender = "Мужской" if callback_query.data == "gender_male" else "Женский"
    await state.update_data(gender=gender)
    await state.set_state(Questionnaire.location)
    await callback_query.message.answer("Укажите вашу страну и город проживания:")
    await callback_query.answer()

# Step 3: Location
@router.message(StateFilter(Questionnaire.location))
async def process_location(message: types.Message, state: FSMContext):
    await state.update_data(location=message.text)
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="Да", callback_data="allergy_yes")],
            [InlineKeyboardButton(text="Нет", callback_data="allergy_no")]
        ]
    )
    await state.set_state(Questionnaire.allergy)
    await message.answer("Есть ли у вас склонность к аллергии?", reply_markup=keyboard)

# Step 4: Allergy
@router.callback_query(StateFilter(Questionnaire.allergy), lambda c: c.data.startswith("allergy_"))
async def process_allergy(callback_query: types.CallbackQuery, state: FSMContext):
    allergy = "Да" if callback_query.data == "allergy_yes" else "Нет"
    await state.update_data(allergy=allergy)
    await state.set_state(Questionnaire.lifestyle)
    await callback_query.message.answer(
        "Особенности образа жизни:\n"
        "1. Частое пребывание на солнце\n"
        "2. Работа в сухом помещении\n"
        "3. Частые физические нагрузки\n"
        "Укажите через запятую все, что применимо (например, 1, 2):"
    )
    await callback_query.answer()

# Step 5: Lifestyle
@router.message(StateFilter(Questionnaire.lifestyle))
async def process_lifestyle(message: types.Message, state: FSMContext):
    await state.update_data(lifestyle=message.text)
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text=str(i), callback_data=f"phototype_{i}") for i in range(1, 7)]
        ]
    )
    await state.set_state(Questionnaire.phototype)
    await message.answer("Какой у вас фототип от 1 до 6?", reply_markup=keyboard)

# Step 6: Phototype
@router.callback_query(StateFilter(Questionnaire.phototype), lambda c: c.data.startswith("phototype_"))
async def process_phototype(callback_query: types.CallbackQuery, state: FSMContext):
    phototype = callback_query.data.split("_")[1]
    await state.update_data(phototype=phototype)
    await state.set_state(Questionnaire.activity)
    await callback_query.message.answer("Каков ваш уровень физической активности?")
    await callback_query.answer()

# Step 7: Physical Activity
@router.message(StateFilter(Questionnaire.activity))
async def process_activity(message: types.Message, state: FSMContext):
    await state.update_data(activity=message.text)
    await state.set_state(Questionnaire.water_intake)
    await message.answer("Опишите ваш питьевой режим:")

# Step 8: Water Intake
@router.message(StateFilter(Questionnaire.water_intake))
async def process_water_intake(message: types.Message, state: FSMContext):
    await state.update_data(water_intake=message.text)
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="Низкий", callback_data="stress_low")],
            [InlineKeyboardButton(text="Средний", callback_data="stress_medium")],
            [InlineKeyboardButton(text="Высокий", callback_data="stress_high")]
        ]
    )
    await state.set_state(Questionnaire.stress)
    await message.answer("Каков уровень вашего стресса?", reply_markup=keyboard)

# Step 9: Stress
@router.callback_query(StateFilter(Questionnaire.stress), lambda c: c.data.startswith("stress_"))
async def process_stress(callback_query: types.CallbackQuery, state: FSMContext):
    stress = {
        "stress_low": "Низкий",
        "stress_medium": "Средний",
        "stress_high": "Высокий"
    }[callback_query.data]
    await state.update_data(stress=stress)
    await state.set_state(Questionnaire.habits)
    await callback_query.message.answer("Есть ли у вас вредные привычки? Опишите:")
    await callback_query.answer()

# Step 10: Habits
@router.message(StateFilter(Questionnaire.habits))
async def process_habits(message: types.Message, state: FSMContext):
    await state.update_data(habits=message.text)
    user_data = await state.get_data()
    buttons = [[InlineKeyboardButton(
        text="Анализ состава 🔍", callback_data="analysis")], [InlineKeyboardButton(
        text="Опросник", callback_data="questionaire")]]
    keyboard = InlineKeyboardMarkup(inline_keyboard=buttons)
    us_id = message.from_user.id

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
        f"Вредные привычки: {user_data['habits']}",
        reply_markup=keyboard
    )

    user_data = {
                "age": f"{user_data['age']}",
                "gender": f"{user_data['gender']}",
                "location": f"{user_data['location']}",
                "allergy": f"{user_data['allergy']}",
                "lifestyle": f"{user_data['lifestyle']}",
                "phototype": f"{user_data['phototype']}",
                "activity": f"{user_data['activity']}",
                "water_intake": f"{user_data['water_intake']}",
                "stress": f"{user_data['stress']}",
                "habits": f"{user_data['habits']}"
            }
    response = await send_user_data(us_id, user_data)
    await message.answer(str(response))
    await state.clear()


@router.message(StateFilter(UserState.recognition))
async def recognition_handler(message: Message, state: FSMContext) -> None:
    user_data = await state.get_data()
    product_type = user_data.get("product_type")
    us_id = str(message.from_user.id)
    if message.text:
        med_name = await generate_response(message.text, us_id, ASSISTANT_ID)
        await message.answer(f"Я определил продукт как: {med_name}, сейчас найду в базе и дам аналитику")
        response1 = await no_thread_ass(med_name, ASSISTANT_ID_2)
        response = await remove_json_block(response1)

        extracted_list = await extract_list_from_input(response1)
        print(extracted_list)
        if extracted_list:
            buttons = [[InlineKeyboardButton(text="Все не то, попробовать снова", callback_data=f"analysis")],]
            product_messages = []
            for product in extracted_list:
                product_messages.append(f"id: {product.get('Identifier')}, name: {product.get('FullName')}")
                buttons.append(
                    [
                InlineKeyboardButton(
                    text=product.get('FullName'),
                    callback_data=f"item_{product_type}_{product.get('Identifier')}"
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
                    callback_data=f"item_{product_type}_{product.get('Identifier')}"
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
                    callback_data=f"item_{product_type}_{product.get('Identifier')}"
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


# @router.callback_query(lambda c: c.data == 'analysis')
# async def process_analysis_cb(callback_query: CallbackQuery, state: FSMContext):
#     us_id = callback_query.from_user.id
#     text = "Скинь мне фото или ссылку твоего средства и я проанализирую? \nИли напиши или надиктуй название"
#     await state.set_state(UserState.recognition)
#     await bot.send_message(us_id, text)
#     await callback_query.answer()

@router.callback_query(lambda c: c.data == 'analysis')
async def process_analysis_cb(callback_query: CallbackQuery, state: FSMContext):
    us_id = callback_query.from_user.id
    text = "Выберите тип продукта: Лицо или Тело"
    buttons = [
        [InlineKeyboardButton(text="Лицо", callback_data="product_type_face")],
        [InlineKeyboardButton(text="Тело", callback_data="product_type_body")],
        [InlineKeyboardButton(text="Волосы", callback_data="product_type_hair")],
    ]
    keyboard = InlineKeyboardMarkup(inline_keyboard=buttons)
    await bot.send_message(us_id, text, reply_markup=keyboard)
    await callback_query.answer()

@router.callback_query(lambda c: c.data.startswith('product_type_'))
async def process_product_type(callback_query: CallbackQuery, state: FSMContext):
    product_type = callback_query.data.split('_')[2]  # Extracts 'face' or 'body'
    await state.update_data(product_type=product_type)
    us_id = callback_query.from_user.id
    text = "Скинь мне фото или ссылку твоего средства и я проанализирую? \nИли напиши или надиктуй название"
    await state.set_state(UserState.recognition)
    await bot.send_message(us_id, text)
    await callback_query.answer()

@router.callback_query(lambda c: c.data == 'questionaire')
async def process_questionaire(callback_query: CallbackQuery, state: FSMContext):
    us_id = callback_query.from_user.id
    text = "Привет! Давайте начнем наш опрос. Сколько вам лет?"
    await bot.send_message(us_id, text)
    await state.set_state(Questionnaire.age)
    await callback_query.answer()


@router.callback_query(lambda c: c.data.startswith('item_'))
async def process_item(callback_query: CallbackQuery, state: FSMContext):
    parts = callback_query.data.split('_')
    analysis_type = parts[1]
    item_id = parts[2]

    analysis_matrix = {
        'face': ANALYSIS_G_FACE_ASS,
        'body': ANALYSIS_G_BODY_ASS,
        'hair': ANALYSIS_G_HAIR_ASS,
    }

    analysis_var = analysis_matrix.get(analysis_type)
    print(f"analysing using {analysis_var}")

    if not analysis_var:
        await callback_query.answer("Invalid analysis type.", show_alert=True)
        return

    us_id = callback_query.from_user.id

    buttons = [
        InlineKeyboardButton(text="yep", callback_data=f'personal_{analysis_type}_{item_id}'),
        InlineKeyboardButton(text="nope", callback_data='analysis')
    ]
    keyboard = InlineKeyboardMarkup(inline_keyboard=[buttons])

    db_info = await fetch_product_details(item_id)
    analysis_result = await no_thread_ass(str(db_info), analysis_var)

    await bot.send_message(us_id, analysis_result)
    await bot.send_message(us_id, "Хочешь персональный анализ?", reply_markup=keyboard)

    await callback_query.answer()

# @router.callback_query(lambda c: c.data.startswith('item_'))
# async def process_analysis(callback_query: CallbackQuery, state: FSMContext):
#     item_id = callback_query.data.split('_')[1]
#     us_id = callback_query.from_user.id
#     buttons = [
#         InlineKeyboardButton(text="yep", callback_data=f'personal_{item_id}'),
#         InlineKeyboardButton(text="nope", callback_data='analysis')
#     ]
#     keyboard = InlineKeyboardMarkup(inline_keyboard=[buttons])                                  #RECHECK THIS ONE
#     db_info = await fetch_product_details(item_id)
#     analysys = await no_thread_ass(str(db_info), ANALYSIS_ASS)
#     await bot.send_message(us_id, analysys)
#     await bot.send_message(us_id, "Хочешь персональный анализ?", reply_markup=keyboard)
#     await callback_query.answer()

@router.callback_query(lambda c: c.data.startswith('personal_'))
async def personal_cb(callback_query: CallbackQuery, state: FSMContext):
    # item_id = callback_query.data.split('_')[1]
    parts = callback_query.data.split('_')
    analysis_type = parts[1]
    item_id = parts[2]
    us_id = callback_query.from_user.id

    analysis_matrix = {
        'face': ANALYSIS_P_FACE_ASS,
        'body': ANALYSIS_P_BODY_ASS,
        'hair': ANALYSIS_P_HAIR_ASS,
    }

    analysis_var = analysis_matrix.get(analysis_type)
    
    db_info = await fetch_product_details(item_id)
    user_info = await get_user_data(us_id)
    gpt_message = f"Информация о продукте: {db_info}, Информация о пользователе: {user_info}"
    pers_analysis = await no_thread_ass(gpt_message, analysis_var)
    await bot.send_message(us_id, pers_analysis)
    await callback_query.answer()


@router.message()
async def default_handler(message: Message, state: FSMContext) -> None:
    current_state = await state.get_state()
    buttons = [[InlineKeyboardButton(
        text="Анализ состава 🔍", callback_data="analysis")], [InlineKeyboardButton(
        text="Опросник", callback_data="questionaire")]]
    keyboard = InlineKeyboardMarkup(inline_keyboard=buttons)
    if not current_state:
        await message.answer("Состояние не установлено. Используйте /start, чтобы начать, или выберите вариант из меню", reply_markup=keyboard)
    else:
        await message.answer(f"Текущее состояние: {current_state}")


async def main() -> None:
    logging.basicConfig(level=logging.INFO, stream=sys.stdout)
    dp.include_router(router)
    dp.message.middleware(StateMiddleware())
    bot = Bot(token=TOKEN, default=DefaultBotProperties(
        parse_mode=ParseMode.HTML))
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
