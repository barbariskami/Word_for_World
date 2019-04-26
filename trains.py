import db_work
import random
from main import back_to_menu
from telegram import ReplyKeyboardMarkup


def word_translate(bot, update, user_data, *args):
    if user_data['training']['sets']:
        s = user_data['training']['sets'].pop()
        user_data['training']['question'] = s
        user_data['training']['type'] = word_translate
        user_data['training']['answer'] = s.word2
        bot.send_message(chat_id=update.effective_user.id,
                         text=s.word1)
    else:
        user_data['training']['is_training'] = False
        bot.send_message(chat_id=update.effective_user.id,
                         text='Тренировка окончена')
        back_to_menu(bot, update, user_data)


def translate_word(bot, update, user_data, *args):
    if user_data['training']['sets']:
        s = user_data['training']['sets'].pop()
        user_data['training']['question'] = s
        user_data['training']['type'] = translate_word
        user_data['training']['answer'] = s.word1
        bot.send_message(chat_id=update.effective_user.id,
                         text=s.word2)
    else:
        user_data['training']['is_training'] = False
        bot.send_message(chat_id=update.effective_user.id,
                         text='Тренировка окончена')
        back_to_menu(bot, update, user_data)


def_word = translate_word


def word_def(bot, update, user_data, *args):
    if user_data['training']['sets']:
        s = user_data['training']['sets'].pop()
        reply_keyboard = [['/OK']]
        user_data['training']['type'] = word_def
        markup = ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=True)
        bot.send_message(chat_id=update.effective_user.id,
                         text=s.word1, reply_markup=markup)
    else:
        user_data['training']['is_training'] = False
        bot.send_message(chat_id=update.effective_user.id,
                         text='Тренировка окончена')
        back_to_menu(bot, update, user_data)


def two_or_three(bot, update, user_data, *args):
    if user_data['training']['sets']:
        s = user_data['training']['sets'].pop()
        user_data['training']['question'] = s
        words = [s.word1, s.word2, s.word3]
        if args[0] == 4:
            words.append(s.word4)
        word = random.randrange(len(words))
        text = ' '.join(['?' if i != word else words[word] for i in range(len(words))])
        bot.send_message(chat_id=update.effective_user.id,
                         text=text)
        user_data['training']['answer'] = ' '.join(words)
        user_data['training']['type'] = two_or_three
    else:
        user_data['training']['is_training'] = False
        bot.send_message(chat_id=update.effective_user.id,
                         text='Тренировка окончена')
        back_to_menu(bot, update, user_data)


def revising(bot, update, user_data, *args):
    if user_data['training']['sets']:
        s = user_data['training']['sets'].pop()
        reply_keyboard = [['/OK']]
        user_data['training']['type'] = revising
        user_data['training']['question'] = s
        markup = ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=True)
        bot.send_message(chat_id=update.effective_user.id,
                         text=s.word3, reply_markup=markup)
    else:
        user_data['training']['is_training'] = False
        bot.send_message(chat_id=update.effective_user.id,
                         text='Тренировка окончена')
        back_to_menu(bot, update, user_data)

