import telebot
import psycopg2

token = '6453195049:AAGEqatrSVgw_SDMngQxy2bz3gvMO9B2mUc'
bot = telebot.TeleBot(token)
conn = psycopg2.connect(dbname="tg", host="localhost", user="postgres", password="postgrespw", port="32769")
cursor = conn.cursor()
conn.autocommit = True


@bot.message_handler(commands=['start'])
def start_message(message):
    user = message.from_user

    user_id = user.id
    user_username = user.username
    user = (user_username,user_id)
    cursor.execute("INSERT INTO users (username, tgid) VALUES (%s, %s)", user)


    response = (
        f"регистрация прошла успешно {user_id}\n"

    )

    bot.reply_to(message, response)



bot.infinity_polling()
