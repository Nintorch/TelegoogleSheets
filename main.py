import telebot
from bot import bot, get_event_data, check_cancel, acquire_table

# Импортируем все команды (см. commands/__init__.py)
from commands import *

"""
Перед тем, как использовать данный скрипт, нужно создать бота через @BotFather
в Telegram и вставить его токен в файл token.txt

Далее нужно подготовить аккаунт Google. Следуйте уроку на сайте
https://habr.com/ru/articles/483302/
Читайте от заголовка "Регистрация в сервисах Google и установка библиотек" до "Теперь переходим к установке библиотек."
Скачанный .json файл с ключом добавьте в папку с данным скриптом и переименуйте его в "service_account.json"

Далее скрипт должен запуститься.
Также вы можете установить список команд в BotFather:
1. Отправьте /setcommands
2. Выберете нужного бота
3. Отправьте следующее:
start - Список команд
cancel - Отмена действия
create - Создать Google таблицу с заметками
addnote - Добавить заметку в Google таблицу
findnote - Найти заметку, изменить или удалить найденную заметку
deleteall - Удалить все заметки в таблице

"""


class BotCommand:
    commands_list: list = None

    def __init__(self, command_text: str, command_readable: str, description: str, start_message: str,
                 next_step_handler):
        self._command_text = command_text
        self._description = description

        self.command_readable = command_readable
        self.start_message = start_message
        self.next_step_handler = next_step_handler

    def get_command_text(self):
        return "/" + self._command_text

    def get_description(self):
        return self._description.replace("<cmd>", "/" + self._command_text)

    def get_telebot_button(self):
        return telebot.types.KeyboardButton(self.command_readable)

    @staticmethod
    def init_commands():
        if BotCommand.commands_list is not None:
            return

        BotCommand.commands_list = [
            # <cmd> заменяется на текст команды (например, /create)
            BotCommand("create", "💡 Создать таблицу", "Чтобы создать таблицу с заметками, введите <cmd>",
                       start_message="Назовите файл с заметками.",
                       next_step_handler=create_table_start),

            BotTableCommand("addnote", "📝 Добавить заметку", "Чтобы добавить заметку, введите <cmd>",
                            start_message=add_note_command_text,
                            next_step_handler=add_note_start),

            BotTableCommand("findnote", "🔍 Найти заметку и совершить действия",
                            "Чтобы найти заметки и произвести действия, введите <cmd>",
                            start_message="Введите номер строки с заметкой или данные заметки.\n"
                                          "Обратите внимание, что поиск зависит от регистра!",
                            next_step_handler=find_note_start),

            BotTableCommand("deleteall", "🗑 Удалить все заметки", "Чтобы удалить все заметки, введите <cmd>",
                            start_message="", next_step_handler=delete_all_start, run_immediately=True),

            BotCommand("cancel", "❌ Отмена", "Чтобы отменить ввод команды, введите <cmd>",
                       # Этот текст выводится из функции get_text_messages(), т.е. тогда,
                       # когда команда не была начата
                       start_message="Вы не начали использовать команду.", next_step_handler=None),
        ]

    @staticmethod
    def get_command(text: str):
        for cmd in BotCommand.commands_list:
            if cmd.get_command_text() == text or cmd.command_readable == text:
                return cmd
        return None

    @staticmethod
    def has_command(text: str):
        return BotCommand.get_command(text) is not None


class BotTableCommand(BotCommand):
    def __init__(self, command_text: str, command_readable: str, description: str, start_message: str,
                 next_step_handler, run_immediately=False):
        super().__init__(command_text,
                         command_readable,
                         description,
                         "Введите ID таблицы либо её название файла с заметками.",
                         self.run_command)
        self._command_text = command_text
        self._description = description

        self.command_readable = command_readable
        self.table_start_message = start_message
        self.table_function = next_step_handler
        self.run_immediately = run_immediately

    def run_command(self, message):
        if check_cancel(message): return

        if acquire_table(message):
            if self.run_immediately:
                self.table_function(message)
            else:
                bot.send_message(message.from_user.id, self.table_start_message)
                bot.register_next_step_handler(message, self.table_function)


@bot.message_handler(content_types=['text'])
def get_text_messages(message):
    if message.text == "/start":
        markup = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True)
        buttons = [cmd.get_telebot_button() for cmd in BotCommand.commands_list]
        markup.add(*buttons)

        message_entries = ["Привет!"] + [cmd.get_description() for cmd in BotCommand.commands_list]

        bot.send_message(message.from_user.id, '\n'.join(message_entries), reply_markup=markup)

    elif BotCommand.has_command(message.text):
        command = BotCommand.get_command(message.text)
        bot.send_message(message.from_user.id, command.start_message)

        # Будет None для /cancel, так как эта команда не совершает никаких действий
        # в этой функции (get_text_messages())
        if command.next_step_handler is not None:
            bot.register_next_step_handler(message, command.next_step_handler)

    else:
        bot.send_message(message.from_user.id, "Нераспознанная команда.")


BotCommand.init_commands()
bot.polling(none_stop=True, interval=0)
