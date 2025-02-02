import asyncio
import logging
import os
import random
import time
from collections import Counter
from enum import Enum

from aiogram import Dispatcher, types, F
from aiogram import filters
from aiogram.types.input_file import FSInputFile
from dotenv import load_dotenv

import keyboards as kb
from image_handling import *
from working_with_db_functions import *

logging.basicConfig(level=logging.INFO)

load_dotenv()  # Загружает переменные из .env

token = os.getenv('API_TOKEN')

bot = Bot(token)
dp = Dispatcher()

initial_tries = 6
games = {}


class Hint(Enum):
    ABSENT = 0
    PRESENT = 1
    CORRECT = 2


keyboard = "абвгдеёжзийклмнопрстуфхцчшщъыьэюя"
dictionary = {}


# ===============================================
def get_word_id_from_db(word):
    with sqlite3.connect('words_with_sentence_examples.db') as con:
        record = con.execute('SELECT id FROM words where word=?',
                             (word,)).fetchone()

    return record[0]


def get_random_example(word_id: int) -> dict[str, str]:
    with sqlite3.connect('words_with_sentence_examples.db') as con:
        con.row_factory = sqlite3.Row
        random_example = con.execute(
            f'SELECT example, target_word, source '
            f'FROM examples WHERE word_id={word_id} '
            f'ORDER BY RANDOM() LIMIT 1').fetchone()

    return dict(random_example)


def format_example(example: dict[str, str]) -> str:
    example['example'] = example['example'].replace(example['target_word'],
                                                    f'{len(example["target_word"]) * "🟩 "}')
    return f'{example["example"]}\n\n_{example["source"]}_'


def tip(secret_word, guessed_word):
    pool = Counter(s for s, g in zip(secret_word, guessed_word) if s != g)
    hint = []

    for s, g in zip(secret_word, guessed_word):
        if s == g:
            hint.append(Hint.CORRECT)
        elif g in secret_word and pool[g] > 0:
            hint.append(Hint.PRESENT)
            pool[g] -= 1
        else:
            hint.append(Hint.ABSENT)

    return hint


def start_game(chat_id):
    global games, dictionary
    games[chat_id] = {'tries': initial_tries,
                      'word': random.choice(dictionary),
                      'guesses': [],
                      'dicty': {},
                      'photo': 0,
                      'players': []}
    return "Я загадал слово"


def score_guess(user_id, user_name, user_surname, user_word):
    with sqlite3.connect('d_base.db') as con:
        con = con.cursor()
        query = ('INSERT INTO player_words (user_id, '
                 'user_name, user_surname, word, time_of_move)'
                 'VALUES (?,?,?,?,?)',
                 (user_id, user_name, user_surname, user_word, round(time.time()))
                 )
        con.execute(*query)


def declension(a):
    """Changes declension of the word "попытка"."""
    if a == 5:
        return "попыток"
    elif a in range(2, 5):
        return "попытки"
    else:
        return "попытка"


def draw_picture(chat_id, guesses_text, keyboard_text):
    word = games[chat_id]['word']
    dicty = games[chat_id]['dicty']
    img = Image.new('RGB', (500, 300), color=(31, 48, 78))

    draw = ImageDraw.Draw(img)
    font_keyboard = ImageFont.truetype('fonts/RubikMonoOne-Regular.ttf',
                                       size=20)
    font_grid = ImageFont.truetype('fonts/Jetbrainsmonobold.ttf',
                                   size=30)

    x0, y0 = 60, 65
    x1, y1 = 200, 65
    counter = 0
    while counter != 6:
        draw.line((x0, y0, x1, y1), fill='white', width=3)
        y0 += 35
        y1 += 35
        counter += 1

    grid_width = 60
    grid_height = 65
    ad_pix_grid = 30
    for item in guesses_text:
        hint = tip(word, item)
        for i, h in enumerate(hint):
            letter = item[i]
            if letter in dicty:
                if h == Hint.CORRECT:
                    draw.text((grid_width, grid_height),
                              letter.upper(),
                              fill="green",
                              font=font_grid)
                    grid_width += ad_pix_grid
                elif h == Hint.PRESENT:
                    draw.text((grid_width, grid_height),
                              letter.upper(), fill="yellow",
                              font=font_grid)
                    grid_width += ad_pix_grid
                else:
                    draw.text((grid_width, grid_height),
                              letter.upper(),
                              fill="red",
                              font=font_grid)
                    grid_width += ad_pix_grid
            else:
                draw.text((grid_width, grid_height),
                          letter.upper(),
                          font=font_grid)
        grid_height += 35
        grid_width = 60

    width = 250
    height = 100
    additional_pixels = 20
    for i in keyboard_text:
        if width < 470:
            pass
        else:
            width = 250
            height += 25
        if i in dicty:
            if dicty[i] == Hint.CORRECT:
                draw.text((width, height), i.upper(),
                          fill="green", font=font_keyboard)
                width += additional_pixels
            elif dicty[i] == Hint.PRESENT:
                draw.text((width, height), i.upper(),
                          fill="yellow", font=font_keyboard)
                width += additional_pixels
            else:
                draw.text((width, height), i.upper(),
                          fill=(31, 48, 78,), font=font_keyboard)
                width += additional_pixels
        else:
            draw.text((width, height), i.upper(), font=font_keyboard)
            width += additional_pixels
    photo_name = f'result{chat_id}.png'
    img.save(photo_name)
    return photo_name


# New handler style for callbacks
@dp.callback_query(F.data == "button1")
async def process_callback_button1(callback_query: types.CallbackQuery):
    word = games[callback_query.message.chat.id]['word']
    await callback_query.answer()  # Always answer callback first
    await callback_query.message.answer(
        format_example(get_random_example(get_word_id_from_db(word))),
        parse_mode='Markdown'
    )


@dp.message(filters.Command("hint"))
async def send_help(message: types.Message):
    global games
    word = games[message.chat.id]['word']
    await bot.send_message(message.chat.id,
                           format_example(get_random_example(get_word_id_from_db(word))),
                           parse_mode='Markdown')


def word_definition(word_def):
    with sqlite3.connect('d_base.db') as con:
        definitions = con.execute("select Article from Dict where Word=:word",
                                  {"word": word_def}).fetchone()
        if definitions is None:
            return ""
        else:
            return "\n".join(definitions[0].split("<br>")[1:])


@dp.message(filters.CommandStart())
async def send_start(message: types.Message):
    await message.reply(start_game(message.chat.id))


@dp.message(filters.Command("giveup"))
async def send_give_up(message: types.Message):
    word = games[message.chat.id]['word']
    await bot.send_message(message.chat.id,
                           f"Вы проиграли, слово было такое: "
                           f"*{word.upper()}*\n_{word_definition(word)}_",
                           parse_mode="Markdown")
    await message.reply(start_game(message.chat.id))


@dp.message(filters.Command("help"))
async def send_help(message: types.Message):
    await message.reply("""
Привет 🙋. Я СЛОВЛ
Я загадываю слово, а ты должен его угадать.
Используй команды: 
/gifInstruction - гиф инструкция
/start — начать игру
/giveUp — сдаться
/help — помощь
/about — дополнительная информация об игре и разработчиках
    """)


@dp.message(filters.Command("gifinstruction"))
async def send_help(message: types.Message):
    # Open the file in binary mode and pass it directly
    video_path = "video_instruction.mp4"
    video_file = FSInputFile(video_path)
    await bot.send_video(message.chat.id, video_file)


@dp.message(filters.Command("about"))
async def send_help(message: types.Message):
    await message.answer("""
@kuzantiv - Founder
@gulitsky - Cofounder
@winzitu  - VentureAngel
Github - https://github.com/kuzantiv
    """)


@dp.message(filters.Command("g") or filters.Command("у"))
@dp.message(F.reply_to_message)
async def send_guess(message: types.Message):
    global games, dictionary
    word = games[message.chat.id]['word']
    tries = games[message.chat.id]['tries']
    dicty = games[message.chat.id]['dicty']
    guesses = games[message.chat.id]['guesses']
    players = games[message.chat.id]['players']
    print(word)

    guess = message.text.lower().split(' ')[-1]
    if guess == word:
        score_guess(message.from_user.id,
                    message.from_user.first_name,
                    message.from_user.last_name, guess)
        await message.reply(f"\n\n{word_definition(word)}")

        draw_winner_name(chat_id=message.chat.id,
                         user_full_name=message.from_user.full_name,
                         user_id=message.from_user.id)
        file_path = f'last_winners/last_winner_pic_chat{message.chat.id}user{message.from_user.id}.jpg'
        input_file = FSInputFile(file_path)
        await bot.send_photo(message.chat.id, input_file)

        await message.reply(start_game(message.chat.id))
    elif tries == 1:
        await bot.send_message(message.chat.id,
                               f'Вы проиграли, слово было такое:\n'
                               f'*{word.upper()}*\n_{word_definition(word)}_',
                               parse_mode="Markdown")
        await message.answer(start_game(message.chat.id))
    elif guess not in dictionary:
        await message.reply("Такого слова нет в пяти-буквенном словаре")
        await message.answer("Если сложно, нажимай",
                             reply_markup=kb.inline_kb1)

    else:
        score_guess(message.from_user.id,
                    message.from_user.first_name,
                    message.from_user.last_name, guess)
        hint = tip(word, guess)
        for i, h in enumerate(hint):
            g = guess[i]
            if h == Hint.CORRECT:
                games[message.chat.id]['dicty'][g] = h
            elif h == Hint.PRESENT:
                if g not in dicty.keys() or dicty[g] != Hint.CORRECT:
                    games[message.chat.id]['dicty'][g] = h
            else:
                games[message.chat.id]['dicty'][g] = Hint.ABSENT

        games[message.chat.id]['guesses'].append(guess)
        tries -= 1
        games[message.chat.id]['tries'] = tries
        players.append(f'{message.from_user.id}')

        result_pic = draw_picture(message.chat.id, guesses, keyboard)
        path_to_downloaded_avatar = await download_avatar(bot,
                                                          message.chat.id,
                                                          message.from_user.id)
        crop_circle_from_avatar(src=path_to_downloaded_avatar,
                                dst=path_to_downloaded_avatar)
        resize_picture(path_to_downloaded_avatar)
        insert_users_logo(result_pic, message.chat.id, players)

        photo = f'result{message.chat.id}.png'
        photo_f = FSInputFile(photo, photo)
        message = await bot.send_photo(message.chat.id, photo_f)
        await message.answer("Если сложно, нажимай",
                             reply_markup=kb.inline_kb1)
        if games[message.chat.id]['photo']:
            await bot.delete_message(message.chat.id,
                                     games[message.chat.id]['photo'])
        games[message.chat.id]['photo'] = message.message_id
        os.remove(f'result{message.chat.id}.png')


async def main():
    global dictionary
    dictionary = get_words_that_have_examples('words_with_sentence_examples.db')
    await dp.start_polling(bot, skip_updates=True)


if __name__ == '__main__':
    asyncio.run(main())
