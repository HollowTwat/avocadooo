import os
import re
import json
import asyncio
import aiohttp
import asyncio
import aiogram
from aiogram import Bot, Dispatcher, types
import openai
import base64
from auth import OPENAI_KEY, ASSISTANT_ID, BOT_TOKEN
import requests
from aiogram import Bot, Dispatcher, html, Router, BaseMiddleware
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.filters import CommandStart, Command
from aiogram.filters.state import StateFilter
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, FSInputFile, InlineKeyboardButton, InlineKeyboardMarkup, CallbackQuery
from openai import AsyncOpenAI, OpenAI
import shelve


TOKEN = BOT_TOKEN
OPENAI_API_KEY = OPENAI_KEY
openai.api_key = OPENAI_API_KEY


bot = Bot(token=TOKEN, default=DefaultBotProperties(
    parse_mode=ParseMode.HTML))
storage = MemoryStorage()
router = Router()
dp = Dispatcher(storage=storage)
client = AsyncOpenAI(api_key=OPENAI_API_KEY)
TRACKER_BOT_TOKEN = "7046656911:AAHzhDbppOgA4e6dbdVURANHPASwX25bGnw"
tracker_bot = Bot(token=TRACKER_BOT_TOKEN, default=DefaultBotProperties(
    parse_mode=ParseMode.HTML))

async def fetch_product_details(product_id):
    url = f"https://avocado-production.up.railway.app/api/TypesCRUD/GetElementInfo?Id={product_id}"
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as response:
            if response.status == 200:
                text_response = await response.text()
                try:
                    data = json.loads(text_response)
                    return data
                except json.JSONDecodeError:
                    print(f"Failed to parse JSON for product {product_id}. Response: {text_response}")
                    return None
            else:
                print(f"Failed to fetch product {product_id}. Status: {response.status}")
                return None
            

async def process_photo(photo_data, user_id, assistant):
    thread_id = await check_if_thread_exists(user_id)

    if thread_id is None:
        print(f"Creating new thread for {user_id}")
        thread = await client.beta.threads.create()
        await store_thread(user_id, thread.id)
        thread_id = thread.id
    else:
        print(f"Retrieving existing thread {user_id}")
        thread = await client.beta.threads.retrieve(thread_id)

    encoded_photo = base64.b64encode(photo_data).decode('utf-8')

    message = await client.beta.threads.messages.create(
        thread_id=thread_id,
        role="user",
        content=encoded_photo,
    )
    new_message = await run_assistant(thread, assistant)
    return new_message


async def check_if_thread_exists(usr_id):
    with shelve.open("threads_db") as threads_shelf:
        return threads_shelf.get(usr_id, None)


async def store_thread(usr_id, thread_id):
    with shelve.open("threads_db", writeback=True) as threads_shelf:
        threads_shelf[usr_id] = thread_id


async def remove_thread(user_id):
    with shelve.open("threads_db", writeback=True) as threads_shelf:
        if user_id in threads_shelf:
            del threads_shelf[user_id]
            print("thread_id deleted")
        else:
            print("didn't delete, not there")

async def process_url(url, usr_id, assistant):
    thread_id = await check_if_thread_exists(usr_id)

    if thread_id is None:
        print(f"Creating new thread for {usr_id}")
        thread = await client.beta.threads.create()
        await store_thread(usr_id, thread.id)
        thread_id = thread.id
    else:
        print(f"Retrieving existing thread {usr_id}")
        thread = await client.beta.threads.retrieve(thread_id)
    print(url)
    thread = await client.beta.threads.create(
        messages=[

            {
                "role": "user",
                "content": [
                    {
                        "type": "image_url",
                        "image_url": {"url": url},
                    },]
            },
        ]
    )
    await store_thread(usr_id, thread.id)

    new_message = await run_assistant(thread, assistant)

    return new_message

async def remove_json_block(input_string):
    cleaned_string = input_string.replace("```json", "").replace("```", "")
    cleaned_string = re.sub(r"【.*?】", "", cleaned_string)
    return cleaned_string

async def extract_list_from_string(input_string):
    # Find the JSON-like list using a regular expression
    match = re.search(r'"Products": (\[.*?\])', input_string)
    if match:
        list_str = match.group(1)
        try:
            return json.loads(list_str)
        except json.JSONDecodeError:
            return None
    return None

async def extract_list_from_input(input_data):
    try:
        # Check if input is valid JSON (as a string or dictionary)
        if isinstance(input_data, str):
            parsed_data = json.loads(input_data)  # Parse string as JSON
        elif isinstance(input_data, dict):
            parsed_data = input_data  # Use dictionary directly
        else:
            parsed_data = None
    except json.JSONDecodeError:
        # If JSON parsing fails, fall back to regex extraction
        match = re.search(r'"Products": (\[.*?\])', input_data, re.DOTALL)
        if match:
            list_str = match.group(1)
            try:
                return json.loads(list_str)
            except json.JSONDecodeError:
                return None
        return None

    # If successfully parsed and contains 'Products'
    if parsed_data and "Products" in parsed_data:
        return parsed_data["Products"]
    return None

async def no_thread_ass(message_body, assistant):

    thread = await client.beta.threads.create()
    message = await client.beta.threads.messages.create(
        thread_id=thread.id,
        role="user",
        content=message_body,
    )
    print(message)

    new_message = await run_assistant(thread, assistant)
    return new_message


async def transcribe_audio(file_path):
    with open(file_path, 'rb') as audio_file:
        response = openai.audio.transcriptions.create(
            model="whisper-1",
            file=audio_file
        )
    return response.text


async def transcribe_audio_from_url(url):
    response = requests.get(url)
    if response.status_code == 200:
        temp_file_path = 'temp_audio.ogg'
        with open(temp_file_path, 'wb') as f:
            f.write(response.content)
        transcription = await transcribe_audio(temp_file_path)
        return transcription
    else:
        raise Exception(f"Failed to fetch audio from URL: {response.status}")


async def audio_file(file_id: str) -> str:
    # try:
    file = await bot.get_file(file_id)
    file_path = file.file_path
    file_url = f"https://api.telegram.org/file/bot{bot.token}/{file_path}"

    transcription = await transcribe_audio_from_url(file_url)
    return transcription


async def generate_response(message_body, usr_id, assistant):
    thread_id = await check_if_thread_exists(usr_id)
    print(message_body, thread_id)

    if thread_id is None:
        print(f"Creating new thread for {usr_id}")
        thread = await client.beta.threads.create()
        await store_thread(usr_id, thread.id)
        thread_id = thread.id
    else:
        print(f"Retrieving existing thread {usr_id}")
        thread = await client.beta.threads.retrieve(thread_id)

    message = await client.beta.threads.messages.create(
        thread_id=thread_id,
        role="user",
        content=message_body,
    )
    print(message)

    new_message = await run_assistant(thread, assistant)
    return new_message


async def run_assistant(thread, assistant_str):
    try:
        print("run_assistant hit")
        assistant = await client.beta.assistants.retrieve(assistant_str)
        run = await client.beta.threads.runs.create(
            thread_id=thread.id,
            assistant_id=assistant.id,
        )

        while run.status != "completed":
            if run.status == "failed":
                messages = await client.beta.threads.messages.list(thread_id=thread.id)
                raise Exception(
                    f"Run failed with status: {run.status} and generated {messages.data[0]}")

            print(run.status)
            await asyncio.sleep(1.5)
            run = await client.beta.threads.runs.retrieve(
                thread_id=thread.id, run_id=run.id)

        messages = await client.beta.threads.messages.list(thread_id=thread.id)
        latest_mssg = messages.data[0].content[0].text.value
        print(f"generated: {latest_mssg}")
        return latest_mssg

    except Exception as e:
        print(f"An error occurred: {e}")
        return f"exception: {e}"