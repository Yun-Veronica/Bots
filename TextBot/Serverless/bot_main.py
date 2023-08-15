import logging
from os import getenv

from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram import Bot, Dispatcher, types
from aiogram.contrib.fsm_storage.memory import MemoryStorage

import json
import requests

SCENARIOS_URL = getenv("SCENARIOS_URL")
AVAILABLE_CHATS_URL = getenv("AVAILABLE_CHATS_URL")

YADISK_TOKEN = getenv("YADISK_TOKEN")
file_path_for_writting = getenv("PATH_FOR_WRITING_CONTACTS")
file_path = getenv("PATH_FOR_READING_CONTACTS")


# получение файла с номером телефона
def getting_link_to_download(path=file_path):
    final_url = f"https://cloud-api.yandex.net/v1/disk/public/resources/download?public_key={path}"
    response = requests.get(final_url)
    parse_href = response.json()['href']
    return parse_href


def get_text_from_file():
    to_download_from_link = getting_link_to_download()
    file = requests.get(to_download_from_link)
    text = dict(file.json())

    return text


def getting_link_to_upload():
    path = file_path_for_writting
    link = f"https://cloud-api.yandex.net/v1/disk/resources/upload"
    response = requests.get(link,
                            headers={"Authorization": f"OAuth {YADISK_TOKEN}", "Content-Type": "application/json"},
                            params={'fields': "href",
                                    "path": f"{path}",
                                    "overwrite": "true"})

    parse_href = response.json()['href']
    return parse_href


# запись файла с номером телефона и айди пользователя
def write_to_file(user_id, user_phone_num):
    text = get_text_from_file()
    text[str(user_id)] = str(user_phone_num)
    return text


def upload_to_disk(user_id, user_phone_num):
    to_download_from_link = getting_link_to_upload()
    # link=f"https://cloud-api.yandex.net/v1/disk/resources/download/?path={path}"
    data = json.dumps(write_to_file(user_id, user_phone_num))
    file = requests.put(to_download_from_link, data=data)
    return file


def get_available_chats():
    try:
        response = requests.get(AVAILABLE_CHATS_URL)
        response.raise_for_status()
        data = response.json()
        return data
    except Exception as e:
        return f"Failed to fetch data: {e}"


def get_bot_messages():
    bot_lines = {}
    response = requests.get(SCENARIOS_URL)
    response.raise_for_status()
    data = response.content.decode(encoding="UTF-8")
    for i in data.split('\r\n'):
        if i != "/n":
            line = i.split("=")
            line_key = line[0].strip().replace("/n", '')
            line_value = line[1].strip().replace("/n", '')
            bot_lines.setdefault(line_key, line_value)
    return bot_lines


# токен для бота берется из перменной окружения
token = getenv('TOKEN')
storage = MemoryStorage()
bot = Bot(token)

# Диспетчер для бота и инициализация хранилище в dp (Dispatcher)
dispatcher = Dispatcher(bot, storage=storage)

BOT_LINES = get_bot_messages()

CANCEL_BUTTON_TEXT = BOT_LINES["CANCEL_BUTTON_TEXT"]
KEYBOARD_BUTTTONS_TEXT = [*get_available_chats().keys()]

log = logging.getLogger(__name__)
log.setLevel('INFO')


# Вывод стартового сообщения
@dispatcher.message_handler(commands=['start'])
async def start(message: types.Message):
    keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    send_contact_keyboard_button = BOT_LINES["SEND_CONTACT_KEYBOARD_BUTTON"]
    keyboard.add(types.KeyboardButton(send_contact_keyboard_button, request_contact=True))
    greeting_and_asking_for_number_reply = BOT_LINES["GREET_AND_ASK_FOR_NUMBER"]
    await message.reply(greeting_and_asking_for_number_reply, reply_markup=keyboard)


@dispatcher.message_handler(commands=['help'])
async def start(message: types.Message):
    help_message = BOT_LINES["HELP_MESSAGE"]
    await message.reply(help_message)


@dispatcher.message_handler(content_types=types.ContentTypes.CONTACT)
async def handle_contact(message: types.Message):
    contact = message.contact
    phone_number = contact.phone_number
    user_id = contact.user_id
    getting_number_reply = BOT_LINES["THANKS_FOR_NUMBER"]

    try:
        result_of_writing = upload_to_disk(user_id=user_id, user_phone_num=phone_number)
        await message.reply(getting_number_reply)
        return result_of_writing
    except Exception as e:
        await message.reply(BOT_LINES["ERROR_DURING_SENDING"])
        return f"write_new_contact_to_file: {e}"


# Хэндлер, который будет запускаться при отправке сообщения боту
@dispatcher.message_handler(content_types=types.ContentTypes.TEXT)
async def start_sending(message: types.Message):
    inline_kb_full = InlineKeyboardMarkup(row_width=3)
    inline_kb_full.add(InlineKeyboardButton(f'{KEYBOARD_BUTTTONS_TEXT[0]}', callback_data='button1'))
    inline_kb_full.add(InlineKeyboardButton(f'{KEYBOARD_BUTTTONS_TEXT[1]}', callback_data='button2'))
    inline_kb_full.add(InlineKeyboardButton(f'{KEYBOARD_BUTTTONS_TEXT[2]}', callback_data='button3'))
    inline_kb_full.add(InlineKeyboardButton(f'{KEYBOARD_BUTTTONS_TEXT[3]}', callback_data='button4'))
    if CANCEL_BUTTON_TEXT != "":
        inline_kb_full.add(InlineKeyboardButton(f'{CANCEL_BUTTON_TEXT}', callback_data='cancel'))
    await message.reply(BOT_LINES["CHOOSE_THE_CHAT"], reply_markup=inline_kb_full)


@dispatcher.message_handler(content_types=types.ContentTypes.VOICE)
async def voice_msg_start_sending(message: types.Message):
    inline_kb_full = InlineKeyboardMarkup(row_width=3)
    inline_kb_full.add(InlineKeyboardButton(f'{KEYBOARD_BUTTTONS_TEXT[0]}', callback_data='button1'))
    inline_kb_full.add(InlineKeyboardButton(f'{KEYBOARD_BUTTTONS_TEXT[1]}', callback_data='button2'))
    inline_kb_full.add(InlineKeyboardButton(f'{KEYBOARD_BUTTTONS_TEXT[2]}', callback_data='button3'))
    inline_kb_full.add(InlineKeyboardButton(f'{KEYBOARD_BUTTTONS_TEXT[3]}', callback_data='button4'))
    if CANCEL_BUTTON_TEXT != "":
        inline_kb_full.add(InlineKeyboardButton(f'{CANCEL_BUTTON_TEXT}', callback_data='cancel'))
    await message.reply(BOT_LINES["CHOOSE_THE_CHAT"], reply_markup=inline_kb_full)


@dispatcher.callback_query_handler(lambda c: c.data == 'button1')
async def process_callback_button1(callback_query: types.CallbackQuery):
    await bot.answer_callback_query(callback_query.id)
    phone_number = get_text_from_file()[str(callback_query.from_user.id)]
    message_from_line = BOT_LINES["MESSAGE_FROM"]
    if callback_query.message.content_type == types.ContentTypes.VOICE:
        caption = f"{message_from_line} {callback_query.from_user.full_name} {phone_number}"

        # user_message = callback_query.message.reply_to_message.voice
        user_voice_message_id = callback_query.message.reply_to_message.voice.file_id
        # используем ID файла, чтобы получить сам файл
        user_message = await bot.get_file(user_voice_message_id)
        try:
            target_group_name = KEYBOARD_BUTTTONS_TEXT[0]
            target_group_id = get_available_chats()[target_group_name]["id"]
            await bot.send_audio(audio=user_message, chat_id=target_group_id, caption=caption)
            successful_sending_line = BOT_LINES["SUCCESSFUL_SENDING"]
            await callback_query.message.reply_to_message.reply(successful_sending_line)

        except Exception as e:
            error_line = BOT_LINES["ERROR_DURING_SENDING"]
            await callback_query.message.reply(error_line)
            return f"send_message_to_chat: {e}"
        return
    user_message = callback_query.message.reply_to_message.text
    message_to_send = f"{message_from_line} {callback_query.from_user.full_name} {phone_number}: \n{user_message}"
    try:
        target_group_name = KEYBOARD_BUTTTONS_TEXT[0]
        target_group_id = get_available_chats()[target_group_name]["id"]
        await bot.send_message(chat_id=target_group_id, text=message_to_send)
        successful_sending_line = BOT_LINES["SUCCESSFUL_SENDING"]
        await callback_query.message.reply_to_message.reply(successful_sending_line)

    except Exception as e:
        error_line = BOT_LINES["ERROR_DURING_SENDING"]
        await callback_query.message.reply(error_line)
        return f"send_message_to_chat: {e}"
    return


@dispatcher.callback_query_handler(lambda c: c.data == 'button2')
async def process_callback_button2(callback_query: types.CallbackQuery):
    await bot.answer_callback_query(callback_query.id)
    phone_number = get_text_from_file()[str(callback_query.from_user.id)]
    message_from_line = BOT_LINES["MESSAGE_FROM"]
    if callback_query.message.content_type == types.ContentTypes.VOICE:
        caption = f"{message_from_line} {callback_query.from_user.full_name} {phone_number}"

        # user_message = callback_query.message.reply_to_message.voice
        user_voice_message_id = callback_query.message.reply_to_message.voice.file_id
        # используем ID файла, чтобы получить сам файл
        user_message = await bot.get_file(user_voice_message_id)
        try:
            target_group_name = KEYBOARD_BUTTTONS_TEXT[1]
            target_group_id = get_available_chats()[target_group_name]["id"]
            await bot.send_audio(audio=user_message, chat_id=target_group_id, caption=caption)
            successful_sending_line = BOT_LINES["SUCCESSFUL_SENDING"]
            await callback_query.message.reply_to_message.reply(successful_sending_line)

        except Exception as e:
            error_line = BOT_LINES["ERROR_DURING_SENDING"]
            await callback_query.message.reply(error_line)
            return f"send_message_to_chat: {e}"
        return
    user_message = callback_query.message.reply_to_message.text
    message_to_send = f"{message_from_line} {callback_query.from_user.full_name} {phone_number}: \n{user_message}"
    try:
        target_group_name = KEYBOARD_BUTTTONS_TEXT[1]
        target_group_id = get_available_chats()[target_group_name]["id"]
        await bot.send_message(chat_id=target_group_id, text=message_to_send)
        successful_sending_line = BOT_LINES["SUCCESSFUL_SENDING"]
        await callback_query.message.reply_to_message.reply(successful_sending_line)

    except Exception as e:
        error_line = BOT_LINES["ERROR_DURING_SENDING"]
        await callback_query.message.reply(error_line)
        return f"send_message_to_chat: {e}"
    return


@dispatcher.callback_query_handler(lambda c: c.data == 'button3')
async def process_callback_button1(callback_query: types.CallbackQuery):
    await bot.answer_callback_query(callback_query.id)
    phone_number = get_text_from_file()[str(callback_query.from_user.id)]
    message_from_line = BOT_LINES["MESSAGE_FROM"]
    if callback_query.message.content_type == types.ContentTypes.VOICE:
        caption = f"{message_from_line} {callback_query.from_user.full_name} {phone_number}"

        # user_message = callback_query.message.reply_to_message.voice
        user_voice_message_id = callback_query.message.reply_to_message.voice.file_id
        # используем ID файла, чтобы получить сам файл
        user_message = await bot.get_file(user_voice_message_id)
        try:
            target_group_name = KEYBOARD_BUTTTONS_TEXT[2]
            target_group_id = get_available_chats()[target_group_name]["id"]
            await bot.send_audio(audio=user_message, chat_id=target_group_id, caption=caption)
            successful_sending_line = BOT_LINES["SUCCESSFUL_SENDING"]
            await callback_query.message.reply_to_message.reply(successful_sending_line)

        except Exception as e:
            error_line = BOT_LINES["ERROR_DURING_SENDING"]
            await callback_query.message.reply(error_line)
            return f"send_message_to_chat: {e}"
        return
    user_message = callback_query.message.reply_to_message.text
    message_to_send = f"{message_from_line} {callback_query.from_user.full_name} {phone_number}: \n{user_message}"
    try:
        target_group_name = KEYBOARD_BUTTTONS_TEXT[2]
        target_group_id = get_available_chats()[target_group_name]["id"]
        await bot.send_message(chat_id=target_group_id, text=message_to_send)
        successful_sending_line = BOT_LINES["SUCCESSFUL_SENDING"]
        await callback_query.message.reply_to_message.reply(successful_sending_line)

    except Exception as e:
        error_line = BOT_LINES["ERROR_DURING_SENDING"]
        await callback_query.message.reply(error_line)
        return f"send_message_to_chat: {e}"
    return


@dispatcher.callback_query_handler(lambda c: c.data == 'button4')
async def process_callback_button1(callback_query: types.CallbackQuery):
    await bot.answer_callback_query(callback_query.id)
    phone_number = get_text_from_file()[str(callback_query.from_user.id)]
    message_from_line = BOT_LINES["MESSAGE_FROM"]
    if callback_query.message.content_type == types.ContentTypes.VOICE:
        caption = f"{message_from_line} {callback_query.from_user.full_name} {phone_number}"

        # user_message = callback_query.message.reply_to_message.voice
        user_voice_message_id = callback_query.message.reply_to_message.voice.file_id
        # используем ID файла, чтобы получить сам файл
        user_message = await bot.get_file(user_voice_message_id)
        try:
            target_group_name = KEYBOARD_BUTTTONS_TEXT[3]
            target_group_id = get_available_chats()[target_group_name]["id"]
            await bot.send_audio(audio=user_message, chat_id=target_group_id, caption=caption)
            successful_sending_line = BOT_LINES["SUCCESSFUL_SENDING"]
            await callback_query.message.reply_to_message.reply(successful_sending_line)

        except Exception as e:
            error_line = BOT_LINES["ERROR_DURING_SENDING"]
            await callback_query.message.reply(error_line)
            return f"send_message_to_chat: {e}"
        return
    user_message = callback_query.message.reply_to_message.text
    message_to_send = f"{message_from_line} {callback_query.from_user.full_name} {phone_number}: \n{user_message}"
    try:
        target_group_name = KEYBOARD_BUTTTONS_TEXT[3]
        target_group_id = get_available_chats()[target_group_name]["id"]
        await bot.send_message(chat_id=target_group_id, text=message_to_send)
        successful_sending_line = BOT_LINES["SUCCESSFUL_SENDING"]
        await callback_query.message.reply_to_message.reply(successful_sending_line)

    except Exception as e:
        error_line = BOT_LINES["ERROR_DURING_SENDING"]
        await callback_query.message.reply(error_line)
        return f"send_message_to_chat: {e}"
    return


@dispatcher.callback_query_handler(lambda c: c.data == 'cancel')
async def process_callback_cancel_button(callback_query: types.CallbackQuery):
    await bot.answer_callback_query(callback_query.id)
    canceled_line = BOT_LINES["LINE_CANCELED"]
    await callback_query.message.reply(canceled_line)


async def process_event(event):
    """
    Converting an Yandex.Cloud functions event to an update and
    handling tha update.
    """

    update = json.loads(event['body'])
    log.debug('Update: ' + str(update))

    Bot.set_current(dispatcher.bot)
    update = types.Update.to_object(update)
    await dispatcher.process_update(update)


async def handler(event, context):
    """Yandex.Cloud functions handler."""

    if event['httpMethod'] == 'POST':
        if 'body' not in event or not event['body']:
            # Если данные отсутствуют или пусты, вернуть ошибку "Bad Request"
            return {'statusCode': 400, 'body': 'Bad Request'}

        try:
            # Попытка преобразовать данные в формат JSON
            request_data = json.loads(event['body'])
        except json.JSONDecodeError:
            # Если данные некорректны, вернуть ошибку "Bad Request"
            return {'statusCode': 400, 'body': 'Invalid JSON data'}

        await process_event(event)
        return {'statusCode': 200, 'body': 'ok'}

    return {'statusCode': 405}
