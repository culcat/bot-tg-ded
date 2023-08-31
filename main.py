import secrets
import sqlite3
import time
import invite_url
import telebot
import psycopg2
from telebot import types
import asyncio

conn = sqlite3.connect("botdb.db")
cursor = conn.cursor()
conn.row_factory = sqlite3.Row

def refresh_cursor():
    global cursor
    cursor.close()
    cursor = conn.cursor()


cursor.execute("SELECT botkey FROM botsettings where botsettingid = 1")
token_row = cursor.fetchone()
token = str(token_row[0])
bot = telebot.TeleBot(token)
cursor.execute("SELECT botkey FROM botsettings where botsettingid = 2")
adminToken_row = cursor.fetchone()
adminToken = str(adminToken_row[0])
cursor.execute("SELECT adminuserid FROM botsettings where botsettingid = 2")
adminUserId_row = cursor.fetchone()
adminUserID = str(adminUserId_row[0])


def create_keyboard():
    # Create a keyboard with four buttons
    keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)

    # Add buttons to the keyboard
    button_invite = types.KeyboardButton('➕ Создать ссылку')
    button_balance = types.KeyboardButton('💰 Мой баланс')
    button_withdraw = types.KeyboardButton('💳 Вывoд')
    button_refs = types.KeyboardButton('\U0001F465 Мои ссылки')
    keyboard.add(button_invite, button_balance, button_withdraw, button_refs)

    return keyboard


@bot.message_handler(commands=['start'])
def handle_start(message):
    keyboard = create_keyboard()

    user_id = message.from_user.id
    username = message.from_user.username
    # Проверка, зарегистрирован ли пользователь уже
    cursor.execute("SELECT * FROM users WHERE tgid = %s", (str(user_id),))
    if cursor.fetchone():
        bot.send_message(user_id, "Вы уже зарегистрированы.", reply_markup=keyboard)
    else:
        # Запись нового пользователя в базу данных
        cursor.execute("INSERT INTO users (tgid, username) VALUES (%s, %s)", (int(user_id), username))
        conn.commit()
        bot.send_message(user_id, f"Добро пожаловать, @{username}! Вы успешно зарегистрированы.", reply_markup=keyboard)

def get_user_invite_count(user_id, cursor):
    cursor.execute("SELECT COUNT(*) FROM referals WHERE idinviter = %s", (user_id,))
    count = cursor.fetchone()[0]
    return count
@bot.message_handler(content_types=['text'])
def start_message(message):
    if message.text.lower() == '💰 мой баланс':
        print(message)
        user = message.from_user
        user_id = user.id
        user_username = user.username
        cursor.execute("SELECT invitelink FROM referals WHERE idinviter = %s", (int(user_id),))
        count = 0

        referal_url = cursor.fetchone()
        if referal_url is not None:
            count = asyncio.run(invite_url.Channel("aleksandrkrainukov").get_link_count_join(referal_url[0]))

        cursor.execute("SELECT reward FROM rewards WHERE id =%s ", '1')
        reward = cursor.fetchone()
        cursor.execute("SELECT balance FROM users WHERE tgid = %s", (str(user_id),))
        balance_row = cursor.fetchone()
        cursor.execute("UPDATE referals SET joinedusers = %s WHERE idinviter = %s", (count, (str(user_id))))
        cursor.execute("SELECT joinedusers FROM referals WHERE idinviter = %s", (str(user_id),))
        invited_count = cursor.fetchone()
        rewards = reward[0]
        invited_count = 0
        plus_balance = invited_count
        if invited_count is not None:
            pluss = int(invited_count) * int(rewards) + int(balance_row[0])
        cursor.execute("UPDATE users SET balance = %s WHERE tgid = %s", (int(pluss), str(user_id)))
        cursor.execute("SELECT balance FROM users WHERE tgid = %s", (str(user_id),))
        balance_upd = cursor.fetchone()
        balance_updd = str(balance_upd)

        if balance_upd:
            balance = balance_upd[0]
            response = f"Баланс: {balance}\n"
        else:
            response = "Пользователь не найден в базе данных."

        bot.reply_to(message, response)
    elif message.text.lower() == '👥 мои ссылки':
        user_id = message.from_user.id
        cursor.execute("SELECT invitelink FROM referals WHERE idinviter = %s", (int(user_id),))
        count = 0
        referal_url = cursor.fetchall()
        cursor.execute("SELECT * from referals WHERE idinviter = %s", (int(user_id),))
        usr = cursor.fetchone()
        if usr is None:
            bot.send_message(user_id, "У вас нету ссылок")

        if referal_url is not None:
            for i in referal_url:
                count = asyncio.run(invite_url.Channel("aleksandrkrainukoчv").get_link_count_join(i[0]))
                cursor.execute("UPDATE referals SET joinedusers = %s WHERE invitelink = %s", (count, i[0]))

        cursor.execute("SELECT invitelink  FROM referals WHERE idinviter = %s", (str(user_id),))
        link = cursor.fetchall()

        cursor.execute("SELECT joinedusers  FROM referals WHERE idinviter = %s", (str(user_id),))
        usrs = cursor.fetchall()

        message = ""
        for i, link_item in enumerate(link):
            usr = usrs[i] if usrs else None

            # Unpack the link and usr items
            link_str, usr_str = link_item[0], usr[0] if usr else "None"

            message += f'🔗 {link_str} | {usr_str} 👥 \n'

        bot.send_message(user_id, message)

    elif message.text.lower() == '➕ создать ссылку':
        user_id = message.from_user.id
        invite_count = get_user_invite_count(user_id, cursor)
        if invite_count < 3:
            invite_link = asyncio.run(invite_url.Channel('aleksandrkrainukov').create_link())
            cursor.execute("INSERT INTO referals (invitelink, idinviter) VALUES (%s, %s)", (invite_link, int(user_id)))
            conn.commit()
            bot.send_message(user_id, f"Приглашение в канал: {invite_link}")
        else:
            bot.send_message(user_id,'Достигли лимита')
    elif message.text.lower() == '💳 вывoд':
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


@bot.message_handler(commands=['start', 'invite', 'balance', 'withdraw', 'button_refs'])
def handle_commands(message):
    global last_refresh_time

    current_time = time.time()
    if current_time - last_refresh_time >= refresh_interval:
        refresh_cursor()
        last_refresh_time = current_time

    bot.reply_to(message, "Command received.")


bot.infinity_polling()
