import asyncio
import re
import aiogram
import random
import os
import logging
from aiogram import Bot, Dispatcher, types
import openai
import asyncio
import logging
import sys
from datetime import datetime
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
from stickerlist import STICKERLIST
import shelve
import json

from functions import *
from longtexts import *

BOT_TOKEN = os.getenv("BOT_TOKEN")
OPENAI_KEY = os.getenv("OPENAI_KEY")
ASSISTANT_ID = os.getenv("RECOGNIZE_MAKEUP_ASS")
ASSISTANT_ID_2 = os.getenv("FIND_PRODUCT_ASS")
YAPP_ASS = os.getenv("YAPP_ASS")

GENERAL_ANALYSIS_ASS = os.getenv("GENERAL_ANALYSIS_ASS")
NOT_FOUND_ASS = os.getenv("NOT_FOUND_ASS")

CONSIST_ANALYSIS_ASS = os.getenv("CONSIST_ANALYSIS_ASS")
ETHICS_ANALYSIS_ASS = os.getenv("ETHICS_ANALYSIS_ASS")
ACTIVE_ANALYSIS_ASS = os.getenv("ACTIVE_ANALYSIS_ASS")
FUNCTIONS_ANALYSIS_ASS = os.getenv("FUNCTIONS_ANALYSIS_ASS")

ANALYSIS_G_FACE_ASS = os.getenv("ANALYSIS_G_FACE_ASS")
ANALYSIS_G_BODY_ASS = os.getenv("ANALYSIS_G_BODY_ASS")
ANALYSIS_G_HAIR_ASS = os.getenv("ANALYSIS_G_HAIR_ASS")

ANALYSIS_P_FACE_ASS = os.getenv("ANALYSIS_P_FACE_ASS")
ANALYSIS_P_BODY_ASS = os.getenv("ANALYSIS_P_BODY_ASS")
ANALYSIS_P_HAIR_ASS = os.getenv("ANALYSIS_P_HAIR_ASS")


USER_ANAL_ASS = os.getenv("USER_INFO_AND_GOALS_ASS")

TOKEN = BOT_TOKEN
arrow_back = "Назад ⬅️" #⬅️
arrow_menu = "В меню 🔼" #🆕⏏️

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
    recognition_2 = State()
    yapp = State()
    menu = State()
    yapp_with_xtra = State()
    transfer = State()

class ImageUploadState(StatesGroup):
    waiting_for_image = State()

class Questionnaire(StatesGroup):
    name = State()
    annoying_shit = State()
    mail = State()
    intro = State()
    age = State()
    gender = State()
    location = State()
    allergy = State()
    lifestyle = State()
    user_lifestyle = State()
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

checkbox_states = {
    "option_1": False,
    "option_2": False,
}


@router.message(CommandStart())
async def command_start_handler(message: Message, state: FSMContext) -> None:
    await ensure_user(message)
    await log_user_message(message)

    await state.update_data(full_sequence=True)
    buttons = [[InlineKeyboardButton(text="Пройти опросник", callback_data="all_questionnaires")]]
    keyboard = InlineKeyboardMarkup(inline_keyboard=buttons)
    step0txt = "Привет, я задам тебе пару вопросов чтобы составить твой профиль"
    await message.answer(step0txt, reply_markup=keyboard)

@router.message(Command("checkbox"))
async def start(message: types.Message):
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(
            text=f"✅ Опция 1" if checkbox_states["option_1"] else "☐ Опция 1",
            callback_data="toggle_option_1"
        )],
        [InlineKeyboardButton(
            text=f"✅ Опция 2" if checkbox_states["option_2"] else "☐ Опция 2",
            callback_data="toggle_option_2"
        )],
        [InlineKeyboardButton(text="Подтвердить", callback_data="confirm")]
    ])
    
    await message.answer("Выберите опции:", reply_markup=keyboard)

@router.message(Command("mail_input_debug"))
async def devmenu_handler(message: Message, state: FSMContext) -> None:
    await state.set_state(Questionnaire.mail)
    await message.answer("Пиши почту")

@router.message(Command("recog_2_test"))
async def devmenu_handler(message: Message, state: FSMContext) -> None:
    isActive1 = await check_is_active_state(message.from_user.id, state)
    isActive = int(isActive1)
    if isActive < 2:
        if isActive<1:
            await message.answer("Пожалуйста, пройдите анкету с самого начала  через ввод \n/start 💚")
            return
        bttns = [
            [InlineKeyboardButton(text="Оплатить", url="https://myavocadobot.ru/")],
            [InlineKeyboardButton(text="-40% по Золотому билету", url="https://myavocadobot.ru/")],
            [InlineKeyboardButton(text="Уже оплачено, ввести почту", callback_data="retry_mail")],
            [InlineKeyboardButton(text="🆘 Написать в поддержку", url="t.me/ai_care")],
            [InlineKeyboardButton(text="В меню 🔼", callback_data="menu")]
            ]
        await message.answer("Кажется, у вас еще нет подписки.\n\nКупить бота можно с супер скидкой -20% прямо сейчас", reply_markup=(InlineKeyboardMarkup(inline_keyboard=bttns)))
        asyncio.create_task(log_bot_response(f"СТАТУС ПОДПИСКИ {isActive}", message.from_user.id))
        return
    await state.set_state(UserState.recognition_2)
    await message.answer("Кажется у нас не получилось распознать этот продукт. Введите полный состав через запятую \n\nПример:\n<i>aqua, parfum/fragrance, centaurea cyanus flower water,  hexyl cinnamal, glycerin, sodium benzoate, linalool, citric acid, potassium sorbate, vanilla planifolia fruit extract.</i>")

@router.callback_query(lambda c: c.data == 'recognition_2_start')
async def devmenu_handler(callback_query: CallbackQuery, state: FSMContext) -> None:
    isActive1 = await check_is_active_state(callback_query.from_user.id, state)
    isActive = int(isActive1)
    if isActive < 2:
        await callback_query.answer()
        if isActive<1:
            await callback_query.message.answer("Пожалуйста, пройдите анкету с самого начала через ввод \n/start 💚")
            return
        bttns = [
            [InlineKeyboardButton(text="Оплатить", url="https://myavocadobot.ru/")],
            [InlineKeyboardButton(text="-40% по Золотому билету", url="https://myavocadobot.ru/")],
            [InlineKeyboardButton(text="Уже оплачено, ввести почту", callback_data="retry_mail")],
            [InlineKeyboardButton(text="🆘 Написать в поддержку", url="t.me/ai_care")],
            [InlineKeyboardButton(text="В меню 🔼", callback_data="menu")]
            ]
        await callback_query.message.answer("Кажется, у вас еще нет подписки.\n\nКупить бота можно с супер скидкой -20% прямо сейчас", reply_markup=(InlineKeyboardMarkup(inline_keyboard=bttns)))
        asyncio.create_task(log_bot_response(f"СТАТУС ПОДПИСКИ {isActive}", callback_query.from_user.id))
        return
    await state.set_state(UserState.recognition_2)
    await callback_query.message.answer("Кажется у нас не получилось распознать этот продукт. Введите полный состав через запятую \n\nПример:\n<i>aqua, parfum/fragrance, centaurea cyanus flower water,  hexyl cinnamal, glycerin, sodium benzoate, linalool, citric acid, potassium sorbate, vanilla planifolia fruit extract.</i>")


@router.callback_query(lambda c: c.data == 'retry_mail')
async def devmenu_handler(callback_query: CallbackQuery, state: FSMContext) -> None:
    await state.set_state(Questionnaire.mail)
    await callback_query.message.answer("Пиши почту")


@router.message(Command("menu"))
async def menu_handler(message: Message, state: FSMContext) -> None:
    await state.set_state(UserState.menu)
    await state.update_data(full_sequence=False)
    buttons = [
        [InlineKeyboardButton(text="Анализ состава 🔍", callback_data="analysis")],
        [InlineKeyboardButton(text="Мой Avocado Box  💚", callback_data="avo_box_menu")],
        [InlineKeyboardButton(text="Спросить Avocado Ai🥑", callback_data="setstate_yapp")],
        [InlineKeyboardButton(text="Маркировка 🔍", callback_data="markings")],
        [InlineKeyboardButton(text="Настройки ⚙️:", callback_data="settings")],
        ]
    keyboard = InlineKeyboardMarkup(inline_keyboard=buttons)
    step0txt = "Меню"
    await message.answer(step0txt, reply_markup=keyboard)

@router.callback_query(lambda c: c.data == 'menu')
async def menu_cb_handler(callback_query: CallbackQuery, state: FSMContext):
    await state.set_state(UserState.menu)
    await state.update_data(full_sequence=False)
    buttons = [
        [InlineKeyboardButton(text="Анализ состава 🔍", callback_data="analysis")],
        [InlineKeyboardButton(text="Мой Avocado Box  💚", callback_data="avo_box_menu")],
        [InlineKeyboardButton(text="Спросить Avocado Ai🥑", callback_data="setstate_yapp")],
        [InlineKeyboardButton(text="Маркировка 🔍", callback_data="markings")],
        [InlineKeyboardButton(text="Настройки ⚙️:", callback_data="settings")],
        ]
    keyboard = InlineKeyboardMarkup(inline_keyboard=buttons)
    step0txt = "Меню"
    await callback_query.message.edit_text(step0txt, reply_markup=keyboard)


@router.message(Command("1"))
async def handler_1(message: types.Message, state: FSMContext):
    text = "Отправьте в чат фото 📸, <i>текст</i> или аудио 🎤 вашего средства.\nНапример:\n<i>Weleda Skin food, крем для лица</i>\n\nВ моей базе пока только средства для лица, тела и волос. "
    await message.answer(text)
    await state.set_state(UserState.recognition)

@router.message(Command("2"))
async def handler_2(message: types.Message, state: FSMContext):
    await state.update_data(full_sequence=False)
    buttons = [
        [InlineKeyboardButton(text="Digital Avocado Box 🥑", callback_data="avo_box")],
        [InlineKeyboardButton(text="Промокоды 💥", callback_data="avo_promo")],
        ]
    keyboard = InlineKeyboardMarkup(inline_keyboard=buttons)
    step0txt = "В этом разделе мы собрали все скидки, созданные специально для вас! 😍 \nС чего начнем?"
    await message.answer(step0txt, reply_markup=keyboard)

@router.message(Command("3"))
async def handler_3(message: types.Message, state: FSMContext):
    await state.set_state(UserState.yapp)
    text = "<b>Хотите узнать больше о правильном уходе? \nЗадайте мне любой вопрос!</b> \nНапишите его текстом ✏️ или запишите голосовое сообщение 🎤.\n\n   Например: Как использовать сыворотку с ретинолом? или Можно ли использовать крем с мочевиной для рук – на тело?"#\n Я всегда готов помочь! 🥑
    await message.answer(text)

@router.message(Command("4"))
async def handler_4(message: types.Message, state: FSMContext):
    buttons = [
        [InlineKeyboardButton(text="Экологические и этические обозначения 🐰", callback_data="markings_1")],
        [InlineKeyboardButton(text="Срок годности и хранение 📅", callback_data="markings_2")],
        [InlineKeyboardButton(text="Утилизация ♻️", callback_data="markings_3")],
        [InlineKeyboardButton(text="Стандарты и сертификация ✅", callback_data="markings_4")],
        [InlineKeyboardButton(text="Прямоугольники на тубе 🛑", callback_data="markings_5")],
        [InlineKeyboardButton(text="Как проверить состав🔍", callback_data="markings_6")],
        [InlineKeyboardButton(text=arrow_menu, callback_data="menu")]
    ]
    keyboard = InlineKeyboardMarkup(inline_keyboard=buttons)
    text = "На упаковках косметических средств можно встретить множество символов и значков 🔃, которые информируют о составе продукта, его безопасности 🚫, способах использования и утилизации♻️.\n\nПонимание этих обозначений поможет сделать осознанный выбор и правильно использовать продукцию.\n\n<blockquote>Ниже представлены основные символы, их изображения и расшифровки.</blockquote>\n\nКакой раздел вам интересен?"
    await message.answer(text, reply_markup=keyboard)

@router.message(Command("5"))
async def handler_5(message: types.Message, state: FSMContext):
    buttons = [
        [InlineKeyboardButton(text="🔖 Как пользоваться ботом", callback_data="explain_4")],
        [InlineKeyboardButton(text="📖 Обновить анкету", callback_data="settings_questionaire")],
        [InlineKeyboardButton(text="💰Условия подписки:", callback_data="settings_sub")],
        [InlineKeyboardButton(text="🆘Служба заботы :", url="t.me/ai_care")],
        [InlineKeyboardButton(text=arrow_menu, callback_data="menu")]
    ]
    keyboard = InlineKeyboardMarkup(inline_keyboard=buttons)
    text = "Настройки ⚙️:"
    await message.answer(text, reply_markup=keyboard)





# @router.message(Command("devmenu"))
# async def devmenu_handler(message: Message, state: FSMContext) -> None:
#     await state.update_data(full_sequence=False)
#     buttons = [
#         [InlineKeyboardButton(text="Мой Avocado Box  💚", callback_data="avo_box")],
#         [InlineKeyboardButton(text="Промокоды 💥", callback_data="avo_promo")],
#         ]
#     keyboard = InlineKeyboardMarkup(inline_keyboard=buttons)
#     step0txt = "В этом разделе мы собрали все скидки, созданные специально для вас! 😍 \nС чего начнем?"
#     await message.answer(step0txt, reply_markup=keyboard)

@router.callback_query(lambda c: c.data == 'avo_box_menu')
async def devmenu_handler_cb(callback_query: CallbackQuery, state: FSMContext) -> None:
    await state.update_data(full_sequence=False)
    buttons = [
        [InlineKeyboardButton(text="Digital Avocado Box 🥑", callback_data="avo_box")],
        [InlineKeyboardButton(text="Промокоды 💥", callback_data="avo_promo")],
        ]
    keyboard = InlineKeyboardMarkup(inline_keyboard=buttons)
    step0txt = "В этом разделе мы собрали все скидки, созданные специально для вас! 😍 \nС чего начнем?"
    await callback_query.message.edit_text(step0txt, reply_markup=keyboard)

@router.callback_query(lambda c: c.data == 'avo_box')
async def process_avo_box(callback_query: CallbackQuery, state: FSMContext):
    buttons = [[InlineKeyboardButton(text="Получить промокоды", callback_data="avo_box_2")]]
    text="<b>Соберите свой идеальный Avocado Box прямо сейчас!</b>\n\nМожно купить все продукты сразу или по-отдельности;\n\nРегулярные подборки премиальной натуральной косметики со скидками до 50% – тестируйте лучшие продукты по суперценам.\n\nГарантия безопасности и качества от Авокадской Конторы 💚\n\n Никаких случайных баночек – только идеальный бьюти-бокс, который подходит именно вашей коже!"
    # text = "Соберите свой идеальный My Avocado Box AI!\n\nВыбирайте только то, что действительно хочется.\n\nРегулярные подборки премиальной натуральной косметики со скидками до 50% – тестируйте лучшие продукты по суперценам.\n\nГарантия безопасности и качества от Авокадской Конторы 💚\n\nНикаких случайных баночек – только идеальный бьюти-бокс, который подходит именно вашей коже!"
    await callback_query.message.edit_text(text, reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons))

@router.callback_query(lambda c: c.data == 'avo_promo')
async def process_avo_promo(callback_query: CallbackQuery, state: FSMContext):
    buttons = [[InlineKeyboardButton(text="Получить промокоды", callback_data="avo_promo_2")]]
    text = "<b>Мы объединили все лучшие эко-бренды – друзей My Avocado Box, чтобы у вас всегда был доступ к безопасной косметике по самой приятной цене.</b>\n\n 🌿 Бренды готовы радовать тебя натуральными и проверенными продуктами.\n\n 💚Постоянные скидки 15-20% – эксклюзивно для наших подписчиков.\n\n ✨ Лучшее из мира эко-косметики всегда доступно в один клик.\n\nВыбирайте, пробуйте, влюбляйтесь – с Avocado Bot вы всегда в выигрыше!"
    # text = "Скидки, созданные специально для вас!\n\nМы объединили все лучшие эко-бренды – друзей My Avocado Box, чтобы у вас всегда был доступ к безопасной косметике по самой приятной цене. \n\n🌿Лучшие бренды готовы радовать тебя натуральными и проверенными продуктами.\n\n💚Постоянные скидки 15-20% – эксклюзивно для наших подписчиков.\n\n✨ Лучшее из мира эко-косметики всегда доступно в один клик.\n\nВыбирайте, пробуйте, влюбляйтесь – с Avocado Bot вы всегда в выигрыше!"
    await callback_query.message.edit_text(text, reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons))

@router.callback_query(lambda c: c.data == 'avo_box_2')
async def process_avo_box_2(callback_query: CallbackQuery, state: FSMContext):
    text1 = "Весенний выпуск Avocado Box 🌷\n\n16 идеальных продуктов от безопасных брендов со скидкой до -50%"
    text3 = ""
    buttons = [
        [InlineKeyboardButton(text="Написать в поддержку 🆘", url="t.me/ai_care")],
        [InlineKeyboardButton(text=arrow_menu, callback_data="menu")]
    ]
    await callback_query.message.answer_photo(caption=text1, photo="AgACAgIAAxkBAAMIaCeYc8Ex1KuJL3xB4q4cUPcUIcIAAiolMhuJjEBJ_yJ7wv_rgcIBAAMCAAN5AAM2BA")
    await callback_query.message.answer_media_group(avo_box_media_gr_1)
    await callback_query.message.answer(avo_box_text_long_2, disable_web_page_preview=True)
    await callback_query.message.answer_media_group(avo_box_media_gr_2)
    await callback_query.message.answer(avo_box_text_long_3, disable_web_page_preview=True, reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons))

@router.callback_query(lambda c: c.data == 'avo_promo_2')
async def process_avo_promo_2(callback_query: CallbackQuery, state: FSMContext):
    buttons = [
        [InlineKeyboardButton(text="Написать в поддержку 🆘", url="t.me/ai_care")],
        [InlineKeyboardButton(text=arrow_menu, callback_data="menu")]
    ]
    await callback_query.message.answer_media_group(promo_media_gr)
    # await callback_query.message.edit_text(promo_text, disable_web_page_preview=True, reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons))
    await callback_query.message.answer(promo_text, disable_web_page_preview=True, reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons))

@router.callback_query(lambda c: c.data.startswith('vote_'))
async def main_process_votes(callback_query: CallbackQuery, state: FSMContext):
    await callback_query.answer()
    vote_num = callback_query.data.split("_")[1]
    await callback_query.message.edit_text("Спасибо за участие в опросе", reply_markup=None)
    succesfull_count = await get_user_vote(callback_query.from_user.id, vote_num)
    asyncio.create_task(log_bot_response(f"user voted {vote_num}, successresponse: {succesfull_count}", callback_query.from_user.id))












######################################## QUESTIONNAIRE
@router.message(StateFilter(Questionnaire.name))
async def process_name(message: types.Message, state: FSMContext):
    await state.update_data(name=message.text)
    text = f"Приятно познакомиться, {message.text}!  🌿 \nЯ здесь, чтобы помочь вам с анализом состава косметики и рассказать, что именно в ней содержится и как работает.\n"    
    "На основе информации о вашей коже и образе жизни я подберу те средства, которые подойдут именно <b>вам</b>.  Могу порекомендовать, какие продукты стоит попробовать, а какие лучше оставить на полке.  Всё просто — вместе мы сделаем выбор безопасным и эффективным и подходящим именно вам!"
    keyboard = InlineKeyboardMarkup(
            inline_keyboard=[
                [InlineKeyboardButton(text="Как ты работаешь, Avocado?", callback_data="annoying_1")]])
    await state.set_state(Questionnaire.annoying_shit)
    await message.answer(text, reply_markup=keyboard)

@router.callback_query(StateFilter(Questionnaire.annoying_shit), lambda c: c.data.startswith("annoying"))
async def process_annoying_1(callback_query: CallbackQuery, state: FSMContext):
    await callback_query.answer()
    if callback_query.data == "annoying_1":
        await callback_query.message.answer("Если нужно, я могу подробнее рассказать, что именно я умею, как подбираю рекомендации и какие магические формулы использую в своей работе. 🧖‍♀️\n\nAvocado всегда радо поделиться всеми секретами красоты и ухода — просто дайте знать!")
        await process_about_avocado(callback_query, state)
    elif callback_query.data == "annoying_2":
        keyboard = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="Хочу", callback_data="annoying_3")]])
        await callback_query.message.answer_video(video=video_1, caption=vid_text_1, reply_markup=keyboard)
    elif callback_query.data == "annoying_3":
        keyboard = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="Вау!", callback_data="annoying_4")]])
        await callback_query.message.answer_video(video=video_2, caption=vid_text_2, reply_markup=keyboard)
    elif callback_query.data == "annoying_4":
        keyboard = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="Скорее начать", callback_data="annoying_5")]])
        await state.set_state(Questionnaire.intro)
        await callback_query.message.answer_video(video=video_3, caption=vid_text_3, reply_markup=keyboard)

@router.message(StateFilter(Questionnaire.mail))
async def main_process_mail(message: Message, state: FSMContext):
    pattern = r'^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$'
    if re.match(pattern, message.text):
        await process_mail(message, state)
    else:
        await message.answer("Какая у тебя электронная почта?\nПожалуйста введи ту же почту, что и при оплате 🙏")


@router.callback_query(StateFilter(Questionnaire.intro), lambda c: c.data == 'annoying_5')
async def process_questionnaire_yapp(callback_query: CallbackQuery, state: FSMContext):
    await callback_query.message.answer(
        "Чтобы проанализировать состав баночки максимально точно, мне нужно немного больше узнать о вас! \n"
        "🤔 Давайте заполним подробную анкету — это поможет мне лучше понять ваши потребности и подобрать самые подходящие продукты именно вам. Готовы?",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="Да", callback_data="agreement_yes"),
             InlineKeyboardButton(text="Нет", callback_data="agreement_no")]
        ])
    )
    await callback_query.answer()

                                                  
@router.callback_query(StateFilter(Questionnaire.intro), lambda c: c.data.startswith("agreement_"))
async def process_agreement(callback_query: types.CallbackQuery, state: FSMContext):
    us_id = callback_query.from_user.id
    print("hit_agreement")
    if callback_query.data == "agreement_no":
        text = ( 
            "Понимаю, что у вас может быть много дел, но без информации о вас, к сожалению, я не смогу подобрать подходящее средство. 😞 \n\n"  
            "Давайте вернемся к этому, когда вам будет удобнее? Avocado всегда рядом!"
        )

        await callback_query.message.edit_text(text)
        await state.clear()

    elif callback_query.data == "agreement_yes":
        keyboard = InlineKeyboardMarkup(
            inline_keyboard=[
                [InlineKeyboardButton(text="Это точно, давай начинать!", callback_data="lesgo")]
            ]
        )
        user_data = await state.get_data()
        text = (
            "<b>Часть 1/4</b> 🟢⚪️⚪️⚪️\n"
            "<b>11 вопросов о тебе </b>\n\n"
            f"{user_data['name']}, чтобы составить для вас идеальную рекомендацию, мне нужно узнать как можно больше о вашем образе жизни, фототипе и предпочтениях.  🌱 "
            "Ведь важно, чтобы предложенное средство полностью соответствовало вашим потребностям и не оказалось неподходящим. Готовы сделать всё как следует? Давайте начнём!"
        )

        await callback_query.message.edit_text(text, reply_markup=keyboard)

@router.callback_query(StateFilter(Questionnaire.intro), lambda c: c.data == 'lesgo')
async def process_questionnaire_lesgo(callback_query: CallbackQuery, state: FSMContext):

    await state.set_state(Questionnaire.age)
    await callback_query.message.edit_text(
        "1) Начнем с простого. Сколько вам годиков?   \n\nНапишите только число. \n<i>Например, 35</i>"
    )
    await callback_query.answer()

@router.message(StateFilter(Questionnaire.age))
async def process_age(message: types.Message, state: FSMContext):
    current_data = await state.get_data()
    print(f"Updated state in process_all_questionnaires: {current_data}")
    await state.update_data(age=message.text)
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="Женский", callback_data="gender_female")],
            [InlineKeyboardButton(text="Мужской", callback_data="gender_male")]
        ]
    )

    pattern = r'^(0|[1-9]\d?|1[01]\d|120)$'
    if re.match(pattern, message.text): 
        await state.set_state(Questionnaire.gender)
        await message.answer("Принято")
        await message.answer("2) Ваш пол пол", reply_markup=keyboard)
    else:
        await message.answer("Не поняла. Попробуй ввести число  ещё раз без дополнительных символов и букв.")

@router.callback_query(StateFilter(Questionnaire.gender), lambda c: c.data.startswith("gender_"))
async def process_gender(callback_query: types.CallbackQuery, state: FSMContext):
    gender = "Женский" if callback_query.data == "gender_female" else "Мужской"
    await state.update_data(gender=gender)
    await state.set_state(Questionnaire.location)
    await callback_query.message.edit_text(
        "3) Для расчёта времени года и климатических условий вашего проживания мне нужно знать, где вы находитесь большую часть времени.\n\n"
        "Напишите, пожалуйста, вот в таком формате: \n<i>Санкт-Петербург</i>"
    )
    
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
    pattern = r'^[А-Яа-яЁё\s-]+$'
    if re.match(pattern, message.text):
        await state.set_state(Questionnaire.allergy)
        await message.answer("Благодарю!")
        await message.answer("4) Есть ли у вас склонность к аллергическим реакциям?", reply_markup=keyboard)
    else:
        await message.answer("Не поняла. Попробуй ввести еще раз.")
        
@router.callback_query(StateFilter(Questionnaire.allergy), lambda c: c.data.startswith("allergy_"))
async def process_allergy(callback_query: types.CallbackQuery, state: FSMContext):
    allergy = "Да" if callback_query.data == "allergy_yes" else "Нет"
    await state.update_data(allergy=allergy)
    await state.set_state(Questionnaire.lifestyle)
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="Часто нахожусь на солнце", callback_data="lifestyle_1")],
            [InlineKeyboardButton(text="Работаю в сухом помещении (с кондиционером или отоплением)", callback_data="lifestyle_2")],
            [InlineKeyboardButton(text="Сидячая и неактивная работа", callback_data="lifestyle_3")],
            [InlineKeyboardButton(text="Часто занимаюсь спортом или физической активностью (высокая потливость),  хорошо загорает", callback_data="lifestyle_4")],
            [InlineKeyboardButton(text="Мой образ жизни не подходит ни под одно из этих описаний", callback_data="lifestyle_5")],
            ]
    )
    await callback_query.message.answer(
        "5) Какие из перечисленных вариантов наиболее точно описывают ваш образ жизни?",
            reply_markup=keyboard
        )
    await callback_query.answer()

@router.callback_query(StateFilter(Questionnaire.lifestyle),lambda c: c.data == 'lifestyle_5')
async def process_lifestyle_5(callback_query: types.CallbackQuery, state: FSMContext):
    await callback_query.message.answer("Могу тогда попросить вас описать своими словами?")
    await state.set_state(Questionnaire.user_lifestyle)
    await callback_query.answer()

@router.message(StateFilter(Questionnaire.user_lifestyle))
async def process_user_lifestyle(message: types.Message, state: FSMContext):
    await state.update_data(lifestyle=message.text)
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="1 — Очень светлая кожа, сразу краснеет", callback_data="phototype_1")],
            [InlineKeyboardButton(text="2 — Светлая кожа, загорает с трудом", callback_data="phototype_2")],
            [InlineKeyboardButton(text="3 — Светлая/средняя кожа, редко сгорает", callback_data="phototype_3")],
            [InlineKeyboardButton(text="4 — Средняя/оливковая кожа,  хорошо загорает", callback_data="phototype_4")],
            [InlineKeyboardButton(text="5 — Темная кожа, не сгорает", callback_data="phototype_5")],
            [InlineKeyboardButton(text="6 — Очень темная кожа, никогда не сгорает", callback_data="phototype_6")],
            ]
    )
    await state.set_state(Questionnaire.phototype)
    await message.answer("6) Теперь задачка поинтереснее. Давайте определим ваш фототип кожи? Это совсем не сложно — всё кратко и понятно описали:",
        reply_markup=keyboard
    )

@router.callback_query(StateFilter(Questionnaire.lifestyle))
async def process_lifestyle(callback_query: types.CallbackQuery, state: FSMContext):
    await callback_query.answer()
    lifestyle_nums = [int(x) for x in callback_query.data.replace("lifestyle_", "").split()]
    lifestlyle_nums_answer_map = {
        1:"Avocado напоминание : солнце может быть как другом, так и врагом. Но SPF — всегда ваш верный союзник!☀️",
        2:"Это частая проблема, но мы знаем, как с ней бороться 💨",
        3:"На правах доброго совета: постарайтесь добавлять в свой день немного активности, даже на рабочем месте 🧘‍♀️\nНапример, прямо сейчас вытяните руки над головой , потянитесь макушкой вверх и почувствуйте как выпрямляется ваш позвоночник. Хорошо, правда?",
        4:"Так держать! Вы просто умника! Avocado за вас радо!💚",
        5:"Могу тогда попросить вас описать своими словами?",
    }
    for lifestyle in lifestyle_nums:
        lifestyle_response = lifestlyle_nums_answer_map[lifestyle]
        await callback_query.message.answer(lifestyle_response)
    lifestyle_descriptions = {
        1 : "Часто нахожусь на солнце",
        2 :  "Работаю в сухом помещении (с кондиционером или отоплением)",
        3 : "Сидячая и неактивная работа",
        4 : "Часто занимаюсь спортом или физической активностью (высокая потливость)",
        5 : "Мой образ жизни не подходит ни под одно из этих описаний",
    }
    lifestyle_texts = [lifestyle_descriptions[lifestyle] for lifestyle in lifestyle_nums if lifestyle in lifestyle_descriptions]
    await state.update_data(lifestyle=lifestyle_texts)

    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            # [InlineKeyboardButton(text=str(i), callback_data=f"phototype_{i}") for i in range(1, 7)]
            [InlineKeyboardButton(text="1 — Очень светлая кожа, сразу краснеет", callback_data="phototype_1")],
            [InlineKeyboardButton(text="2 — Светлая кожа, загорает с трудом", callback_data="phototype_2")],
            [InlineKeyboardButton(text="3 — Светлая/средняя кожа, редко сгорает", callback_data="phototype_3")],
            [InlineKeyboardButton(text="4 — Средняя/оливковая кожа,  хорошо загорает", callback_data="phototype_4")],
            [InlineKeyboardButton(text="5 — Темная кожа, не сгорает", callback_data="phototype_5")],
            [InlineKeyboardButton(text="6 — Очень темная кожа, никогда не сгорает", callback_data="phototype_6")],
            ]
    )
    await state.set_state(Questionnaire.phototype)
    await callback_query.message.answer("6) Теперь задачка поинтереснее. Давайте определим ваш фототип кожи? Это совсем не сложно — всё кратко и понятно описали:",
        # "6) Теперь нужно определить фототип твоей кожи:\n"
        # "1 — Очень светлая кожа, не загорает, сразу краснеет\n"
        # "2 — Светлая кожа, легко сгорает, загорает с трудом\n"
        # "3 — Светлая/средняя кожа, редко сгорает, загорает постепенно\n"
        # "4 — Средняя/оливковая кожа, редко сгорает, хорошо загорает\n"
        # "5 — Темная кожа, практически не сгорает, быстро загорает\n"
        # "6 — Очень темная кожа, никогда не сгорает\n",
        reply_markup=keyboard
    )

@router.callback_query(StateFilter(Questionnaire.phototype), lambda c: c.data.startswith("phototype_"))
async def process_phototype(callback_query: types.CallbackQuery, state: FSMContext):
    phototype = callback_query.data.split("_")[1]
    phototype_map = {
        "1": "Очень светлая кожа, не загорает, сразу краснеет",
        "2": "Светлая кожа, легко сгорает, загорает с трудом",
        "3": "Светлая/средняя кожа, редко сгорает, загорает постепенно",
        "4": "Средняя/оливковая кожа, редко сгорает, хорошо загорает",
        "5": "Темная кожа, практически не сгорает, быстро загорает",
        "6": "Очень темная кожа, никогда не сгорает",
    }
    description = phototype_map.get(phototype, "Неизвестный фототип")
    await state.update_data(phototype=description)
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="Низкая (сидячий образ жизни)", callback_data="activity_low")],
            [InlineKeyboardButton(text="Средняя (регулярная умеренная активность)", callback_data="activity_mid")],
            [InlineKeyboardButton(text="Высокая (активные тренировки и подвижный образ жизни)", callback_data="activity_high")]
        ]
    )
    await state.set_state(Questionnaire.activity)
    await callback_query.message.edit_text("7) Как вы оцениваете уровень своей физической активности?", reply_markup=keyboard)
    await callback_query.answer()

@router.callback_query(StateFilter(Questionnaire.activity), lambda c: c.data.startswith("activity_"))
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
    await state.set_state(Questionnaire.water_intake)
    await callback_query.message.edit_text("8) Сколько воды вы обычно пьёте в течение дня?", reply_markup=keyboard)
    await callback_query.answer()

@router.callback_query(StateFilter(Questionnaire.water_intake), lambda c: c.data.startswith("water_"))
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
    await state.set_state(Questionnaire.stress)
    await callback_query.message.edit_text("9) Ваши нервные клетки успевают восстановиться? Как бы вы описали уровень стресса в своей жизни?", reply_markup=keyboard)
    await callback_query.answer()

@router.callback_query(StateFilter(Questionnaire.stress), lambda c: c.data.startswith("stress_"))
async def process_stress(callback_query: types.CallbackQuery, state: FSMContext):
    stress_map = {
        "stress_low": "Низкий",
        "stress_mid": "Средний",
        "stress_high": "Высокий"
    }
    stress = stress_map[callback_query.data]
    await state.update_data(stress=stress)
    stress_message_map = {
        "stress_low": "Да вы, крепкий орешек! 🥑 Это большая редкость!  Поздравляю вы - стрессоустойчивый человек!",
        "stress_mid": "Это нормально. Но не забывай про самопомощь и поддержку близких💖",
        "stress_high": "Давайте обниму! 🤗Очень вас понимаю! Больше 70% людей подвержены высокому стрессу! Добрый совет: начните медитировать с Prosto и заниматься питанием с Nutri и все наладится вот увидите! 💚"
    }
    await callback_query.message.edit_text(stress_message_map[callback_query.data])
    # keyboard = InlineKeyboardMarkup(
    #     inline_keyboard=[
    #         [InlineKeyboardButton(text="Курение", callback_data="habits_smoking")],
    #         [InlineKeyboardButton(text="Употребление алкоголя", callback_data="habits_drinking")],
    #         [InlineKeyboardButton(text="Курение и употребление алкоголя", callback_data="habits_both")],
    #         [InlineKeyboardButton(text="Нет вредных привычек", callback_data="habits_none")]
    #     ]
    # )
    await state.set_state(Questionnaire.habits)
    await callback_query.message.answer("10) У каждого из нас есть свои маленькие слабости. Какие из перечисленных привычек вам знакомы? Не переживайте, здесь нет осуждения — только забота и понимание.   \n\n1 — Курение \n2 — Употребление алкоголя \n3 — Нет вредных привычек   \n\n<i>Можете выбрать несколько. Укажите ответ через запятую, например: 1, 2</i>")#, reply_markup=keyboard)
    await callback_query.answer()

@router.message(StateFilter(Questionnaire.habits), lambda c: True)
async def process_habits(message: types.Message, state: FSMContext):
    if re.match(
        r'^\s*(?:(?!.*\b(\d+)\b.*\b\1\b))[1-3](?:\s*[ ,]\s*[1-3])*\s*$',  
        message.text,
        flags=re.ASCII
        ):
        # Normalize input by replacing commas with spaces and splitting
        products = [int(x) for x in re.split(r'[ ,]+', message.text.strip())]
        products_descriptions = {
            1 : "Курение",
            2 : "Употребление алкоголя",
            3 : "Нет вредных привычек",
        }
        habits = [products_descriptions[product] for product in products if product in products_descriptions]
        await state.update_data(habits=habits)
        # keyboard = InlineKeyboardMarkup(
        #     inline_keyboard=[
        #         [InlineKeyboardButton(text="Натуральный состав", callback_data="ethics_1")],
        #         [InlineKeyboardButton(text="Не тестируется на животных", callback_data="ethics_2")],
        #         [InlineKeyboardButton(text="Перерабатываемая упаковка", callback_data="ethics_3")],
        #         [InlineKeyboardButton(text="Локальное производство", callback_data="ethics_4")],
        #         [InlineKeyboardButton(text="Социальная ответственность", callback_data="ethics_5")]
        #     ]
        # )
        await state.set_state(Questionnaire.ethics)
        await message.answer("11) Этичные принципы: что для вас наиболее важно при выборе косметики?\n\n1 — Натуральный состав\n2 — Не тестируется на животных\n3 — Перерабатываемая упаковка\n4 — Локальное производство\n5 — Социальная ответственность\n\n<i>Можете выбрать несколько вариантов. Укажите ответ через запятую, например: 1, 2</i>")#, reply_markup=keyboard)
        # await message.answer()
    else:
        await message.answer("Не поняла. Попробуй ввести еще раз.")

@router.message(StateFilter(Questionnaire.ethics), lambda c: True)
async def process_ethics(message: types.Message, state: FSMContext):
    if re.match(
        r'^(?!.*\b(\d+)\b.*\b\1\b)(?:\b([1-5])\b(?:[ ,]+\b([1-5])\b)*)$',  
        message.text,
        flags=re.ASCII
        ):
        products = [int(x) for x in message.text.replace(",", " ").split()]
        products_descriptions = {
            1: "Натуральный состав: только безопасные и природные ингредиенты",
            2: "Не тестируется на животных: продукция, созданная с уважением к братьям нашим меньшим",
            3: "Перерабатываемая упаковка: забота об окружающей среде и минимизация отходов",
            4: "Локальное производство: поддержка местных производителей и снижение углеродного следа",
            5: "Социальная ответственность: Продукты и бренды, которые поддерживают важные инициативы и создают положительный социальный эффект."
        }
        us_id = message.from_user.id
        ethics = [products_descriptions[product] for product in products if product in products_descriptions]
        await state.update_data(ethics=ethics)
        user_data = await state.get_data()
        await message.answer(
            "Спасибо за участие в опросе! "
            # "Вот ваши данные:\n"
            # f"Имя: {user_data['name']}\n"
            # f"Возраст: {user_data['age']}\n"
            # f"Пол: {user_data['gender']}\n"
            # f"Место проживания: {user_data['location']}\n"
            # f"Склонность к аллергии: {user_data['allergy']}\n"
            # f"Особенности образа жизни: {', '.join(map(str, user_data['lifestyle']))}\n"
            # f"Фототип: {user_data['phototype']}\n"
            # f"Уровень физической активности: {user_data['activity']}\n"
            # f"Питьевой режим: {user_data['water_intake']}\n"
            # f"Уровень стресса: {user_data['stress']}\n"
            # f"Вредные привычки: {user_data['habits']}\n"
            # f"Этические предпочтения: {user_data['ethics']}"
        )

        user_data_gen = {
                    "name": f"{user_data['name']}",
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
        response = await send_user_data(us_id, user_data_gen, "SetUserBaseData", "user_data")
        # await callback_query.message.answer(f"Сохранено в базе: {response}")

        full_sequence = user_data.get("full_sequence", False)
        if full_sequence:
            await process_questionnaire_face(message, state)
        else:
            await state.clear()
            await message.answer("Опрос завершен. Спасибо за участие!")
    else:
        await message.answer("Не поняла. Попробуй ввести еще раз.")

@router.callback_query(StateFilter(QuestionnaireFace.skin_type), lambda c: True)
async def process_face_skin_type(callback_query: CallbackQuery, state: FSMContext):
    await state.update_data(face_skin_type=callback_query.data)
    current_data = await state.get_data()
    print(f"Updated state in process_all_questionnaires: {current_data}")
    await state.set_state(QuestionnaireFace.skin_condition)
    await callback_query.message.edit_text(
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
        "dehydrated": "Обезвоженность — это сигнал SOS от кожи! Уже сейчас можно сделать первый шаг — налить себе стакан воды и выпить. Я подожду, никуда не исчезну!  💦",
        "sensitive": "Прекрасно понимаю, как это — когда даже лёгкий ветерок вызывает реакцию. Чувствительная кожа — настоящая леди, ей нужно особое внимание и забота! 🦋",
        "normal": "Вам действительно повезло — нормальная кожа это редкость, которой можно гордиться! ✨🍃Но даже ей нужно немного любви и заботы, чтобы сиять каждый день"
    }
    await callback_query.message.edit_text(pre_message_map[callback_query.data])
    await callback_query.message.answer(
        "14) Есть ли у вашей кожи особенные потребности или сложности? \n\n"
        "1 - Пигментация\n"
        "2 - Неровный тон\n"
        "3 - Акне, постакне\n"
        "4 - Рубцы и шрамы\n"
        "5 - Морщины\n"
        "6 - Расширенные поры\n"
        "7 - Открытые и/или закрытые комедоны\n"
        "8 - Сосудистые проявления\n"
        "9 - Сухость, шелушение\n"
        "10 - Нет особых проблем\n\n"
        "<i>Выберите все варианты, которые вам подходят.\nУкажите ответ через запятую, например: 1, 2</i>",
        reply_markup=None
    )
    await callback_query.answer()

@router.message(StateFilter(QuestionnaireFace.skin_issues))
async def process_face_skin_issues(message: types.Message, state: FSMContext):
    if re.match(
        r'^(?!.*\b(\d+)\b.*\b\1\b)(?:(?:[1-9]|10)(?:[ ,]+(?:[1-9]|10))*)$',
        message.text,
        flags=re.ASCII
        ):
        # issues = [int(x) for x in message.text.replace(",", " ").split()]
        goals = [int(x) for x in message.text.replace(",", " ").split()]
        goal_descriptions = {
            1 : "Пигментация",
            2 :  "Неровный тон",
            3 : "Акне, постакне",
            4 : "Рубцы и шрамы",
            5 : "Морщины",
            6 : "Расширенные поры",
            7 : "Открытые и/или закрытые комедоны",
            8 : "Сосудистые проявления",
            9 : "Сухость, шелушение",
            10 : "Нет особых проблем",
        }
        goal_texts = [goal_descriptions[goal] for goal in goals if goal in goal_descriptions]
        await state.update_data(face_skin_issues=goal_texts)
        await state.set_state(QuestionnaireFace.skin_goals)
        await message.answer(
            "15) Какие цели вы хотели бы достичь для улучшения состояния кожи лица? \n\n"
            "1 - Увлажнённая и гладкая кожа\n"
            "2 - Сияющая свежая кожа\n"
            "3 - Убрать жирный блеск\n"
            "4 - Избавиться от расширенных пор\n"
            "5 - Убрать чёрные точки\n"
            "6 - Убрать воспаления и постакне\n"
            "7 - Убрать морщины\n"
            "8 - Выровнять тон\n"
            "9 - Уменьшить \"мешки\" и тёмные круги под глазами\n"
            "10 - Снять покраснение и раздражение\n\n"
            "<i>Выберите все варианты, которые вам подходят.\nУкажите ответ через запятую, например: 1, 2</i>",
            reply_markup=None
        )
    else:
        await message.answer("Не поняла. Попробуй ввести еще раз.")

@router.message(StateFilter(QuestionnaireFace.skin_goals))
async def process_face_skin_goals(message: types.Message, state: FSMContext):
    if re.match(
        r'^(?!.*\b(\d+)\b.*\b\1\b)(?:(?:[1-9]|10)(?:[ ,]+(?:[1-9]|10))*)$',
        message.text,
        flags=re.ASCII
        ):
        goals = [int(x) for x in message.text.replace(",", " ").split()]
        goal_descriptions = {
            1 : "Увлажнённая и гладкая кожа",
            2 :  "Сияющая свежая кожа",
            3 : "Убрать жирный блеск",
            4 : "Избавиться от расширенных пор",
            5 : "Убрать чёрные точки",
            6 : "Убрать воспаления и постакне",
            7 : "Убрать морщины",
            8 : "Выровнять тон",
            9 : "Уменьшить \"мешки\" и тёмные круги под глазами",
            10 : "Снять покраснение и раздражение",
        }
        goal_texts = [goal_descriptions[goal] for goal in goals if goal in goal_descriptions]
        await state.update_data(face_skin_goals=goal_texts)
        user_data = await state.get_data()
        await message.answer(
            "Спасибо за участие в опросе! "
            # "Вот ваши данные:\n"
            # f"Тип кожи: {user_data['face_skin_type']}\n"
            # f"Состояние кожи: {user_data['face_skin_condition']}\n"
            # f"Проблемы кожи: {', '.join(map(str, user_data['face_skin_issues']))}\n"
            # f"Цели ухода: {', '.join(map(str, user_data['face_skin_goals']))}"
        )
        us_id = message.from_user.id

        user_face_data = {
                    "face_skin_type": f"Тип кожи: {user_data['face_skin_type']}",
                    "face_skin_condition": f"Состояние кожи: {user_data['face_skin_condition']}",
                    "face_skin_issues": f"Проблемы кожи: {', '.join(map(str, user_data['face_skin_issues']))}",
                    "face_skin_goals": f"Цели ухода: {', '.join(map(str, user_data['face_skin_goals']))}",
                }
        response = await send_user_data(us_id, user_face_data, "SetUserFaceData", "user_face_data")
        # await message.answer(f"Сохранено в базе: {response}")

        full_sequence = user_data.get("full_sequence", False)
        if full_sequence:
            print(f"leaving_questionnaire with full_seq:{full_sequence}")
            await start_body_questionnaire(message.from_user.id, state)
        else:
            await state.clear()
            await message.answer("Опрос завершен. Спасибо за участие!")
    else:
        await message.answer("Не поняла. Попробуй ввести еще раз.")

@router.callback_query(StateFilter(QuestionnaireBody.body_skin_type), lambda c: True)
async def process_body_skin_type(callback_query: CallbackQuery, state: FSMContext):
    await state.update_data(body_skin_type=callback_query.data)
    await state.set_state(QuestionnaireBody.body_skin_sensitivity)
    await callback_query.message.edit_text("17) Как вы оцениваете чувствительность кожи вашего тела?\n<i>Ниже будет памятка</i>")
    await callback_query.message.answer(
        "<b>Нормальная кожа</b> (без повышенной чувствительности)\n- Не реагирует на внешние раздражители\n- Редко возникают покраснения, шелушения или зуд\n- Хорошо переносит разные средства ухода\n\n<b>Умеренно чувствительная кожа</b>\n- Иногда реагирует на изменения климата, косметику или моющие средства\n- Возможны легкие покраснения или зуд при использовании новых продуктов\n\n<b>Чувствительная кожа</b>\n- Часто проявляет реакции на раздражители, такие как сухой воздух, горячая вода, солнце или неподходящая косметика\n- Часто ощущается стянутость, зуд или покраснение\n\n<b>Очень чувствительная кожа </b> \n- Реагирует даже на мягкие раздражители, включая ткань одежды или воду\n- Постоянные покраснения, зуд, раздражения, шелушения или высыпания\n- Требует специализированного ухода и минимального контакта с потенциальными аллергенами",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="Чувствительная", callback_data="sensitive")],
            [InlineKeyboardButton(text="Нормальная кожа", callback_data="normal")],
            [InlineKeyboardButton(text="Умеренно чувствительная кожа", callback_data="mid_sensitive")],
            [InlineKeyboardButton(text="Очень чувствительная кожа", callback_data="very_sensitive")]
        ])
    )
    await callback_query.answer()

@router.callback_query(StateFilter(QuestionnaireBody.body_skin_sensitivity), lambda c: True)
async def process_body_skin_sensitivity(callback_query: CallbackQuery, state: FSMContext):
    await state.update_data(body_skin_sensitivity=callback_query.data)
    await state.set_state(QuestionnaireBody.body_skin_condition)
    pre_message_map = {
        "sensitive": "Чувствительная кожа — как нежный цветок, который требует деликатной заботы. Я с вами — буду её оберегать и лелеять, рекомендуя только подходящие мази красоты! 🌸💛",
        "normal": "Какая удача! Ваша кожа словно неприступная крепость — ни раздражения, ни капризов. Ей позавидует любой дерматолог! ✨🛡️",
        "mid_sensitive": "Немного чувствительности добавляет индивидуальности, правда? Но не переживайте, с правильным уходом ваша кожа всегда будет чувствовать себя комфортно! 🌿😊",
        "very_sensitive": "Я понимаю, как это бывает — кожа реагирует даже на малейшее прикосновение. Ничего, мы вместе найдём самые мягкие средства, которые подойдут идеально. 🤲💕"
    }
    await callback_query.message.edit_text(pre_message_map[callback_query.data])
    await callback_query.message.answer(
        "18) Как ты оцениваешь текущее состояние кожи на теле?   \n\n1 — Сухость и шелушение \n2 — потеря упругости \n3 — целлюлит \n4 — акне/прыщи на теле \n5 — пигментация \n6 — покраснения и раздражения \n7 — трещины на коже (например, на пятках) \n8 — морщины \n9 — без проблем       \n\n<i>Выберите все варианты, которые вам подходят. Укажите ответ через запятую, например: 1, 5</i>"#,
        # reply_markup=InlineKeyboardMarkup(inline_keyboard=[
        #     [InlineKeyboardButton(text="Сухость и шелушение", callback_data="dryness")],
        #     [InlineKeyboardButton(text="Потеря упругости", callback_data="loss_of_elasticity")],
        #     [InlineKeyboardButton(text="Целлюлит", callback_data="cellulite")],
        #     [InlineKeyboardButton(text="Акне/прыщи на теле", callback_data="acne")],
        #     [InlineKeyboardButton(text="Пигментация", callback_data="pigmentation")],
        #     [InlineKeyboardButton(text="Покраснения и раздражения", callback_data="redness")],
        #     [InlineKeyboardButton(text="Трещины на коже (например, на пятках)", callback_data="cracks")],
        #     [InlineKeyboardButton(text="Морщины", callback_data="wrinkles")],
        #     [InlineKeyboardButton(text="Нет особых проблем", callback_data="no_problems")]
        # ])
    )
    await callback_query.answer()

@router.message(StateFilter(QuestionnaireBody.body_skin_condition), lambda c: True)
async def process_body_skin_condition(message: Message, state: FSMContext):
    if re.match(
        r'^(?:(?!(?:.*\b(\d+)\b.*\b\1\b))(?:(?:[1-8](?:[ ,]+[1-8])*)|9))$',  
        message.text,
        flags=re.ASCII
        ):
        products = [int(x) for x in message.text.replace(",", " ").split()]
        products_descriptions = {
        1 : "Сухость и шелушение",
        2 : "потеря упругости",
        3 : "целлюлит",
        4 : "акне/прыщи на теле",
        5 : "пигментация",
        6 : "покраснения и раздражения",
        7 : "трещины на коже (например, на пятках)",
        8 : "морщины",
        9 : "без проблем",
        }
        products_texts = [products_descriptions[product] for product in products if product in products_descriptions]
        await state.update_data(body_skin_condition=products_texts)
        await state.set_state(QuestionnaireBody.body_hair_issues)
        await message.answer(
            "19) Замечаете ли вы какие-либо особенности или сложности, связанные с уходом за волосами на теле?",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="Иногда беспокоят вросшие волосы", callback_data="ingrown_hairs")],
                [InlineKeyboardButton(text="Раздражение после бритья", callback_data="irritation")],
                [InlineKeyboardButton(text="Все отлично, проблем нет", callback_data="no_problems")]
            ])
        )
    else:
        await message.answer("Не поняла. Попробуй ввести еще раз.")

@router.callback_query(StateFilter(QuestionnaireBody.body_hair_issues), lambda c: True)
async def process_body_hair_issues(callback_query: CallbackQuery, state: FSMContext):
    await state.update_data(body_hair_issues=callback_query.data)
    await state.set_state(QuestionnaireBody.body_attention_areas)
    pre_message_map = {
        "ingrown_hairs": "Понимаю, это так неприятно. Мы вместе найдем решение, как с этим справиться! 🍃",
        "irritation": "Знаю, это может сильно огорчать. У меня есть решения, которые помогут сделать процесс более комфортным 💧",
        "no_problems": "Вы просто счастливчик! Никаких хлопот — наслаждайтесь! 🌟"
    }
    await callback_query.message.edit_text(pre_message_map[callback_query.data])
    await callback_query.message.answer(
        "20) Есть ли участки на теле, которые требуют особого внимания?\nНапример, зоны, где кожа нуждается в усиленном увлажнении или требует заботы из-за появления трещинок.",
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
    await callback_query.message.edit_text(
        "21) Какие задачи вы бы хотели решить для улучшения состояния кожи тела?\n"
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
        "13 - Чтобы средство вкусно пахло\n\n"
        "<i>Укажите ответ через запятую, например: 1, 5</i>",
        reply_markup=None
    )

@router.message(StateFilter(QuestionnaireBody.body_goals))
async def process_body_goals(message: types.Message, state: FSMContext):
    if re.match(
        r'^(?!.*\b(\d+)\b.*\b\1\b)(?:(?:[1-9]|1[0-3])(?:[ ,]+(?:[1-9]|1[0-3]))*)$',
        message.text,
        flags=re.ASCII
        ):
        goals = [int(x) for x in message.text.replace(",", " ").split()]
        goal_descriptions = {
            1 : "Увлажнение",
            2 :  "Питание",
            3 : "Смягчение",
            4 : "Тонизирование",
            5 : "Отшелушивание",
            6 : "Антицеллюлитный эффект",
            7 : "Осветление кожи",
            8 : "Снятие раздражений",
            9 : "Защита кожи",
            10 : "Массаж",
            11 : "Убрать вросшие волосы",
            12 : "Убрать акне",
            13 : "Чтобы средство вкусно пахло",
        }
        goal_texts = [goal_descriptions[goal] for goal in goals if goal in goal_descriptions]
        await state.update_data(body_goals=goal_texts)
        user_data = await state.get_data()
        print(f"user: {message.from_user.id}, full_seq: {user_data.get("full_sequence")}")
        await message.answer(
            "Спасибо за участие в опросе! "
            # "Вот ваши данные:\n"
            # f"Тип кожи тела: {user_data['body_skin_type']}\n"
            # f"Чувствительность кожи: {user_data['body_skin_sensitivity']}\n"
            # f"Состояние кожи: {user_data['body_skin_condition']}\n"
            # f"Проблемы с волосами: {user_data['body_hair_issues']}\n"
            # f"Участки с особыми потребностями: {user_data['body_attention_areas']}\n"
            # f"Цели ухода: {', '.join(map(str, user_data['body_goals']))}"
        )

        us_id = message.from_user.id

        user_body_data = {
                    "body_skin_type": f"Тип кожи тела: {user_data['body_skin_type']}",
                    "body_skin_sensitivity": f"Чувствительность кожи: {user_data['body_skin_sensitivity']}",
                    "body_skin_condition": f"Состояние кожи: {user_data['body_skin_condition']}",
                    "body_hair_issues": f"Проблемы с волосами: {user_data['body_hair_issues']}",
                    "body_attention_areas": f"Участки с особыми потребностями: {user_data['body_attention_areas']}",
                    "body_goals": f"Цели ухода: {', '.join(map(str, user_data['body_goals']))}",
                }

        response = await send_user_data(us_id, user_body_data, "SetUserBodyData", "user_body_data")
        # await message.answer(f"Сохранено в базе: {response}")

        full_sequence = user_data.get("full_sequence", False)
        if full_sequence:
            await start_hair_questionnaire(message.from_user.id, state)
        else:
            await state.clear()
            await message.answer("Опрос завершен. Спасибо за участие!")
    else:
        await message.answer("Не поняла. Попробуй ввести еще раз.")

@router.callback_query(StateFilter(QuestionnaireHair.scalp_type), lambda c: True)
async def process_hair_scalp_type(callback_query: CallbackQuery, state: FSMContext):
    await state.update_data(hair_scalp_type=callback_query.data)
    await state.set_state(QuestionnaireHair.hair_thickness)
    await callback_query.message.edit_text(
        "23.1) Как бы вы описали толщину ваших волос?\n<i>Выберите наиболее подходящий вариант:</i>",
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
    await callback_query.message.edit_text(
        "23.2) Какова длина ваших волос?",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="Короткие", callback_data="short"),
             InlineKeyboardButton(text="Средней длины", callback_data="medium"),
             InlineKeyboardButton(text="Длинные", callback_data="long")]
        ])
    )
    await callback_query.answer()

@router.callback_query(StateFilter(QuestionnaireHair.hair_length), lambda c: True)
async def process_hair_length(callback_query: CallbackQuery, state: FSMContext):
    await state.update_data(hair_length=callback_query.data)
    await state.set_state(QuestionnaireHair.hair_structure)
    await callback_query.message.edit_text(
        "23.3) Какая структура ваших волос?",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="Прямые", callback_data="straight"),
             InlineKeyboardButton(text="Волнистые", callback_data="wavy"),
             InlineKeyboardButton(text="Кудрявые", callback_data="curly")]
        ])
    )
    await callback_query.answer()

@router.callback_query(StateFilter(QuestionnaireHair.hair_structure), lambda c: True)
async def process_hair_structure(callback_query: CallbackQuery, state: FSMContext):
    await state.update_data(hair_structure=callback_query.data)
    await state.set_state(QuestionnaireHair.hair_condition)
    await callback_query.message.edit_text(
        "23.4) В каком состоянии находятся ваши волосы?",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="Поврежденные (например, окрашиванием)", callback_data="damaged"),
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
    await callback_query.message.edit_text(
        "24) Какие цели ухода за волосами для вас наиболее важны?\n\n<i>Выберите один или несколько пунктов, которые актуальны для вас:</i>\n\n"
        "1 - Контроль жирности кожи головы\n"
        "2 - Увлажнение и питание волос\n"
        "3 - Восстановление поврежденных волос\n"
        "4 - Устранение перхоти\n"
        "5 - Защита от термического воздействия (фен, плойка, утюжок)\n"
        "6 - Усиление роста волос\n"
        "7 - Укрепление корней и предотвращение выпадения\n"
        "8 - Блеск и гладкость\n"
        "9 - Сохранение объёма и лёгкости\n"
        "10 - Борьба с секущимися кончиками\n"
        "11 - Легкость расчёсывания и укладки\n\n"
        "<i>Укажите ответ через запятую, например: 1, 5</i>",
        reply_markup=None
    )

@router.message(StateFilter(QuestionnaireHair.hair_goals))
async def process_hair_goals(message: types.Message, state: FSMContext):
    if re.match(
        r'^(?!.*\b(\d+)\b.*\b\1\b)(?:(?:[1-9]|1[0-3])(?:[ ,]+(?:[1-9]|1[0-1]))*)$',
        message.text,
        flags=re.ASCII
        ):
        goals = [int(x) for x in message.text.replace(",", " ").split()]
        goal_descriptions = {
            1 : "Контроль жирности кожи головы",
            2 : "Увлажнение и питание волос",
            3 : "Восстановление поврежденных волос",
            4 : "Устранение перхоти",
            5 : "Защита от термического воздействия (фен, плойка, утюжок)",
            6 : "Усиление роста волос",
            7 : "Укрепление корней и предотвращение выпадения",
            8 : "Блеск и гладкость",
            9 : "Сохранение объёма и лёгкости",
            10 : "Борьба с секущимися кончиками",
            11 : "Легкость расчёсывания и укладки",
        }
        goal_texts = [goal_descriptions[goal] for goal in goals if goal in goal_descriptions]
        await state.update_data(hair_goals=goal_texts)
        await state.set_state(QuestionnaireHair.washing_frequency)
        await message.answer(
            "25) Как часто вы моете голову?  \n<i>Укажите ваш привычный режим ухода:</i>",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="Каждый день", callback_data="daily"),
                InlineKeyboardButton(text="Каждые 2 дня", callback_data="every_2_days")],
                [InlineKeyboardButton(text="2 раза в неделю", callback_data="twice_weekly"),
                InlineKeyboardButton(text="1 раз в неделю", callback_data="once_weekly")]
            ])
        )
    else:
        await message.answer("Не поняла. Попробуй ввести еще раз.")

@router.callback_query(StateFilter(QuestionnaireHair.washing_frequency), lambda c: True)
async def process_washing_frequency(callback_query: CallbackQuery, state: FSMContext):
    await state.update_data(washing_frequency=callback_query.data)
    await state.set_state(QuestionnaireHair.current_products)
    await callback_query.message.edit_text(
        "26) Какие средства вы используете для ухода за волосами сейчас?  \n<i>Выберите все подходящие варианты:</i>\n\n"
        "1 — Шампунь\n"
        "2 — Кондиционер\n"
        "3 — Маска\n"
        "4 — Несмываемый уход (масла, сыворотки, спреи)\n"
        "5 — Скраб или пилинг для кожи головы\n"
        "6 — Тоники или спреи для роста\n"
        "7 — Укладочные средства (гели, пенки, лаки)"
        #,
        # reply_markup=InlineKeyboardMarkup(inline_keyboard=[
        #     [InlineKeyboardButton(text="Шампунь", callback_data="shampoo"),
        #      InlineKeyboardButton(text="Кондиционер", callback_data="conditioner")],
        #     [InlineKeyboardButton(text="Маска", callback_data="mask"),
        #      InlineKeyboardButton(text="Несмываемый уход (масла, сыворотки, спреи)", callback_data="leave_in_care")],
        #     [InlineKeyboardButton(text="Скраб или пилинг для кожи головы", callback_data="scrub")],
        #     [InlineKeyboardButton(text="Тоники или спреи для роста", callback_data="tonic")],
        #     [InlineKeyboardButton(text="Укладочные средства (гели, пенки, лаки)", callback_data="styling")],
        #     [InlineKeyboardButton(text="Ничего из вышеперечисленного", callback_data="nothing")]
        # ])
    )
    await callback_query.answer()

@router.message(StateFilter(QuestionnaireHair.current_products), lambda c: True)
async def process_current_products(message: types.Message, state: FSMContext):
    
    if re.match(
        r'^(?!.*\b(\d+)\b.*\b\1\b)(?:\b([1-7])\b(?:[ ,]+\b([1-7])\b)*)$',  
        message.text,
        flags=re.ASCII
        ):
        products = [int(x) for x in message.text.replace(",", " ").split()]
        products_descriptions = {
        1 : "Шампунь",
        2 : "Кондиционер",
        3 : "Маска",
        4 : "Несмываемый уход (масла, сыворотки, спреи)",
        5 : "Скраб или пилинг для кожи головы",
        6 : "Тоники или спреи для роста",
        7 : "Укладочные средства (гели, пенки, лаки)",
        }
        products_texts = [products_descriptions[product] for product in products if product in products_descriptions]
        await state.update_data(current_products=products_texts)
        await state.set_state(QuestionnaireHair.product_texture)
        await message.answer(
        "27) Какую текстуру ухода вы предпочитаете?",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="Легкие спреи или тоники", callback_data="light"),
             InlineKeyboardButton(text="Кремовые текстуры", callback_data="cream")],
            [InlineKeyboardButton(text="Плотные масла или бальзамы", callback_data="dense"),
             InlineKeyboardButton(text="Гелевые или сывороточные текстуры", callback_data="gel")],
             [InlineKeyboardButton(text="Не имеет значения, главное — результат", callback_data="any")],
        ])
        )
    else:
        await message.answer("Не поняла. Попробуй ввести еще раз.")

@router.callback_query(StateFilter(QuestionnaireHair.product_texture), lambda c: True)
async def process_product_texture(callback_query: CallbackQuery, state: FSMContext):
    await state.update_data(product_texture=callback_query.data)
    await state.set_state(QuestionnaireHair.sensitivity)
    pre_message_map = {
        "light": "Понимаю вас! Тоже обожаю средства, которые не оставляют следов и ощущение липкости 🙏",
        "cream": "Приятный выбор! Кремовые текстуры всегда создают ощущение комфорта и заботы 🫶",
        "dense": "О, вы из тех, кто любит глубокий уход! Масла и бальзамы — это настоящая находка для питания и восстановления 🌟",
        "gel": "Так свежо и невесомо! Гели и сыворотки идеально подходят для легкости в уходе 💧",
        "any": "Какой прагматичный подход! Главное — добиться того, что нужно, независимо от текстуры 💼"
    }
    await callback_query.message.edit_text(pre_message_map[callback_query.data])
    await callback_query.message.answer(
        "28) Есть ли у вас аллергия или повышенная чувствительность к каким-либо компонентам, которые могут воздействовать на кожу головы?  \n<i>Например: сульфаты, эфирные масла, ароматизаторы или другие вещества.</i>",
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
    await callback_query.message.edit_text(
        "29) Используете ли вы термоукладочные приборы?  \n<i>Например, фен, утюжок, плойку или другие инструменты для укладки.</i>",
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
    await callback_query.message.edit_text(
        "Спасибо за участие в опросе! "
        # "Вот ваши данные:\n"
        # f"Тип кожи головы: {user_data['hair_scalp_type']}\n"
        # f"Толщина волос: {user_data['hair_thickness']}\n"
        # f"Длина волос: {user_data['hair_length']}\n"
        # f"Структура волос: {user_data['hair_structure']}\n"
        # f"Состояние волос: {user_data['hair_condition']}\n"
        # f"Цели ухода: {', '.join(map(str, user_data['hair_goals']))}\n"
        # f"Частота мытья головы: {user_data['washing_frequency']}\n"
        # f"Используемые средства: {user_data['current_products']}\n"
        # f"Предпочитаемая текстура: {user_data['product_texture']}\n"
        # f"Чувствительность: {user_data['sensitivity']}\n"
        # f"Термоукладочные приборы: {user_data['styling_tools']}"
    )

    us_id = callback_query.from_user.id

    user_hair_data = {
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
    response = await send_user_data(us_id, user_hair_data, "SetUserHairData", "user_hair_data")

    # await callback_query.message.answer(f"Сохранено в базе: {response}", reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons))
    await bot.send_message(us_id,"Ура, мы закончили!  \nТеперь я соберу воедино все данные и выведу идеальный бьюти-портрет с персонализированными рекомендациями     \nОсталось немного подождать — результаты скоро будут готовы! 🪴")
    sticker_mssg = await callback_query.message.answer_sticker(sticker=random.choice(STICKERLIST))
    user_data = await state.get_data()
    gpt_response = await no_thread_ass(f"{str(user_data)}, today_date: {datetime.now().date()}", USER_ANAL_ASS)
    gpt_resp = remove_tags(gpt_response)
    await sticker_mssg.delete()
    # await bot.send_message(us_id,f"<b>А вот и ваша аналитика от Аvocado Bot:</b>   \n\n👶 Возраст: {user_data['age']} \n⚠️ Аллергены: {user_data['allergy']}   \n\n🍓 <b>Кожа лица {user_data['face_skin_type']}</b>  \т\тВаша цель: {', '.join(map(str, user_data['face_skin_goals']))}  \n\n Рекомендации (минимум 2 средства): тип средства, наличие компонентов, за что отвечают компоненты и как они подходят к цели, частота использования (без марок и брендов)   \n\n<b>🥭 Кожа тела {user_data['body_skin_type']}</b>   \n\nВаша цель: {', '.join(map(str, user_data['body_goals']))}   \n\nРекомендации (минимум 2 средства): тип средства, наличие компонентов, за что от﻿вечают компоненты и как они подходят к цели, частота использования (без марок и брендов) \n\n🍊<b>Голова и волос {user_data['hair_scalp_type']}</b>   \n\nВаша цель: {', '.join(map(str, user_data['hair_goals']))}   \n\nРекомендации (минимум 2 средства): тип средства, наличие компонентов, за что от﻿вечают компоненты и как они подходят к цели, частота использования (без марок и брендов)")
    await callback_query.message.answer(gpt_resp)
    await state.set_state(Questionnaire.mail)
    await callback_query.message.answer("Какая у вас электронная почта?\nПожалуйста введите ту же почту, что и при оплате — это важно")


async def process_about_avocado(callback_query: CallbackQuery, state: FSMContext):
    img1="AgACAgIAAxkBAAMMaCeYzD72eqrJyBKNDhqSvQiciToAAislMhuJjEBJVEbBKvzHY3gBAAMCAAN5AAM2BA"
    img2="AgACAgIAAxkBAAMQaCeY8SFTF8fBW94WkJq2WDnEnh4AAi0lMhuJjEBJ4UU_ElwWeWUBAAMCAAN5AAM2BA"
    img3="AgACAgIAAxkBAAMUaCeZCvADuIhyjA9RIJcxRBWSDj8AAi4lMhuJjEBJbX4-xR58gYQBAAMCAAN5AAM2BA"
    img4="AgACAgIAAxkBAAMYaCeZIoDUKrkPiICSdWRLnMiJPvMAAi8lMhuJjEBJLdjhcmh6p1IBAAMCAAN5AAM2BA"
    img5="AgACAgIAAxkBAAMcaCeZPkEEY1qHDlEPBl1Y8lXCgNIAAjAlMhuJjEBJk7t92n2oy8EBAAMCAAN5AAM2BA"
    img6="AgACAgIAAxkBAAMgaCeZUl1uVTMgRE1Rs4wmgKkNB5kAAjMlMhuJjEBJiWsF6uC24t0BAAMCAAN5AAM2BA"
    media_files = [
        InputMediaPhoto(media=img1),
        InputMediaPhoto(media=img2),
        InputMediaPhoto(media=img3),
        InputMediaPhoto(media=img4),
        InputMediaPhoto(media=img5),
        InputMediaPhoto(media=img6)
    ]
    await callback_query.message.answer_media_group(media=media_files)
    await callback_query.message.answer(
        "Рассказываю, что именно я умею, как подбираю рекомендации и какие магические формулы использую в своей работе 🧖‍♀️\n\nAvocado всегда радо поделиться всеми секретами красоты и ухода!",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="Ух ты", callback_data="annoying_2")]
        ])
    )
    # await state.clear()

async def process_about_avocado_2(callback_query: CallbackQuery, state: FSMContext):
    img1="AgACAgIAAxkBAAMMaCeYzD72eqrJyBKNDhqSvQiciToAAislMhuJjEBJVEbBKvzHY3gBAAMCAAN5AAM2BA"
    img2="AgACAgIAAxkBAAMQaCeY8SFTF8fBW94WkJq2WDnEnh4AAi0lMhuJjEBJ4UU_ElwWeWUBAAMCAAN5AAM2BA"
    img3="AgACAgIAAxkBAAMUaCeZCvADuIhyjA9RIJcxRBWSDj8AAi4lMhuJjEBJbX4-xR58gYQBAAMCAAN5AAM2BA"
    img4="AgACAgIAAxkBAAMYaCeZIoDUKrkPiICSdWRLnMiJPvMAAi8lMhuJjEBJLdjhcmh6p1IBAAMCAAN5AAM2BA"
    img5="AgACAgIAAxkBAAMcaCeZPkEEY1qHDlEPBl1Y8lXCgNIAAjAlMhuJjEBJk7t92n2oy8EBAAMCAAN5AAM2BA"
    img6="AgACAgIAAxkBAAMgaCeZUl1uVTMgRE1Rs4wmgKkNB5kAAjMlMhuJjEBJiWsF6uC24t0BAAMCAAN5AAM2BA"
    media_files = [
        InputMediaPhoto(media=img1),
        InputMediaPhoto(media=img2),
        InputMediaPhoto(media=img3),
        InputMediaPhoto(media=img4),
        InputMediaPhoto(media=img5),
        InputMediaPhoto(media=img6)
    ]
    await callback_query.message.answer_media_group(media=media_files)
    buttons = [
        [InlineKeyboardButton(text="Анализ состава 🔍", callback_data="analysis")],
        [InlineKeyboardButton(text="Мой Avocado Box  💚", callback_data="avo_box_menu")],
        [InlineKeyboardButton(text="Спросить Avocado Ai🥑", callback_data="setstate_yapp")],
        [InlineKeyboardButton(text="Маркировка 🔍", callback_data="markings")],
        [InlineKeyboardButton(text="Настройки ⚙️:", callback_data="settings")],
        ]
    await callback_query.message.answer(
        "Вот и все пора начинать! С чего хотите начать?",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons)
    )
    await state.clear()


@router.message(StateFilter(UserState.yapp))
async def yapp_handler(message: Message, state: FSMContext) -> None:
    await log_user_message(message)
    user_data = await state.get_data()

    # db_matrix = {
    #     'face': "face",
    #     'body': "body",
    #     'hair': "hair",
    # }
    # db_var = db_matrix.get(analysis_type)
    # user_info_type = await fetch_user_data(us_id, db_var)
    us_id = str(message.from_user.id)
    user_info_general = await fetch_user_data(us_id, "general")
    chat_id = message.chat.id
    thinking_mssg = await message.answer("Анализирую 🔍 ")
    sticker_message = await bot.send_sticker(chat_id=chat_id, sticker=random.choice(STICKERLIST))
    # await remove_thread(us_id)
    buttons = [
        [InlineKeyboardButton(text=arrow_menu, callback_data="menu")],
    ]
    if message.text:
        response_1 = await generate_response_threaded(f"Вопрос пользователя: {message.text}. Информация о пользователе: {user_info_general}", us_id, YAPP_ASS)
        response = remove_tags(response_1)
        await thinking_mssg.delete()
        await sticker_message.delete()
        await message.answer(f"{response}")
        await message.answer("Вы можете продолжить общаться со мной или вернуться в меню 💚", reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons))
        await log_bot_response(f"{response}", message.from_user.id)
    elif message.voice:
        trainscription = await audio_file(message.voice.file_id)
        await message.answer(trainscription)
        response_1 = await generate_response_threaded(trainscription, us_id, YAPP_ASS)
        response = remove_tags(response_1)
        await thinking_mssg.delete()
        await sticker_message.delete()
        await message.answer(f"{response}")
        await message.answer("Вы можете продолжить общаться со мной или вернуться в меню 💚", reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons))
        await log_bot_response(f"{response}", message.from_user.id)
    elif message.photo:
        file = await bot.get_file(message.photo[-1].file_id)
        file_path = file.file_path
        file_url = f"https://api.telegram.org/file/bot{bot.token}/{file_path}"
        caption = message.caption if message.caption else None
        response1 = await generate_response2(caption, us_id, YAPP_ASS, file_url)
        response = remove_tags(response1)
        await thinking_mssg.delete()
        await sticker_message.delete()
        await message.answer(response)
        await message.answer("Вы можете продолжить общаться со мной или вернуться в меню 💚", reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons))

        asyncio.create_task(log_bot_response(f"{response}", message.from_user.id))



@router.message(StateFilter(UserState.yapp_with_xtra))
async def yapp_handler(message: Message, state: FSMContext) -> None:
    await log_user_message(message)
    user_data = await state.get_data()
    pers_analysis = user_data['pers_analysis']
    db_info = user_data['db_info']
    us_id = str(message.from_user.id)
    chat_id = message.chat.id
    buttons = [
        [InlineKeyboardButton(text="Меню", callback_data="menu")],
    ]
    thinking_mssg = await message.answer("Анализирую 🔍 ")
    sticker_message = await bot.send_sticker(chat_id=chat_id, sticker=random.choice(STICKERLIST))
    await remove_thread(us_id)
    if message.text:
        response_1 = await generate_response_threaded(f"Прошлый анализ продукта: {pers_analysis}, информация о продукте {db_info}, вопрос пользователя: {message.text} ", us_id, YAPP_ASS)
        response = remove_tags(response_1)
        await thinking_mssg.delete()
        await sticker_message.delete()
        await message.answer(response)
        await message.answer("Вы можете продолжить общаться со мной или вернуться в меню 💚", reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons))
        await log_bot_response(response, message.from_user.id)
    elif message.voice:
        trainscription = await audio_file(message.voice.file_id)
        await message.answer(trainscription)
        response_1 = await generate_response_threaded(f"Прошлый анализ продукта: {pers_analysis}, информация о продукте {db_info}, вопрос пользователя: {trainscription}", us_id, YAPP_ASS)
        response = remove_tags(response_1)
        await thinking_mssg.delete()
        await sticker_message.delete()
        await message.answer(response)
        await message.answer("Вы можете продолжить общаться со мной или вернуться в меню 💚", reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons))
        await log_bot_response(response, message.from_user.id)
    elif message.photo:
        file = await bot.get_file(message.photo[-1].file_id)
        file_path = file.file_path
        file_url = f"https://api.telegram.org/file/bot{bot.token}/{file_path}"
        caption = message.caption if message.caption else None
        if caption:
            caption = f"Прошлый анализ продукта: {pers_analysis}, информация о продукте {db_info}, вопрос пользователя: {caption}, фото прикреплено"
        if not caption:
            caption = f"Прошлый анализ продукта: {pers_analysis}, информация о продукте {db_info}, фото прикреплено"

        response1 = await generate_response2(caption, us_id, YAPP_ASS, file_url)
        response = remove_tags(response1)
        await thinking_mssg.delete()
        await sticker_message.delete()
        await message.answer(response)

        asyncio.create_task(log_bot_response(f"{response}", message.from_user.id))
        await message.answer("Вы можете продолжить общаться со мной или вернуться в меню 💚", reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons))

        # await message.answer("Введи текст или надиктуй голосом")
        # file = await bot.get_file(message.photo[-1].file_id)
        # file_path = file.file_path
        # file_url = f"https://api.telegram.org/file/bot{bot.token}/{file_path}"
        # url_response_1 = await process_url(file_url, us_id, YAPP_ASS)
        # url_response = remove_tags(url_response_1)
        # await bot.delete_message(chat_id=chat_id, message_id=sticker_message.message_id)
        # await message.answer(url_response)

@router.message(StateFilter(UserState.recognition_2))
async def recognition_2_handler(message: Message, state: FSMContext) -> None:
    asyncio.create_task(log_user_message(message))
    us_id = str(message.from_user.id)
    chat_id = message.chat.id
    if message.text:
        info_message = await message.answer("Анализирую 🔍")
        sticker_message = await bot.send_sticker(chat_id=chat_id, sticker=random.choice(STICKERLIST))
        response = await generate_response(message.text, us_id, NOT_FOUND_ASS)
        response_clean = remove_tags(response)

        await sticker_message.delete()
        await info_message.delete()

        await message.answer(response_clean)
        asyncio.create_task(log_bot_response(response_clean, us_id))
        keyboard = InlineKeyboardMarkup(
            inline_keyboard=[
                [InlineKeyboardButton(text="Да, проверить еще", callback_data="analysis")],
                [InlineKeyboardButton(text="🆘Служба заботы", url="t.me/ai_care")],
                [InlineKeyboardButton(text=arrow_menu, callback_data="menu")]
            ])
        await message.answer("Спасибо, что помогаете нам улучшать нашу базу средств🌿\n\nСейчас у нас 110 000 баночек. Теперь  на +1 стало больше 😍\n\nПроверим что-то еще?", reply_markup=keyboard)
    else:
        keyboard = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="Тык", callback_data="analysis")]])
        message.answer("Я пока принимаю только текст при ожидании состава, если хочешь распознать средство тыкай тут")

            
@router.message(StateFilter(UserState.recognition))
async def recognition_handler(message: Message, state: FSMContext) -> None:
    asyncio.create_task(log_user_message(message))
    user_data = await state.get_data()
    # product_type = user_data.get("product_type")    
    us_id = str(message.from_user.id)
    chat_id = message.chat.id
    if message.text:
        info_message = await message.answer("Анализирую 🔍")
        sticker_message = await bot.send_sticker(chat_id=chat_id, sticker=random.choice(STICKERLIST))
        med_name = await generate_response(message.text, us_id, ASSISTANT_ID)
        await sticker_message.delete()
        await info_message.edit_text("Ищу в базе🔍")


        # await message.answer(f"Я определил продукт как: {med_name}, сейчас найду в базе и дам аналитику")
        asyncio.create_task(log_bot_response(f"бот определил продукт как: {med_name}", message.from_user.id))

        sticker_message1 = await bot.send_sticker(chat_id=chat_id, sticker=random.choice(STICKERLIST))
        response1 = await no_thread_ass(med_name, ASSISTANT_ID_2)
        await sticker_message1.delete()
        await info_message.delete()

        extracted_list = await extract_list_from_input(response1)
        if extracted_list:

            product_list = "\n".join(
            f"{idx + 1} — {product.get('FullName')}" 
            for idx, product in enumerate(extracted_list[:4]))
            buttons = [
                [InlineKeyboardButton(
                    text=str(idx + 1), 
                    callback_data=f"item_{product.get('Identifier')}"
                ) for idx, product in enumerate(extracted_list[:4])],
                [InlineKeyboardButton(text="Никакое, ввести свой состав", callback_data="recognition_2_start")],
                [InlineKeyboardButton(text="🆘Служба заботы", url="t.me/ai_care")],
                [InlineKeyboardButton(text=arrow_menu,callback_data="menu")]
            ]
            text = (
                f"Найдено несколько похожих средств 🔎\n"
                f"{product_list}\n\n"
                f"Какое анализируем?"
            )
            keyboard = InlineKeyboardMarkup(inline_keyboard=buttons)
            await message.answer(text, reply_markup=keyboard)
            asyncio.create_task(log_bot_response(f"{extracted_list}", message.from_user.id))
        else:
            await message.answer("Упс, не получилось распознать этот продукт. Введите полный состав через запятую \n\nПример:\n<i>aqua, parfum/fragrance, centaurea cyanus flower water,  hexyl cinnamal, glycerin, sodium benzoate, linalool, citric acid, potassium sorbate, vanilla planifolia fruit extract.</i>")
            await state.set_state(UserState.recognition_2)
            asyncio.create_task(log_bot_response("Не распознали", message.from_user.id))
    elif message.voice:

        transcribed_text = await audio_file(message.voice.file_id)

        info_message = await message.answer("Анализирую 🔍")
        sticker_message = await bot.send_sticker(chat_id=chat_id, sticker=random.choice(STICKERLIST))
        med_name = await generate_response(transcribed_text, us_id, ASSISTANT_ID)
        asyncio.create_task(log_bot_response(f"бот определил продукт как: {med_name}", message.from_user.id))
        await sticker_message.delete()
        await info_message.edit_text("Ищу в базе🔍")

        sticker_message1 = await bot.send_sticker(chat_id=chat_id, sticker=random.choice(STICKERLIST))
        response1 = await no_thread_ass(med_name, ASSISTANT_ID_2)
        await sticker_message1.delete()
        await info_message.delete()

        extracted_list = await extract_list_from_input(response1)
        if extracted_list:

            product_list = "\n".join(
            f"{idx + 1} — {product.get('FullName')}" 
            for idx, product in enumerate(extracted_list[:4]))
            buttons = [
                [InlineKeyboardButton(
                    text=str(idx + 1), 
                    callback_data=f"item_{product.get('Identifier')}"
                ) for idx, product in enumerate(extracted_list[:4])],
                [InlineKeyboardButton(text="Никакое, ввести свой состав", callback_data="recognition_2_start")],
                [InlineKeyboardButton(text="🆘Служба заботы", url="t.me/ai_care")],
                [InlineKeyboardButton(text=arrow_menu,callback_data="menu")]
            ]
            text = (
                f"Найдено несколько похожих средств 🔎\n"
                f"{product_list}\n\n"
                f"Какое анализируем?"
            )
            keyboard = InlineKeyboardMarkup(inline_keyboard=buttons)
            await message.answer(text, reply_markup=keyboard)
            asyncio.create_task(log_bot_response(f"{extracted_list}", message.from_user.id))
        # if extracted_list:
        #     buttons = [[InlineKeyboardButton(text="Все не то, попробовать снова", callback_data=f"analysis")],]
        #     for product in extracted_list[:5]:
        #         buttons.append(
        #             [
        #         InlineKeyboardButton(
        #             text=product.get('FullName'),
        #             callback_data=f"item_{product.get('Identifier')}"
        #         )
        #     ]
        # )
        #     text = f"Определила средство как: <code>{med_name}</code>\nВ базе нашла несколько похожих средств.\n\nКакое нужно проанализировать?"
            # keyboard = InlineKeyboardMarkup(inline_keyboard=buttons)
            # await message.answer(text, reply_markup=keyboard)
            # await log_bot_response(f"{extracted_list}", message.from_user.id)
        else:
        #     keyboard = InlineKeyboardMarkup(
        #         inline_keyboard=[
        #             [InlineKeyboardButton(text="Еще раз", callback_data="analysis")],
        #             [InlineKeyboardButton(text=arrow_menu, callback_data="menu")]
        #         ]
        #     )
            await message.answer("Упс, не получилось распознать этот продукт. Введите полный состав через запятую \n\nПример:\n<i>aqua, parfum/fragrance, centaurea cyanus flower water,  hexyl cinnamal, glycerin, sodium benzoate, linalool, citric acid, potassium sorbate, vanilla planifolia fruit extract.</i>")
            await state.set_state(UserState.recognition_2)
            # await message.answer("К сожалению, этого товара нет в наличии! 🥲\nПришлите нам ссылку на товар в любом интернет-магазине.\n\nМы его добавим и сразу сообщим 💚", reply_markup=keyboard)
            asyncio.create_task(log_bot_response(f"Не распознали", message.from_user.id))
    elif message.photo:

        file = await bot.get_file(message.photo[-1].file_id)
        file_path = file.file_path
        file_url = f"https://api.telegram.org/file/bot{bot.token}/{file_path}"
        info_message = await message.answer("Анализирую 🔍")
        sticker_message = await bot.send_sticker(chat_id=chat_id, sticker=random.choice(STICKERLIST))
        med_name = await process_url(file_url, us_id, ASSISTANT_ID)
        asyncio.create_task(log_bot_response(f"бот определил продукт как: {med_name}", message.from_user.id))
        await sticker_message.delete()
        await info_message.edit_text("Ищу в базе🔍")
        # await message.answer(f"Я определил продукт как: {med_name}, сейчас найду в базе и дам аналитику")

        sticker_message1 = await bot.send_sticker(chat_id=chat_id, sticker=random.choice(STICKERLIST))
        response1 = await no_thread_ass(med_name, ASSISTANT_ID_2)
        # response = await remove_json_block(response1)
        await sticker_message1.delete()
        await info_message.delete()
        # await message.answer(f"Вот информация по продукту в базе: {response}")
        extracted_list = await extract_list_from_input(response1)
        
        if extracted_list:

            product_list = "\n".join(
            f"{idx + 1} — {product.get('FullName')}" 
            for idx, product in enumerate(extracted_list[:4]))
            buttons = [
                [InlineKeyboardButton(
                    text=str(idx + 1), 
                    callback_data=f"item_{product.get('Identifier')}"
                ) for idx, product in enumerate(extracted_list[:4])],
                [InlineKeyboardButton(text="Никакое, ввести свой состав", callback_data="recognition_2_start")],
                [InlineKeyboardButton(text="🆘Служба заботы", url="t.me/ai_care")],
                [InlineKeyboardButton(text=arrow_menu,callback_data="menu")]
            ]
            text = (
                f"Найдено несколько похожих средств 🔎\n"
                f"{product_list}\n\n"
                f"Какое анализируем?"
            )
            keyboard = InlineKeyboardMarkup(inline_keyboard=buttons)
            await message.answer(text, reply_markup=keyboard)
            asyncio.create_task(log_bot_response(f"{extracted_list}", message.from_user.id))
        else:
            await message.answer("Упс, не получилось распознать этот продукт. Введите полный состав через запятую \n\nПример:\n<i>aqua, parfum/fragrance, centaurea cyanus flower water,  hexyl cinnamal, glycerin, sodium benzoate, linalool, citric acid, potassium sorbate, vanilla planifolia fruit extract.</i>")
            await state.set_state(UserState.recognition_2)
            asyncio.create_task(log_bot_response(f"Не распознали", message.from_user.id))
    else:
        await message.answer("Я принимаю только текст голосовое или фото")

@router.callback_query(lambda c: c.data == 'analysis')
async def process_analysis_cb(callback_query: CallbackQuery, state: FSMContext):
    text = "Отправьте в чат фото 📸, <i>текст</i> или аудио 🎤 вашего средства.\nНапример:\n<i>Weleda Skin food, крем для лица</i>\n\nВ моей базе пока только средства для лица, тела и волос. "
    await callback_query.message.edit_text(text)
    await state.set_state(UserState.recognition)
    # await callback_query.answer()

@router.callback_query(lambda c: c.data.startswith('product_type_'))
async def process_product_type(callback_query: CallbackQuery, state: FSMContext):
    await log_user_callback(callback_query)
    product_type = callback_query.data.split('_')[2]
    await state.update_data(product_type=product_type)
    us_id = callback_query.from_user.id
    text = "Отправьте в чат фото 📸 , текст или аудио 🎤 вашего средства.\nНапример:\n<i>Weleda, крем для лица Skin food</i>\nВ моей базе пока только средства для лица, тела и волос."
    await state.set_state(UserState.recognition)
    await callback_query.message.edit_text(text)
    await callback_query.answer()


@router.callback_query(lambda c: c.data == 'questionaire2')
async def process_questionaire2(callback_query: CallbackQuery, state: FSMContext):
    current_data = await state.get_data()
    if not current_data.get("full_sequence", True):
        await state.update_data(full_sequence=False)
    us_id = callback_query.from_user.id
    text = ( 
        "Холи Гуакамоле! 😊\nЯ — Avocado Bot, ваш карманный защитник в мире безопасной косметики. А как вас зовут?"
    )

    await callback_query.message.edit_text(text)
    await state.set_state(Questionnaire.name)
    await callback_query.answer()

@router.callback_query(lambda c: c.data == 'setstate_yapp')
async def process_setstate_yapp(callback_query: CallbackQuery, state: FSMContext):
    await state.set_state(UserState.yapp)
    await callback_query.answer()
    # await callback_query.answer("yapp_state_set")
    text = "<b>Хотите узнать больше о правильном уходе? \nЗадайте мне любой вопрос!</b> \nНапишите его текстом ✏️ или запишите голосовое сообщение 🎤.\n\n   Например: Как использовать сыворотку с ретинолом? или Можно ли использовать крем с мочевиной для рук – на тело?"#\n Я всегда готов помочь! 🥑
    await callback_query.message.answer(text)

@router.callback_query(lambda c: c.data == 'yapp_with_extra_info')
async def process_yapp_with_extra_info(callback_query: CallbackQuery, state: FSMContext):
    await state.set_state(UserState.yapp_with_xtra)
    await callback_query.answer()
    text = "<b>Хотите узнать больше о правильном уходе? \nЗадайте мне любой вопрос!</b> \nНапишите его текстом ✏️ или запишите голосовое сообщение 🎤.\n\n   Например: Как использовать сыворотку с ретинолом? или Можно ли использовать крем с мочевиной для рук – на тело?"#\n Я всегда готов помочь! 🥑
    await callback_query.message.answer(text)

@router.callback_query(lambda c: c.data.startswith('setstate_yapp_transfer_'))
async def process_product_type(callback_query: CallbackQuery, state: FSMContext):
    transfer_type = callback_query.data.split('_')[3]
    user_data = await state.get_data()
    us_id = str(callback_query.from_user.id)
    buttons = [
        [InlineKeyboardButton(text="Меню", callback_data="menu")],
    ]
    thinking_mssg = await callback_query.message.answer("Анализирую 🔍 ")
    sticker_message = await callback_query.message.answer_sticker(random.choice(STICKERLIST))
    if transfer_type == "txt":
        txt = user_data['transfer_text']
        response_1 = await generate_response(txt, us_id, YAPP_ASS)
        response = remove_tags(response_1)
        await thinking_mssg.delete()
        await sticker_message.delete()
        await callback_query.message.answer(f"{response}")
        await callback_query.message.answer("Вы можете продолжить общаться со мной или вернуться в меню 💚", reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons))
        await state.set_state(UserState.yapp)
    elif transfer_type == "voice":
        voice = user_data['transfer_voice']
        trainscription = await audio_file(voice)
        response_1 = await generate_response(trainscription, us_id, YAPP_ASS)
        response = remove_tags(response_1)
        await thinking_mssg.delete()
        await sticker_message.delete()
        await callback_query.message.answer(f"{response}")
        await callback_query.message.answer("Вы можете продолжить общаться со мной или вернуться в меню 💚", reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons))
        await state.set_state(UserState.yapp)


@router.callback_query(lambda c: c.data == 'markings')
async def process_markings(callback_query: CallbackQuery, state: FSMContext):
    us_id = callback_query.from_user.id
    buttons = [
        [InlineKeyboardButton(text="Экологические и этические обозначения 🐰", callback_data="markings_1")],
        [InlineKeyboardButton(text="Срок годности и хранение 📅", callback_data="markings_2")],
        [InlineKeyboardButton(text="Утилизация ♻️", callback_data="markings_3")],
        [InlineKeyboardButton(text="Стандарты и сертификация ✅", callback_data="markings_4")],
        [InlineKeyboardButton(text="Прямоугольники на тубе 🛑", callback_data="markings_5")],
        [InlineKeyboardButton(text="Как проверить состав🔍", callback_data="markings_6")],
        [InlineKeyboardButton(text=arrow_menu, callback_data="menu")]
    ]
    keyboard = InlineKeyboardMarkup(inline_keyboard=buttons)
    text = "На упаковках косметических средств можно встретить множество символов и значков 🔃, которые информируют о составе продукта, его безопасности 🚫, способах использования и утилизации♻️.\n\nПонимание этих обозначений поможет сделать осознанный выбор и правильно использовать продукцию.\n\n<blockquote>Ниже представлены основные символы, их изображения и расшифровки.</blockquote>\n\nКакой раздел вам интересен?"
    await callback_query.message.edit_text(text, reply_markup=keyboard)

@router.callback_query(lambda c: c.data.startswith('markings_'))
async def process_markingstext(callback_query: CallbackQuery, state: FSMContext):
    await callback_query.answer()
    parts = callback_query.data.split('_')
    markings_num = parts[1]
    markings_matr = {
        '1': markings_1,
        '2': markings_2,
        '3': markings_3,
        '4': markings_4,
        '5': markings_5,
        '6': markings_6,
    }
    media_group_matr = {
        '1': markings_mg_1,
        '2': markings_mg_2,
        '3': markings_mg_3,
        '4': markings_mg_4,
        '5': markings_mg_5,
        '6': markings_mg_6,
    }
    media_gr = media_group_matr.get(markings_num)
    markings_text = markings_matr.get(markings_num)
    buttons = [[InlineKeyboardButton(text=arrow_back, callback_data="markings"), InlineKeyboardButton(text=arrow_menu, callback_data="menu")]]
    keyboard = InlineKeyboardMarkup(inline_keyboard=buttons)
    await callback_query.message.delete()
    await callback_query.message.answer_media_group(media=media_gr)
    await callback_query.message.answer("Хотите узнать что-то еще? 😇", reply_markup=keyboard)
    return






@router.callback_query(lambda c: c.data == 'settings')
async def process_settings(callback_query: CallbackQuery, state: FSMContext):
    us_id = callback_query.from_user.id
    buttons = [
        [InlineKeyboardButton(text="🔖 Как пользоваться ботом", callback_data="explain_4")],
        [InlineKeyboardButton(text="📖 Обновить анкету", callback_data="settings_questionaire")],
        [InlineKeyboardButton(text="💰Условия подписки:", callback_data="settings_sub")],
        [InlineKeyboardButton(text="🆘Служба заботы :", url="t.me/ai_care")],
        [InlineKeyboardButton(text=arrow_menu, callback_data="menu")]
    ]
    keyboard = InlineKeyboardMarkup(inline_keyboard=buttons)
    text = "Настройки ⚙️:"
    await callback_query.message.edit_text(text, reply_markup=keyboard)

@router.callback_query(lambda c: c.data == 'explain_4')
async def process_explain_four(callback_query: CallbackQuery, state: FSMContext):
    text = "Инструкция по применению Avocado Bot 🔖\nДавайте покажу, что я умею 🙌"
    await callback_query.message.edit_text(text, reply_markup=None)
    await process_about_avocado_2(callback_query, state)

@router.callback_query(lambda c: c.data == 'settings_sub')
async def process_sub_sett(callback_query: CallbackQuery, state: FSMContext):
    subtype, repayment_time = await get_user_sub_info(callback_query.from_user.id)
    buttons = [
        # [InlineKeyboardButton(text="Продлить подписку", callback_data="re_sub")],
        [InlineKeyboardButton(text="Отменить подписку", callback_data="un_sub")],
        [InlineKeyboardButton(text=arrow_back, callback_data="settings"),InlineKeyboardButton(text=arrow_menu, callback_data="menu")]
    ]
    if subtype == False:
        bttns = [[InlineKeyboardButton(text="Хочу оплатить", url="https://nutri-ai.ru/?promo=COMMUNITY&utm_medium=referral&utm_source=telegram&utm_campaign=COMMUNITY")], [InlineKeyboardButton(text=" 🆘 Помощь", url="t.me/ai_care")], [InlineKeyboardButton(text="Уже оплачено, ввести почту", callback_data="retry_mail")]]
        await callback_query.message.answer("У тебя нету подписки или произошла ошибка при получении информации о ней \n\n Если ты не вводил почту, то твоя подписка не привязана к аккаунту", reply_markup=InlineKeyboardMarkup(inline_keyboard=bttns))
        return
    keyboard = InlineKeyboardMarkup(inline_keyboard=buttons)
    # message = f"Ваш текущий тариф: {subtype}\n\nВаша подписка истекает {repayment_time}, не забудьте продлить"
    message = "Хотите отменить продление подписки?"
    # message = "Твой текущий тариф:\n\n"
    # if subtype == "Подписка навсегда" or subtype == "Тариф Навсегда":
    #     message += "☑️ Подписка на сервис Авокадо навсегда"
    # elif subtype == "Подписка на 1 год":
    #     message += "☑️ Подписка на сервис Авокадо на 1 год"
    # elif subtype == "Подписка на 3 месяца" or subtype == "Тариф на 3 месяца":
    #     message += f"☑️ Подписка на сервис Авокадо на 3 месяца\n"
    #     message += f"☑️ Дата автоматического продления: {repayment_time}"
    # elif subtype == "Тариф Бесплатный доступ":
    #     message += "☑️ Тариф Бесплатный доступ"
    # else:
    #     message += "☑️ Неизвестный тариф"
    
    await callback_query.message.edit_text(message, reply_markup=keyboard)

@router.callback_query(lambda c: c.data == 're_sub')
async def process_re_sub(callback_query: CallbackQuery, state: FSMContext):
    text = "Перекидывать на лендинг / система оплаты в ТГ"
    buttons = [
        [InlineKeyboardButton(text=arrow_back, callback_data="settings_sub"),InlineKeyboardButton(text=arrow_menu, callback_data="menu")]
    ]
    await callback_query.message.answer(text, reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons))

@router.callback_query(lambda c: c.data == 'un_sub')
async def process_un_sub(callback_query: CallbackQuery, state: FSMContext):
    buttons = [
        [InlineKeyboardButton(text="Да", callback_data="un_sub_yes")],
        [InlineKeyboardButton(text="Нет, я остаюсь", callback_data="un_sub_no")],
        [InlineKeyboardButton(text=arrow_back, callback_data="settings_sub"),InlineKeyboardButton(text=arrow_menu, callback_data="menu")]
    ]
    keyboard = InlineKeyboardMarkup(inline_keyboard=buttons)
    text = "Вы уверены? Avocado Bot всегда вас ждёт 💚"
    await callback_query.message.edit_text(text, reply_markup=keyboard)

@router.callback_query(lambda c: c.data == 'settings_questionaire')
async def process_re_quest(callback_query: CallbackQuery, state: FSMContext):
    us_id = callback_query.from_user.id
    buttons = [
        [InlineKeyboardButton(text="Заполнить заново 🪴", callback_data="all_questionnaires")],
        # [InlineKeyboardButton(text="Внести изменения 🌱", callback_data="questionnaires_pick")],
        [InlineKeyboardButton(text=arrow_back, callback_data="settings"),InlineKeyboardButton(text=arrow_menu, callback_data="menu")]
    ]
    keyboard = InlineKeyboardMarkup(inline_keyboard=buttons)
    text = "Хотите внести несколько изменений или пройти анкету с самого начала?"
    await callback_query.message.edit_text(text, reply_markup=keyboard)

@router.callback_query(lambda c: c.data == 'un_sub_yes')
async def process_un_sub_yes(callback_query: CallbackQuery, state: FSMContext):
    buttons = [
        [InlineKeyboardButton(text=arrow_menu, callback_data="menu")]
    ]
    text = "1) Зайдите на сайт: https://my.cloudpayments.ru/\n\n2) Введете данные своей карты\n\n3)  Нажмите на кнопку «Найти подписки»\n\nТеперь вы сможете отменить подписку.\n\nСм. инструкцию https://cloudpayments.ru/blog/kak-polzovatsya-servisom-otmeny-podpisok/"
    # await callback_query.message.edit_text("Подписка отменена. Возвращайтесь скорее 💚", reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons))
    await callback_query.message.edit_text(text, reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons))

@router.callback_query(lambda c: c.data == 'un_sub_no')
async def process_un_sub_no(callback_query: CallbackQuery, state: FSMContext):
    await callback_query.message.edit_text("Аvocado очень радо! 🥰")

@router.callback_query(lambda c: c.data == 'questionnaires_pick')
async def process_re_quest_pick(callback_query: CallbackQuery, state: FSMContext):
    us_id = callback_query.from_user.id
    us_data = await get_user_data(us_id)
    # await callback_query.message.answer(
    #     f"<b>Общая информация:</b> \n "   
    #     # f"Имя: {us_data['name']}\n"
    #     f"Возраст: {us_data['age']}\n"
    #     f"Пол: {us_data['gender']}\n"
    #     f"Место проживания: {us_data['location']}\n"
    #     f"Склонность к аллергии: {us_data['allergy']}\n"
    #     f"Особенности образа жизни: {us_data['lifestyle']}\n"
    #     # f"Фототип: {us_data['phototype']}\n"
    #     f"Уровень физической активности: {us_data['activity']}\n"
    #     f"Питьевой режим: {us_data['waterIntake']}\n"
    #     f"Уровень стресса: {us_data['stress']}\n"
    #     f"Вредные привычки: {us_data['habits']}\n"
    #     # f"Этические предпочтения: {us_data['ethics']}\n"
    #     f"\n<b>Информация о лице:</b>\n"
    #     f"{us_data['face_skin_type']}\n",
    #     f"{us_data['face_skin_condition']}\n",
    #     f"{us_data['face_skin_issues']}\n",
    #     f"{us_data['face_skin_goals']}\n",       
    #     f"\n<b>Информация о теле:</b>\n"    
    #     f"{us_data['body_skin_type']}\n"
    #     f"{us_data['body_skin_sensitivity']}\n"
    #     f"{us_data['body_skin_condition']}\n"
    #     f"{us_data['body_hair_issues']}\n"
    #     f"{us_data['body_attention_areas']}\n"
    #     f"{us_data['body_goals']}\n"
    #     f"\n<b>Информация о волосах:</b>\n"
    #     f"{us_data['hair_scalp_type']}\n"
    #     f"{us_data['hair_thickness']}\n"
    #     f"{us_data['hair_length']}\n"
    #     f"{us_data['hair_structure']}\n"
    #     f"{us_data['hair_condition']}\n"
    #     f"{us_data['hair_goals']}\n"
    #     f"{us_data['washing_frequency']}\n"
    #     f"{us_data['current_products']}\n"
    #     f"{us_data['product_texture']}\n"
    #     f"{us_data['sensitivity']}\n"
    #     f"{us_data['styling_tools']}"
    # )
    await callback_query.message.answer(f"{us_data}")
    buttons = [
        [InlineKeyboardButton(text="Опросник Общее", callback_data="questionaire2")],
        [InlineKeyboardButton(text="Опросник Лицо", callback_data="questionnaire_face")],
        [InlineKeyboardButton(text="Опросник Тело", callback_data="questionnaire_body")],
        [InlineKeyboardButton(text="Опросник Волосы", callback_data="questionnaire_hair")],
        [InlineKeyboardButton(text=arrow_back, callback_data="settings_questionaire"),InlineKeyboardButton(text=arrow_menu, callback_data="menu")]
    ]
    keyboard = InlineKeyboardMarkup(inline_keyboard=buttons)
    text = "Выберите, в какой части анкеты хотите внести изменения. Когда будете готовы, нажмите «Завершить редактирование» — и вуаля, ваша анкета обновится!"
    await callback_query.message.answer(text, reply_markup=keyboard)

@router.callback_query(lambda c: c.data == 'questionnaire_face')
async def process_questionnaire_face(message_or_callback: types.Message | types.CallbackQuery, state: FSMContext):
    await state.set_state(UserState.info_coll)
    current_data = await state.get_data()
    user_id = message_or_callback.from_user.id
    await state.set_state(QuestionnaireFace.skin_type)
    if not current_data.get("full_sequence", True):
        await state.update_data(full_sequence=False)
    print(f"user: {user_id}, full_seq: {current_data.get("full_sequence")}")
    if isinstance(message_or_callback, types.CallbackQuery):
        await message_or_callback.message.answer(
            "<b>Часть 2/4</b> 🟢🟢⚪️⚪️ \n<b>4 вопроса о вашем прекрасном лице</b> \nСпасибо за искренние ответы! Теперь переходим к следующему этапу — давайте ближе познакомимся с вашей кожей.  🙌"
            )
        await message_or_callback.message.answer(
            "12) Какой тип кожи у вас на лице? \nВыберите наиболее подходящий вариант. Если сомневаетесь, подумайте, как ваша кожа обычно реагирует в течение дня — это поможет сделать правильный выбор! 🌿",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="Нормальная", callback_data="normal"),
                InlineKeyboardButton(text="Сухая", callback_data="dry")],
                [InlineKeyboardButton(text="Жирная", callback_data="oily"),
                InlineKeyboardButton(text="Комбинированная", callback_data="combination")]
            ])
        )
        await message_or_callback.answer()
    else:
        await message_or_callback.answer(
            "<b>Часть 2/4</b> 🟢🟢⚪️⚪️ \n<b>4 вопроса о вашем прекрасном лице</b> \nСпасибо за искренние ответы! Теперь переходим к следующему этапу — давайте ближе познакомимся с вашей кожей.  🙌"
            )
        await message_or_callback.answer(
            "12) Какой тип кожи у вас на лице? \nВыберите наиболее подходящий вариант. Если сомневаетесь, подумайте, как ваша кожа обычно реагирует в течение дня — это поможет сделать правильный выбор! 🌿",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="Нормальная", callback_data="normal"),
                InlineKeyboardButton(text="Сухая", callback_data="dry")],
                [InlineKeyboardButton(text="Жирная", callback_data="oily"),
                InlineKeyboardButton(text="Комбинированная", callback_data="combination")]
            ])
        )


async def start_body_questionnaire(user_id: int, state: FSMContext):
    current_data = await state.get_data()
    full_sequence = current_data.get("full_sequence", False)
    print(f"user: {user_id}, full_seq: {full_sequence}")
    await state.set_state(QuestionnaireBody.body_skin_type)
    if not current_data.get("full_sequence", True):
        await state.update_data(full_sequence=False)
    print(f"user: {user_id}, full_seq: {current_data.get("full_sequence")}")
    await bot.send_message(
        user_id,
        "<b>Часть 3/4 🟢🟢🟢⚪️ \n6 вопросов о вашем теле</b> \n\nС лицом мы разобрались — вы просто молодец!  💪Теперь настало время поговорить о самой \"основательной\" части — вашем теле. Здесь все будет проще, но не менее важно. 😉"
    )
    await bot.send_message(
        user_id,
        "16) Как бы вы описали тип кожи вашего тела?",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="Нормальная", callback_data="normal"),
             InlineKeyboardButton(text="Сухая", callback_data="dry")],
            [InlineKeyboardButton(text="Жирная", callback_data="oily"),
             InlineKeyboardButton(text="Комбинированная", callback_data="combination")]
        ])
    )

@router.callback_query(lambda c: c.data == 'questionnaire_body')
async def process_questionnaire_body(callback_query: CallbackQuery, state: FSMContext):
    await state.set_state(UserState.info_coll)
    await state.update_data(full_sequence=False)
    await start_body_questionnaire(callback_query.from_user.id, state)
    await callback_query.answer()


async def start_hair_questionnaire(user_id: int, state: FSMContext):
    current_data = await state.get_data()
    await state.set_state(QuestionnaireHair.scalp_type)
    if not current_data.get("full_sequence", False):
        await state.update_data(full_sequence=False)
    print(f"user: {user_id}, full_seq: {current_data.get("full_sequence")}")
    await bot.send_message(
        user_id,
        "<b>Часть 4/4 🟢🟢🟢🟢 \n8 вопросов о волосах и коже головы</b> 💆‍♀️ \n8 вопросов о ваших волосах и коже головы♀️ ‍♀️ \nСовсем чуть-чуть осталось! Теперь давайте поговорим о ваших волосах — распустите свои локоны, Рапунцель, мы готовы узнать о них всё. \nВсего 8 вопросов, и мы на финишной прямой! 😊"
    )
    await bot.send_message(
        user_id,
        "22) Какой у вас тип кожи головы?  \n*Попробуйте оценить ощущения после обычного ухода за волосами или вспомнить, как часто вам нужно мыть голову.",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="Нормальная: свежие волосы через 2–3 дня после мытья", callback_data="normal")],
            [InlineKeyboardButton(text="Сухая: зуд или шелушение", callback_data="dry")],
            [InlineKeyboardButton(text="Жирная: кожа головы быстро становится жирной", callback_data="oily")],
            [InlineKeyboardButton(text="Комбинированная: корни жирные, а кончики сухие", callback_data="combination")]
        ])
    )


@router.callback_query(lambda c: c.data == 'questionnaire_hair')
async def process_questionnaire_hair(callback_query: CallbackQuery, state: FSMContext):
    await state.set_state(UserState.info_coll)
    current_data = await state.get_data()
    if not current_data.get("full_sequence", False):
        await state.update_data(full_sequence=False)
    await start_hair_questionnaire(callback_query.from_user.id, state)
    await callback_query.answer()

@router.callback_query(lambda c: c.data == 'all_questionnaires')
async def process_all_questionnaires(callback_query: CallbackQuery, state: FSMContext):
    current_data = await state.get_data()
    print(f"Updated state in process_all_questionnaires: {current_data}")
    await state.set_state(UserState.info_coll)
    await state.update_data(full_sequence=True)
    await process_questionaire2(callback_query, state)


@router.callback_query(lambda c: c.data.startswith('remenu_'))
async def remenu_after_thang(callback_query: CallbackQuery, state: FSMContext):
    await callback_query.answer()
    parts = callback_query.data.split('_')
    item_id = parts[1]
    buttons = [
        [InlineKeyboardButton(text="Да, хочу еще", callback_data="analysis")],
        [InlineKeyboardButton(text="Подробный анализ 🔍", callback_data=f"extra_analysis")],
        [InlineKeyboardButton(text="Получить оценку 🌟", callback_data=f"selecttype_{item_id}")],
        [InlineKeyboardButton(text="❌ Ошибка, ввести состав текстом", callback_data="recognition_2_start")],
        [InlineKeyboardButton(text=arrow_menu, callback_data='menu')]]
    keyboard = InlineKeyboardMarkup(inline_keyboard=buttons)
    await callback_query.message.answer("✅ Анализ завершён\n\nХотите проверить еще одно средство?", reply_markup=keyboard)

@router.callback_query(lambda c: c.data.startswith('item_'))
async def process_item(callback_query: CallbackQuery, state: FSMContext):

    isActive1 = await check_is_active_state(callback_query.from_user.id, state)
    isActive = int(isActive1)
    if isActive < 2:
        await callback_query.answer()
        if isActive<1:
            await callback_query.message.answer("Пожалуйста, пройдите анкету с самого начала  через ввод \n/start 💚")
            return
        bttns = [
            [InlineKeyboardButton(text="Оплатить", url="https://myavocadobot.ru/")],
            [InlineKeyboardButton(text="-40% по Золотому билету", url="https://myavocadobot.ru/")],
            [InlineKeyboardButton(text="Уже оплачено, ввести почту", callback_data="retry_mail")],
            [InlineKeyboardButton(text="🆘 Написать в поддержку", url="t.me/ai_care")],
            [InlineKeyboardButton(text="В меню 🔼", callback_data="menu")]
            ]
        await callback_query.message.answer("Кажется, у вас еще нет подписки.\n\nКупить бота можно с супер скидкой -20% прямо сейчас", reply_markup=(InlineKeyboardMarkup(inline_keyboard=bttns)))
        asyncio.create_task(log_bot_response(f"СТАТУС ПОДПИСКИ {isActive}", callback_query.from_user.id))
        return
    await log_user_callback(callback_query)
    await callback_query.answer()
    parts = callback_query.data.split('_')
    item_id = parts[1]
    await state.update_data(current_item_id=item_id)

    chat_id = callback_query.message.chat.id
    us_id = callback_query.from_user.id

    buttons = [
        [InlineKeyboardButton(text="Да, хочу еще", callback_data="analysis")],
        [InlineKeyboardButton(text="Подробный анализ 🔍", callback_data=f"extra_analysis")],
        [InlineKeyboardButton(text="Получить оценку 🌟", callback_data=f"selecttype_{item_id}")],
        [InlineKeyboardButton(text="❌ Ошибка, ввести состав текстом", callback_data="recognition_2_start")],
        [InlineKeyboardButton(text=arrow_menu, callback_data='menu')]
    ]
    # if callback_query.from_user.id == 464682207:
    #     buttons = [
    #         [InlineKeyboardButton(text="Да, хочу еще", callback_data="analysis")],
    #         [InlineKeyboardButton(text="Подробный анализ 🔍", callback_data=f"extra_analysis")],
    #         [InlineKeyboardButton(text="Получить оценку 🌟", callback_data=f"selecttype_{item_id}")],
    #         [InlineKeyboardButton(text="❌ Ошибка, ввести состав текстом", callback_data="recognition_2_start")],
    #         [InlineKeyboardButton(text=arrow_menu, callback_data='menu')]
    #     ]
    keyboard = InlineKeyboardMarkup(inline_keyboard=buttons)

    analys_mssg = await callback_query.message.answer("Анализирую 🔍")
    sticker_message = await bot.send_sticker(chat_id=callback_query.message.chat.id, sticker=random.choice(STICKERLIST))
    db_info = await fetch_product_details(item_id)
    product_name = db_info["Name"]
    await state.update_data(current_item_name=product_name)
    # analysis_result1 = await no_thread_ass(str(db_info), GENERAL_ANALYSIS_ASS)
    analysis_result1 = await run_with_timeout(
    bot=bot,
    us_id=us_id,
    coro=no_thread_ass(str(db_info), GENERAL_ANALYSIS_ASS),
    timeout=30,
    timeout_message="Извините что задерживаюсь, результат все еще в обработке"
)

    analysis_result = remove_tags(analysis_result1)
    await analys_mssg.delete()
    await bot.delete_message(chat_id=chat_id, message_id=sticker_message.message_id)

    await bot.send_message(us_id, analysis_result)
    await bot.send_message(us_id, "✅ Анализ завершён\n\nХотите проверить еще одно средство?", reply_markup=keyboard)
    await log_bot_response(analysis_result, callback_query.from_user.id)

    try:
        await callback_query.answer()
    except Exception as e:
        print("cb_timeout")

@router.callback_query(lambda c: c.data.startswith('selecttype_'))
async def process_pers_type(callback_query: CallbackQuery, state: FSMContext):
    asyncio.create_task(log_user_callback(callback_query))
    await callback_query.answer()
    parts = callback_query.data.split('_')
    item_id = parts[1]
    buttons = [
        [InlineKeyboardButton(text="Для лица 👄", callback_data=f"personal_face_{item_id}")],
        [InlineKeyboardButton(text="Для волос 💇‍♀️", callback_data=f"personal_hair_{item_id}")],
        [InlineKeyboardButton(text="Для тела 🧖‍♀️", callback_data=f"personal_body_{item_id}")]]
    await callback_query.message.edit_reply_markup(reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons))

@router.callback_query(lambda c: c.data == 'extra_analysis')
async def process_extra_analysis_menu(callback_query: CallbackQuery, state: FSMContext):
    state_data = await state.get_data()
    product_name = state_data['current_item_name']
    buttons = [
        [InlineKeyboardButton(text="Состав 🔬", callback_data="analysis_consist")],
        [InlineKeyboardButton(text="Свойства 💧", callback_data="analysis_functions")],
        [InlineKeyboardButton(text="Активные компоненты 🧬", callback_data="analysis_active")],
        [InlineKeyboardButton(text="Этичность 🌱", callback_data="analysis_ethics")],
    ]
    await callback_query.message.edit_text(f"<b>Подробный анализ средства:</b>\n\n<i>{product_name}</i>\n\nЧто вы хотите узнать глубже?", reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons))

@router.callback_query(lambda c: c.data == 'analysis_consist')
async def process_analysis_consist(callback_query: CallbackQuery, state: FSMContext):
    state_data = await state.get_data()
    product_id = state_data['current_item_id']
    buttons = [
        [InlineKeyboardButton(text=arrow_back, callback_data="extra_analysis")],
        [InlineKeyboardButton(text=arrow_menu, callback_data="menu")],
    ]
    # analys_mssg = await callback_query.message.answer("Анализирую 🔍")
    sticker_message = await bot.send_sticker(chat_id=callback_query.message.chat.id, sticker=random.choice(STICKERLIST))
    db_info = await fetch_product_details(product_id)
    analysis_result1 = await no_thread_ass(str(db_info), CONSIST_ANALYSIS_ASS)
    analysis_result = remove_tags(analysis_result1)
    # await analys_mssg.delete()
    await sticker_message.delete()

    await callback_query.message.edit_text(analysis_result)
    await callback_query.message.answer("Продолжим? 😇", reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons))

@router.callback_query(lambda c: c.data == 'analysis_functions')
async def process_analysis_functions(callback_query: CallbackQuery, state: FSMContext):
    state_data = await state.get_data()
    product_id = state_data['current_item_id']
    buttons = [
        [InlineKeyboardButton(text=arrow_back, callback_data="extra_analysis")],
        [InlineKeyboardButton(text=arrow_menu, callback_data="menu")],
    ]
    # analys_mssg = await callback_query.message.answer("Анализирую 🔍")
    sticker_message = await bot.send_sticker(chat_id=callback_query.message.chat.id, sticker=random.choice(STICKERLIST))
    db_info = await fetch_product_details(product_id)
    analysis_result1 = await no_thread_ass(str(db_info), FUNCTIONS_ANALYSIS_ASS)
    analysis_result = remove_tags(analysis_result1)
    # await analys_mssg.delete()
    await sticker_message.delete()

    await callback_query.message.edit_text(analysis_result)
    await callback_query.message.answer("Продолжим? 😇", reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons))

@router.callback_query(lambda c: c.data == 'analysis_active')
async def process_analysis_active(callback_query: CallbackQuery, state: FSMContext):
    state_data = await state.get_data()
    product_id = state_data['current_item_id']
    buttons = [
        [InlineKeyboardButton(text=arrow_back, callback_data="extra_analysis")],
        [InlineKeyboardButton(text=arrow_menu, callback_data="menu")],
    ]
    # analys_mssg = await callback_query.message.answer("Анализирую 🔍")
    sticker_message = await bot.send_sticker(chat_id=callback_query.message.chat.id, sticker=random.choice(STICKERLIST))
    db_info = await fetch_product_details(product_id)
    analysis_result1 = await no_thread_ass(str(db_info), ACTIVE_ANALYSIS_ASS)
    analysis_result = remove_tags(analysis_result1)
    # await analys_mssg.delete()
    await sticker_message.delete()

    await callback_query.message.edit_text(analysis_result)
    await callback_query.message.answer("Продолжим? 😇", reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons))

@router.callback_query(lambda c: c.data == 'analysis_ethics')
async def process_analysis_ethics(callback_query: CallbackQuery, state: FSMContext):
    state_data = await state.get_data()
    product_id = state_data['current_item_id']
    buttons = [
        [InlineKeyboardButton(text=arrow_back, callback_data="extra_analysis")],
        [InlineKeyboardButton(text=arrow_menu, callback_data="menu")],
    ]
    # analys_mssg = await callback_query.message.answer("Анализирую 🔍")
    sticker_message = await bot.send_sticker(chat_id=callback_query.message.chat.id, sticker=random.choice(STICKERLIST))
    db_info = await fetch_product_details(product_id)
    analysis_result1 = await no_thread_ass(str(db_info), ETHICS_ANALYSIS_ASS)
    analysis_result = remove_tags(analysis_result1)
    # await analys_mssg.delete()
    await sticker_message.delete()

    await callback_query.message.edit_text(analysis_result)
    await callback_query.message.answer("Продолжим? 😇", reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons))


@router.callback_query(lambda c: c.data.startswith('personal_'))
async def personal_cb(callback_query: CallbackQuery, state: FSMContext):
    await callback_query.answer()
    await log_user_callback(callback_query)
    parts = callback_query.data.split('_')
    analysis_type = parts[1]
    item_id = parts[2]
    us_id = callback_query.from_user.id

    analysis_matrix = {
        'face': ANALYSIS_P_FACE_ASS,
        'body': ANALYSIS_P_BODY_ASS,
        'hair': ANALYSIS_P_HAIR_ASS,
    }
    db_matrix = {
        'face': "face",
        'body': "body",
        'hair': "hair",
    }

    
    buttons = [
        [InlineKeyboardButton(text="Да, хочу еще", callback_data="analysis")],
        [InlineKeyboardButton(text="Подробный анализ 🔍", callback_data=f"extra_analysis")],
        [InlineKeyboardButton(text="Получить оценку 🌟", callback_data=f"selecttype_{item_id}")],
        [InlineKeyboardButton(text="❌ Ошибка, ввести состав текстом", callback_data="recognition_2_start")],
        [InlineKeyboardButton(text=arrow_menu, callback_data='menu')]
    ]
    await callback_query.message.edit_reply_markup(reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons))

    analysis_var = analysis_matrix.get(analysis_type)
    db_var = db_matrix.get(analysis_type)
    
    sticker_message = await bot.send_sticker(chat_id=callback_query.message.chat.id, sticker=random.choice(STICKERLIST))
    db_info = await fetch_product_details(item_id)
    # user_info = await get_user_data(us_id)
    user_info_general = await fetch_user_data(us_id, "general")
    user_info_type = await fetch_user_data(us_id, db_var)
    gpt_message = f"Информация о продукте: {db_info}, Информация о пользователе: {user_info_general}, {user_info_type}"
    pers_analysis1 = await no_thread_ass(gpt_message, analysis_var)
    pers_analysis = remove_tags(pers_analysis1)
    await sticker_message.delete()
    await state.update_data(pers_analysis=pers_analysis)
    await state.update_data(db_info=db_info)
    buttons = [
        [InlineKeyboardButton(text="Назад ⬅️", callback_data=f"remenu_{item_id}")],
        [InlineKeyboardButton(text="В меню 🔼", callback_data="menu")],
        # [InlineKeyboardButton(text="Задать вопрос Авокадо Bot про эту баночку", callback_data="yapp_with_extra_info")]
    ]

    await callback_query.message.answer(pers_analysis, reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons))
    await log_bot_response(pers_analysis, callback_query.from_user.id)


@router.message(Command("upload_image"))
async def upload_image_command(message: types.Message, state: FSMContext):
    await state.set_state(ImageUploadState.waiting_for_image)
    await message.answer("Please send me an image, and I'll give you its file_id.")

@router.message(Command("message_info_command"))
async def message_info(message: types.Message, state: FSMContext):
    await message.answer(str(message))
    print(message)


@router.message(ImageUploadState.waiting_for_image)
async def handle_image_upload(message: types.Message, state: FSMContext):
    if message.photo:
        file_id = message.photo[-1].file_id
        await message.answer(f"Here is the file_id of your image:\n\n<code>{file_id}</code>\n\n"
                            "You can use this file_id to send the image in your bot.")
    elif message.video:
        file_id = message.video.file_id
        await message.answer(f"Here is the file_id of your vid:\n\n<code>{file_id}</code>\n\n"
                            "You can use this file_id to send the vid in your bot.")

    await state.set_state(UserState.menu)
    


@router.message()
async def default_handler(message: Message, state: FSMContext) -> None:
    await state.set_state(UserState.transfer)
    await state.update_data(full_sequence=False)
    if message.photo:
        await state.set_state(UserState.recognition)
        await recognition_handler(message, state)
        # button = [[InlineKeyboardButton(text="Анализ состава 🔍", callback_data="analysis")]]
        # await message.answer("Если ты хочешь опознать баночку надо сначала выбрать к какой категории она относится", reply_markup=InlineKeyboardMarkup(inline_keyboard=button))
        # file_id = message.photo[-1].file_id
        # await message.answer(f"Here is the file_id of your image:\n\n<code>{file_id}</code>\n\n"
        #                     "You can use this file_id to send the image in your bot.")
    if message.text:
        buttons = [
        [InlineKeyboardButton(text="Анализ состава 🔍", callback_data="analysis")],
        [InlineKeyboardButton(text="Спросить Avocado Ai🥑", callback_data="setstate_yapp_transfer_txt")],
        ]
        keyboard = InlineKeyboardMarkup(inline_keyboard=buttons)
        await state.update_data(transfer_text = message.text)
        await message.answer("Ты хочешь распознать это как баночку или задать вопрос авокадо?", reply_markup=keyboard)
    if message.voice:
        buttons = [
        [InlineKeyboardButton(text="Анализ состава 🔍", callback_data="analysis")],
        [InlineKeyboardButton(text="Спросить Avocado Ai🥑", callback_data="setstate_yapp_transfer_voice")],
        ]
        keyboard = InlineKeyboardMarkup(inline_keyboard=buttons)
        await state.update_data(transfer_voice = message.voice.file_id)
        await message.answer("Ты хочешь распознать это как баночку или задать вопрос авокадо?", reply_markup=keyboard)
    if message.sticker:
        sticker_id = message.sticker.file_id
        await message.answer(f"<code>{sticker_id}</code>")
    # else: 
    #     await message.answer("Состояние не установлено. Используйте /start, чтобы начать, или выберите вариант из меню", reply_markup=keyboard)



async def main() -> None:
    init_db()
    logging.basicConfig(level=logging.INFO, stream=sys.stdout)
    dp.include_router(router)
    dp.message.middleware(StateMiddleware())
    bot = Bot(token=TOKEN, default=DefaultBotProperties(
        parse_mode=ParseMode.HTML))
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
