import telebot
import gspread

# Считываем токен и создаём интерфейс для бота, манипулирования Google Таблицами
with open("token.txt") as file:
    token = file.read()
bot = telebot.TeleBot(token)
gc = gspread.service_account("service_account.json")
_event_data = {}


def check_cancel(message):
    if message.text == "/cancel" or '/' in message.text or \
            message.text == "❌ Отмена":
        bot.send_message(message.from_user.id, "Отмена действия.")
        return True
    return False


def get_event_data(user_id):
    if user_id not in _event_data:
        _event_data[user_id] = {}

    return _event_data[user_id]


def get_event_data_from_message(message):
    return get_event_data(message.from_user.id)


def acquire_table(message):
    try:
        result = gc.open_by_key(message.text)
    except (gspread.exceptions.APIError, gspread.exceptions.SpreadsheetNotFound):
        try:
            result = gc.open(message.text)
        except (gspread.exceptions.APIError, gspread.exceptions.SpreadsheetNotFound):
            bot.send_message(message.from_user.id, "Таблица не найдена.")
            return False
    get_event_data_from_message(message)["table"] = result
    return True
