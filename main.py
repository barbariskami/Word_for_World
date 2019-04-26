from telegram.ext import Updater, MessageHandler, Filters, CommandHandler, CallbackQueryHandler, ConversationHandler
from telegram import ReplyKeyboardMarkup, ReplyKeyboardRemove, InlineKeyboardMarkup, InlineKeyboardButton
import infoDetails
import json
import db_work
import trains
import random

modules_type_codes = {'w_t': 'Слово - перевод', 'w_def': 'Слово - определение', '3_w': '3 слова', '4_w': '4 слова',
                      'w_t_e': 'Слово - перевод - определение', }

modules_training = {'w_t': ['Слово - Перевод', 'Перевод - Слово'],
                    'w_def': ['Определение - Термин', 'Термин - Определение'],
                    '3_w': ['Одно слово - Остальные два'], '4_w': ['Одно слово - Остальные три'],
                    'w_t_e': ['Повторение'], }


def find_out(bot, update, user_data):
    print(user_data)


def main():
    token = '802480610:AAGWxK1UkY9p-WW99yr6Mu4mBypaGD-3rFM'
    updater = Updater(token)
    dp = updater.dispatcher

    dp.add_handler(CommandHandler('start', start))
    dp.add_handler(CommandHandler('info', info, pass_user_data=True))
    dp.add_handler(CommandHandler('save_module', finish_adding, pass_user_data=True))
    dp.add_handler(CommandHandler('find_out', find_out, pass_user_data=True))
    dp.add_handler(CommandHandler('menu', back_to_menu))
    dp.add_handler(CommandHandler('add_module', start_adding, pass_user_data=True))
    dp.add_handler(CommandHandler('OK', word_def_ok, pass_user_data=True))
    dp.add_handler(CallbackQueryHandler(inline_q_handler, pass_user_data=True))
    dp.add_handler(MessageHandler(Filters.text, message_updater, pass_user_data=True))

    updater.start_polling()

    updater.idle()


def message_updater(bot, update, user_data):
    text = update.message.text

    if 'new_module' in user_data.keys() and user_data['new_module']['need_name']:
        if not db_work.ModulesDB.query.filter_by(name=text).all():
            user_data['new_module']['name'] = text
            user_data['new_module']['need_name'] = False
            ask_for_type(bot, update)
        else:
            update.message.reply_text('Такой модуль уже существует. Введите другое имя')
    elif 'new_module' in user_data.keys() and user_data['new_module']['adding_sets']:
        new_set = tuple(update.message.text.split('='))
        if (len(new_set) == 2 and (
                user_data['new_module']['type'] == 'w_t' or user_data['new_module']['type'] == 'w_def')) or (
                len(new_set) == 3 and (
                user_data['new_module']['type'] == '3_w' or user_data['new_module']['type'] == 'w_t_e')) or (
                len(new_set) == 4 and user_data['new_module']['type'] == '4_w'):
            user_data['new_module']['sets'].append(new_set)
        else:
            update.message.reply_text('Вы ввели что-то не то')
    elif 'training' in user_data.keys() and 'is_training' in user_data['training'].keys() and user_data['training'][
        'is_training']:
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
    else:
        update.message.reply_text('Извините, но я вас не понимаю')


def finish_adding(bot, update, user_data):
    try:
        if 'new_module' in user_data.keys() and user_data['new_module']['process']:
            if user_data['new_module']['sets']:
                module = db_work.ModulesDB(user_id=update.effective_user.id,
                                           name=user_data['new_module']['name'],
                                           type=user_data['new_module']['type'])
                db_work.db.session.add(module)
                db_work.db.session.commit()
                module_id = db_work.ModulesDB.query.filter_by(name=user_data['new_module']['name']).first().module_id
                for s in user_data['new_module']['sets']:
                    new_set = db_work.WordsSets(module_id=module_id,
                                                word1=s[0],
                                                word2=s[1],
                                                word3='' if len(s) < 3 else s[2],
                                                word4='' if len(s) < 4 else s[3], )
                    db_work.db.session.add(new_set)
                db_work.db.session.commit()
                update.message.reply_text('Модуль сохранен!')
                user_data['new_module']['adding_sets'] = False
            else:
                update.message.reply_text('Вы не добавили ни одну пару. Этот модуль не будет сохранен')
                user_data['new_module']['adding_sets'] = False
            back_to_menu(bot, update, user_data)
        else:
            update.message.reply_text('Эта функция не работает вне процесса создания модуля')
    except Exception as ex:
        print(32323, ex)


def info(bot, update, user_data):
    try:
        text = open('texts/info.txt', mode='r', encoding='utf8').read()
        keyboard = InlineKeyboardMarkup([[InlineKeyboardButton(text='Слово - перевод', callback_data='w_t_info')],
                                         [InlineKeyboardButton(text='Слово - определение', callback_data='w_def_info')],
                                         [InlineKeyboardButton(text='3/4 слова', callback_data='w34_info')],
                                         [InlineKeyboardButton(text='Слово - перевод - пример',
                                                               callback_data='w_t_e_info')],
                                         [InlineKeyboardButton(text='Добавление модуля', callback_data='add_info')],
                                         [InlineKeyboardButton(text='Тренировки', callback_data='train_info')],
                                         [InlineKeyboardButton(text='Главное меню', callback_data='back_to_main')]
                                         ])
        if 'info_message' not in user_data.keys() or not user_data['info_message']:
            user_data['info_message'] = bot.send_message(update.effective_user.id, text, reply_markup=keyboard)
        else:
            bot.edit_message_text(text, update.effective_user.id, user_data['info_message'].message_id,
                                  reply_markup=keyboard)
        return text
    except Exception as ex:
        print(ex)


def back_to_menu(bot, update, user_data):
    text = 'Выбери нужную опцию'
    button1 = InlineKeyboardButton(text='Информация', callback_data='main_info')
    button2 = InlineKeyboardButton(text='Добавить модуль', callback_data='add_mod|1|2|3')
    button3 = InlineKeyboardButton(text='Тренироваться', callback_data='train')
    keyboard = InlineKeyboardMarkup([[button1],
                                     [button2],
                                     [button3]])
    bot.send_message(update.effective_user.id, text, reply_markup=keyboard)
    user_data['info_message'] = False


def start(bot, update):
    text = 'Привет! Я - бот Word for World. ' \
           'Я помогу вам выучить иностранные слова или термины и определения. ' \
           'Вот основные функции, которые вам понадобятся:\n'
    text += open('texts/start.txt', mode='r', encoding='utf8').read()

    keyboard = InlineKeyboardMarkup([[InlineKeyboardButton(text='Информация', callback_data='main_info')],
                                     [InlineKeyboardButton(text='Добавить модуль', callback_data='add_mod|1|2|3')],
                                     [InlineKeyboardButton(text='Тренироваться', callback_data='train')]])
    try:
        update.message.reply_text(text, reply_markup=keyboard)
    except Exception as e:
        print(e, type(e))


def inline_q_handler(bot, update, user_data):
    def nothing():
        pass

    def main_info():
        info(bot, update, user_data)

    def add_mod(*args):
        start_adding(bot, update, user_data)

    def train(*args):
        start_training(bot, update, user_data)

    def back_to_main(*args):
        back_to_menu(bot, update, user_data)

    def w_t_info(*args):
        infoDetails.w_t_info(bot, update, user_data)

    def w_def_info(*args):
        infoDetails.w_def_info(bot, update, user_data)

    def w34_info(*args):
        infoDetails.w34_info(bot, update, user_data)

    def w_t_e_info(*args):
        infoDetails.w_t_e_info(bot, update, user_data)

    def add_info(*args):
        infoDetails.add_info(bot, update, user_data)

    def train_info(*args):
        infoDetails.train_info(bot, update, user_data)

    def set_type(*args):
        user_data['new_module']['type'] = args[0]
        bot.delete_message(chat_id=update.callback_query.from_user.id,
                           message_id=update.callback_query.message.message_id)
        bot.send_message(chat_id=update.callback_query.from_user.id,
                         text='Вы выбрали тип {}'.format(modules_type_codes[args[0]].lower()))

        reply_keyboard = [['/save_module']]
        markup = ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=True)
        bot.send_message(chat_id=update.callback_query.from_user.id,
                         text='Теперь вам нужно вводить пары (тройки/четверки) слов '
                              'или слово и определение, разделенные знаком "=" без пробелов например "привет=hello".'
                              'чтобы закончить ввод, нажмите на кнопку ниже',
                         reply_markup=markup)
        user_data['new_module']['adding_sets'] = True
        user_data['new_module']['sets'] = []

    def set_active_module(*args):
        bot.delete_message(chat_id=update.effective_user.id,
                           message_id=user_data['training']['choose_module_btns'].message_id)
        user_data['training']['active_module'] = db_work.ModulesDB.query.filter_by(module_id=int(args[0])).first()
        bot.send_message(chat_id=update.effective_user.id,
                         text='Вы выбрали модуль ' + user_data['training']['active_module'].name)
        keyboard = [[InlineKeyboardButton(text=i, callback_data='to_train|' + i)] for i in
                    modules_training[user_data['training']['active_module'].type]]
        keyboard = InlineKeyboardMarkup(keyboard)
        user_data['training']['choose_module_btns'] = bot.send_message(chat_id=update.effective_user.id,
                                                                       text='Теперь выберите тренировку',
                                                                       reply_markup=keyboard)

    def page_forward(*args):
        keyboard = []
        if len(user_data['training']['modules']) - int(args[0]) <= 10:
            for i in user_data['training']['modules'][int(args[0]):]:
                button = [InlineKeyboardButton(text=i.name, callback_data='set_active_module|' + str(i.module_id))]
                keyboard.append(button)
            button = [InlineKeyboardButton(text='<-', callback_data='page_back|' + args[0])]
            keyboard.append(button)
        else:
            for i in user_data['training']['modules'][int(args[0]):int(args[0]) + 10]:
                button = [InlineKeyboardButton(text=i.name, callback_data='set_active_module|' + str(i.module_id))]
                keyboard.append(button)
            button = [InlineKeyboardButton(text='<-', callback_data='page_back|' + args[0]),
                      InlineKeyboardButton(text='->', callback_data='page_forward|' + str(int(args[0]) + 10))]
            keyboard.append(button)
        keyboard = InlineKeyboardMarkup(keyboard)
        bot.edit_message_reply_markup(chat_id=update.effective_user.id,
                                      message_id=user_data['training']['choose_module_btns'].message_id,
                                      reply_markup=keyboard)

    def page_back(*args):
        keyboard = []
        for i in user_data['training']['modules'][int(args[0]) - 10:int(args[0])]:
            button = [InlineKeyboardButton(text=i.name, callback_data='set_active_module|' + str(i.module_id))]
            keyboard.append(button)
        button = []
        if int(args[0]) != 10:
            button = [InlineKeyboardButton(text='<-', callback_data='page_back|' + str(int(args[0]) - 10))]
        button.append(InlineKeyboardButton(text='->', callback_data='page_forward|' + args[0]))
        keyboard.append(button)
        keyboard = InlineKeyboardMarkup(keyboard)
        bot.edit_message_reply_markup(chat_id=update.effective_user.id,
                                      message_id=user_data['training']['choose_module_btns'].message_id,
                                      reply_markup=keyboard)

    def to_train(*args):
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
            trains.word_translate(bot, update, user_data)
            user_data['training']['mode'] = None
        elif args[0] == 'Перевод - Слово':
            trains.translate_word(bot, update, user_data)
            user_data['training']['mode'] = None
        elif args[0] == 'Определение - Термин':
            trains.def_word(bot, update, user_data)
            user_data['training']['mode'] = None
        elif args[0] == 'Термин - Определение':
            trains.word_def(bot, update, user_data)
            user_data['training']['mode'] = None
        elif args[0] == 'Одно слово - Остальные два':
            trains.two_or_three(bot, update, user_data, 3)
            user_data['training']['mode'] = 3
        elif args[0] == 'Одно слово - Остальные три':
            trains.two_or_three(bot, update, user_data, 4)
            user_data['training']['mode'] = 4
        elif args[0] == 'Повторение':
            trains.revising(bot, update, user_data)

    method, *payload = update.callback_query.data.split('|')
    try:
        text = locals().get(method, lambda d: None)(*payload)
        bot.answer_callback_query(update.callback_query.id, text=text)
    except Exception as ex:
        print(666, ex, type(ex))
        bot.sendMessage(125562178, text='hey')


def start_adding(bot, update, user_data):
    text = 'Введите название модуля'
    bot.send_message(update.effective_user.id, text)
    user_data['new_module'] = {}
    user_data['new_module']['process'] = True
    user_data['new_module']['need_name'] = True


def ask_for_type(bot, update):
    keyboard = InlineKeyboardMarkup([[InlineKeyboardButton(text='Слово - перевод', callback_data='set_type|w_t')],
                                     [InlineKeyboardButton(text='Слово - определение', callback_data='set_type|w_def')],
                                     [InlineKeyboardButton(text='3 слова', callback_data='set_type|3_w')],
                                     [InlineKeyboardButton(text='4 слова', callback_data='set_type|4_w')],
                                     [InlineKeyboardButton(text='Слово - перевод - пример',
                                                           callback_data='set_type|w_t_e')]
                                     ])

    try:
        update.message.reply_text('Теперь выбери тип модуля', reply_markup=keyboard)
    except Exception as ex:
        print(10101, ex)


def start_training(bot, update, user_data):
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
        keyboard = InlineKeyboardMarkup(keyboard)
        try:
            user_data['training']['choose_module_btns'] = bot.send_message(update.effective_user.id, text,
                                                                           reply_markup=keyboard)
        except Exception as ex:
            print(2121, ex)
    else:
        keyboard = InlineKeyboardMarkup([[InlineKeyboardButton(text='Добавить модуль', callback_data='add_mod')]])
        bot.send_message(update.effective_user.id,
                         'Вы еще не создали ни одного модуля. Создайте и начните тренироваться прямо сейчас!',
                         reply_markup=keyboard)


def word_def_ok(bot, update, user_data):
    if user_data['training']['type'] == trains.revising:
        try:
            bot.send_message(update.effective_user.id,
                             text='Слово: ' + user_data['training']['question'].word1 + ' - ' + user_data['training'][
                                 'question'].word2)
            trains.revising(bot, update, user_data)
        except Exception as ex:
            print(ex)
    elif user_data['training']['type'] == trains.word_def:
        trains.word_def(bot, update, user_data)


if __name__ == '__main__':
    main()
