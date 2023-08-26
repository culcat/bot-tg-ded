import secrets

import telebot
import psycopg2

conn = psycopg2.connect(dbname="tg", host="localhost", user="postgres", password="postgrespw", port="32770")
cursor = conn.cursor()
conn.autocommit = True

cursor.execute("SELECT botkey FROM botsettings")
token_row = cursor.fetchone()
token = str(token_row[0])
bot = telebot.TeleBot(token)


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

    # Извлекаем токен из команды /start
    invite_token = message.text.split('/start ')[-1]
    # Поиск пригласившего пользователя по токену
    cursor.execute("SELECT inviteruserid FROM invitations WHERE token = %s", (invite_token,))
    inviter_row = cursor.fetchone()

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

    bot.reply_to(message, response)


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
def balance_message(message):
    user = message.from_user
    user_id = user.id
    cursor.execute("SELECT balance FROM users WHERE tgid = %s", (str(user_id),))
    balance_row = cursor.fetchone()

    if balance_row:
        balance = balance_row[0]
        if balance >= 500:
            response = f"Подать заявку на вывод\n"
        else:
            response = "У вас недостаточно средств для вывода баланса."
    else:
        response = "Пользователь не найден в базе данных."

    bot.reply_to(message, response)


bot.infinity_polling()
