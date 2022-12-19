import logging
import aiogram
import functions as function
from os import getenv

# токен для бота берется из перменной окружения
token = getenv('TOKEN')
bot_creation = aiogram.Bot(token)

# Диспетчер для бота
dispatcher = aiogram.Dispatcher(bot_creation)

# Включаем логирование, чтобы не пропустить важные сообщения
logging.basicConfig(level=logging.INFO)

print('BOT IS ALIVE')


# Вывод стартового сообщения
@dispatcher.message_handler(aiogram.dispatcher.filters.Text(equals='/start'))
async def start(message):
    await message.reply(f'Приветствую, {message.from_user.first_name}! Меня зовут Прогнозист.'
                        f' Я понимаю только сообщения написанные на русском языке, а так же комманды,'
                        f' поэтому если вдруг у тебя что-то не получается, проверь раскладку своей клавиатуры 🙃')


# открытие клавиатуры по запросу пользователя
@dispatcher.message_handler(commands=['keyboard_open'])
async def open_keyboard(message):
    keyboard = aiogram.types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    buttons = ['🌦️ what_weather', '❓ help', '❌ close_keyboard', '📋 what_to_do']
    keyboard.add(*buttons)
    await message.answer("Клавиатура открыта", reply_markup=keyboard)

# закрытие клавиатуры
@dispatcher.message_handler(commands=['close_keyboard'])
@dispatcher.message_handler(aiogram.dispatcher.filters.Text(equals="❌ close_keyboard"))
async def close_keyboard(message):
    await message.reply("Клавиатура закрыта", reply_markup=aiogram.types.ReplyKeyboardRemove())


# эхо-функция на отправленные гифки
@dispatcher.message_handler(content_types=[aiogram.types.ContentType.ANIMATION])
async def echo_document(message: aiogram.types.Message):
    await message.reply_animation(message.animation.file_id)


@dispatcher.message_handler(commands=['what_weather'])
@dispatcher.message_handler(aiogram.dispatcher.filters.Text(equals='🌦️ what_weather'))
async def command_what_weather(message):
    await message.reply(function.command_what_weather())


@dispatcher.message_handler(lambda message: 'погод' in message.text.lower())
async def what_is_weather(message):
    city = function.what_city(message.text.lower())
    if not city:
        wrong_answer = 'Я не знаю такого города. Попробуйте написать строчку на русском языке: Погода Город'
        await message.reply(wrong_answer)
    else:
        weather = function.what_weather(city)
        await message.reply(f'Погода в городе {city}: {weather}')

@dispatcher.message_handler(commands=['what_to_do'])
@dispatcher.message_handler(lambda message: message.text.lower() == '📋 what_to_do')
async def advises_what_to_do(message):
    user_id = message['from']['id']
    doing = function.what_to_do(user_id=user_id)
    await message.reply(f'Не знаешь чем заняться? Предлагаю на сегодня следующее задание:\n{doing}')
""


# простая заглушка для обработки сообщений, не входящих в список комманд бота
# отвечает на сообщения пользователя через метод  message.reply


@dispatcher.message_handler(content_types=['text'])
async def unknown_message(message: aiogram.types.Message):
    await message.reply(f'Что-то ты не понятное напечатал. {function.failure_answer()}')
    # await message.reply("Test 1")


def run():
    aiogram.executor.start_polling(dispatcher, skip_updates=True)


if __name__ == "__main__":
    '''Запуск бота'''
    run()

# Хэндлер на команду /test1 или текст test1
# @dispatcher.message_handler(lambda message: message.text == 'test1') ---можно так
# а можно и так:
# @dispatcher.message_handler(aiogram.dispatcher.filters.Text(equals="test1"))
# async def cmd_test1(message: aiogram.types.Message):
#     await message.reply("Test 1")

# просто печатает сообщения в чат
# @dp.message_handler(commands="answer")
# async def cmd_answer(message: types.Message):
#     await message.answer("Это простой ответ")
