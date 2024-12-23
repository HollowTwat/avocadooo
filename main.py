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

class QuestionnaireFace(StatesGroup):
    skin_type = State()
    skin_condition = State()
    skin_issues = State()
    skin_goals = State()

class QuestionnaireBody(StatesGroup):
    body_skin_type = State()
    body_skin_sensitivity = State()
    body_skin_condition = State()
    body_hair_issues = State()
    body_attention_areas = State()
    body_goals = State()

class QuestionnaireHair(StatesGroup):
    scalp_type = State()
    hair_thickness = State()
    hair_length = State()
    hair_structure = State()
    hair_condition = State()
    hair_goals = State()
    washing_frequency = State()
    current_products = State()
    product_texture = State()
    sensitivity = State()
    styling_tools = State()


@router.message(CommandStart())
async def command_start_handler(message: Message, state: FSMContext) -> None:
    buttons = [[InlineKeyboardButton(
        text="Анализ состава 🔍", callback_data="analysis")], [InlineKeyboardButton(
        text="Опросник", callback_data="questionaire")], [InlineKeyboardButton(
        text="Опросник_2", callback_data="questionaire2")], [InlineKeyboardButton(
        text="Опросник_Лицо", callback_data="questionnaire_face")], [InlineKeyboardButton(
        text="Опросник_Тело", callback_data="questionnaire_body")], [InlineKeyboardButton(
        text="Опросник_Волосы", callback_data="questionnaire_hair")]]
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


@router.callback_query(StateFilter(QuestionnaireFace.skin_type), lambda c: True)
async def process_face_skin_type(callback_query: CallbackQuery, state: FSMContext):
    await state.update_data(face_skin_type=callback_query.data)
    await state.set_state(QuestionnaireFace.skin_condition)
    await callback_query.message.answer(
        "13) Как ты оцениваешь текущее состояние кожи своего лица?",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="Обезвоженная", callback_data="dehydrated")],
            [InlineKeyboardButton(text="Чувствительная", callback_data="sensitive")],
            [InlineKeyboardButton(text="Нормальная", callback_data="normal")]
        ])
    )
    await callback_query.answer()

@router.callback_query(StateFilter(QuestionnaireFace.skin_condition), lambda c: True)
async def process_face_skin_condition(callback_query: CallbackQuery, state: FSMContext):
    await state.update_data(face_skin_condition=callback_query.data)
    await state.set_state(QuestionnaireFace.skin_issues)
    pre_message_map = {
        "dehydrated": "Уже сейчас можешь пойти и выпить стаканчик воды, я никуда не убегу 💦",
        "sensitive": "Хорошо тебя понимаю, муха мимо пролетит, а у меня уже всё краснеет 🦋",
        "normal": "Не многие могут таким похвастаться ✨🍃"
    }
    await callback_query.message.answer(pre_message_map[callback_query.data])
    await callback_query.message.answer(
        "14) Есть ли у тебя какие-либо осложнения с кожей на лице? Напиши все подходящие варианты\n"
        "1) Пигментация\n"
        "2) Неровный тон\n"
        "3) Акне, постакне\n"
        "4) Рубцы и шрамы\n"
        "5) Морщины\n"
        "6) Расширенные поры\n"
        "7) Открытые и/или закрытые комедоны\n"
        "8) Сосудистые проявления\n"
        "9) Сухость, шелушение\n"
        "10) Нет особых проблем",
        reply_markup=None
    )
    await callback_query.answer()

@router.message(StateFilter(QuestionnaireFace.skin_issues))
async def process_face_skin_issues(message: types.Message, state: FSMContext):
    # issues = [int(x) for x in message.text.replace(",", " ").split()]
    goals = [int(x) for x in message.text.replace(",", " ").split()]
    goal_descriptions = {
        "1": "Пигментация",
        "2":  "Неровный тон",
        "3" : "Акне, постакне",
        "4" : "Рубцы и шрамы",
        "5" : "Морщины",
        "6" : "Расширенные поры",
        "7" : "Открытые и/или закрытые комедоны",
        "8" : "Сосудистые проявления",
        "9" : "Сухость, шелушение",
        "10" : "Нет особых проблем",
    }
    goal_texts = [goal_descriptions[goal] for goal in goals if goal in goal_descriptions]
    await state.update_data(face_skin_issues=goal_texts)
    await state.set_state(QuestionnaireFace.skin_goals)
    await message.answer(
        "15) Какие задачи ты могла бы себе поставить для улучшения кожи лица? Выбирай несколько вариантов\n"
        "1) Увлажнённая и гладкая кожа\n"
        "2) Сияющая свежая кожа\n"
        "3) Убрать жирный блеск\n"
        "4) Избавиться от расширенных пор\n"
        "5) Убрать чёрные точки\n"
        "6) Убрать воспаления и постакне\n"
        "7) Убрать морщины\n"
        "8) Выровнять тон\n"
        "9) Уменьшить \"мешки\" и тёмные круги под глазами\n"
        "10) Снять покраснение и раздражение",
        reply_markup=None
    )

@router.message(StateFilter(QuestionnaireFace.skin_goals))
async def process_face_skin_goals(message: types.Message, state: FSMContext):
    goals = [int(x) for x in message.text.replace(",", " ").split()]
    goal_descriptions = {
        "1": "Увлажнённая и гладкая кожа",
        "2":  "Сияющая свежая кожа",
        "3" : "Убрать жирный блеск",
        "4" : "Избавиться от расширенных пор",
        "5" : "Убрать чёрные точки",
        "6" : "Убрать воспаления и постакне",
        "7" : "Убрать морщины",
        "8" : "Выровнять тон",
        "9" : "Уменьшить \"мешки\" и тёмные круги под глазами",
        "10" : "Снять покраснение и раздражение",
    }
    goal_texts = [goal_descriptions[goal] for goal in goals if goal in goal_descriptions]
    await state.update_data(face_skin_goals=goal_texts)
    user_data = await state.get_data()
    await message.answer(
        "Спасибо за участие в опросе! Вот ваши данные:\n"
        f"Тип кожи: {user_data['face_skin_type']}\n"
        f"Состояние кожи: {user_data['face_skin_condition']}\n"
        f"Проблемы кожи: {', '.join(map(str, user_data['face_skin_issues']))}\n"
        f"Цели ухода: {', '.join(map(str, user_data['face_skin_goals']))}"
    )
    us_id = message.from_user.id

    user_data = {
                "face_skin_type": f"Тип кожи: {user_data['face_skin_type']}",
                "face_skin_condition": f"Состояние кожи: {user_data['face_skin_condition']}",
                "face_skin_issues": f"Проблемы кожи: {', '.join(map(str, user_data['face_skin_issues']))}",
                "face_skin_goals": f"Цели ухода: {', '.join(map(str, user_data['face_skin_goals']))}",
            }
    # response = await send_user_data(us_id, user_data)
    await state.clear()


@router.callback_query(StateFilter(QuestionnaireBody.body_skin_type), lambda c: True)
async def process_body_skin_type(callback_query: CallbackQuery, state: FSMContext):
    await state.update_data(body_skin_type=callback_query.data)
    await state.set_state(QuestionnaireBody.body_skin_sensitivity)
    await callback_query.message.answer(
        "17) Укажи степень чувствительности кожи тела:",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="Чувствительная", callback_data="sensitive")],
            [InlineKeyboardButton(text="Нормальная чувствительность", callback_data="normal")]
        ])
    )
    await callback_query.answer()

@router.callback_query(StateFilter(QuestionnaireBody.body_skin_sensitivity), lambda c: True)
async def process_body_skin_sensitivity(callback_query: CallbackQuery, state: FSMContext):
    await state.update_data(body_skin_sensitivity=callback_query.data)
    await state.set_state(QuestionnaireBody.body_skin_condition)
    pre_message_map = {
        "sensitive": "Я тоже чувствительна и к погоде, и к прикосновениям, и даже к плотной одежде 💔",
        "normal": "А ты счастливый человек, я вот довольно чувствительна и к погоде, и к прикосновениям, и даже к плотной одежде 💔"
    }
    await callback_query.message.answer(pre_message_map[callback_query.data])
    await callback_query.message.answer(
        "18) Как ты оцениваешь текущее состояние кожи на теле:",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="Сухость и шелушение", callback_data="dryness")],
            [InlineKeyboardButton(text="Потеря упругости", callback_data="loss_of_elasticity")],
            [InlineKeyboardButton(text="Целлюлит", callback_data="cellulite")],
            [InlineKeyboardButton(text="Акне/прыщи на теле", callback_data="acne")],
            [InlineKeyboardButton(text="Пигментация", callback_data="pigmentation")],
            [InlineKeyboardButton(text="Покраснения и раздражения", callback_data="redness")],
            [InlineKeyboardButton(text="Трещины на коже", callback_data="cracks")],
            [InlineKeyboardButton(text="Морщины", callback_data="wrinkles")],
            [InlineKeyboardButton(text="Нет особых проблем", callback_data="no_problems")]
        ])
    )
    await callback_query.answer()

@router.callback_query(StateFilter(QuestionnaireBody.body_skin_condition), lambda c: True)
async def process_body_skin_condition(callback_query: CallbackQuery, state: FSMContext):
    await state.update_data(body_skin_condition=callback_query.data)
    await state.set_state(QuestionnaireBody.body_hair_issues)
    await callback_query.message.answer(
        "19) Есть ли у тебя проблемы, связанные с волосами на теле?",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="Вросшие волосы", callback_data="ingrown_hairs")],
            [InlineKeyboardButton(text="Раздражение после депиляции", callback_data="irritation")],
            [InlineKeyboardButton(text="Нет проблем", callback_data="no_problems")]
        ])
    )
    await callback_query.answer()

@router.callback_query(StateFilter(QuestionnaireBody.body_hair_issues), lambda c: True)
async def process_body_hair_issues(callback_query: CallbackQuery, state: FSMContext):
    await state.update_data(body_hair_issues=callback_query.data)
    await state.set_state(QuestionnaireBody.body_attention_areas)
    pre_message_map = {
        "ingrown_hairs": "Сочувствую от всей души, но мы поработаем над этим🥺",
        "irritation": "Сочувствую от всей души, но мы поработаем над этим🥺",
        "no_problems": "Везунчик! Самый настоящий😜"
    }
    await callback_query.message.answer(pre_message_map[callback_query.data])
    await callback_query.message.answer(
        "20) Есть ли у тебя участки, которым нужно особое внимание (бо́льшее увлажнение или серьезные трещины)?",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="Локти", callback_data="elbows")],
            [InlineKeyboardButton(text="Колени", callback_data="knees")],
            [InlineKeyboardButton(text="Спина", callback_data="back")],
            [InlineKeyboardButton(text="Пятки", callback_data="heels")],
            [InlineKeyboardButton(text="Нет проблем", callback_data="no_problems")]
        ])
    )
    await callback_query.answer()

@router.callback_query(StateFilter(QuestionnaireBody.body_attention_areas), lambda c: True)
async def process_body_attention_areas(callback_query: CallbackQuery, state: FSMContext):
    await state.update_data(body_attention_areas=callback_query.data)
    await state.set_state(QuestionnaireBody.body_goals)
    await callback_query.message.answer(
        "21) Какие задачи ты могла бы себе поставить для улучшения кожи тела? Выбирай несколько вариантов\n"
        "1 - Увлажнение\n"
        "2 - Питание\n"
        "3 - Смягчение\n"
        "4 - Тонизирование\n"
        "5 - Отшелушивание\n"
        "6 - Антицеллюлитный эффект\n"
        "7 - Осветление кожи\n"
        "8 - Снятие раздражений\n"
        "9 - Защита кожи\n"
        "10 - Массаж\n"
        "11 - Убрать вросшие волосы\n"
        "12 - Убрать акне\n"
        "13 - Чтобы средство вкусно пахло",
        reply_markup=None
    )

@router.message(StateFilter(QuestionnaireBody.body_goals))
async def process_body_goals(message: types.Message, state: FSMContext):
    goals = [int(x) for x in message.text.replace(",", " ").split()]
    goal_descriptions = {
        "1": "Увлажнение",
        "2":  "Питание",
        "3" : "Смягчение",
        "4" : "Тонизирование",
        "5" : "Отшелушивание",
        "6" : "Антицеллюлитный эффект",
        "7" : "Осветление кожи",
        "8" : "Снятие раздражений",
        "9" : "Защита кожи",
        "10" : "Массаж",
        "11": "Убрать вросшие волосы",
        "12" : "Убрать акне",
        "13" : "Чтобы средство вкусно пахло",
    }
    goal_texts = [goal_descriptions[goal] for goal in goals if goal in goal_descriptions]
    await state.update_data(body_goals=goal_texts)
    user_data = await state.get_data()
    await message.answer(
        "Спасибо за участие в опросе! Вот ваши данные:\n"
        f"Тип кожи тела: {user_data['body_skin_type']}\n"
        f"Чувствительность кожи: {user_data['body_skin_sensitivity']}\n"
        f"Состояние кожи: {user_data['body_skin_condition']}\n"
        f"Проблемы с волосами: {user_data['body_hair_issues']}\n"
        f"Участки с особыми потребностями: {user_data['body_attention_areas']}\n"
        f"Цели ухода: {', '.join(map(str, user_data['body_goals']))}"
    )

    us_id = message.from_user.id

    user_data = {
                "body_skin_type": f"Тип кожи тела: {user_data['body_skin_type']}",
                "body_skin_sensitivity": f"Чувствительность кожи: {user_data['body_skin_sensitivity']}",
                "body_skin_condition": f"Состояние кожи: {user_data['body_skin_condition']}",
                "body_hair_issues": f"Проблемы с волосами: {user_data['body_hair_issues']}",
                "body_attention_areas": f"Участки с особыми потребностями: {user_data['body_attention_areas']}",
                "body_goals": f"Цели ухода: {', '.join(map(str, user_data['body_goals']))}",
            }
    # response = await send_user_data(us_id, user_data)
    await state.clear()

@router.callback_query(StateFilter(QuestionnaireHair.scalp_type), lambda c: True)
async def process_hair_scalp_type(callback_query: CallbackQuery, state: FSMContext):
    await state.update_data(hair_scalp_type=callback_query.data)
    await state.set_state(QuestionnaireHair.hair_thickness)
    await callback_query.message.answer(
        "23.1) Какой у тебя тип волос: толщина?",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="Тонкие", callback_data="thin"),
             InlineKeyboardButton(text="Средние", callback_data="medium"),
             InlineKeyboardButton(text="Густые", callback_data="thick")]
        ])
    )
    await callback_query.answer()

@router.callback_query(StateFilter(QuestionnaireHair.hair_thickness), lambda c: True)
async def process_hair_thickness(callback_query: CallbackQuery, state: FSMContext):
    await state.update_data(hair_thickness=callback_query.data)
    await state.set_state(QuestionnaireHair.hair_length)
    await callback_query.message.answer(
        "23.2) Какой у тебя тип волос: длина?",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="Короткие", callback_data="short"),
             InlineKeyboardButton(text="Средние", callback_data="medium"),
             InlineKeyboardButton(text="Длинные", callback_data="long")]
        ])
    )
    await callback_query.answer()

@router.callback_query(StateFilter(QuestionnaireHair.hair_length), lambda c: True)
async def process_hair_length(callback_query: CallbackQuery, state: FSMContext):
    await state.update_data(hair_length=callback_query.data)
    await state.set_state(QuestionnaireHair.hair_structure)
    await callback_query.message.answer(
        "23.3) Какой у тебя тип волос: структура?",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="Прямые", callback_data="straight"),
             InlineKeyboardButton(text="Вьющиеся", callback_data="wavy"),
             InlineKeyboardButton(text="Кудрявые", callback_data="curly")]
        ])
    )
    await callback_query.answer()

@router.callback_query(StateFilter(QuestionnaireHair.hair_structure), lambda c: True)
async def process_hair_structure(callback_query: CallbackQuery, state: FSMContext):
    await state.update_data(hair_structure=callback_query.data)
    await state.set_state(QuestionnaireHair.hair_condition)
    await callback_query.message.answer(
        "23.4) Какой у тебя тип волос: состояние?",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="Поврежденные", callback_data="damaged"),
             InlineKeyboardButton(text="Ломкие", callback_data="brittle")],
            [InlineKeyboardButton(text="Секущиеся кончики", callback_data="split_ends"),
             InlineKeyboardButton(text="Здоровые", callback_data="healthy")]
        ])
    )
    await callback_query.answer()

@router.callback_query(StateFilter(QuestionnaireHair.hair_condition), lambda c: True)
async def process_hair_condition(callback_query: CallbackQuery, state: FSMContext):
    await state.update_data(hair_condition=callback_query.data)
    await state.set_state(QuestionnaireHair.hair_goals)
    await callback_query.message.answer(
        "24) Какие цели ухода для тебя важны? Выбери один или несколько пунктов\n"
        "1. Увлажнение кожи головы и волос\n"
        "2. Восстановление структуры волос\n"
        "3. Борьба с перхотью\n"
        "4. Укрепление волос\n"
        "5. Уменьшение выпадения волос\n"
        "6. Стимуляция роста волос\n"
        "7. Защита окрашенных волос\n"
        "8. Термозащита",
        reply_markup=None
    )

@router.message(StateFilter(QuestionnaireHair.hair_goals))
async def process_hair_goals(message: types.Message, state: FSMContext):
    goals = [int(x) for x in message.text.replace(",", " ").split()]
    goal_descriptions = {
        1: "Увлажнение кожи головы и волос",
        2: "Восстановление структуры волос",
        3: "Борьба с перхотью",
        4: "Укрепление волос",
        5: "Уменьшение выпадения волос",
        6: "Стимуляция роста волос",
        7: "Защита окрашенных волос",
        8: "Термозащита"
    }
    goal_texts = [goal_descriptions[goal] for goal in goals if goal in goal_descriptions]
    await state.update_data(hair_goals=goal_texts)
    await state.set_state(QuestionnaireHair.washing_frequency)
    await message.answer(
        "25) Как часто ты моешь голову?",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="Каждый день", callback_data="daily"),
             InlineKeyboardButton(text="Каждые 2 дня", callback_data="every_2_days")],
            [InlineKeyboardButton(text="2 раза в неделю", callback_data="twice_weekly"),
             InlineKeyboardButton(text="1 раз в неделю", callback_data="once_weekly")]
        ])
    )

@router.callback_query(StateFilter(QuestionnaireHair.washing_frequency), lambda c: True)
async def process_washing_frequency(callback_query: CallbackQuery, state: FSMContext):
    await state.update_data(washing_frequency=callback_query.data)
    await state.set_state(QuestionnaireHair.current_products)
    await callback_query.message.answer(
        "26) Какие средства ты используешь сейчас? Можно выбрать несколько",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="Шампунь", callback_data="shampoo"),
             InlineKeyboardButton(text="Кондиционер", callback_data="conditioner")],
            [InlineKeyboardButton(text="Маска", callback_data="mask"),
             InlineKeyboardButton(text="Несмываемый уход", callback_data="leave_in_care")],
            [InlineKeyboardButton(text="Скраб или пилинг для кожи головы", callback_data="scrub")]
        ])
    )
    await callback_query.answer()

@router.callback_query(StateFilter(QuestionnaireHair.current_products), lambda c: True)
async def process_current_products(callback_query: CallbackQuery, state: FSMContext):
    await state.update_data(current_products=callback_query.data)
    await state.set_state(QuestionnaireHair.product_texture)
    await callback_query.message.answer(
        "27) Какую текстуру средства ты предпочитаешь?",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="Легкую", callback_data="light"),
             InlineKeyboardButton(text="Плотную", callback_data="dense")]
        ])
    )
    await callback_query.answer()

@router.callback_query(StateFilter(QuestionnaireHair.product_texture), lambda c: True)
async def process_product_texture(callback_query: CallbackQuery, state: FSMContext):
    await state.update_data(product_texture=callback_query.data)
    await state.set_state(QuestionnaireHair.sensitivity)
    pre_message_map = {
        "light": "Понимаю, тоже не люблю жирные средства и ощущение липкости 🙏",
        "dense": "Согласна, по плотной структуре будто больше кажется, что средство \"работает\" 😂"
    }
    await callback_query.message.answer(pre_message_map[callback_query.data])
    await callback_query.message.answer(
        "28) Есть ли у тебя аллергия или чувствительность к каким-либо компонентам на коже головы (например, сульфатам, эфирным маслам, ароматизаторам)?",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="Да", callback_data="yes"),
             InlineKeyboardButton(text="Нет", callback_data="no")]
        ])
    )
    await callback_query.answer()

@router.callback_query(StateFilter(QuestionnaireHair.sensitivity), lambda c: True)
async def process_sensitivity(callback_query: CallbackQuery, state: FSMContext):
    await state.update_data(sensitivity=callback_query.data)
    await state.set_state(QuestionnaireHair.styling_tools)
    await callback_query.message.answer(
        "29) Используешь ли ты термоукладочные приборы (фен, утюжок)?",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="Да, часто", callback_data="often"),
             InlineKeyboardButton(text="Иногда", callback_data="sometimes"),
             InlineKeyboardButton(text="Нет", callback_data="never")]
        ])
    )
    await callback_query.answer()

@router.callback_query(StateFilter(QuestionnaireHair.styling_tools), lambda c: True)
async def process_styling_tools(callback_query: CallbackQuery, state: FSMContext):
    await state.update_data(styling_tools=callback_query.data)
    user_data = await state.get_data()
    await callback_query.message.answer(
        "Спасибо за участие в опросе! Вот ваши данные:\n"
        f"Тип кожи головы: {user_data['hair_scalp_type']}\n"
        f"Толщина волос: {user_data['hair_thickness']}\n"
        f"Длина волос: {user_data['hair_length']}\n"
        f"Структура волос: {user_data['hair_structure']}\n"
        f"Состояние волос: {user_data['hair_condition']}\n"
        f"Цели ухода: {', '.join(map(str, user_data['hair_goals']))}\n"
        f"Частота мытья головы: {user_data['washing_frequency']}\n"
        f"Используемые средства: {user_data['current_products']}\n"
        f"Предпочитаемая текстура: {user_data['product_texture']}\n"
        f"Чувствительность: {user_data['sensitivity']}\n"
        f"Термоукладочные приборы: {user_data['styling_tools']}"
    )

    us_id = callback_query.from_user.id

    user_data = {
                "hair_scalp_type": f"Тип кожи головы: {user_data['hair_scalp_type']}",
                "hair_thickness": f"Толщина волос: {user_data['hair_thickness']}",
                "hair_length": f"Длина волос: {user_data['hair_length']}",
                "hair_structure": f"Структура волос: {user_data['hair_structure']}",
                "hair_condition": f"Состояние волос: {user_data['hair_condition']}",
                "hair_goals": f"Цели ухода: {', '.join(map(str, user_data['hair_goals']))}",
                "washing_frequency": f"Частота мытья головы: {user_data['washing_frequency']}",
                "current_products": f"Используемые средства: {user_data['current_products']}",
                "product_texture": f"Предпочитаемая текстура: {user_data['product_texture']}",
                "sensitivity": f"Чувствительность: {user_data['sensitivity']}",
                "styling_tools": f"Термоукладочные приборы: {user_data['styling_tools']}",
            }
    # response = await send_user_data(us_id, user_data)
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
        "<b>Часть 1/4</b> 🟢⚪️⚪️⚪️\n"
        "<b>11 вопросов о тебе </b>\n\n"
        "Имя, при составлении твоей индивидуальной рекомендации того или иного средства – я должна знать всё о твоем стиле жизни, фототипе и предпочтениях. "
        "Чтобы не получилось так, что я для тебя одобрила средство, которое абсолютно не подходит тебе по этическим предпочтениям."
    )
    await bot.send_message(us_id, text)
    await state.set_state(Questionnaire2.intro_answer)
    await callback_query.answer()


@router.callback_query(lambda c: c.data == 'questionnaire_face')
async def process_questionnaire_face(callback_query: CallbackQuery, state: FSMContext):
    await state.set_state(QuestionnaireFace.skin_type)
    await callback_query.message.answer(
        "<b> Часть 2/4 🟢🟢⚪️⚪️\n"
        "4 вопроса о твоём чудесном лице </b>\n"
        "Спасибо за честные ответы, перейдем к “знакомству” с твоей кожей 🙌\n\n"
        "12) Какой у тебя тип кожи на лице?",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="Нормальная", callback_data="normal"),
             InlineKeyboardButton(text="Сухая", callback_data="dry")],
            [InlineKeyboardButton(text="Жирная", callback_data="oily"),
             InlineKeyboardButton(text="Комбинированная", callback_data="combination")]
        ])
    )
    await callback_query.answer()


@router.callback_query(lambda c: c.data == 'questionnaire_body')
async def process_questionnaire_body(callback_query: CallbackQuery, state: FSMContext):
    await state.set_state(QuestionnaireBody.body_skin_type)
    await callback_query.message.answer(
        "<b> Часть 3/4 🟢🟢🟢⚪️\n"
        "6 вопросов о твоем теле </b>\n"
        "С лицом закончили, это была самая сложная часть, теперь к самой “основной” части твоего прекрасного тела!\n\n"
        "16) Какой у тебя тип кожи тела?",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="Нормальная", callback_data="normal"),
             InlineKeyboardButton(text="Сухая", callback_data="dry")],
            [InlineKeyboardButton(text="Жирная", callback_data="oily"),
             InlineKeyboardButton(text="Комбинированная", callback_data="combination")]
        ])
    )
    await callback_query.answer()


@router.callback_query(lambda c: c.data == 'questionnaire_hair')
async def process_questionnaire_hair(callback_query: CallbackQuery, state: FSMContext):
    await state.set_state(QuestionnaireHair.scalp_type)
    await callback_query.message.answer(
        "<b>Часть 4/4 🟢🟢🟢🟢\n"
        "8 вопросов о волосах и коже головы </b> 💆‍♀️\n"
        "Ну, и немного осталось узнать про “спусти свои косы, Рапунцель” твои волосы)\n\n"
        "22) Какой у тебя тип кожи головы?",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="Нормальная", callback_data="normal"),
             InlineKeyboardButton(text="Сухая", callback_data="dry")],
            [InlineKeyboardButton(text="Жирная", callback_data="oily"),
             InlineKeyboardButton(text="Комбинированная", callback_data="combination")],
            [InlineKeyboardButton(text="Чувствительная", callback_data="sensitive")]
        ])
    )
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
        text="Опросник_2", callback_data="questionaire2")], [InlineKeyboardButton(
        text="Опросник_Лицо", callback_data="questionnaire_face")], [InlineKeyboardButton(
        text="Опросник_Тело", callback_data="questionnaire_body")], [InlineKeyboardButton(
        text="Опросник_Волосы", callback_data="questionnaire_hair")]]
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
