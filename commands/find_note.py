from bot import bot, check_cancel, get_event_data_from_message, get_event_data
from .add_note import command_text as add_note_command_text, prepare_data

import telebot
import re


# Поиск заметки

# Заметка была найдена
def note_found(message, row, worksheet):
    # Действия с заметкой
    markup = telebot.types.InlineKeyboardMarkup()
    btn_edit = telebot.types.InlineKeyboardButton(text="Изменить", callback_data="EditNote")
    btn_delete = telebot.types.InlineKeyboardButton(text="Удалить", callback_data="DeleteNote")
    markup.add(btn_edit, btn_delete)

    # Отправляем ообщение с найденной заметкой
    row_str = '\n'.join(worksheet.row_values(row))
    bot.send_message(message.from_user.id, f"Заметка №{row}: {row_str}",
                     reply_markup=markup)


def start(message):
    if check_cancel(message): return

    event_data: dict = get_event_data_from_message(message)

    # Пользователь ввёл число, значит он хочет найти запись по номеру её строки в таблице
    if message.text.isnumeric():
        sheet = event_data["table"]
        worksheet = sheet.sheet1

        # Номер строки в таблице
        row = int(message.text)

        if worksheet.cell(row, 1).value is None:
            bot.send_message(message.from_user.id, "Данная строка пуста.")
            bot.register_next_step_handler(message, start)
            return
        if row < 3:
            bot.send_message(message.from_user.id, "Данный номер строки выходит за пределы таблицы заметок.")
            bot.register_next_step_handler(message, start)
            return

        note_found(message, row, worksheet)
        return

    # Пользователь ввёл текст, значит он хочет найти запись по её содержимому

    bot.send_message(message.from_user.id, "Ищу заметки...")

    sheet = event_data["table"]
    worksheet = sheet.sheet1
    regular_expr = re.compile(message.text, re.I)
    cell_list = worksheet.findall(regular_expr)
    found_notes = set()

    # Проходимся по всем найденным записям
    if len(cell_list) > 0:
        for cell in cell_list:
            if cell.row not in found_notes:
                note_found(message, cell.row, worksheet)
                found_notes.add(cell.row)
    # Записей нет
    else:
        bot.send_message(message.from_user.id, "Заметки не найдены. Попробуйте поменять критерии поиска.")
        bot.register_next_step_handler(message, start)


def get_row_from_message(message_text):
    # В тексте сообщения с информацией о заметке между символами "№" и ":" заключён номер строки в таблице
    start = message_text.find('№')
    end = message_text.find(':')
    row = int(message_text[start + 1:end])
    return row


@bot.callback_query_handler(func=lambda call: call.data == "EditNote")
def callback_editnote(call):
    event_data: dict = get_event_data(call.message.chat.id)
    if "table" not in event_data:
        bot.send_message(call.message.chat.id, "Действия над этой таблицей уже не производятся.")
        bot.answer_callback_query(callback_query_id=call.id, show_alert=False)
        return

    event_data["row"] = get_row_from_message(call.message.text)

    # Сообщение с текстом про добавление строки
    # (для изменения строки используется тот же самый формат)
    bot.send_message(call.message.chat.id, add_note_command_text)
    bot.register_next_step_handler(call.message, editnote)

    bot.answer_callback_query(callback_query_id=call.id, show_alert=False)


def editnote(message):
    if check_cancel(message): return

    # Данные для строки в таблице
    data = prepare_data(message)
    if not data:
        return

    bot.send_message(message.from_user.id, "Изменяю заметку в таблице...")

    event_data = get_event_data_from_message(message)
    sheet = event_data["table"]
    worksheet = sheet.sheet1

    # Изменяем строку в таблице
    worksheet.update(f"A{event_data['row']}", [data])

    bot.send_message(message.from_user.id, "Заметка успешно изменена!")
    event_data.clear()


@bot.callback_query_handler(func=lambda call: call.data == "DeleteNote")
def callback_deletenode(call):
    event_data: dict = get_event_data(call.message.chat.id)
    if "table" not in event_data:
        bot.send_message(call.message.chat.id, "Действия над этой таблицей уже не производятся.")
        bot.answer_callback_query(callback_query_id=call.id, show_alert=False)
        return

    row = get_row_from_message(call.message.text)

    bot.send_message(call.message.chat.id, "Удаляю заметку из таблицы...")

    sheet = event_data["table"]
    worksheet = sheet.sheet1

    # Чтобы удалить строку в таблице, нужно переместить все данные после этой строки на одну строку раньше
    # (тем самым заменив данные в этой строке и удалив её)
    worksheet.copy_range(f"A{row + 1}:E{worksheet.row_count}", f"A{row}")

    # Убираем строку с конца (она не была заменена командой выше)
    worksheet.update(f"A{worksheet.row_count}", [[""] * 5])

    bot.send_message(call.message.chat.id, "Заметка успешно удалена!")
    bot.answer_callback_query(callback_query_id=call.id, show_alert=False)

    event_data.clear()
