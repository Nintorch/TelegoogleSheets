import telebot
from bot import bot, get_event_data_from_message, get_event_data


def start(message):
    # Клавиатура с кнопкной "Да" для сообщения с вопросом
    markup = telebot.types.InlineKeyboardMarkup()
    btn_yes = telebot.types.InlineKeyboardButton(text="Да", callback_data="DeleteAll")
    markup.add(btn_yes)

    bot.send_message(message.from_user.id, "Вы уверены в том, что хотите удалить все заметки в таблице \""
                                           f"{get_event_data_from_message(message)['table'].title}\"? "
                                           "Восстановить их будет невозможно!",
                     reply_markup=markup)


@bot.callback_query_handler(func=lambda call: call.data == "DeleteAll")
def callback_deleteall(call):
    event_data: dict = get_event_data(call.message.chat.id)
    if "table" not in event_data:
        bot.send_message(call.message.chat.id, "Действия над этой таблицей уже не производятся.")
        bot.answer_callback_query(callback_query_id=call.id, show_alert=False)
        return

    sheet = event_data["table"]
    worksheet = sheet.sheet1
    worksheet.update("A3", [[""] * 5] * (worksheet.row_count - 3))
    bot.send_message(call.message.chat.id, "Заметки успешно удалены.")
    bot.answer_callback_query(callback_query_id=call.id, show_alert=False)
