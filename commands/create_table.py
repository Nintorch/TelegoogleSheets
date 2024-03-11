import gspread_formatting as gspf
from bot import bot, gc, check_cancel, get_event_data_from_message


# Создание файла с заметками

def start(message):
    if check_cancel(message): return

    # Записываем название файла таблицы
    get_event_data_from_message(message)["name"] = message.text
    bot.send_message(message.from_user.id, "Назовите свой адрес электронной почты, "
                                           "чтобы бот мог выдать доступ к файлу.")
    bot.register_next_step_handler(message, create_get_email)


def create_get_email(message):
    if check_cancel(message): return

    if '@' not in message.text:
        bot.send_message(message.from_user.id, "Вы ввели неправильный адрес электронной почты. Попробуйте снова.")
        bot.register_next_step_handler(message, create_get_email)
        return

    # Если email был введён правильно, сохраняем его
    get_event_data_from_message(message)["email"] = message.text

    bot.send_message(message.from_user.id, "(По желанию) Введите своё имя/псевдоним,"
                                           "чтобы отображать его в заголовке таблицы,"
                                           "или напишите \"Нет\".")
    bot.register_next_step_handler(message, create_get_person_name)


def create_get_person_name(message):
    if check_cancel(message): return

    event_data = get_event_data_from_message(message)

    # Если пользователь указал своё имя/свой псевдоним, сохраняем
    if message.text.lower() != "нет":
        event_data["person_name"] = message.text

    create_create_sheet(message)


def create_create_sheet(message):
    if check_cancel(message): return

    event_data: dict = get_event_data_from_message(message)
    bot.send_message(message.from_user.id, f"Создаю Google таблицу \"{event_data['name']}\"...")

    # Создание таблицы
    sheet = gc.create(event_data["name"])
    sheet.share(event_data["email"], perm_type="user", role="writer")
    worksheet = sheet.sheet1

    # Название таблицы + имя/псевдоним пользователя (если пользователь это указал) в первой строке
    if "person_name" in event_data:
        worksheet.update("A1", f"Список заметок \"{event_data['person_name']}\"")
    else:
        worksheet.update("A1", f"Список заметок")

    # Колонки
    columns = [
        ["Задание", 200],
        ["Начальная дата", 150],
        ["Конечная дата", 150],
        ["Степень важности", 150],
        ["Статус", 100]
    ]

    # Названия колонок во второй строке таблицы (первая строка заполнена выше)
    worksheet.update("A2", [[col[0] for col in columns]])

    # Ширина колонок
    last_column = ''
    for idx, col in enumerate(columns):
        last_column = chr(ord('A') + idx)
        gspf.set_column_width(worksheet, last_column, col[1])

    # Пусть названия колонок используют жирный шрифт
    gspf.format_cell_range(worksheet, f"A2:{last_column}2",
                           gspf.CellFormat(textFormat=gspf.TextFormat(bold=True)))

    # Таблица готова к использованию, информируем пользователя

    link = "https://docs.google.com/spreadsheets/d/" + sheet.id
    bot.send_message(message.from_user.id, f"Ссылка на Google таблицу: {link}\n"
                                           f"ID таблицы: {sheet.id}\n"
                                           "Не теряйте ID таблицы, так как (если вы забудете имя таблицы) "
                                           "изменения можно провести только через него.\n"
                                           "Чтобы добавить заметку, используйте команду /addnote\n"
                                           "Чтобы совершить поиск по заметкам и выполнить действия над ними, "
                                           "используйте команду /findnote")
    event_data.clear()
