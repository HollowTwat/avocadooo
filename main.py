import asyncio
import aiogram
import os
import logging
from aiogram import Bot, Dispatcher, types
import openai
from auth import BOT_TOKEN, ASSISTANT_ID, ASSISTANT_ID_2, ANALYSIS_ASS
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
TOKEN = BOT_TOKEN
# OPENAI_API_KEY = OPENAI_KEY
# openai.api_key = OPENAI_API_KEY
error_chat = -1002200108684

bot = Bot(token=TOKEN, default=DefaultBotProperties(
    parse_mode=ParseMode.HTML))
storage = MemoryStorage()
router = Router()
dp = Dispatcher(storage=storage)
# client = AsyncOpenAI(api_key=OPENAI_API_KEY)


class StateMiddleware(BaseMiddleware):
    async def __call__(self, handler, event: Message, data: dict):
        state = data['state']
        current_state = await state.get_state()
        data['current_state'] = current_state
        return await handler(event, data)


class UserState(StatesGroup):
    info_coll = State()
    recognition = State()

@router.message(CommandStart())
async def command_start_handler(message: Message, state: FSMContext) -> None:
    buttons = [InlineKeyboardButton(
        text="Анализ состава 🔍", callback_data="analysis")]
    keyboard = InlineKeyboardMarkup(inline_keyboard=[buttons])
    step0txt = "Привет"
    await message.answer(step0txt, reply_markup=keyboard)

@router.message(StateFilter(UserState.recognition))
async def recognition_handler(message: Message, state: FSMContext) -> None:
    us_id = str(message.from_user.id)
    if message.text:
        med_name = await generate_response(message.text, us_id, ASSISTANT_ID)
        await message.answer(f"Я определил продукт как: {med_name}, сейчас найду в базе и дам аналитику")
        response1 = await no_thread_ass(med_name, ASSISTANT_ID_2)
        response = await remove_json_block(response1)

        await message.answer(f"Вот информация по продукту в базе: {response}")
        extracted_list = await extract_list_from_input(response1)
        print(extracted_list)
        if extracted_list:
            for product in extracted_list:
                await message.answer(f"id: {product.get('Identifier')}, name: {product.get('FullName')}")
                
            await message.answer(f"Прогоним первый из продуктов по анализу. Имя продукта: {extracted_list[0].get('FullName')}")
            db_info = await fetch_product_details(extracted_list[0].get('Identifier'))
            print(db_info)
            analysys = await no_thread_ass(str(db_info), ANALYSIS_ASS)
            await message.answer(analysys)
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
            for product in extracted_list:
                await message.answer(f"id: {product.get('Identifier')}, name: {product.get('FullName')}")
                
            await message.answer(f"Прогоним первый из продуктов по анализу. Имя продукта: {extracted_list[0].get('FullName')}")
            db_info = await fetch_product_details(extracted_list[0].get('Identifier'))
            print(db_info)
            analysys = await no_thread_ass(str(db_info), ANALYSIS_ASS)
            await message.answer(analysys)
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
            for product in extracted_list:
                await message.answer(f"id: {product.get('Identifier')}, name: {product.get('FullName')}")
                
            await message.answer(f"Прогоним первый из продуктов по анализу. Имя продукта: {extracted_list[0].get('FullName')}")
            db_info = await fetch_product_details(extracted_list[0].get('Identifier'))
            print(db_info)
            analysys = await no_thread_ass(str(db_info), ANALYSIS_ASS)
            await message.answer(analysys)
    else:
        await message.answer("Я принимаю только текст голосовое или фото")


@router.callback_query(lambda c: c.data == 'analysis')
async def process_analysis(callback_query: CallbackQuery, state: FSMContext):
    us_id = callback_query.from_user.id
    text = "Скинь мне фото или ссылку твоего средства и я проанализирую? \nИли напиши или надиктуй название"
    await state.set_state(UserState.recognition)
    await bot.send_message(us_id, text)
    await callback_query.answer()


@router.message()
async def default_handler(message: Message, state: FSMContext, current_state: str) -> None:
    if current_state is not ['redact', 'new_food', 'out_of_uses']:
        await message.answer('В пробной версии свободное общение с нутри ограниченно')


async def main() -> None:
    dp.include_router(router)
    dp.message.middleware(StateMiddleware())
    bot = Bot(token=TOKEN, default=DefaultBotProperties(
        parse_mode=ParseMode.HTML))
    await dp.start_polling(bot)

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, stream=sys.stdout)
    asyncio.run(main())
