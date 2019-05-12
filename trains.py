import db_work
import random
from main import back_to_menu
from telegram import ReplyKeyboardMarkup, InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardRemove


def choose_module(bot, update, user_data):
    modules = sorted(db_work.ModulesDB.query.filter_by(user_id=update.effective_user.id).all(),
                     key=lambda x: x.module_id,
                     reverse=True)
    if modules:
        text = 'Выберите модуль, который хотите тренировать (если созданных вами модулей больше ' \
               '10, они отображаются по 10'
        user_data['training'] = {}
        user_data['training']['modules'] = modules
        keyboard = []
        if len(modules) <= 10:
            for i in modules:
                button = [InlineKeyboardButton(text=i.name, callback_data='set_active_module|' + str(i.module_id))]
                keyboard.append(button)
        else:
            for i in modules[:10]:
                button = [InlineKeyboardButton(text=i.name, callback_data='set_active_module|' + str(i.module_id))]
                keyboard.append(button)
            button = [InlineKeyboardButton(text='->', callback_data='page_forward|10')]
            keyboard.append(button)
        keyboard.append([InlineKeyboardButton(text='Главное меню', callback_data='back_to_main')])
        keyboard = InlineKeyboardMarkup(keyboard)
        try:
            if user_data['last_message']:
                user_data['training']['choose_module_btns'] = bot.edit_message_text(text,
                                                                                    update.effective_user.id,
                                                                                    user_data['last_message'].message_id,
                                                                                    reply_markup=keyboard)
            else:
                user_data['training']['choose_module_btns'] = bot.send_message(update.effective_user.id,
                                                                               text,
                                                                               reply_markup=keyboard)
        except Exception as ex:
            print(2121, ex)
    else:
        keyboard = InlineKeyboardMarkup([[InlineKeyboardButton(text='Добавить модуль', callback_data='add_mod')]])
        bot.send_message(update.effective_user.id,
                         'Вы еще не создали ни одного модуля. Создайте и начните тренироваться!',
                         reply_markup=keyboard)


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
                       message_id=user_data['last_message'].message_id)
    user_data['last_message'] = None
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
        if s.image:
            bot.send_photo(chat_id=update.effective_user.id,
                           photo=open('users_data/images/' + s.image, mode='rb'),
                           caption=s.word1)
        else:
            bot.send_message(chat_id=update.effective_user.id,
                             text=s.word1)
    else:
        user_data['training']['is_training'] = False
        bot.send_message(chat_id=update.effective_user.id,
                         text='Тренировка окончена',
                         reply_markup=ReplyKeyboardRemove())
        back_to_menu(bot, update, user_data)


def translate_word(bot, update, user_data, *args):
    if user_data['training']['sets']:
        s = user_data['training']['sets'].pop()
        user_data['training']['question'] = s
        user_data['training']['type'] = translate_word
        user_data['training']['answer'] = s.word1
        if s.image:
            bot.send_photo(chat_id=update.effective_user.id,
                           photo=open('users_data/images/' + s.image, mode='rb'),
                           caption=s.word2)
        else:
            bot.send_message(chat_id=update.effective_user.id,
                             text=s.word2)
    else:
        user_data['training']['is_training'] = False
        bot.send_message(chat_id=update.effective_user.id,
                         text='Тренировка окончена',
                         reply_markup=ReplyKeyboardRemove())
        back_to_menu(bot, update, user_data)


def_word = translate_word


def word_def(bot, update, user_data, *args):
    if user_data['training']['sets']:
        s = user_data['training']['sets'].pop()
        reply_keyboard = [['/OK'],
                          ['✖️ Завершить тренировку ✖️']]
        user_data['training']['type'] = word_def
        user_data['training']['answer'] = s.word2
        markup = ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=True)
        if s.image:
            bot.send_photo(chat_id=update.effective_user.id,
                           photo=open('users_data/images/' + s.image, mode='rb'),
                           caption=s.word1,
                           reply_markup=markup)
        else:
            bot.send_message(chat_id=update.effective_user.id,
                             text=s.word1, reply_markup=markup)
    else:
        user_data['training']['is_training'] = False
        bot.send_message(chat_id=update.effective_user.id,
                         text='Тренировка окончена',
                         reply_markup=ReplyKeyboardRemove())
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
        if s.image:
            bot.send_photo(chat_id=update.effective_user.id,
                           photo=open('users_data/images/' + s.image, mode='rb'),
                           caption=text)
        else:
            bot.send_message(chat_id=update.effective_user.id,
                             text=text)
        user_data['training']['answer'] = ' '.join(words)
        user_data['training']['type'] = two_or_three
    else:
        user_data['training']['is_training'] = False
        bot.send_message(chat_id=update.effective_user.id,
                         text='Тренировка окончена',
                         reply_markup=ReplyKeyboardRemove())
        back_to_menu(bot, update, user_data)


def revising(bot, update, user_data, *args):
    if user_data['training']['sets']:
        s = user_data['training']['sets'].pop()
        reply_keyboard = [['/OK'],
                          ['✖️ Завершить тренировку ✖️']]
        user_data['training']['type'] = revising
        user_data['training']['question'] = s
        markup = ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=True)
        if s.image:
            bot.send_photo(chat_id=update.effective_user.id,
                           photo=open('users_data/images/' + s.image, mode='rb'),
                           caption=s.word3,
                           reply_markup=markup)
        else:
            bot.send_message(chat_id=update.effective_user.id,
                             text=s.word3, reply_markup=markup)
    else:
        user_data['training']['is_training'] = False
        bot.send_message(chat_id=update.effective_user.id,
                         text='Тренировка окончена',
                         reply_markup=ReplyKeyboardRemove())
        back_to_menu(bot, update, user_data)


def word_def_ok(bot, update, user_data):
    if user_data['training']['type'] == revising:
        try:
            bot.send_message(update.effective_user.id,
                             text='Слово: ' + user_data['training']['question'].word1 + ' - ' + user_data['training'][
                                 'question'].word2)
            revising(bot, update, user_data)
        except Exception as ex:
            print(ex)
    elif user_data['training']['type'] == word_def:
        update.message.reply_text('Определение\n' + str(user_data['training']['answer']))
        word_def(bot, update, user_data)
