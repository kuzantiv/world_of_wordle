import logging
import random
from collections import Counter
from enum import Enum

import wikipedia as wikipedia
from aiogram import Bot, Dispatcher, executor, types

import config

# Configure logging
logging.basicConfig(level=logging.INFO)

# Initialize bot and dispatcher
bot = Bot(token=config.API_TOKEN)
dp = Dispatcher(bot)

word = ""
initial_tries = 6
tries = initial_tries
guess = ""

guesses = []


class Hint(Enum):
    ABSENT = 0
    PRESENT = 1
    CORRECT = 2


def draw_grid(secret_word, guessed_words):
    global initial_tries
    new_line = '\n'
    delimiter = "+---" * len(secret_word) + "+"
    grid = f"{delimiter}{new_line}"
    for i in range(initial_tries):
        row = "|"
        w = ""
        if i >= len(guessed_words):
            w = " " * 5
        else:
            w = guessed_words[i]

        for c in w:
            row += f" {c.upper()} |"
        grid += f"{row}{new_line}{delimiter}{new_line}"
    return grid


# def tip(secret_word, guessed_word):
#     pool = Counter(s for s, g in zip(secret_word, guessed_word) if s != g)
#     hint = []
#
#     for s, g in zip(secret_word, guessed_word):
#         if s == g:
#             hint.append(Hint.CORRECT)
#         elif g in word and pool[g] > 0:
#             hint.append(Hint.PRESENT)
#             pool[g] -= 1
#         else:
#             hint.append(Hint.ABSENT)

            # picture keyboard


# def picture_keyboard():
#     my_image = Image.open("background_for_keyboard.jpg")
#     title_font = ImageFont.truetype('playfair/playfair-font.ttf', 200)
#     title_text =
#     image_editable = ImageDraw.Draw(my_image)
#     image_editable.text((15, 15), title_text, (237, 230, 211), font=title_font)
#     my_image.save("result.jpg")


def start_game():
    global word, dictionary, tries, guesses
    tries = initial_tries
    word = random.choice(dictionary)
    guesses = []
    return "Я загадал слово"


def declension(a):
    if a == 5:
        return "попыток"
    elif a in range(2, 5):
        return "попытки"
    else:
        return "попытка"


def word_definition(word_def):
    new_line = "\n"
    wikipedia.set_lang("ru")
    return f"{new_line} {wikipedia.summary(word_def, sentences=5)}"


@dp.message_handler(commands=['Начало'])
async def send_start(message: types.Message):
    await message.reply(start_game())


@dp.message_handler(commands=['сдаюсь'])
async def send_start(message: types.Message):
    await message.reply(f"Вы проебали, слово было такое: {word}{word_definition(word)}")
    await message.reply(start_game())


@dp.message_handler(commands=['У'])
async def send_guess(message: types.Message):
    global word, tries, dictionary, guess
    guess = message.get_args().lower()
    if guess == word:
        guess_with_spaces = ""
        for i in guess:
            guess_with_spaces += i + "__"
        await message.reply(f"🟩  🟩  🟩  🟩  🟩  \n{guess_with_spaces[:-2]}\nПИЗДЕЦ ТЫ МОЛОДЕЦ{word_definition(word)}")
        await message.reply(start_game())
    elif tries == 1:
        await message.reply(f"Вы проебал, слово было такое: {word}{word_definition(word)}")
        await message.reply(start_game())
    elif guess not in dictionary:
        await message.reply("Такого слова нет в пяти-буквенном словаре")
    else:
        hint = ""
        green = "🟩  "
        yellow = "🟨  "
        red = "🟥  "

        pool = Counter(s for s, g in zip(word, guess) if s != g)

        for s, g in zip(word, guess):
            if s == g:
                hint += green
            elif g in word and pool[g] > 0:
                hint += yellow
                pool[g] -= 1
            else:
                hint += red

        guesses.append(guess)
        tries -= 1
        guess_with_spaces = ""
        for i in guess:
            guess_with_spaces += i + "__"
        await message.reply(
            f"{hint} \n {draw_grid(guess, guesses)} \nосталось {str(tries)} {declension(tries)}")


if __name__ == '__main__':
    with open("five_letter_nouns.txt", "r", encoding="utf-8") as fr:
        dictionary = fr.read().splitlines()
    start_game()
    executor.start_polling(dp, skip_updates=True)

"""
1. склонение слова 'ПОПЫТОК'              ✅✅✅
2. алгоритм 2 букв                        ✅✅✅
(сначала помечать зеленые , потом желтые) 
3. клавиатура 
4. подсказки в виде вариантов
5. 
"""
