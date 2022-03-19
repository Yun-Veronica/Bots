# Отчет Портфель
# Компания №1:
#   количество: 5
#   средняя цена за акцию в портфеле: 133.3
#   текущая цена за акцию: 150
#   итог(прибыль или убыток): убыток

# Компания №2:
#   Количество: 10
#   Средняя цена : 200
#   Текущая цена : 200
#   Итог : Прибыль = 0
#


import logging
from aiogram import Bot, Dispatcher, executor, types
import os
import json
from random import randint


def read_db():
    '''
    чтение данных из файла дб
    :return: считатный словарь
    '''
    file_path = 'BotDB.json'
    with open(file_path, 'r', encoding='UTF-8') as db_file:
        db = json.load(db_file)

    return db


def remove_from_bd(company_index, user_id, date=False):
    db = read_db()
    user_id = str(user_id)
    if not date:
        del (db[user_id][company_index])
    else:
        del (db[user_id][company_index][date])

    write_db(db, user_id)
    # return 'Successfully deleted'
    return True


def write_db(new_data: dict, user_id):
    '''
    запись данных в файл бд
    :param new_data: словарь, в котором находятя все новые данные
    :return:
    '''
    file_path = 'BotDB.json'
    db = read_db()
    user_id = str(user_id)
    if not (user_id in db):
        new_data_ = {user_id: new_data}
        db.update(new_data_)
    else:
        db[user_id].update(new_data)

    with open(file_path, 'w', encoding='UTF-8') as db_file:
        json.dump(db, fp=db_file, indent=1)

    return 1


def count_avg(db: dict):
    '''
    Расчет средней цены за акцию
    :param db: словарь для компании {"date":[price1, amount1]}
    :return: int,среднюю цену за акцию
    '''
    # formula: su
    all_amount_of_shares = 0
    sum_of_all_shares = 0
    for date in db:
        if date != 'Company':
            amount = db[date][1]
            price = db[date][0]
            sum_of_all_shares += (int(price) * int(amount))
            all_amount_of_shares += int(amount)

    avg = sum_of_all_shares // all_amount_of_shares
    return avg


def is_profit(shares_avg_price, price_for_now):
    '''
    считает это прибыль или убыток
    :param shares_avg_price: средняя цена акции в портфеле
    :param price_for_now: текущая цена акции
    :return: возвращает "прибыль", "убыль" или "мель/равно"
    '''
    profit_sum = shares_avg_price - price_for_now
    if profit_sum == 0:
        return ' 0'
    else:
        return f' {profit_sum:+}'


def make_text(data, company_code):
    """
     подготавливает данные для выгрузки
    :param data: словарь со значениями  пользователя
    :param company_code: код компании
    :return: словарь с готовыми значениями для таблицы
    """
    company_data = data[company_code]
    company_name = company_data['Company']
    amount = 0
    price_for_now = 0
    result = 0
    avg = 0
    max_date = '0'

    for date in company_data:
        if date != 'Company':
            shares = company_data[date]
            # ищем текущую цену
            if date > max_date:
                max_date = date
                price_for_now = int(shares[0])
            amount += int(shares[1])

    avg = count_avg(company_data)
    result = is_profit(shares_avg_price=avg, price_for_now=price_for_now)
    # добавление новых записей в список
    full_table = {
        'Код компании': company_code,
        'Компания': company_name,
        'Количество': amount,
        'Моя цена': avg,
        'Текущая цена': price_for_now,
        'Итог': result,
    }

    return full_table


def make_msg(text: dict):
    '''
    Создает валидное сообщение для пользователя
    :param text: id пользователя, который общается с ботом
    :return:
    '''
    ready_msg = ''
    for key in text:
        ready_msg += f'* {key} : {text[key]}\n'
    ready_msg += '\n'
    return ready_msg


def run_report(user_id):
    '''
    функция запуска создания отчета
    :param user_id: id пользователя, который общается с ботом
    :return: отчет для определенного пользователя
    '''
    # пример: user_id = 820453395
    data = read_db()
    user_data = data[str(user_id)]
    msg = ''

    for companies in user_data:
        ready_data = make_text(user_data, companies)
        msg += make_msg(ready_data)
    return msg


def write_down(msg):
    # print(user_id, msg)
    msg_data = msg.split(':')
    code = msg_data[0]
    company = msg_data[1]
    date = msg_data[2]
    summ = msg_data[3]
    amount = msg_data[4]

    ready_dict = {code: {"Company": company, date: [summ, amount]}}

    return ready_dict


def run_writing_down(id, text):
    new_data = write_down(text)
    write_db(new_data, id)
    # return 'Successfully written'
    return True


def take_answer(message_id, user_id, text):
    if run_writing_down(user_id, text):
        id = int(f"{message_id}{user_id}{randint(0, 25)}")
        # Todo запись во вторую таблицу
        return f"Данные о компании и акции записаны. Id операции:{id}"


# Объект бота
token = os.getenv(key="INVEST_BOT_TOKEN")
bot = Bot(token=token)

# Диспетчер для бота
dp = Dispatcher(bot)

# Включаем логирование, чтобы не пропустить важные сообщения
logging.basicConfig(level=logging.INFO)


# Todo : Дописать механику бота: удаление компании из бд и добавить боту через BotFather команды(help,delete, etc )
# Todo: Запуск бота в serverless: Yandex functions
# Todo: Запуск бота в serverless: Yandex functions и переписать с исп настоящей БД
# Todo :Добавить функцию создания id and second db, that could store all operations with their id

@dp.message_handler(commands="report")
async def cmd_report(message: types.Message):
    # await message.reply(f"{message.from_user.username}, К сожалению данная функция находится в разработке.")
    await message.reply(
        f"{message.from_user.username}, вот Ваш Отчет Портфель: \n\n {run_report(message.from_user.id)}")

    # await message.reply(f" {message.from_user.username}")


@dp.message_handler(commands="start")
async def cmd_report(message: types.Message):
    await message.reply(f"Приветствую, {message.from_user.username}")


@dp.message_handler(commands="add")
async def cmd_add(message: types.Message):
    # await message.reply(f"{message.from_user.username}, К сожалению данная функция находится в разработке.")
    await message.reply(
        f"{message.from_user.username}, ответьте на это сообщение в следующем формате:\n Индекс Компании:компания:дата в формате дд.мм.гггг:цена за акцию:количество ")


@dp.message_handler(commands="delete_company")
async def cmd_delete(message: types.Message):
    # await message.reply(f"{message.from_user.username}, К сожалению данная функция находится в разработке.")
    await message.reply(f"{message.from_user.username}, введите Индекс Компании ответом на это сообщение")


@dp.message_handler(commands="delete_operation")
async def cmd_delete(message: types.Message):
    # await message.reply(f"{message.from_user.username}, К сожалению данная функция находится в разработке.")
    await message.reply(f"{message.from_user.username}, введите id операции ответом на это сообщение ")
    # await message.reply(
    #     f"{message.from_user.username}, вот Ваш Отчет Портфель: \n\n {run_report(message.from_user.id)}")

    # await message.reply(f" {message.from_user.username}")


@dp.message_handler(content_types="text")
async def messages_id(message: types.Message):
    if message.reply_to_message:
        if message.message_id - message.reply_to_message["message_id"] == 1 and "id операции " in \
                message.reply_to_message["text"]:
            # Todo: доработать эту функцию, должен удалять определенную операцию по ее id
            await message.reply(f"Операция №{message.text} удалена")
        elif message.message_id - message.reply_to_message["message_id"] == 1 and "Индекс Компании:компания:" in \
                message.reply_to_message["text"]:
            await message.reply(
                take_answer(message_id=message.message_id, user_id=message.from_user.id, text=message.text))
        elif message.message_id - message.reply_to_message["message_id"] == 1 and "Индекс Компании" in \
                message.reply_to_message["text"]:
            if remove_from_bd(company_index=message.text, user_id=message.from_user.id):
                await message.reply(f"Компании с индексом '{message.text}' удалена")

    else:
        await message.reply('Я не понимаю')


# TODO: добавить комментарии в репозиторий на гитхаб для бота и комметарии к выводу, бд, к каждой функции
#  и тому что в целом делает бот

if __name__ == "__main__":
    # Запуск бота
    executor.start_polling(dp, skip_updates=True)
