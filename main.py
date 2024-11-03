from telebot import TeleBot, types
from telebot.util import quick_markup
from Parser import Parser
from datetime import datetime
import math

API_TOKEN = ""

bot = TeleBot(API_TOKEN)
user_filters = dict()
filter_markup = None
parser = Parser()


@bot.message_handler(commands=["start"])
def start_actions(message):
    user_id = message.from_user.id
    user_filters[user_id] = set()
    display_markup(message)


@bot.callback_query_handler(func=lambda callback: callback.data.startswith("filter_"))
def process_filters(callback):
    user_id = callback.from_user.id
    filter_name = callback.data.split('_')[1]
    button_status = ""
    button_row_index, button_col_index = map(int, callback.data.split('_')[2::])

    if filter_name not in user_filters[user_id]:
        user_filters[user_id].add(filter_name)
        answer_result = "Добавлено"
        button_status = "✅"
    else:
        user_filters[user_id].remove(filter_name)
        answer_result = "Удалено"

    bot.answer_callback_query(callback_query_id=callback.id, text=answer_result)

    old_keyboard = callback.message.reply_markup.keyboard
    if "✅" not in old_keyboard[button_row_index][button_col_index].text:
        new_button_label = old_keyboard[button_row_index][button_col_index].text + button_status
    else:
        new_button_label = old_keyboard[button_row_index][button_col_index].text[:-1]

    old_keyboard[button_row_index][button_col_index] = types.InlineKeyboardButton(new_button_label,
                                                                                  callback_data=callback.data)
    new_keyboard = types.InlineKeyboardMarkup(old_keyboard)

    bot.edit_message_reply_markup(chat_id=callback.message.chat.id,
                                  message_id=callback.message.message_id,
                                  reply_markup=new_keyboard)


@bot.callback_query_handler(func=lambda callback: callback.data == "done")
def process_done(callback):
    user_id = callback.from_user.id

    if user_filters[user_id]:
        bot.send_message(callback.message.chat.id, "Начинаю поиск...🔎")

        matched_films = parser.get_films(user_filters[user_id])
        with open("logs.txt", 'a', encoding='utf-8') as file:
            file.write(f"{datetime.now().strftime("%y-%m-%d %H:%M:%S")} {user_id}:\n"
                       f"Запрос: {user_filters[user_id]}\n"
                       f"Найдено: {matched_films}\n\n")

        if not matched_films:
            bot.send_message(callback.message.chat.id, "Ой, я ничего не нашёл :(")
        else:
            send_films(callback.message, matched_films)

        user_filters[user_id] = set()
        bot.answer_callback_query(callback_query_id=callback.id)
    else:
        bot.send_message(callback.message.chat.id, "Нет выбранных фильтров")


def display_markup(message):
    bot.send_message(message.chat.id,
                     "Выбери нужные фильтры, затем нажми \"Готово\".",
                     reply_markup=filter_markup)


def setup_filter_markup(width=2):
    global filter_markup
    filters = dict()
    genres = list(reversed(parser.get_genres()))
    if not genres:
        exit(-1)

    rows = math.ceil(len(genres) / width)
    for row in range(rows):
        for col in range(width):
            if genres:
                filter_name = genres.pop()
                filters[filter_name] = {"callback_data": f"filter_{filter_name}_{row}_{col}"}
            else:
                break

    filter_markup = quick_markup(filters, row_width=width)
    filter_markup.add(types.InlineKeyboardButton("Готово", callback_data="done"))


def send_films(message, films):
    films_markup = dict()
    for title, attributes in films.items():
        films_markup[title] = {"url": f"https://www.google.com/search{attributes}"}

    films_markup = quick_markup(films_markup, row_width=1)
    bot.send_message(message.chat.id, "Вот что мне удалось найти:", reply_markup=films_markup)


setup_filter_markup()
bot.infinity_polling()
