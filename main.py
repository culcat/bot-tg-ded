import secrets
import telebot
import psycopg2
from telebot import types

conn = psycopg2.connect(dbname="tg", host="localhost", user="postgres", password="postgrespw", port="32770")
cursor = conn.cursor()
conn.autocommit = True

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
    keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)
    button_invite = types.KeyboardButton('/invite')
    button_balance = types.KeyboardButton('/balance')
    button_withdraw = types.KeyboardButton('/withdraw')
    keyboard.add(button_invite, button_balance, button_withdraw)
    return keyboard
@bot.message_handler(commands=['invite'])
def invite_message(message):
    user = message.from_user

    # Генерируем уникальный токен для приглашения
    invite_token = secrets.token_urlsafe(16)

    # Сохраняем токен и информацию о пригласившем пользователе
    cursor.execute("INSERT INTO invitations (token, inviteruserid) VALUES (%s, %s)", (invite_token, user.id))
    conn.commit()

    invite_link = f"https://t.me/itDeadTgBot?start={invite_token}"
    response = f"Ваша ссылка для приглашения: {invite_link}"
    bot.reply_to(message, response)


@bot.message_handler(commands=['start'])
def start_message(message):
    user = message.from_user

    # Проверка, не зарегистрирован ли пользователь уже
    cursor.execute("SELECT tgid FROM users WHERE tgid = %s", (str(user.id),))
    registered_user = cursor.fetchone()

    if registered_user:
        response = "Вы уже зарегистрированы."
        bot.reply_to(message, response)
        return
    else:
        user_id = user.id
        user_username = user.username
        user = (user_username, user_id)
        cursor.execute("INSERT INTO users (username, tgid) VALUES (%s, %s)", user)
        response = "Вы успешно зарегистрированы."
        bot.reply_to(message, response)



    # Извлекаем токен из команды /start
    invite_token = message.text.split('/start ')[-1]
    # Поиск пригласившего пользователя по токену
    cursor.execute("SELECT inviteruserid FROM invitations WHERE token = %s", (invite_token,))
    inviter_row = cursor.fetchone()
    user = message.from_user

    if inviter_row:
        inviter_id = inviter_row[0]

        # Если идентификатор пригласившего совпадает с идентификатором приглашенного
        if inviter_id == user.id:
            response = "Вы не можете пригласить самого себя."
        else:
            # Начисление баланса пригласившему пользователю
            cursor.execute("UPDATE users SET balance = balance + 1 WHERE tgid = %s", (str(inviter_id),))
            cursor.execute("UPDATE invitations SET inviteduserid = %s WHERE token = %s ", (user.id, invite_token))
            conn.commit()
            response = f"Вы были приглашены пользователем {inviter_id}. Баланс начислен."
    else:
        response = "Пригласитель не найден."

    bot.reply_to(message, response, reply_markup=create_keyboard())


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
                admin_user_id = "326646054"
                admin_message = f"Пользователь {user_id} хочет вывести {withdrawal_amount}.\nТекущий баланс: {balance}"
                send_admin_notification(admin_message)

                # Обновление баланса пользователя в базе данных
                # Обновление баланса пользователя в базе данных
                new_balance = float(balance) - withdrawal_amount
                cursor.execute("UPDATE users SET balance = %s WHERE tgid = %s", (new_balance, str(user_id)))
                conn.commit()

                bot.send_message(user_id, "Заявка на вывод отправлена администратору. Ваш баланс обновлен.")
            else:
                bot.send_message(user_id, "Недостаточно средств для вывода указанной суммы или сумма меньше минимальной (500).")
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
bot.infinity_polling()