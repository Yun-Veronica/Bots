import logging
from os import getenv

from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram import Bot, Dispatcher, types
from aiogram.contrib.fsm_storage.memory import MemoryStorage

import json
import boto3

SCENARIOS_KEY = getenv("SCENARIOS_KEY")
AVAILABLE_CHATS_KEY = getenv("AVAILABLE_CHATS_KEY")

KEY_FOR_WRITING_CONTACTS = getenv("KEY_FOR_WRITING_CONTACTS")
BUCKET_NAME = getenv("BUCKET_NAME")
YANDEX_CLOUD_ACCESS_KEY = getenv("YANDEX_CLOUD_ACCESS_KEY")
YANDEX_CLOUD_SECRET_ACCESS_KEY = getenv("YANDEX_CLOUD_SECRET_ACCESS_KEY")

# Yandex Objext Storage Access
boto = boto3.client(
    's3',
    aws_access_key_id=YANDEX_CLOUD_ACCESS_KEY,
    aws_secret_access_key=YANDEX_CLOUD_SECRET_ACCESS_KEY,
    region_name='ru-central1',
    endpoint_url='https://storage.yandexcloud.net',

)


def get_json_text_from_file(key=KEY_FOR_WRITING_CONTACTS):
    """
    Getting conten of json file from bucket
    :param key: string, key for object in bucket (name and extension, example: "file.json")
    :return: content of json file
    """
    try:
        get_object_response = boto.get_object(Bucket=BUCKET_NAME, Key=key)
        content = json.loads(get_object_response['Body'].read())
        return content
    except Exception as e:
        return f"Failed to fetch data: {e}"


def write_to_file(user_id, user_phone_num):
    """
    Writing info to the cloud object
    :param user_id: id of user
    :param user_phone_num: phone_number_of_user
    :return:
    """
    text = get_json_text_from_file(key=KEY_FOR_WRITING_CONTACTS)
    text[str(user_id)] = str(user_phone_num)
    info_to_write = json.dumps(text)
    resp = boto.put_object(Bucket=BUCKET_NAME, Key=KEY_FOR_WRITING_CONTACTS, Body=info_to_write,
                           StorageClass='STANDARD')
    return resp


get_available_chats = get_json_text_from_file(AVAILABLE_CHATS_KEY)


def get_bot_messages():
    bot_lines = {}
    get_object_response = boto.get_object(Bucket=BUCKET_NAME, Key=SCENARIOS_KEY)
    content = get_object_response['Body'].read()
    data = content.decode(encoding="UTF-8")
    for i in data.split('\r\n'):
        if i != "/n":
            line = i.split("=")
            line_key = line[0].strip().replace("/n", '')
            line_value = line[1].strip().replace("/n", '')
            bot_lines.setdefault(line_key, line_value)
    return bot_lines


token = getenv('TOKEN')
storage = MemoryStorage()
bot = Bot(token)

dispatcher = Dispatcher(bot, storage=storage)

BOT_LINES = get_bot_messages()

CANCEL_BUTTON_TEXT = BOT_LINES["CANCEL_BUTTON_TEXT"]
KEYBOARD_BUTTONS_TEXT = [*get_available_chats.keys()]
GROUP_NAME_FOR_COPIES = KEYBOARD_BUTTONS_TEXT[3]

log = logging.getLogger(__name__)
log.setLevel('INFO')


async def send_text_message(user_message, user_full_name, phone_number, target_group_name, type="orginal",
                            original_group_name=""):
    """

    :param user_message: message that will be sent
    :param user_full_name: full name of the user from whom message was received
    :param phone_number: phone number of user
    :param target_group_name: name of the group to which message will be sent to
    :param type: string, 'original' or 'copy'
    :param original_group_name: if "type" is copy, then there must be the name of group where it was originally sent to
    :return: none
    """
    message_from_line = BOT_LINES["MESSAGE_FROM"]
    message_from_group_line = BOT_LINES["MESSAGE_FROM_GROUP"]
    target_group_id = get_available_chats[target_group_name]["id"]

    if type == "copy":
        real_name_of_group = get_available_chats[original_group_name]['real_name']
        message_to_send = f"{message_from_line} {user_full_name} {phone_number} {message_from_group_line} {real_name_of_group}: \n{user_message}"
    else:
        message_to_send = f"{message_from_line} {user_full_name} {phone_number}: \n{user_message}"

    await bot.send_message(chat_id=target_group_id, text=message_to_send)


async def send_voice_message(user_voice_message_id, user_full_name, phone_number, target_group_name, type="orginal",
                             original_group_name=""):
    """

    :param user_voice_message_id: id of voice message that will be sent to group
    :param user_full_name: full name of the user from whom message was received
    :param phone_number:  phone number of user
    :param target_group_name: ame of the group to which message will be sent to
    :param type:  string, 'original' or 'copy'
    :param original_group_name: if "type" is copy, then there must be the name of group where it was originally sent to
    :return: none
    """
    message_from_line = BOT_LINES["MESSAGE_FROM"]
    message_from_group_line = BOT_LINES["MESSAGE_FROM_GROUP"]
    target_group_id = get_available_chats[target_group_name]["id"]

    if type == "copy":
        real_name_of_group = get_available_chats[original_group_name]['real_name']
        caption = f"{message_from_line} {user_full_name} {phone_number} {message_from_group_line} {real_name_of_group}"
    else:
        caption = f"{message_from_line} {user_full_name} {phone_number}"

    await bot.send_voice(voice=str(user_voice_message_id), chat_id=target_group_id, caption=caption)


@dispatcher.message_handler(commands=['start'])
async def start(message: types.Message):
    keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    send_contact_keyboard_button = BOT_LINES["SEND_CONTACT_KEYBOARD_BUTTON"]
    keyboard.add(types.KeyboardButton(send_contact_keyboard_button, request_contact=True))
    greeting_and_asking_for_number_reply = BOT_LINES["GREET_AND_ASK_FOR_NUMBER"]
    await message.reply(greeting_and_asking_for_number_reply, reply_markup=keyboard)


@dispatcher.message_handler(commands=['help'])
async def help(message: types.Message):
    help_message = BOT_LINES["HELP_MESSAGE"]
    await message.reply(help_message)


@dispatcher.message_handler(content_types=types.ContentTypes.CONTACT)
async def handle_contact(message: types.Message):
    contact = message.contact
    phone_number = contact.phone_number
    user_id = contact.user_id
    getting_number_reply = BOT_LINES["THANKS_FOR_NUMBER"]

    try:
        result_of_writing = write_to_file(user_id=user_id, user_phone_num=phone_number)
        await message.reply(getting_number_reply)
        return result_of_writing
    except Exception as e:
        await message.reply(BOT_LINES["ERROR_DURING_SENDING"])
        return f"write_new_contact_to_file: {e}"


@dispatcher.message_handler(content_types=types.ContentTypes.TEXT)
async def text_msg_start_sending(message: types.Message):
    inline_kb_full = InlineKeyboardMarkup(row_width=3)
    inline_kb_full.add(InlineKeyboardButton(f'{KEYBOARD_BUTTONS_TEXT[0]}', callback_data='button1'))
    inline_kb_full.add(InlineKeyboardButton(f'{KEYBOARD_BUTTONS_TEXT[1]}', callback_data='button2'))
    inline_kb_full.add(InlineKeyboardButton(f'{KEYBOARD_BUTTONS_TEXT[2]}', callback_data='button3'))
    inline_kb_full.add(InlineKeyboardButton(f'{KEYBOARD_BUTTONS_TEXT[3]}', callback_data='button4'))
    if CANCEL_BUTTON_TEXT != "":
        inline_kb_full.add(InlineKeyboardButton(f'{CANCEL_BUTTON_TEXT}', callback_data='cancel'))
    await message.reply(BOT_LINES["CHOOSE_THE_CHAT"], reply_markup=inline_kb_full)


@dispatcher.message_handler(content_types=types.ContentTypes.VOICE)
async def voice_msg_start_sending(message: types.Message):
    inline_kb_full = InlineKeyboardMarkup(row_width=3)
    inline_kb_full.add(InlineKeyboardButton(f'{KEYBOARD_BUTTONS_TEXT[0]}', callback_data='button1'))
    inline_kb_full.add(InlineKeyboardButton(f'{KEYBOARD_BUTTONS_TEXT[1]}', callback_data='button2'))
    inline_kb_full.add(InlineKeyboardButton(f'{KEYBOARD_BUTTONS_TEXT[2]}', callback_data='button3'))
    inline_kb_full.add(InlineKeyboardButton(f'{KEYBOARD_BUTTONS_TEXT[3]}', callback_data='button4'))
    if CANCEL_BUTTON_TEXT != "":
        inline_kb_full.add(InlineKeyboardButton(f'{CANCEL_BUTTON_TEXT}', callback_data='cancel'))
    await message.reply(BOT_LINES["CHOOSE_THE_CHAT"], reply_markup=inline_kb_full)


@dispatcher.callback_query_handler(lambda c: c.data == 'button1')
async def process_callback_button1(callback_query: types.CallbackQuery):
    await bot.answer_callback_query(callback_query.id)
    phone_number = get_json_text_from_file()[str(callback_query.from_user.id)]
    user_full_name = callback_query.from_user.full_name
    target_group_name = KEYBOARD_BUTTONS_TEXT[0]

    try:
        if callback_query.message.reply_to_message.content_type == "voice":
            user_voice_message_id = callback_query.message.reply_to_message.voice.file_id

            await send_voice_message(user_voice_message_id=user_voice_message_id, user_full_name=user_full_name,
                                     phone_number=phone_number, target_group_name=target_group_name)
            await send_voice_message(user_voice_message_id=user_voice_message_id, user_full_name=user_full_name,
                                     phone_number=phone_number, target_group_name=GROUP_NAME_FOR_COPIES,
                                     type="copy", original_group_name=target_group_name)
        else:
            user_message = callback_query.message.reply_to_message.text

            await send_text_message(user_message=user_message, user_full_name=user_full_name,
                                    phone_number=phone_number, target_group_name=target_group_name)

            await send_text_message(user_message=user_message, user_full_name=user_full_name,
                                    phone_number=phone_number, target_group_name=GROUP_NAME_FOR_COPIES,
                                    type="copy", original_group_name=target_group_name)

        successful_sending_line = BOT_LINES["SUCCESSFUL_SENDING"]
        await callback_query.message.reply_to_message.reply(successful_sending_line)

    except Exception as e:
        error_line = BOT_LINES["ERROR_DURING_SENDING"]
        await callback_query.message.reply(error_line)
        return f"process_callback_button1: {e}"
    return


@dispatcher.callback_query_handler(lambda c: c.data == 'button2')
async def process_callback_button2(callback_query: types.CallbackQuery):
    await bot.answer_callback_query(callback_query.id)
    phone_number = get_json_text_from_file()[str(callback_query.from_user.id)]
    user_full_name = callback_query.from_user.full_name
    target_group_name = KEYBOARD_BUTTONS_TEXT[1]

    try:
        if callback_query.message.reply_to_message.content_type == "voice":
            user_voice_message_id = callback_query.message.reply_to_message.voice.file_id

            await send_voice_message(user_voice_message_id=user_voice_message_id, user_full_name=user_full_name,
                                     phone_number=phone_number, target_group_name=target_group_name)
            await send_voice_message(user_voice_message_id=user_voice_message_id, user_full_name=user_full_name,
                                     phone_number=phone_number, target_group_name=GROUP_NAME_FOR_COPIES,
                                     type="copy", original_group_name=target_group_name)
        else:
            user_message = callback_query.message.reply_to_message.text

            await send_text_message(user_message=user_message, user_full_name=user_full_name,
                                    phone_number=phone_number, target_group_name=target_group_name)
            await send_text_message(user_message=user_message, user_full_name=user_full_name,
                                    phone_number=phone_number, target_group_name=GROUP_NAME_FOR_COPIES,
                                    type="copy", original_group_name=target_group_name)

        successful_sending_line = BOT_LINES["SUCCESSFUL_SENDING"]
        await callback_query.message.reply_to_message.reply(successful_sending_line)

    except Exception as e:
        error_line = BOT_LINES["ERROR_DURING_SENDING"]
        await callback_query.message.reply(error_line)
        return f"process_callback_button2: {e}"
    return


@dispatcher.callback_query_handler(lambda c: c.data == 'button3')
async def process_callback_button3(callback_query: types.CallbackQuery):
    await bot.answer_callback_query(callback_query.id)
    phone_number = get_json_text_from_file()[str(callback_query.from_user.id)]
    user_full_name = callback_query.from_user.full_name
    target_group_name = KEYBOARD_BUTTONS_TEXT[2]

    try:
        if callback_query.message.reply_to_message.content_type == "voice":
            user_voice_message_id = callback_query.message.reply_to_message.voice.file_id

            await send_voice_message(user_voice_message_id=user_voice_message_id, user_full_name=user_full_name,
                                     phone_number=phone_number, target_group_name=target_group_name)
            await send_voice_message(user_voice_message_id=user_voice_message_id, user_full_name=user_full_name,
                                     phone_number=phone_number, target_group_name=GROUP_NAME_FOR_COPIES,
                                     type="copy", original_group_name=target_group_name)
        else:
            user_message = callback_query.message.reply_to_message.text

            await send_text_message(user_message=user_message, user_full_name=user_full_name,
                                    phone_number=phone_number, target_group_name=target_group_name)
            await send_text_message(user_message=user_message, user_full_name=user_full_name,
                                    phone_number=phone_number, target_group_name=GROUP_NAME_FOR_COPIES,
                                    type="copy", original_group_name=target_group_name)

        successful_sending_line = BOT_LINES["SUCCESSFUL_SENDING"]
        await callback_query.message.reply_to_message.reply(successful_sending_line)

    except Exception as e:
        error_line = BOT_LINES["ERROR_DURING_SENDING"]
        await callback_query.message.reply(error_line)
        return f"process_callback_button3: {e}"
    return


@dispatcher.callback_query_handler(lambda c: c.data == 'button4')
async def process_callback_button4(callback_query: types.CallbackQuery):
    await bot.answer_callback_query(callback_query.id)
    phone_number = get_json_text_from_file()[str(callback_query.from_user.id)]
    user_full_name = callback_query.from_user.full_name
    target_group_name = KEYBOARD_BUTTONS_TEXT[3]

    try:
        if callback_query.message.reply_to_message.content_type == "voice":
            user_voice_message_id = callback_query.message.reply_to_message.voice.file_id

            await send_voice_message(user_voice_message_id=user_voice_message_id, user_full_name=user_full_name,
                                     phone_number=phone_number, target_group_name=target_group_name)

        else:
            user_message = callback_query.message.reply_to_message.text

            await send_text_message(user_message=user_message, user_full_name=user_full_name,
                                    phone_number=phone_number, target_group_name=target_group_name)

        successful_sending_line = BOT_LINES["SUCCESSFUL_SENDING"]
        await callback_query.message.reply_to_message.reply(successful_sending_line)

    except Exception as e:
        error_line = BOT_LINES["ERROR_DURING_SENDING"]
        await callback_query.message.reply(error_line)
        return f"process_callback_button3: {e}"
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
            return {'statusCode': 400, 'body': 'Bad Request'}

        try:
            request_data = json.loads(event['body'])
        except json.JSONDecodeError:
            return {'statusCode': 400, 'body': 'Invalid JSON data'}

        await process_event(event)
        return {'statusCode': 200, 'body': 'ok'}

    return {'statusCode': 405}
