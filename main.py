import traceback
import os
from telegram.ext import Updater, MessageHandler, Filters, CommandHandler, CallbackQueryHandler
from telegram import ReplyKeyboardMarkup, ReplyKeyboardRemove, InlineKeyboardMarkup, InlineKeyboardButton
import infoDetails
import db_work
import trains
import modules_work_tools
from serveces.barcode_scanner_image import scan_barcode

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

    dp.add_handler(CommandHandler('start', start, pass_user_data=True, pass_args=True))
    dp.add_handler(CommandHandler('info', info, pass_user_data=True))
    dp.add_handler(CommandHandler('find_out', find_out, pass_user_data=True))
    dp.add_handler(CommandHandler('menu', back_to_menu))
    dp.add_handler(CommandHandler('add_module', start_adding, pass_user_data=True))
    dp.add_handler(CommandHandler('OK', trains.word_def_ok, pass_user_data=True))
    dp.add_handler(CallbackQueryHandler(inline_q_handler, pass_user_data=True))
    dp.add_handler(MessageHandler(Filters.text, message_updater, pass_user_data=True))
    dp.add_handler(MessageHandler(Filters.photo, image_updater, pass_user_data=True))

    updater.start_polling()

    updater.idle()


def image_updater(bot, update, user_data):
    try:
        data = update.message.photo
        if 'new_module' in user_data.keys() and user_data['new_module']['adding_sets']:
            new_set = tuple(update.message.caption.split('='))
            if (len(new_set) == 2 and (
                    user_data['new_module']['type'] == 'w_t' or user_data['new_module']['type'] == 'w_def')) or (
                    len(new_set) == 3 and (
                    user_data['new_module']['type'] == '3_w' or
                    user_data['new_module']['type'] == 'w_t_e')) or (
                    len(new_set) == 4 and user_data['new_module']['type'] == '4_w'):
                im_name = str(update.message.from_user.id) + str(update.message.message_id) + '.jpg'
                user_data['new_module']['sets'].append({'set': new_set, 'image': im_name})
                try:
                    ph = data[1].get_file().download(
                        custom_path='users_data/images/' + im_name)
                except Exception as ex:
                    print(ex)
                    update.message.reply_text('Какие-то проблемы с сохранением картинки. Эта пара '
                                              'не сохранена. Попробуйте вновь, либо продолжайте ввод')
                    del user_data['new_module']['sets'][-1]
            else:
                update.message.reply_text('Вы ввели что-то не то. Пропробуйте еще раз')

        elif 'edit' in user_data.keys() and user_data['edit']['adding_pair']:
            user_data['last_message'] = None
            mod_type = db_work.ModulesDB.query.filter_by(module_id=user_data['edit']['adding_pair']).first().type
            new_set = tuple(update.message.caption.split('='))
            if (len(new_set) == 2 and (mod_type == 'w_t' or mod_type == 'w_def')) or (
                    len(new_set) == 3 and (mod_type == '3_w' or mod_type == 'w_t_e')) or (
                    len(new_set) == 4 and mod_type == '4_w'):
                im_name = str(update.message.from_user.id) + str(update.message.message_id) + '.jpg'
                try:
                    ph = data[1].get_file().download(
                        custom_path='users_data/images/' + im_name)
                except:
                    traceback.print_exc()
                    keyboard = InlineKeyboardMarkup(
                        [[InlineKeyboardButton(text='Вернуться', callback_data='cancel_editing_module')]])
                    update.message.reply_text('Какие-то проблемы с сохранением картинки. Эта пара '
                                              'не сохранена. Попробуйте вновь, либо вернитесь к '
                                              'выбору пары для изменения',
                                              reply_markup=keyboard)
                    return

                set_obj = db_work.WordsSets(module_id=user_data['edit']['adding_pair'],
                                            word1=new_set[0].strip(),
                                            word2=new_set[1].strip(),
                                            word3='' if len(new_set) < 3 else new_set[2].strip(),
                                            word4='' if len(new_set) < 4 else new_set[3].strip(),
                                            image=im_name)
                db_work.db.session.add(set_obj)
                db_work.db.session.commit()
                update.message.reply_text('Отлично! Пара сохранена. Можете продолжать редактирование.')
                modules_work_tools.choose_edit_set(bot, update, user_data, user_data['edit']['adding_pair'])

            else:
                update.message.reply_text('Вы ввели что-то не то')
        elif 'edit' in user_data.keys() and user_data['edit']['edit_mod']['mod'] == 'image':
            editing_set = db_work.WordsSets.query.filter_by(set_id=user_data['edit']['edit_mod']['set_id']).first()
            im_name = str(update.message.from_user.id) + str(update.message.message_id) + '.jpg'
            try:
                ph = data[1].get_file().download(
                    custom_path='users_data/images/' + im_name)
            except Exception:
                traceback.print_exc()
                keyboard = InlineKeyboardMarkup(
                    [[InlineKeyboardButton(text='Вернуться', callback_data='cancel_editing_module')]])
                update.message.reply_text('Какие-то проблемы с сохранением картинки. Эта пара '
                                          'не сохранена. Попробуйте вновь, либо вернитесь к '
                                          'выбору пары для изменения',
                                          reply_markup=keyboard)
                return
            if editing_set.image:
                os.remove('users_data/images/' + editing_set.image)
            db_work.db.session.delete(editing_set)
            new_set = db_work.WordsSets(module_id=editing_set.module_id,
                                        word1=editing_set.word1,
                                        word2=editing_set.word2,
                                        word3=editing_set.word3,
                                        word4=editing_set.word4,
                                        image=im_name)
            db_work.db.session.add(new_set)
            db_work.db.session.commit()
            update.message.reply_text('Изменение сохранено!')
            mod_id = db_work.ModulesDB.query.filter_by(module_id=editing_set.module_id).first().module_id
            user_data['edit']['edit_mod']['mod'] = None
            user_data['edit']['edit_mod']['set_id'] = None

            modules_work_tools.choose_edit_set(bot, update, user_data, mod_id)

        else:
            try:
                data = update.message.photo
                ph = data[1].get_file().download(
                    custom_path='users_data/images/code.jpg')
                res = scan_barcode('users_data/images/code.jpg')
                print(res)
                module = db_work.ModulesDB.query.filter_by(module_id=int(res.split('=')[-1])).first()
                modules_work_tools.copy_module(bot, update, module)
                update.message.reply_text('Модуль успешно скоприрован! Можете продолжать работу')
                if not res:
                    update.message.reply_text('Вы прислали мне картинку. Но зачем?🤷‍♂️')
            except Exception:
                traceback.print_exc()

    except Exception as ex:
        traceback.print_exc()
        update.message.reply_text('Вы прислали мне картинку без подписи. Если вы создаете '
                                  'модуль с телефона, выберите фотографию галочкой, затем '
                                  'нажмите на нее и добавьте подпись внизу экрана. Можете '
                                  'продолжать добавление слов')


def message_updater(bot, update, user_data):
    try:
        text = update.message.text

        if text == '📥 Сохранить модуль':
            finish_adding(bot, update, user_data)

        elif text == '🏠 Главное меню 🏠':
            message = 'Вы действительно хотите выйти из режима добавления? Модуль не ' \
                      'будет сохранен.'
            keyboard = InlineKeyboardMarkup([[InlineKeyboardButton(text='Да', callback_data='continue_add_mod|1')],
                                             [InlineKeyboardButton(text='Отмена',
                                                                   callback_data='continue_add_mod|')]])
            user_data['cancel_message'] = bot.send_message(update.effective_user.id, message, reply_markup=keyboard)

        elif text == '✖️ Завершить тренировку ✖️':
            message = 'Вы действительно хотите завершить тренировку досрочно? Вы повторили еще не все слова.'
            keyboard = InlineKeyboardMarkup([[InlineKeyboardButton(text='Да', callback_data='continue_training_mod|1')],
                                             [InlineKeyboardButton(text='Отмена',
                                                                   callback_data='continue_training_mod|')]])
            user_data['cancel_message'] = bot.send_message(update.effective_user.id, message, reply_markup=keyboard)


        elif 'new_module' in user_data.keys() and user_data['new_module']['need_name']:
            if not db_work.ModulesDB.query.filter_by(name=text).all():
                user_data['new_module']['name'] = text
                user_data['new_module']['need_name'] = False
                ask_for_type(bot, update, user_data)
            else:
                update.message.reply_text('Такой модуль уже существует. Введите другое имя')

        # Добавление нового модуля
        elif 'new_module' in user_data.keys() and user_data['new_module']['adding_sets']:
            new_set = tuple(update.message.text.split('='))
            if (len(new_set) == 2 and (
                    user_data['new_module']['type'] == 'w_t' or user_data['new_module']['type'] == 'w_def')) or (
                    len(new_set) == 3 and (
                    user_data['new_module']['type'] == '3_w' or user_data['new_module']['type'] == 'w_t_e')) or (
                    len(new_set) == 4 and user_data['new_module']['type'] == '4_w'):
                user_data['new_module']['sets'].append({'set': new_set, 'image': ''})
            else:
                update.message.reply_text('Вы ввели что-то не то')

        # Проверка ответа во время тренировки
        elif 'training' in user_data.keys() and 'is_training' in user_data['training'].keys() and \
                user_data['training']['is_training']:
            try:
                trains.check_answer(bot, update, user_data, text)
            except KeyError:
                update.message.reply_text('Не нужно ничего присылать. Если вы уже повторили предложение,'
                                          ' нажмите кнопку OK')

        # Добавление пары в уже существующий модуль
        elif 'edit' in user_data.keys() and user_data['edit']['adding_pair']:
            user_data['last_message'] = None
            mod_type = db_work.ModulesDB.query.filter_by(module_id=user_data['edit']['adding_pair']).first().type
            new_set = tuple(update.message.text.split('='))
            if (len(new_set) == 2 and (mod_type == 'w_t' or mod_type == 'w_def')) or (
                    len(new_set) == 3 and (mod_type == '3_w' or mod_type == 'w_t_e')) or (
                    len(new_set) == 4 and mod_type == '4_w'):
                set_obj = db_work.WordsSets(module_id=user_data['edit']['adding_pair'],
                                            word1=new_set[0].strip(),
                                            word2=new_set[1].strip(),
                                            word3='' if len(new_set) < 3 else new_set[2].strip(),
                                            word4='' if len(new_set) < 4 else new_set[3].strip(),
                                            image='')
                db_work.db.session.add(set_obj)
                db_work.db.session.commit()
                update.message.reply_text('Отлично! Пара сохранена. Можете продолжать редактирование.')
                modules_work_tools.choose_edit_set(bot, update, user_data, user_data['edit']['adding_pair'])
                user_data['edit']['adding_pair'] = False
            else:
                keyboard = InlineKeyboardMarkup(
                    [[InlineKeyboardButton(text='Вернуться', callback_data='cancel_editing_module')]])
                update.message.reply_text('Вы ввели не то колличество слов. Введите вновь или отмените действие',
                                          reply_markup=keyboard)

        elif 'edit' in user_data.keys() and user_data['edit']['edit_mod']['mod'] == 'words':
            set = db_work.WordsSets.query.filter_by(set_id=user_data['edit']['edit_mod']['set_id']).first()
            db_work.db.session.delete(set)
            new_words = tuple(update.message.text.split('='))
            mod_type = db_work.ModulesDB.query.filter_by(module_id=set.module_id).first().type
            if (len(new_words) == 2 and (mod_type == 'w_t' or mod_type == 'w_def')) or (
                    len(new_words) == 3 and (mod_type == '3_w' or mod_type == 'w_t_e')) or (
                    len(new_words) == 4 and mod_type == '4_w'):
                new_set = db_work.WordsSets(module_id=set.module_id,
                                            word1=new_words[0],
                                            word2=new_words[1],
                                            word3='' if len(new_words) < 3 else new_words[2].strip(),
                                            word4='' if len(new_words) < 4 else new_words[3].strip(),
                                            image=set.image)
                db_work.db.session.add(new_set)
                db_work.db.session.commit()
                mod_id = db_work.ModulesDB.query.filter_by(module_id=set.module_id).first().module_id
                update.message.reply_text('Изменение сохранено!')
                user_data['edit']['edit_mod']['mod'] = None
                user_data['edit']['edit_mod']['set_id'] = None
                modules_work_tools.choose_edit_set(bot, update, user_data, mod_id)
            else:
                keyboard = InlineKeyboardMarkup(
                    [[InlineKeyboardButton(text='Вернуться', callback_data='cancel_editing_module')]])
                update.message.reply_text('Вы ввели не то колличество слов. Введите вновь или отмените действие',
                                          reply_markup=keyboard)

        else:
            update.message.reply_text('Извините, но я вас не понимаю')
    except:
        traceback.print_exc()


def finish_adding(bot, update, user_data):
    try:
        if 'new_module' in user_data.keys() and user_data['new_module']['process']:
            if user_data['new_module']['sets']:
                module = db_work.ModulesDB(user_id=update.effective_user.id,
                                           name=user_data['new_module']['name'],
                                           type=user_data['new_module']['type'],
                                           lang=user_data['new_module']['language'])
                db_work.db.session.add(module)
                db_work.db.session.commit()
                module_id = db_work.ModulesDB.query.filter_by(name=user_data['new_module']['name']).first().module_id
                for s in user_data['new_module']['sets']:
                    new_set = db_work.WordsSets(module_id=module_id,
                                                word1=s['set'][0].strip(),
                                                word2=s['set'][1].strip(),
                                                word3='' if len(s['set']) < 3 else s['set'][2].strip(),
                                                word4='' if len(s['set']) < 4 else s['set'][3].strip(),
                                                image=s['image'])
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
    except Exception:
        traceback.print_exc()


def info(bot, update, user_data):
    try:
        text = open('texts/info.txt', mode='r', encoding='utf8').read()
        keyboard = InlineKeyboardMarkup([[InlineKeyboardButton(text='Слово - перевод', callback_data='w_t_info')],
                                         [InlineKeyboardButton(text='Слово - определение', callback_data='w_def_info')],
                                         [InlineKeyboardButton(text='3/4 слова', callback_data='w34_info')],
                                         [InlineKeyboardButton(text='Слово - перевод - пример',
                                                               callback_data='w_t_e_info')],
                                         [InlineKeyboardButton(text='Работа с модулями', callback_data='add_info')],
                                         [InlineKeyboardButton(text='Тренировки', callback_data='train_info')],
                                         [InlineKeyboardButton(text='Главное меню', callback_data='back_to_main')]
                                         ])
        if not user_data['last_message']:
            user_data['last_message'] = bot.send_message(update.effective_user.id, text, reply_markup=keyboard)
        else:
            bot.edit_message_text(text, update.effective_user.id, user_data['last_message'].message_id,
                                  reply_markup=keyboard)
        return text
    except Exception:
        traceback.print_exc()


def back_to_menu(bot, update, user_data):
    text = 'Выбери нужную опцию'
    button1 = InlineKeyboardButton(text='❓Информация', callback_data='main_info')
    button2 = InlineKeyboardButton(text='📋Работа с модулями', callback_data='modules_work')
    button3 = InlineKeyboardButton(text='✏️Тренироваться️', callback_data='train')
    keyboard = InlineKeyboardMarkup([[button1],
                                     [button2],
                                     [button3]])
    if user_data['last_message']:
        bot.edit_message_text(text, update.effective_user.id,
                              user_data['last_message'].message_id,
                              reply_markup=keyboard)
    else:
        user_data['last_message'] = bot.send_message(update.effective_user.id, text, reply_markup=keyboard)


def start(bot, update, user_data, args):
    text = 'Привет! Я - бот Word for World. ' \
           'Я помогу вам выучить иностранные слова или термины и определения. ' \
           '\nВы можете добавлять Модули - порции слов, которые можно тренировать. ' \
           'Чтобы добавить новый модуль, перейдите в раздел "Работа с модулями"\n' \
           'Если вы перешли сюда с помощью qr-кода, и если с вами кто-то поделился модулем, ' \
           'прищлите код еще раз. И вообще, если вы хотите добавить модуль, которым' \
           'с вами поделились, пришлите код в любой момент. Модуль будет добавлен вам,' \
           'и вы сможете дальше продолжать работу.\n' \
           'Вот основные функции, которые вам понадобятся:\n'
    text += open('texts/start.txt', mode='r', encoding='utf8').read()
    user_data.clear()

    keyboard = InlineKeyboardMarkup([[InlineKeyboardButton(text='❓Информация', callback_data='main_info')],
                                     [InlineKeyboardButton(text='📋Работа с модулями', callback_data='modules_work')],
                                     [InlineKeyboardButton(text='✏️Тренироваться', callback_data='train')]])
    update.message.reply_text(text, reply_markup=ReplyKeyboardRemove())
    user_data['last_message'] = update.message.reply_text('Меню', reply_markup=keyboard)
    try:
        if args:
            module = db_work.ModulesDB.query.filter_by(module_id=int(args[0])).first()
            if module:
                modules_work_tools.copy_module(bot, update, module)
                update.message.reply_text('Вы начали работу с помошью ссылки, которая нужна для копирования '
                                          'модуля. Модуль сохранен в вашу папку.')
            else:
                update.message.reply_text('Вы начали работу с помошью ссылки, которая нужна для копирования '
                                          'модуля. Но видимо модуль, который вы хотите сохранить, был удален. '
                                          'Нам правда жаль.')
    except:
        traceback.print_exc()
        update.message.reply_text('Ой, что-то пошло не так!')


def inline_q_handler(bot, update, user_data):
    def nothing():
        pass

    def main_info():
        info(bot, update, user_data)

    def modules_work(*args):
        modules_work_menu(bot, update, user_data)

    def add_mod(*args):
        start_adding(bot, update, user_data)

    def continue_add_mod(*args):
        if args[0]:
            if user_data['last_message']:
                bot.delete_message(update.effective_user.id, user_data['last_message'].message_id)
            bot.delete_message(update.effective_user.id, user_data['cancel_message'].message_id)
            bot.send_message(update.effective_user.id, 'Модуль не сохранен')
            user_data['last_message'] = None
            back_to_menu(bot, update, user_data)
        else:
            keyboard = ReplyKeyboardMarkup([['🏠 Главное меню 🏠']], one_time_keyboard=True)
            bot.delete_message(update.effective_user.id, user_data['cancel_message'].message_id)
            bot.send_message(update.effective_user.id, 'Продолжайте с того же места, на котором закончили',
                             reply_markup=keyboard)

    def edit_mod(*args):
        modules_work_tools.start_edit_mod(bot, update, user_data)

    def choose_edit_set(*args):
        modules_work_tools.choose_edit_set(bot, update, user_data, args[0])

    def choose_edit_action(*args):
        modules_work_tools.choose_edit_action(bot, update, user_data, args[0])

    def edit_action(*args):
        if args[0] == 'words':
            modules_work_tools.edit_words(bot, update, user_data, int(args[1]))
        elif args[0] == 'image':
            modules_work_tools.edit_image(bot, update, user_data, int(args[1]))
        elif args[0] == 'ask_del':
            modules_work_tools.delete_set(bot, update, user_data, int(args[1]), False)
        elif args[0] == 'del':
            modules_work_tools.delete_set(bot, update, user_data, int(args[1]), True)

    def add_pair(*args):
        modules_work_tools.add_pair(bot, update, user_data, int(args[0]))

    def del_mod(*args):
        modules_work_tools.start_del_mod(bot, update, user_data)

    def delete_module(*args):
        modules_work_tools.delete_module(bot, update, user_data, int(args[0]), False if len(args) == 1 else True)

    def share_mod(*args):
        modules_work_tools.start_share_mod(bot, update, user_data)

    def share_module(*args):
        modules_work_tools.share_module(bot, update, user_data, args[0])

    def train(*args):
        if args:
            trains.choose_module(bot, update, user_data, True)
        else:
            trains.choose_module(bot, update, user_data, False)

    def continue_training_mod(*args):
        if args[0]:
            if user_data['last_message']:
                bot.delete_message(update.effective_user.id, user_data['last_message'].message_id)
            bot.delete_message(update.effective_user.id, user_data['cancel_message'].message_id)
            bot.send_message(update.effective_user.id, 'Тренировка окончена')
            user_data['training']['is_training'] = False
            user_data['last_message'] = None
            back_to_menu(bot, update, user_data)
        else:
            keyboard = ReplyKeyboardMarkup([['✖️ Завершить тренировку ✖️']], one_time_keyboard=True)
            bot.delete_message(update.effective_user.id, user_data['cancel_message'].message_id)
            bot.send_message(update.effective_user.id, 'Продолжайте с того же места, на котором закончили',
                             reply_markup=keyboard)

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

    def edit_info(*args):
        infoDetails.edit_info(bot, update, user_data)

    def cancel_adding_module(*args):
        user_data['edit']['adding_pair'] = False
        modules_work_tools.choose_edit_set(bot, update, user_data, user_data['edit']['adding_pair'])

    def set_type(*args):
        try:
            user_data['new_module']['type'] = args[0]
            user_data['last_message'] = None
            bot.delete_message(chat_id=update.callback_query.from_user.id,
                               message_id=update.callback_query.message.message_id)
            bot.send_message(chat_id=update.callback_query.from_user.id,
                             text='Вы выбрали тип {}'.format(modules_type_codes[args[0]].lower()))
            if user_data['new_module']['type'] != 'w_def':
                ask_for_language(bot, update, user_data)
            else:
                start_add_sets(bot, update, user_data)
        except:
            traceback.print_exc()

    def set_lang(*args):
        user_data['new_module']['language'] = args[0]
        start_add_sets(bot, update, user_data)

    def set_active_module(*args):
        bot.delete_message(chat_id=update.effective_user.id,
                           message_id=user_data['training']['choose_module_btns'].message_id)
        if user_data['training']['inbuilt']:
            user_data['training']['active_module'] = db_work.InbuiltModule.query.filter_by(
                module_id=int(args[0])).first()
        else:
            user_data['training']['active_module'] = db_work.ModulesDB.query.filter_by(module_id=int(args[0])).first()
        keyboard = ReplyKeyboardMarkup([['✖️ Завершить тренировку ✖️']], one_time_keyboard=True)
        bot.send_message(chat_id=update.effective_user.id,
                         text='Вы выбрали модуль ' + user_data['training']['active_module'].name,
                         reply_markup=keyboard)
        keyboard = [[InlineKeyboardButton(text=i, callback_data='to_train|' + i)] for i in
                    modules_training[user_data['training']['active_module'].type]]
        keyboard = InlineKeyboardMarkup(keyboard)
        user_data['last_message'] = bot.send_message(chat_id=update.effective_user.id,
                                                     text='Теперь выберите тренировку',
                                                     reply_markup=keyboard)

    def page_forward(*args):
        keyboard = []
        if user_data['training']['inbuilt']:
            keyboard.append([InlineKeyboardButton(text='Перейти ко встроенным модулям', callback_data='train|1')])
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
        if not user_data['training']['inbuilt']:
            keyboard.append([InlineKeyboardButton(text='Главное меню', callback_data='back_to_main')])
        else:
            keyboard.append([InlineKeyboardButton(text='Назад к вашим модулям', callback_data='train')])
        keyboard = InlineKeyboardMarkup(keyboard)
        bot.edit_message_reply_markup(chat_id=update.effective_user.id,
                                      message_id=user_data['last_message'].message_id,
                                      reply_markup=keyboard)

    def page_back(*args):
        keyboard = []
        if user_data['training']['inbuilt']:
            keyboard.append([InlineKeyboardButton(text='Перейти ко встроенным модулям', callback_data='train|1')])
        for i in user_data['training']['modules'][int(args[0]) - 10:int(args[0])]:
            button = [InlineKeyboardButton(text=i.name, callback_data='set_active_module|' + str(i.module_id))]
            keyboard.append(button)
        button = []
        if int(args[0]) != 10:
            button = [InlineKeyboardButton(text='<-', callback_data='page_back|' + str(int(args[0]) - 10))]
        button.append(InlineKeyboardButton(text='->', callback_data='page_forward|' + args[0]))
        keyboard.append(button)
        if not user_data['training']['inbuilt']:
            keyboard.append([InlineKeyboardButton(text='Главное меню', callback_data='back_to_main')])
        else:
            keyboard.append([InlineKeyboardButton(text='Назад к вашим модулям', callback_data='train')])
        keyboard = InlineKeyboardMarkup(keyboard)
        bot.edit_message_reply_markup(chat_id=update.effective_user.id,
                                      message_id=user_data['last_message'].message_id,
                                      reply_markup=keyboard)

    def edit_mod_page_forward(*args):
        modules_work_tools.edit_mod_page_forward(bot, update, user_data, args[0], int(args[1]),
                                                 None if args[0] != 'sets' else args[2])

    def edit_mod_page_back(*args):
        modules_work_tools.edit_mod_page_back(bot, update, user_data, args[0], int(args[1]),
                                              None if args[0] != 'sets' else args[2])

    def to_train(*args):
        trains.start(bot, update, user_data, *args)

    method, *payload = update.callback_query.data.split('|')
    try:
        text = locals().get(method, lambda d: None)(*payload)
        bot.answer_callback_query(update.callback_query.id, text=text)
    except Exception:
        traceback.print_exc()


def start_adding(bot, update, user_data):
    text = 'Введите название модуля'
    user_id = update.effective_user.id
    keyboard = ReplyKeyboardMarkup([['🏠 Главное меню 🏠']], one_time_keyboard=True)
    bot.delete_message(update.effective_user.id, user_data['last_message'].message_id)
    bot.send_message(user_id, text, reply_markup=keyboard)
    user_data['last_message'] = None
    user_data['new_module'] = {}
    user_data['new_module']['process'] = True
    user_data['new_module']['need_name'] = True


def modules_work_menu(bot, update, user_data):
    keyboard = InlineKeyboardMarkup([[InlineKeyboardButton(text='Добавить модуль', callback_data='add_mod')],
                                     [InlineKeyboardButton(text='Редактировать модуль', callback_data='edit_mod')],
                                     [InlineKeyboardButton(text='Удалить модуль', callback_data='del_mod')],
                                     [InlineKeyboardButton(text='Поделиться модулем', callback_data='share_mod')],
                                     [InlineKeyboardButton(text='Главное меню', callback_data='back_to_main')]
                                     ])
    text = 'Выберите дальнейшее действие'
    if user_data['last_message']:
        user_data['last_message'] = bot.edit_message_text(text, update.effective_user.id,
                                                          user_data['last_message'].message_id,
                                                          reply_markup=keyboard)
    else:
        user_data['last_message'] = bot.send_message(update.effective_user.id, text, reply_markup=keyboard)


def ask_for_type(bot, update, user_data):
    keyboard = InlineKeyboardMarkup([[InlineKeyboardButton(text='Слово - перевод', callback_data='set_type|w_t')],
                                     [InlineKeyboardButton(text='Слово - определение', callback_data='set_type|w_def')],
                                     [InlineKeyboardButton(text='3 слова', callback_data='set_type|3_w')],
                                     [InlineKeyboardButton(text='4 слова', callback_data='set_type|4_w')],
                                     [InlineKeyboardButton(text='Слово - перевод - пример',
                                                           callback_data='set_type|w_t_e')]
                                     ])

    try:
        user_data['last_message'] = bot.send_message(update.effective_user.id, 'Теперь выбери тип модуля',
                                                     reply_markup=keyboard)
    except Exception as ex:
        traceback.print_exc()


def ask_for_language(bot, update, user_data):
    keyboard = [[InlineKeyboardButton(text='Английский', callback_data='set_lang|en-US')],
                [InlineKeyboardButton(text='Турецкий', callback_data='set_lang|tr-TR')],
                [InlineKeyboardButton(text='Русский', callback_data='set_lang|ru-RU')],
                [InlineKeyboardButton(text='Другой', callback_data='set_lang|')]
                ]
    keyboard = InlineKeyboardMarkup(keyboard)
    user_data['last_message'] = bot.send_message(update.effective_user.id,
                                                 'Выберите язык ПЕРВОГО слова (слов) в модуле. Это '
                                                 'необходимо для произношения слов.',
                                                 reply_markup=keyboard)


def start_add_sets(bot, update, user_data):
    if user_data['last_message']:
        bot.delete_message(chat_id=update.effective_user.id,
                           message_id=user_data['last_message'].message_id)
        user_data['last_message'] = None
    reply_keyboard = [['📥 Сохранить модуль'],
                      ['🏠 Главное меню 🏠']]
    markup = ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=True)
    bot.send_message(chat_id=update.callback_query.from_user.id,
                     text='Теперь вам нужно вводить пары (тройки/четверки) слов '
                          'или слово и определение, разделенные знаком "=" без пробелов например '
                          '"hello=привет" (в зависимости от модуля) каждое ОТДЕЛЬНЫМ СООБЩЕНИЕМ. '
                          'Если хотите добавить картинку к модулю, '
                          'пришлите ее и текст в качестве подписи (Чтбы сделать это с телефона, СНАЧАЛА '
                          'выберите картинку, после этого нажмите на нее и введите тест в качестве подписи '
                          'внизу экрана). \nЧтобы закончить ввод, нажмите на кнопку "Сохранить модуль" '
                          '(Если вы пользуетесь ботом с телефона, кнопка будет скрыта, нажмите на значок '
                          '⚃ рядом со значком микрофона)',
                     reply_markup=markup)
    user_data['new_module']['adding_sets'] = True
    user_data['new_module']['sets'] = []


if __name__ == '__main__':
    main()
