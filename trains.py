import db_work
import random
from main import back_to_menu
from telegram import ReplyKeyboardMarkup

def check_answer(bot, update, user_data, text):
    if text.lower() == user_data['training']['answer'].lower():
        update.message.reply_text('Верно')
        user_data['training']['type'](bot, update, user_data, user_data['training']['mode'])
    else:
        try:
            update.message.reply_text('Неверно. Правильный ответ:\n' + user_data['training']['answer'])
            user_data['training']['sets'].insert(0, user_data['training']['question'])
            user_data['training']['type'](bot, update, user_data, user_data['training']['mode'])
        except Exception as e:
            print(e)


def start(bot, update, user_data, *args):
    bot.delete_message(chat_id=update.effective_user.id,
                       message_id=user_data['training']['choose_module_btns'].message_id)
    bot.send_message(chat_id=update.effective_user.id,
                     text='Тренировка ' + args[0])
    user_data['training']['is_training'] = True
    module_id = user_data['training']['active_module'].module_id
    sets = db_work.WordsSets.query.filter_by(module_id=module_id).all()
    random.shuffle(sets)
    user_data['training']['sets'] = sets

    if args[0] == 'Слово - Перевод':
        word_translate(bot, update, user_data)
        user_data['training']['mode'] = None
    elif args[0] == 'Перевод - Слово':
        translate_word(bot, update, user_data)
        user_data['training']['mode'] = None
    elif args[0] == 'Определение - Термин':
        def_word(bot, update, user_data)
        user_data['training']['mode'] = None
    elif args[0] == 'Термин - Определение':
        word_def(bot, update, user_data)
        user_data['training']['mode'] = None
    elif args[0] == 'Одно слово - Остальные два':
        two_or_three(bot, update, user_data, 3)
        user_data['training']['mode'] = 3
    elif args[0] == 'Одно слово - Остальные три':
        two_or_three(bot, update, user_data, 4)
        user_data['training']['mode'] = 4
    elif args[0] == 'Повторение':
        revising(bot, update, user_data)


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
        user_data['training']['answer'] = s.word2
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
