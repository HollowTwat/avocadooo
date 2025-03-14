import os
import re
import json
import asyncio
import aiohttp
import asyncio
import aiogram
from aiogram import Bot, Dispatcher, types
import openai
import datetime
import base64
# from auth import OPENAI_KEY, ASSISTANT_ID, BOT_TOKEN
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


BOT_TOKEN = os.getenv("BOT_TOKEN")
OPENAI_KEY = os.getenv("OPENAI_KEY")
ASSISTANT_ID = os.getenv("ASSISTANT_ID")
ASSISTANT_ID_2 = os.getenv("ASSISTANT_ID_2")
ANALYSIS_ASS = os.getenv("ANALYSIS_ASS")
CHAT_ID = os.getenv("LOGS_CHAT_ID")

TOKEN = BOT_TOKEN
OPENAI_API_KEY = OPENAI_KEY
openai.api_key = OPENAI_API_KEY


bot = Bot(token=TOKEN, default=DefaultBotProperties(
    parse_mode=ParseMode.HTML))
storage = MemoryStorage()
router = Router()
dp = Dispatcher(storage=storage)
client = AsyncOpenAI(api_key=OPENAI_API_KEY)


async def get_user_sub_info(id):
    url = f"https://avocado-production.up.railway.app/api/Subscription/GetUserSubDetail?tgId={id}"
    async with aiohttp.ClientSession() as session:
        try:
            async with session.get(url=url) as response:
                data = await response.text()
                data1 = json.loads(data)
                type_value = data1["type"]
                date_update = data1["dateUpdate"]
                formatted_date_update = datetime.fromisoformat(date_update).strftime("%Y-%m-%d")
                return type_value, formatted_date_update
        except aiohttp.ClientError as e:
            return False, e

def remove_tags(input_string):
    output = re.sub(r"</?br\s*/?>", "", input_string)
    output1 = re.sub(r'【.*?】', '', output)
    return output1

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
            
async def send_user_data(tg_id, data_json, method, data_name):
    url = f'https://avocado-production.up.railway.app/api/TypesCRUD/{method}'

    payload = {
        "tg_id": tg_id,
        f"{data_name}": data_json
    }
    print(payload)

    async with aiohttp.ClientSession() as session:
        try:
            async with session.post(url, json=payload) as response:
                if response.status != 200:
                    raise Exception(f"HTTP error! status: {response.status}")

                response_data = await response.json()
                print('Response:', response_data)
                return response_data
        except Exception as e:
            print('Error sending data:', e)
            raise

async def get_user_data(tg_id):
    url = f'https://avocado-production.up.railway.app/api/TypesCRUD/GetUserData?userTgId={tg_id}'

    async with aiohttp.ClientSession() as session:
        try:
            async with session.get(url) as response:
                if response.status != 200:
                    raise Exception(f"HTTP error! status: {response.status}")

                response_data = await response.json()
                print('Retrieved Data:', response_data)
                return response_data
        except Exception as e:
            print('Error retrieving data:', e)
            raise
            

async def fetch_user_data(user_tg_id, infotype):
    url = f"https://avocado-production.up.railway.app/api/TypesCRUD/GetUserData?userTgId={user_tg_id}"
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as response:
            if response.status == 200:
                text_response = await response.text()
                try:
                    data = json.loads(text_response)
                    return format_user_data(data, infotype)
                except json.JSONDecodeError:
                    print(f"Failed to parse JSON for user {user_tg_id}. Response: {text_response}")
                    return None
            else:
                print(f"Failed to fetch user data {user_tg_id}. Status: {response.status}")
                return None

def format_user_data(data, infotype):
    if infotype == "general":
        return {
            "user_data": {
                "age": data.get("age", ""),
                "gender": data.get("gender", ""),
                "location": data.get("location", ""),
                "allergy": data.get("allergy", ""),
                "lifestyle": data.get("lifestyle", ""),
                "phototype": data.get("phototype", ""),
                "activity": data.get("activity", ""),
                "water_intake": data.get("waterIntake", ""),
                "stress": data.get("stress", ""),
                "habits": data.get("habits", ""),
                "ethics": data.get("ethics", "")
            }
        }
    elif infotype == "face":
        return {
            "user_face_data": {
                "face_skin_type": data.get("faceskintype", ""),
                "face_skin_condition": data.get("faceskincondition", ""),
                "face_skin_issues": data.get("faceskinissues", ""),
                "face_skin_goals": data.get("faceskingoals", "")
            }
        }
    elif infotype == "body":
        return {
            "user_body_data": {
                "body_skin_type": data.get("bodyskintype", ""),
                "body_skin_sensitivity": data.get("bodyskinsensitivity", ""),
                "body_skin_condition": data.get("bodyskincondition", ""),
                "body_hair_issues": data.get("bodyhairissues", ""),
                "body_attention_areas": data.get("bodyattentionareas", ""),
                "body_goals": data.get("bodygoals", "")
            }
        }
    elif infotype == "hair":
        return {
            "user_hair_data": {
                "hair_scalp_type": data.get("hairscalptype", ""),
                "hair_thickness": data.get("hairthickness", ""),
                "hair_length": data.get("hairlength", ""),
                "hair_structure": data.get("hairstructure", ""),
                "hair_condition": data.get("haircondition", ""),
                "hair_goals": data.get("hairgoals", ""),
                "washing_frequency": data.get("hairwashingfrequency", ""),
                "current_products": data.get("haircurrentproducts", ""),
                "product_texture": data.get("hairproducttexture", ""),
                "sensitivity": data.get("hairsensitivity", ""),
                "styling_tools": data.get("hairstylingtools", "")
            }
        }
    else:
        print(f"Invalid infotype: {infotype}")
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
    
async def get_existing_topics():
    topics = await bot.get_forum_topics(CHAT_ID)
    return {topic.name: topic.message_thread_id for topic in topics.topics}
    
async def log_user_message(message):

    existing_topics = await get_existing_topics()
    user_id = message.from_user.id

    if str(user_id) not in existing_topics:
        topic = await bot.create_forum_topic(CHAT_ID, name=str(user_id))
        existing_topics[str(user_id)] = topic.message_thread_id

    if message.text:
        content = message.text
    elif message.photo:
        photo = message.photo[-1]
        content = f"📷 Photo: {photo.file_id}"
    elif message.voice:
        content = f"🎤 Voice: {message.voice.file_id}"
    elif message.document:
        content = f"📄 Document: {message.document.file_id}"
    elif message.video:
        content = f"🎥 Video: {message.video.file_id}"
    elif message.audio:
        content = f"🎵 Audio: {message.audio.file_id}"
    else:
        content = "Unsupported message type"

    await bot.send_message(
        chat_id=CHAT_ID,
        text=f"User {user_id} sent:\n{content}",
        message_thread_id=existing_topics[str(user_id)]
    )

async def log_user_callback(callback_query):

    existing_topics = await get_existing_topics()
    user_id = callback_query.from_user.id

    if str(user_id) not in existing_topics:
        topic = await bot.create_forum_topic(CHAT_ID, name=str(user_id))
        existing_topics[str(user_id)] = topic.message_thread_id

    await bot.send_message(
        chat_id=CHAT_ID,
        text=f"callback:{callback_query.data}",
        message_thread_id=existing_topics[str(user_id)]
    )

async def log_bot_response(text, user_id):
    existing_topics = await get_existing_topics()

    if str(user_id) not in existing_topics:
        topic = await bot.create_forum_topic(CHAT_ID, name=str(user_id))
        existing_topics[str(user_id)] = topic.message_thread_id

    await bot.send_message(
        chat_id=CHAT_ID,
        text=text,
        message_thread_id=existing_topics[str(user_id)]
    )