from aiogram.dispatcher.filters.state import State, StatesGroup
from aiogram import Bot, Dispatcher, executor, types
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.dispatcher import FSMContext
from os import getenv
import json
import logging
from aiogram.contrib.middlewares.logging import LoggingMiddleware


def get_bot_messages():
    bot_lines = {}
    with open("bot_text_scenarios.txt", "r", encoding="UTF-8") as read_file:
        data = read_file.readlines()
        for i in data:
            if i != "/n":
                line = i.split("=")
                line_key = line[0].strip().replace("/n", '')
                line_value = line[1].strip().replace("/n", '')
                bot_lines.setdefault(line_key, line_value)
    return bot_lines


def reading_file(file_name="available_chats.json"):
    with open(file_name, "r", encoding="UTF-8") as read_file:
        data = json.load(read_file)
    return data


def write_new_contact_to_file(user_id, phone_number, file_name="settings.json"):
    data = reading_file(file_name)
    try:
        if data[user_id] in data:
            return
    except KeyError:
        data[user_id] = str(phone_number)
        with open(file_name, "w") as file:
            try:
                json.dump(data, file)
            except Exception as e:
                logging.exception("write_new_contact_to_file: ", exc_info=e)
            return True


# токен для бота берется из перменной окружения
token = getenv('TOKEN')
storage = MemoryStorage()
bot = Bot(token)

# # Диспетчер для бота и инициализация хранилище в dp (Dispatcher)
dispatcher = Dispatcher(bot, storage=storage)

# Включаем логирование, чтобы не пропустить важные сообщения
logging.basicConfig(filename="logs.txt", level=logging.INFO)
dispatcher.middleware.setup(LoggingMiddleware())

BOT_LINES = get_bot_messages()

print('BOT IS ALIVE')


# Вывод стартового сообщения
@dispatcher.message_handler(commands=['start'])
async def start(message: types.Message):
    keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    send_contact_keyboard_button = BOT_LINES["SEND_CONTACT_KEYBOARD_BUTTON"]
    keyboard.add(types.KeyboardButton(send_contact_keyboard_button, request_contact=True))
    greeting_and_asking_for_number_reply = BOT_LINES["GREET_AND_ASK_FOR_NUMBER"]

    await message.reply(greeting_and_asking_for_number_reply, reply_markup=keyboard)


@dispatcher.message_handler(content_types=types.ContentTypes.CONTACT)
async def handle_contact(message: types.Message):
    contact = message.contact
    phone_number = contact.phone_number
    user_id = contact.user_id
    write_new_contact_to_file(str(user_id), str(phone_number))
    getting_number_reply = BOT_LINES["THANKS_FOR_NUMBER"]
    await message.reply(getting_number_reply)
    return


CANCEL_BUTTON_TEXT = BOT_LINES["CANCEL_BUTTON_TEXT"]


class UserState(StatesGroup):
    WaitingForMessage = State()
    WaitingForChat = State()


# Хэндлер, который будет запускаться при отправке сообщения боту
@dispatcher.message_handler(state=None)
async def start_sending(message: types.Message, state: FSMContext):
    # Переход в состояние WaitingForMessage и ожидание сообщения от пользователя
    await state.update_data(message_to_send=message.text)

    # Сохранение сообщения пользователя в состояние
    keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=3, one_time_keyboard=True)
    if CANCEL_BUTTON_TEXT != "":
        keyboard_buttons = [*reading_file().keys(), CANCEL_BUTTON_TEXT]
    else:
        keyboard_buttons = [*reading_file().keys()]
    keyboard.add(*keyboard_buttons)
    await message.reply(BOT_LINES["CHOOSE_THE_CHAT"], reply_markup=keyboard)

    # Переход в состояние WaitingForChat и ожидание выбора чата пользователем
    await UserState.WaitingForChat.set()



# Хэндлер для получения выбора чата от пользователя
@dispatcher.message_handler(state=UserState.WaitingForChat)
async def send_message_to_chat(message: types.Message, state: FSMContext):
    # Получение данных из состояния (сообщения и ID сообщения для отправки)
    data = await state.get_data()
    user_message = data.get("message_to_send")
    phone_number = reading_file(file_name="settings.json")[str(message.from_user.id)]
    message_from_line = BOT_LINES["MESSAGE_FROM"]
    message_to_send = f"{message_from_line} {message.from_user.full_name} {phone_number}: \n{user_message}"

    # Проверяем, не является ли полученное сообщение командой отмены
    if CANCEL_BUTTON_TEXT != "" and message.text == CANCEL_BUTTON_TEXT:
        canceled_line = BOT_LINES["LINE_CANCELED"]
        await message.reply(canceled_line)
        # Сбрасываем состояния пользователя
        await state.finish()
    else:
        # В переменной message.text хранится ID или название группы, куда нужно отправить сообщение
        target_group_name = message.text
        try:

            # Отправляем сообщение в указанную группу
            target_group_id = reading_file()[target_group_name]["id"]
            await bot.send_message(chat_id=target_group_id, text=message_to_send)

        except Exception as e:
            logging.exception("send_message_to_chat: ", exc_info=e)
            error_line = BOT_LINES["ERROR_DURING_SENDING"]
            await message.reply(error_line)

        # Сбрасываем состояния пользователя
        await state.finish()


# Запуск бота для пк
def run():
    executor.start_polling(dispatcher, skip_updates=True)


if __name__ == "__main__":
    '''Запуск бота'''
    run()
