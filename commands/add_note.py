from bot import bot, check_cancel, get_event_data_from_message
import datetime


# Создание заметки

command_text = "Введите следующие данные, используя новую строку как разделитель:\n" \
               "Задание, начальная дата, конечная дата, степень важности, статус.\n" \
               "\"Задание\" и \"Степень важности\" могут быть любым текстом.\n" \
               "Формат для дат следующий: ДД-ММ-ГГГГ. Вставьте \"!\", чтобы " \
               "использовать сегодняшнюю дату. Вставьте \"-\", чтобы оставить поле" \
               "пустым.\n" \
               "Статус также может быть любым текстом, но рекомендуется использовать " \
               "\"В процессе\", \"Закончено\" или \"Отложено\".\n" \
               "Поле статуса и степени важности могут быть заменены прочерком (\"-\")" \
               " или пропущены. В таком случае будут введены значения по умолчанию " \
               "(\"В процессе\" и \"Опционально\" соответственно)."


def get_date(text):
    # Пользователь решил выбрать сегодняшнюю (для него) дату (см. текст команды выше)
    if text == "!":
        ret = datetime.date.today().strftime('%d-%m-%Y')
    # Пользователь решил оставить это поле пустым (см. текст команды выше)
    elif text == "-":
        ret = ""
    else:
        # Получаем данные введённой даты
        date = [int(i) for i in text.split('-')]
        ret = datetime.date(date[2], date[1], date[0]).strftime('%d-%m-%Y')
    return ret


# Получаем данные для записи в таблицу
def prepare_data(message, start_function):
    # Получаем строки из сообщения
    data: list = message.text.split('\n')
    if len(data) < 3:
        bot.send_message(message.from_user.id, "Неправильный формат ответа (количество строк меньше, чем 3).")
        bot.register_next_step_handler(message, start_function)
        return
    if len(data) > 5:
        bot.send_message(message.from_user.id, "Неправильный формат ответа (количество строк больше, чем 5).")
        bot.register_next_step_handler(message, start_function)
        return

    # Текст задания пустой/содержит только пробелы
    if data[0].strip() == "":
        bot.send_message(message.from_user.id, "Текст задания не может быть пустым.")
        return

    try:
        # Получаем начальную (data[1]) и конечную (data[2]) даты
        data[1] = get_date(data[1])
        data[2] = get_date(data[2])
    except ValueError:
        bot.send_message(message.from_user.id, "Дата введена в неправильном формате. Убедитесь, "
                                               "что она была введена в формате ДД-ММ-ГГГГ.")
        bot.register_next_step_handler(message, start_function)
        return

    # Пусть элементов в массиве будет ровно 5
    data.extend(["" for _ in range(5-len(data))])

    # Значения для степени важности и статуса по умолчанию (см. текст команды выше)
    if data[3].strip() == "":
        data[3] = "Опционально"
    if data[4].strip() == "":
        data[4] = "В процессе"

    return data


def start(message):
    if check_cancel(message): return

    # Данные для строки в таблице
    data = prepare_data(message, start)
    if not data:
        return

    event_data: dict = get_event_data_from_message(message)
    sheet = event_data["table"]
    worksheet = sheet.sheet1

    # Ищем первую свободную строку
    row = 3
    while worksheet.cell(row, 1).value:
        row += 1

    bot.send_message(message.from_user.id, "Добавляю заметку в таблицу...")

    # Добавляем новую запись на свободной строке
    worksheet.update(f"A{row}", [data])

    bot.send_message(message.from_user.id, f"Заметка успешно добавлена в строку под номером {row}!")
    event_data.clear()
