import secrets
import time
from http import client

import telebot
import psycopg2
from telebot import types
from telebot.apihelper import create_chat_invite_link

conn = psycopg2.connect(dbname="tg", host="localhost", user="postgres", password="postgrespw", port="32770")
cursor = conn.cursor()
conn.autocommit = True

def refresh_cursor():
    global cursor
    cursor.close()
    cursor = conn.cursor()


cursor.execute("SELECT botkey FROM botsettings where botsettingid = 1")
token_row = cursor.fetchone()
token = str(token_row[0])
bot = telebot.TeleBot(token)
channel_id = '-1001962381384'
cursor.execute("SELECT botkey FROM botsettings where botsettingid = 2")
adminToken_row = cursor.fetchone()
adminToken = str(adminToken_row[0])
cursor.execute("SELECT adminuserid FROM botsettings where botsettingid = 2")
adminUserId_row = cursor.fetchone()
adminUserID = str(adminUserId_row[0])

print(bot.get_chat_member("-1001962381384",326646054))


def create_keyboard():
    keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)
    button_invite = types.KeyboardButton('/invite')
    button_balance = types.KeyboardButton('/balance')
    button_withdraw = types.KeyboardButton('/withdraw')
    keyboard.add(button_invite, button_balance, button_withdraw)
    return keyboard


referral_dict = {}
@bot.message_handler(commands=['invite'])
def generate_invite_link(message):
    user_id = message.from_user.id


    invite_link = bot.create_chкat_invite_link(channel_id, member_limit=1)

    # Запись информации о пригласившем пользователе в базу данных
    cursor.execute("INSERT INTO referrals (inviter_tgid, referral_tgid) VALUES (%s, NULL)", (str(user_id),))
    conn.commit()

    bot.send_message(user_id, f"Приглашение в канал: {invite_link.invite_link}")




@bot.message_handler(func=lambda message: message.text.startswith('/start '))
def handle_referral(message):
    user_id = message.from_user.id
    referral_code = message.text.split('/start ')[1]  # Извлечение кода реферала из текста сообщения

    # Проверка, есть ли такой код реферала в словаре и получение идентификатора пригласившего пользователя
    if referral_code in referral_dict:
        inviter_id = referral_dict[referral_code]

        # Запись информации о реферале и пригласившем пользователе в базу данных
        cursor.execute("INSERT INTO referrals (inviter_tgid, referral_tgid) VALUES (%s, %s)", (inviter_id, user_id))
        conn.commit()

        bot.send_message(user_id, f"Вы были приглашены пользователем с ID {inviter_id}. Добро пожаловать!")
    else:
        bot.send_message(user_id, "Неверный код реферала. Пожалуйста, используйте корректную ссылку для приглашения.")


@bot.message_handler(commands=['start'])
def handle_start(message):
    user_id = message.from_user.id
    username = message.from_user.username
    # Проверка, зарегистрирован ли пользователь уже
    cursor.execute("SELECT * FROM users WHERE tgid = %s", (str(user_id),))
    if cursor.fetchone():
        bot.send_message(user_id, "Вы уже зарегистрированы.")
    else:
        # Запись нового пользователя в базу данных
        cursor.execute("INSERT INTO users (tgid, username) VALUES (%s, %s)", (str(user_id), username))
        conn.commit()
        bot.send_message(user_id, f"Добро пожаловать, @{username}! Вы успешно зарегистрированы.")


@bot.message_handler(commands=['balance'])
def start_message(message):
    user = message.from_user

    user_id = user.id
    user_username = user.username
    cursor.execute("SELECT balance FROM users WHERE tgid = %s", (str(user_id),))
    balance_row = cursor.fetchone()

    if balance_row:
        balance = balance_row[0]
        response = f"Баланс: {balance}\n"
    else:
        response = "Пользователь не найден в базе данных."

    bot.reply_to(message, response)


@bot.message_handler(commands=['withdraw'])
def withdraw_request(message):
    user = message.from_user
    user_id = user.id
    cursor.execute("SELECT balance FROM users WHERE tgid = %s", (str(user_id),))
    balance_row = cursor.fetchone()

    if balance_row:
        balance = balance_row[0]
        if balance >= 500:
            bot.send_message(user_id, "Введите сумму для вывода:")
            bot.register_next_step_handler(message, process_withdrawal)
        else:
            bot.reply_to(message, "У вас недостаточно средств для вывода баланса.")
    else:
        bot.reply_to(message, "Пользователь не найден в базе данных.")


@bot.message_handler(func=lambda message: True)
def process_withdrawal(message):
    try:
        withdrawal_amount = float(message.text)
        user_id = message.from_user.id

        cursor.execute("SELECT balance FROM users WHERE tgid = %s", (str(user_id),))
        balance_row = cursor.fetchone()

        if balance_row:
            balance = balance_row[0]
            if withdrawal_amount <= balance and withdrawal_amount >= 500:  # Добавлено ограничение до 500
                # Отправка данных админскому боту
                admin_message = f"Пользователь {user_id} хочет вывести {withdrawal_amount}.\nТекущий баланс: {balance}"
                send_admin_notification(admin_message)

                # Обновление баланса пользователя в базе данных
                # Обновление баланса пользователя в базе данных
                new_balance = float(balance) - withdrawal_amount
                cursor.execute("UPDATE users SET balance = %s WHERE tgid = %s", (new_balance, str(user_id)))
                conn.commit()

                bot.send_message(user_id, "Заявка на вывод отправлена администратору. Ваш баланс обновлен.")
            else:
                bot.send_message(user_id,
                                 "Недостаточно средств для вывода указанной суммы или сумма меньше минимальной (500).")
        else:
            bot.send_message(user_id, "Пользователь не найден в базе данных.")
    except ValueError:
        user_id = message.from_user.id
        bot.send_message(user_id, "Введите корректную сумму.")


# Функция для отправки уведомления админу
def send_admin_notification(message):
    admin_bot = telebot.TeleBot(adminToken)
    admin_user_id = adminUserID
    admin_bot.send_message(admin_user_id, message)


refresh_interval = 1800

last_refresh_time = time.time()


@bot.message_handler(commands=['start', 'invite', 'balance', 'withdraw'])
def handle_commands(message):
    global last_refresh_time

    current_time = time.time()
    if current_time - last_refresh_time >= refresh_interval:
        refresh_cursor()
        last_refresh_time = current_time

    bot.reply_to(message, "Command received.")


#bot.infinity_polling()
