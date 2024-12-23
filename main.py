import asyncio
import aiogram
import os
import logging
from aiogram import Bot, Dispatcher, types
import openai
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
ASSISTANT_ID = os.getenv("RECOGNIZE_MAKEUP_ASS")
ASSISTANT_ID_2 = os.getenv("FIND_PRODUCT_ASS")

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

class Questionnaire2(StatesGroup):
    intro_answer = State()
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
    ethics = State()

@router.message(CommandStart())
async def command_start_handler(message: Message, state: FSMContext) -> None:
    buttons = [[InlineKeyboardButton(
        text="Анализ состава 🔍", callback_data="analysis")], [InlineKeyboardButton(
        text="Опросник", callback_data="questionaire")], [InlineKeyboardButton(
        text="Опросник_2", callback_data="questionaire2")]]
    keyboard = InlineKeyboardMarkup(inline_keyboard=buttons)
    step0txt = "Привет"
    await message.answer(step0txt, reply_markup=keyboard)

@router.message(StateFilter(Questionnaire2.intro_answer))
async def process_intro_answer(message: types.Message, state: FSMContext):
    await state.set_state(Questionnaire2.age)
    await message.answer(
        "1) Раз уж у нас с тобой честный разговор, скажи, сколько тебе лет =) Обещаю, это останется между нами! Напиши только число. Например, 35"
    )

@router.message(StateFilter(Questionnaire2.age))
async def process_age(message: types.Message, state: FSMContext):
    await state.update_data(age=message.text)
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="Женский", callback_data="gender_female")],
            [InlineKeyboardButton(text="Мужской", callback_data="gender_male")]
        ]
    )
    await state.set_state(Questionnaire2.gender)
    await message.answer("2) Твой пол", reply_markup=keyboard)

@router.callback_query(StateFilter(Questionnaire2.gender), lambda c: c.data.startswith("gender_"))
async def process_gender(callback_query: types.CallbackQuery, state: FSMContext):
    gender = "Женский" if callback_query.data == "gender_female" else "Мужской"
    await state.update_data(gender=gender)
    await state.set_state(Questionnaire2.location)
    await callback_query.message.answer(
        "3) Для расчета времени года и климата проживания, мне нужно знать, где ты находишься большая часть года\n"
        "Напиши вот в таком формате: Россия, Санкт-Петербург"
    )
    await callback_query.answer()

@router.message(StateFilter(Questionnaire2.location))
async def process_location(message: types.Message, state: FSMContext):
    await state.update_data(location=message.text)
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="Да", callback_data="allergy_yes")],
            [InlineKeyboardButton(text="Нет", callback_data="allergy_no")]
        ]
    )
    await state.set_state(Questionnaire2.allergy)
    await message.answer("4) Есть ли у тебя склонность к аллергическим реакциям?", reply_markup=keyboard)

@router.callback_query(StateFilter(Questionnaire2.allergy), lambda c: c.data.startswith("allergy_"))
async def process_allergy(callback_query: types.CallbackQuery, state: FSMContext):
    allergy = "Да" if callback_query.data == "allergy_yes" else "Нет"
    await state.update_data(allergy=allergy)
    await state.set_state(Questionnaire2.lifestyle)
    await callback_query.message.answer(
        "5) Особенности образа жизни: какой из вариантов больше описывает твою жизнь? Можно выбрать несколько вариантов\n"
        "1) Часто нахожусь на солнце\n"
        "2) Работаю в сухом помещении (с кондиционером или отоплением)\n"
        "3) Сидячая и неактивная работа\n"
        "4) Часто занимаюсь спортом или физической активностью (высокая потливость)\n"
        "5) Мой образ жизни не подходит ни под одно из этих описаний\n"
        "Укажи через запятую все, что применимо (например, 1, 2)"
    )
    await callback_query.answer()

@router.message(StateFilter(Questionnaire2.lifestyle))
async def process_lifestyle(message: types.Message, state: FSMContext):
    lifestyle = [int(x) for x in message.text.replace(",", " ").split()]
    await state.update_data(lifestyle=lifestyle)
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[[
            InlineKeyboardButton(text=str(i), callback_data=f"phototype_{i}") for i in range(1, 7)
        ]]
    )
    await state.set_state(Questionnaire2.phototype)
    await message.answer(
        "6) Теперь нужно определить фототип твоей кожи:\n"
        "1 — Очень светлая кожа, не загорает, сразу краснеет\n"
        "2 — Светлая кожа, легко сгорает, загорает с трудом\n"
        "3 — Светлая/средняя кожа, редко сгорает, загорает постепенно\n"
        "4 — Средняя/оливковая кожа, редко сгорает, хорошо загорает\n"
        "5 — Темная кожа, практически не сгорает, быстро загорает\n"
        "6 — Очень темная кожа, никогда не сгорает",
        reply_markup=keyboard
    )

@router.callback_query(StateFilter(Questionnaire2.phototype), lambda c: c.data.startswith("phototype_"))
async def process_phototype(callback_query: types.CallbackQuery, state: FSMContext):
    phototype = callback_query.data.split("_")[1]
    await state.update_data(phototype=phototype)
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="Низкая", callback_data="activity_low")],
            [InlineKeyboardButton(text="Средняя", callback_data="activity_mid")],
            [InlineKeyboardButton(text="Высокая", callback_data="activity_high")]
        ]
    )
    await state.set_state(Questionnaire2.activity)
    await callback_query.message.answer("7) Как ты оцениваешь свою физическую активность?", reply_markup=keyboard)
    await callback_query.answer()

@router.callback_query(StateFilter(Questionnaire2.activity), lambda c: c.data.startswith("activity_"))
async def process_activity(callback_query: types.CallbackQuery, state: FSMContext):
    activity_map = {
        "activity_low": "Низкая",
        "activity_mid": "Средняя",
        "activity_high": "Высокая"
    }
    activity = activity_map[callback_query.data]
    await state.update_data(activity=activity)
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="Меньше 1 литра", callback_data="water_<1")],
            [InlineKeyboardButton(text="1–2 литра", callback_data="water_1-2")],
            [InlineKeyboardButton(text="Более 2 литров", callback_data="water_>2")]
        ]
    )
    await state.set_state(Questionnaire2.water_intake)
    await callback_query.message.answer("8) Сколько воды ты пьешь ежедневно?", reply_markup=keyboard)
    await callback_query.answer()

@router.callback_query(StateFilter(Questionnaire2.water_intake), lambda c: c.data.startswith("water_"))
async def process_water_intake(callback_query: types.CallbackQuery, state: FSMContext):
    water_map = {
        "water_<1": "Меньше 1 литра",
        "water_1-2": "1–2 литра",
        "water_>2": "Более 2 литров"
    }
    water_intake = water_map[callback_query.data]
    await state.update_data(water_intake=water_intake)
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="Низкий", callback_data="stress_low")],
            [InlineKeyboardButton(text="Средний", callback_data="stress_mid")],
            [InlineKeyboardButton(text="Высокий", callback_data="stress_high")]
        ]
    )
    await state.set_state(Questionnaire2.stress)
    await callback_query.message.answer("9) Какой уровень стресса в твоей жизни наиболее соответствует реальности?", reply_markup=keyboard)
    await callback_query.answer()

@router.callback_query(StateFilter(Questionnaire2.stress), lambda c: c.data.startswith("stress_"))
async def process_stress(callback_query: types.CallbackQuery, state: FSMContext):
    stress_map = {
        "stress_low": "Низкий",
        "stress_mid": "Средний",
        "stress_high": "Высокий"
    }
    stress = stress_map[callback_query.data]
    await state.update_data(stress=stress)
    stress_message_map = {
        "stress_low": "Получается, ты очень стрессоустойчивый человек! Редкость 🌍",
        "stress_mid": "Это нормально. Но не забывай про самопомощь и поддержку близких💖",
        "stress_high": "Очень и очень тебя понимаю! Больше 70% людей подвержены высокому стрессу, не забывай себя иногда сильно-сильно баловать 🌸"
    }
    await callback_query.message.answer(stress_message_map[callback_query.data])
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="Курение", callback_data="habits_smoking")],
            [InlineKeyboardButton(text="Употребление алкоголя", callback_data="habits_drinking")],
            [InlineKeyboardButton(text="Курение и употребление алкоголя", callback_data="habits_both")],
            [InlineKeyboardButton(text="Нет вредных привычек", callback_data="habits_none")]
        ]
    )
    await state.set_state(Questionnaire2.habits)
    await callback_query.message.answer("10) Какая из вредных привычек тебе свойственна?", reply_markup=keyboard)
    await callback_query.answer()

@router.callback_query(StateFilter(Questionnaire2.habits), lambda c: c.data.startswith("habits_"))
async def process_habits(callback_query: types.CallbackQuery, state: FSMContext):
    habits_map = {
        "habits_smoking": "Курение",
        "habits_drinking": "Употребление алкоголя",
        "habits_both": "Курение и употребление алкоголя",
        "habits_none": "Нет вредных привычек"
    }
    habits = habits_map[callback_query.data]
    await state.update_data(habits=habits)
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="Натуральный состав, Vegan продукт и Cruelty-free", callback_data="ethics_cruelty_free")],
            [InlineKeyboardButton(text="Это не имеет значения", callback_data="ethics_none")]
        ]
    )
    await state.set_state(Questionnaire2.ethics)
    await callback_query.message.answer("11) Этические предпочтения: что для тебя важно в косметике?", reply_markup=keyboard)
    await callback_query.answer()

@router.callback_query(StateFilter(Questionnaire2.ethics), lambda c: c.data.startswith("ethics_"))
async def process_ethics(callback_query: types.CallbackQuery, state: FSMContext):
    ethics = "Натуральный состав, Vegan продукт и Cruelty-free" if callback_query.data == "ethics_cruelty_free" else "Это не имеет значения"
    await state.update_data(ethics=ethics)
    user_data = await state.get_data()
    await callback_query.message.answer(
        "Спасибо за участие в опросе! Вот ваши данные:\n"
        f"Возраст: {user_data['age']}\n"
        f"Пол: {user_data['gender']}\n"
        f"Место проживания: {user_data['location']}\n"
        f"Склонность к аллергии: {user_data['allergy']}\n"
        f"Особенности образа жизни: {', '.join(map(str, user_data['lifestyle']))}\n"
        f"Фототип: {user_data['phototype']}\n"
        f"Уровень физической активности: {user_data['activity']}\n"
        f"Питьевой режим: {user_data['water_intake']}\n"
        f"Уровень стресса: {user_data['stress']}\n"
        f"Вредные привычки: {user_data['habits']}\n"
        f"Этические предпочтения: {user_data['ethics']}"
    )
    await state.clear()

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

@router.callback_query(StateFilter(Questionnaire.gender), lambda c: c.data.startswith("gender_"))
async def process_gender(callback_query: types.CallbackQuery, state: FSMContext):
    gender = "Мужской" if callback_query.data == "gender_male" else "Женский"
    await state.update_data(gender=gender)
    await state.set_state(Questionnaire.location)
    await callback_query.message.answer("Укажите вашу страну и город проживания:")
    await callback_query.answer()

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

@router.callback_query(StateFilter(Questionnaire.phototype), lambda c: c.data.startswith("phototype_"))
async def process_phototype(callback_query: types.CallbackQuery, state: FSMContext):
    phototype = callback_query.data.split("_")[1]
    await state.update_data(phototype=phototype)
    await state.set_state(Questionnaire.activity)
    await callback_query.message.answer("Каков ваш уровень физической активности?")
    await callback_query.answer()

@router.message(StateFilter(Questionnaire.activity))
async def process_activity(message: types.Message, state: FSMContext):
    await state.update_data(activity=message.text)
    await state.set_state(Questionnaire.water_intake)
    await message.answer("Опишите ваш питьевой режим:")

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
            combined_message = "\n".join(product_messages)
            keyboard = InlineKeyboardMarkup(inline_keyboard=buttons)
            await message.answer(f"Выбери один из товаров \n{combined_message}", reply_markup=keyboard)
    else:
        await message.answer("Я принимаю только текст голосовое или фото")

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

@router.callback_query(lambda c: c.data == 'questionaire2')
async def process_questionaire(callback_query: CallbackQuery, state: FSMContext):
    us_id = callback_query.from_user.id
    text = (
        "Часть 1/4 🟢⚪️⚪️⚪️\n"
        "11 вопросов о тебе\n\n"
        "Имя, при составлении твоей индивидуальной рекомендации того или иного средства – я должна знать всё о твоем стиле жизни, фототипе и предпочтениях. "
        "Чтобы не получилось так, что я для тебя одобрила средство, которое абсолютно не подходит тебе по этическим предпочтениям."
    )
    await bot.send_message(us_id, text)
    await state.set_state(Questionnaire2.intro_answer)
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
    analysis_result1 = await no_thread_ass(str(db_info), analysis_var)
    analysis_result = remove_tags(analysis_result1)

    await bot.send_message(us_id, analysis_result)
    await bot.send_message(us_id, "Хочешь персональный анализ?", reply_markup=keyboard)

    await callback_query.answer()

@router.callback_query(lambda c: c.data.startswith('personal_'))
async def personal_cb(callback_query: CallbackQuery, state: FSMContext):
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
        text="Опросник", callback_data="questionaire")], [InlineKeyboardButton(
        text="Опросник_2", callback_data="questionaire2")]]
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
