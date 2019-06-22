import traceback
import os
from telegram.ext import Updater, MessageHandler, Filters, CommandHandler, CallbackQueryHandler, ConversationHandler
from telegram import ReplyKeyboardMarkup, ReplyKeyboardRemove, InlineKeyboardMarkup, InlineKeyboardButton
import infoDetails
import db_work
import trains
import modules_work_tools
from serveces.barcode_scanner_image import scan_barcode
from serveces.translation import translate

# Словарь сопостовляющий код типа модуля и его название
modules_type_codes = {'w_t': 'Слово - перевод', 'w_def': 'Слово - определение', '3_w': '3 слова', '4_w': '4 слова',
                      'w_t_e': 'Слово - перевод - пример', }

# Словарь в котором коду модуля соответствуют списки тренировок, доступных для этого модуля
modules_training = {'w_t': ['Слово - Перевод', 'Перевод - Слово'],
                    'w_def': ['Определение - Термин', 'Термин - Определение'],
                    '3_w': ['Одно слово - Остальные два'], '4_w': ['Одно слово - Остальные три'],
                    'w_t_e': ['Повторение'], }


def find_out(bot, update, user_data):
    print(user_data)


# Главная функция
def main():
    token = '683346269:AAE66lBZvg--IDGUbUh-mPK2SWRrAv_Tvhw'
    updater = Updater(token)
    dp = updater.dispatcher

    dp.add_handler(CommandHandler('start', start, pass_user_data=True, pass_args=True))
    dp.add_handler(CommandHandler('info', info, pass_user_data=True))
    dp.add_handler(CommandHandler('find_out', find_out, pass_user_data=True))
    dp.add_handler(CommandHandler('menu', back_to_menu))
    dp.add_handler(CommandHandler('add_module', start_adding, pass_user_data=True))
    dp.add_handler(CommandHandler('OK', trains.word_def_ok, pass_user_data=True))

    check_finishing_adding = MessageHandler(Filters.text, ask_about_finishing_adding, pass_user_data=True)
    # Хэндлер для диалога на добавление модуля:
    add_module_conversation = ConversationHandler(
        entry_points=[CallbackQueryHandler(start_adding, pattern='add_mod', pass_user_data=True)],
        states={'ask_for_type': [MessageHandler(Filters.text, ask_for_type, pass_user_data=True)],
                'ask_for_language': [CallbackQueryHandler(ask_for_language, pass_user_data=True)],
                'ask_about_translation': [CallbackQueryHandler(ask_about_translation, pass_user_data=True)],
                'ask_first_word': [CallbackQueryHandler(ask_first_word, pass_user_data=True)],
                'ask_second_word': [MessageHandler(Filters.text, ask_second_word, pass_user_data=True)],
                'ask_translation': [MessageHandler(Filters.text, ask_translation, pass_user_data=True),
                                    CallbackQueryHandler(ask_translation, pass_user_data=True)],
                'receive_answer_about_finishing_adding':
                    [CallbackQueryHandler(receive_answer_about_finishing_adding, pass_user_data=True)]
                },
        fallbacks=[CommandHandler('start', start, pass_user_data=True, pass_args=True)])
    dp.add_handler(add_module_conversation)

    dp.add_handler(MessageHandler(Filters.text, message_updater, pass_user_data=True))
    dp.add_handler(MessageHandler(Filters.photo, image_updater, pass_user_data=True))
    dp.add_handler(CallbackQueryHandler(inline_q_handler, pass_user_data=True))

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
    print('обрабатывается обычным разработчиком')
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

        # elif 'new_module' in user_data.keys() and user_data['new_module']['need_name']:
        #     if not db_work.ModulesDB.query.filter_by(name=text).all():
        #         user_data['new_module']['name'] = text
        #         user_data['new_module']['need_name'] = False
        #         ask_for_type(bot, update, user_data)
        #     else:
        #         update.message.reply_text('Такой модуль уже существует. Введите другое имя')

        # Добавление нового модуля
        # elif 'new_module' in user_data.keys() and user_data['new_module']['adding_sets']:
        #     new_set = tuple(update.message.text.split('='))
        #     if (len(new_set) == 2 and (
        #             user_data['new_module']['type'] == 'w_t' or user_data['new_module']['type'] == 'w_def')) or (
        #             len(new_set) == 3 and (
        #             user_data['new_module']['type'] == '3_w' or user_data['new_module']['type'] == 'w_t_e')) or (
        #             len(new_set) == 4 and user_data[' new_module']['type'] == '4_w'):
        #         user_data['new_module']['sets'].append({'set': new_set, 'image': ''})
        #     else:
        #         update.message.reply_text('Вы ввели что-то не то')

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


# Отображает основную информацию и кнопки для перехода на следующие разделы
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


# Еще одна версия открытия главного меню (в этом плане аналогична старту)
def back_to_menu(bot, update, user_data):
    text = 'Выбери нужную опцию'
    keyboard = InlineKeyboardMarkup([[InlineKeyboardButton(text='❓Информация', callback_data='main_info')],
                                     [InlineKeyboardButton(text='📋Работа с модулями', callback_data='modules_work')],
                                     [InlineKeyboardButton(text='✏️Тренироваться️', callback_data='train')]])
    if user_data['last_message']:
        bot.edit_message_text(text, update.effective_user.id,
                              user_data['last_message'].message_id,
                              reply_markup=keyboard)
    else:
        user_data['last_message'] = bot.send_message(update.effective_user.id, text, reply_markup=keyboard)
    return ConversationHandler.END


# Запуск (перезапуск) бота
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
    # Проверка ссылки на наличие аргументов:
    try:
        # Если бот запускался ссылкой, имеющей аргументы, значит это была ссылка для копирования модуля
        if args:
            # Пытаемся достать этот модуль и скопировать его пользователю
            module = db_work.ModulesDB.query.filter_by(module_id=int(args[0])).first()
            if module:
                modules_work_tools.copy_module(bot, update, module)
                update.message.reply_text('Вы начали работу с помошью ссылки, которая нужна для копирования '
                                          'модуля. Модуль сохранен в вашу папку.')
            else:
                update.message.reply_text('Вы начали работу с помошью ссылки, которая нужна для копирования '
                                          'модуля. Но видимо модуль, который вы хотите сохранить, был удален '
                                          'или ссылка была неправильной. Нам правда жаль.')
    except:
        traceback.print_exc()
        update.message.reply_text('Ой, наверное вам должен был добавится модуль, но что-то пошло не так!')
    # Завершает диалог, если он был начат ранее для полного обнуления бота
    return ConversationHandler.END


def inline_q_handler(bot, update, user_data):
    # Запускает вызов основного меню информации
    def main_info():
        info(bot, update, user_data)

    # Запускает открытие меню выбора действия с модулем
    def modules_work(*args):
        modules_work_menu(bot, update, user_data)

    # def add_mod(*args):
    #     start_adding(bot, update, user_data)

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

    # def set_type(*args):
    #     try:
    #         user_data['new_module']['type'] = args[0]
    #         user_data['last_message'] = None
    #         bot.delete_message(chat_id=update.callback_query.from_user.id,
    #                            message_id=update.callback_query.message.message_id)
    #         bot.send_message(chat_id=update.callback_query.from_user.id,
    #                          text='Вы выбрали тип {}'.format(modules_type_codes[args[0]].lower()))
    #         if user_data['new_module']['type'] != 'w_def':
    #             ask_for_language(bot, update, user_data)
    #         else:
    #             start_add_sets(bot, update, user_data)
    #     except:
    #         traceback.print_exc()

    # def set_lang(*args):
    #     user_data['new_module']['language'] = args[0]
    #     start_add_sets(bot, update, user_data)

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
        f = locals().get(method, None)
        if f:
            text = f(*payload)
        else:
            text = ''
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
    # user_data['new_module']['need_name'] = True
    return 'ask_for_type'


# Меню выбора действия с модулем
def modules_work_menu(bot, update, user_data):
    # Просим выбрать следующие действие
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
    text = update.message.text
    # Если такого модуля еще нет, сохраняем, иначе переспрашиваем
    if not db_work.ModulesDB.query.filter_by(name=text).all():
        user_data['new_module']['name'] = text
        # user_data['new_module']['need_name'] = False
    else:
        update.message.reply_text('Такой модуль уже существует. Введите другое имя')
        user_data['new_module']['step'] = 'ask_for_type'
        return 'ask_for_type'

    # Спрашиваем тип модуля
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
        user_data['new_module']['step'] = 'ask_for_language'
        return 'ask_for_language'
    except Exception as ex:
        traceback.print_exc()


def ask_for_language(bot, update, user_data):
    # Сохраняем выбранный тип
    user_data['new_module']['type'] = update.callback_query.data.split('|')[1]
    # Удаляем старое сообщение с клавиатурой
    user_data['last_message'] = None
    bot.delete_message(chat_id=update.callback_query.from_user.id,
                       message_id=update.callback_query.message.message_id)
    # Пишем пользователю, какой тип он выбрал
    bot.send_message(chat_id=update.callback_query.from_user.id,
                     text='Вы выбрали тип {}'.format(
                         modules_type_codes[update.callback_query.data.split('|')[1].lower()]))
    # Если тип - слово-определение, то язык и переводчик не нужны
    # Сразу переходим к вводу первой пары
    if user_data['new_module']['type'] == 'w_def':
        user_data['new_module']['language'] = ''
        user_data['new_module']['translation'] = False
        user_data['new_module']['step'] = get_term(bot, update, user_data)
        return user_data['new_module']['step']
    # Иначе запрашиваем у пользователя язык модуля
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
    user_data['new_module']['step'] = 'ask_about_translation'
    return 'ask_about_translation'


def ask_about_translation(bot, update, user_data):
    user_data['new_module']['language'] = update.callback_query.data.split('|')[1]
    if user_data['last_message']:
        # Удаляем старое сообщение с клавиатурой
        bot.delete_message(chat_id=update.effective_user.id,
                           message_id=user_data['last_message'].message_id)
        user_data['last_message'] = None

    # Спрашиваем пользователя, хотел бы он получать подсказки от переводчика
    keyboard = [[InlineKeyboardButton(text='Да', callback_data='set_translation|1')],
                [InlineKeyboardButton(text='Нет', callback_data='set_translation|')],
                ]
    keyboard = InlineKeyboardMarkup(keyboard)
    lang = update.callback_query.data.split('|')[1]
    # Уточняем пользователю возможности выбранного языка
    if lang == 'en-US' or lang == 'tr-TR' or lang == 'ru-RU':
        answer = 'Для этого языка доступно и аудио произношение и перевод. '
    else:
        answer = 'К сожалению для этого языкане доступно произношение, но доступен переводчик. '
    text = '{}Хотите ли вы, чтобы я предложил вам вариант перевода слова, которое вы вводите?'.format(answer)
    if user_data['new_module']['type'] == 'w_3' or user_data['new_module']['type'] == 'w_4':
        text += '\n!!!Если вы захотите воспользоваться подсказкой, вы должны будете обязательно ввести на одно слово ' \
                'меньше, а потом отдельно добавить ему перевод после подсказки'
    user_data['last_message'] = bot.send_message(update.effective_user.id,
                                                 text,
                                                 reply_markup=keyboard)
    user_data['new_module']['step'] = 'ask_first_word'
    return 'ask_first_word'


def ask_first_word(bot, update, user_data):
    print('Спрашиваю первое слово')
    try:
        if 'translation' not in user_data['new_module'].keys():
            # Если ответ не был введен раньше, берем его из нажатой кнопки
            user_data['new_module']['translation'] = bool(update.callback_query.data.split('|')[1])
    except:
        traceback.print_exc()

    if 'second' in user_data['new_module'].keys() and user_data['new_module']['second']:
        user_data['new_module']['sets'].append({'first': user_data['new_module']['first'],
                                                'second': user_data['new_module']['second']})
        user_data['new_module']['second'] = []
        user_data['new_module']['first'] = None
        print(user_data['new_module']['sets'])

    try:
        # Если слова еще ни разу не вводились, нашинаем ввод и объясняем пользователю, что он должен делать
        if 'sets' not in user_data['new_module'].keys() or not user_data['new_module']['sets']:
            user_data['new_module']['sets'] = []
            # Запрос пользователю меняется в зависимости от типа модуля
            if user_data['new_module']['type'] == 'w_t' or user_data['new_module']['type'] == 'w_t_e':
                text = 'Теперь введите первое слово на ИНОСТРАННОМ языке'
            elif user_data['new_module']['type'] == 'w_3' or user_data['new_module']['type'] == 'w_4':
                # Колличество слов изменяется в зависимости от того, есть подсказка или нет
                words = int(user_data['new_module']['type'][-1]) - int(user_data['new_module']['translation'])
                exc = ''
                if user_data['new_module']['type'] == 'w_3' and user_data['new_module']['translation']:
                    exc = 'man\nmen'
                elif user_data['new_module']['type'] == 'w_3' and not user_data['new_module']['translation']:
                    exc = 'man\nmen\nмужчина'
                elif user_data['new_module']['type'] == 'w_4' and user_data['new_module']['translation']:
                    exc = 'be\nwas\nbeen'
                elif user_data['new_module']['type'] == 'w_4' and not user_data['new_module']['translation']:
                    exc = 'be\nwas\nbeen\nбыть'

                # Пояснение пользователю, что именно нужно вводить
                if user_data['new_module']['translation']:
                    explanation = 'Теперь введите {} формы слова на иностранном языке,'.format(str(words))
                else:
                    explanation = 'Теперь введите {} формы слова на иностранном языке и перевод,'.format(str(words - 1))
                text = '{} разделяя их переносом строки (с компьютера - Shift + Enter)' \
                       '\nНапример:\n{}'.format(explanation, exc)

            bot.send_message(update.effective_user.id, text)
            keyboard = ReplyKeyboardMarkup([['🏠 Главное меню 🏠'], ['📥 Сохранить модуль']], one_time_keyboard=True)
            bot.send_message(update.effective_user.id,
                             'Как только закончите ввод слов, нажмите на кнопку "📥 Сохранить модуль"',
                             reply_markup=keyboard)
            if user_data['new_module']['translation']:
                user_data['new_module']['step'] = 'ask_second_word'
                return 'ask_second_word'
            else:
                user_data['new_module']['step'] = 'get_pair'
                return 'get_pair'

        else:
            print('я спрашиваю новое первое слово!!!')
            if user_data['new_module']['type'] == 'w_t' or user_data['new_module']['type'] == 'w_t_e':
                text = 'Введите слово на ИНОСТРАННОМ языке'
            elif user_data['new_module']['type'] == 'w_3' or user_data['new_module']['type'] == 'w_4':
                # Колличество слов изменяется в зависимости от того, есть подсказка или нет
                words = int(user_data['new_module']['type'][-1]) - int(user_data['new_module']['translation'])
                exc = ''
                if user_data['new_module']['type'] == 'w_3' and user_data['new_module']['translation']:
                    exc = 'man\nmen'
                elif user_data['new_module']['type'] == 'w_3' and not user_data['new_module']['translation']:
                    exc = 'man\nmen\nмужчина'
                elif user_data['new_module']['type'] == 'w_4' and user_data['new_module']['translation']:
                    exc = 'be\nwas\nbeen'
                elif user_data['new_module']['type'] == 'w_4' and not user_data['new_module']['translation']:
                    exc = 'be\nwas\nbeen\nбыть'

                # Пояснение пользователю, что именно нужно вводить
                if user_data['new_module']['translation']:
                    explanation = 'Введите {} формы слова на иностранном языке,'.format(str(words))
                else:
                    explanation = 'Введите {} формы слова на иностранном языке и перевод,'.format(str(words - 1))
                text = '{} разделяя их переносом строки (с компьютера - Shift + Enter)' \
                       '\nНапример:\n{}'.format(explanation, exc)
            bot.send_message(update.effective_user.id, text)
            if user_data['new_module']['translation']:
                user_data['new_module']['step'] = 'ask_second_word'
                return 'ask_second_word'
            else:
                user_data['new_module']['step'] = 'get_pair'
                return 'get_pair'
    except:
        traceback.print_exc()


def ask_second_word(bot, update, user_data):
    text = update.message.text
    if update.message.text == '📥 Сохранить модуль':
        return ask_about_finishing_adding(bot, update, user_data)
    w_t = not ((user_data['new_module']['type'] == 'w_t' or user_data['new_module']['type'] == 'w_t_e') and len(
        text.split('\n'))) == 1
    w_3_t = not (user_data['new_module']['type'] == 'w_3' and user_data['new_module']['translation'] and len(
        text.split('\n')) == 2)
    w_3_f = not (user_data['new_module']['type'] == 'w_3' and (not user_data['new_module']['translation']) and len(
        text.split('\n')) == 3)
    w_4_t = not (user_data['new_module']['type'] == 'w_4' and user_data['new_module']['translation'] and len(
        text.split('\n')) == 3)
    w_4_f = not (user_data['new_module']['type'] == 'w_4' and (not user_data['new_module']['translation']) and len(
        text.split('\n')) == 4)
    if not (w_t or w_3_t or w_3_f or w_4_f or w_4_t):
        bot.send_message(update.effective_user.id, 'Вы ввели что-то не то')
        user_data['new_module']['step'] = 'ask_first_word'
        return 'ask_first_word'

    user_data['new_module']['second'] = []

    user_data['new_module']['first'] = text
    if user_data['new_module']['translation']:
        user_data['new_module']['translation_options'] = translate(text.split('\n')[0],
                                                                   user_data['new_module']['language'].split('-')[
                                                                       0] + '-ru')
    else:
        user_data['new_module']['translation_options'] = []

    if user_data['new_module']['translation'] and not user_data['new_module']['translation_options']:
        text = 'К сожалению мы не нашли ни одного перевода этого слова с указанного языка. ' \
               'Введите свои варианты перевода (не более трех)'
        keyboard = InlineKeyboardMarkup(
            [[InlineKeyboardButton(text='⛔️Закончить⛔', callback_data='finish_translation')]])
        user_data['last_message'] = bot.send_message(update.effective_user.id, text, reply_markup=keyboard)
        user_data['new_module']['step'] = 'ask_translation'
        return 'ask_translation'
    elif not user_data['new_module']['translation']:
        text = 'Введите свой вариант перевода'
        keyboard = InlineKeyboardMarkup(
            [[InlineKeyboardButton(text='⛔️Закончить⛔', callback_data='finish_translation')]])
        bot.send_message(update.effective_user.id, text, reply_markup=keyboard)
        user_data['last_message'] = user_data['new_module']['step'] = 'ask_translation'
        return 'ask_translation'
    else:
        text = 'Выберите наиболее подходящие вам варианты перевода. Также можете прислать свои варианты ' \
               '(просто введите их). Вы можете выбрать до ТРЕХ вариантов перевода (или меньше), включая свои ' \
               'собственные. Выбрав один, нажмите на кнопку с другим переводом. Если вам достаточно менее трех ' \
               'переводов, нажмите кнопку "⛔️Закончить⛔️"'
        keyboard = [[InlineKeyboardButton(text=i, callback_data='add_translation|' + i)] for i in
                    user_data['new_module']['translation_options']]
        keyboard.append([InlineKeyboardButton(text='⛔️Закончить⛔', callback_data='finish_translation')])
        user_data['last_message'] = bot.send_message(update.effective_user.id, text,
                                                     reply_markup=InlineKeyboardMarkup(keyboard))
        user_data['new_module']['step'] = 'ask_translation'
        return 'ask_translation'


def ask_translation(bot, update, user_data):
    try:
        translation = update.message.text
        print(translation)
        if update.message.text == '📥 Сохранить модуль':
            return ask_about_finishing_adding(bot, update, user_data)
    except:
        translation = update.callback_query.data.split('|')[-1]
        if translation == 'finish_translation':
            bot.delete_message(chat_id=update.effective_user.id,
                               message_id=user_data['last_message'].message_id)
            user_data['last_message'] = None
            user_data['new_module']['step'] = ask_first_word(bot, update, user_data)
            return user_data['new_module']['step']
        else:
            bot.send_message(update.effective_user.id, translation)

    user_data['new_module']['second'].append(translation)

    if len(user_data['new_module']['second']) == 3:
        bot.send_message(update.effective_user.id, 'Вы ввели 3 варианта перевода. Больше нельзя')
        user_data['new_module']['step'] = ask_first_word(bot, update, user_data)
        return user_data['new_module']['step']
    else:
        user_data['new_module']['step'] = 'ask_translation'
        return 'ask_translation'


def ask_about_finishing_adding(bot, update, user_data):
    if update.message.text == '📥 Сохранить модуль':
        keyboard = [[InlineKeyboardButton(text='Завершить', callback_data='finish')],
                    [InlineKeyboardButton(text='Продолжить', callback_data='continue')]]
        text = 'Вы действительно хотите завершить?'
        if 'sets' not in user_data['new_module'].keys() or not user_data['new_module']['sets']:
            text += 'Вы не создали ни одной пары, модуль не будет сохранен'
        user_data['last_message'] = bot.send_message(update.effective_user.id, 'Вы действительно хотите завершить?',
                                                     reply_markup=InlineKeyboardMarkup(keyboard))
        return 'receive_answer_about_finishing_adding'
    else:
        bot.send_message(update.effective_user.id, 'Я вас не понимаю, но вы продолжайте '
                                                   'с того же места, где прервались')
        return user_data['new_module']['step']


def receive_answer_about_finishing_adding(bot, update, user_data):
    bot.delete_message(chat_id=update.effective_user.id,
                       message_id=user_data['last_message'].message_id)
    user_data['last_message'] = None
    if update.callback_query.data == 'finish':
        try:
            if user_data['new_module']['sets']:
                module = db_work.ModulesDB(user_id=update.effective_user.id,
                                           name=user_data['new_module']['name'],
                                           type=user_data['new_module']['type'],
                                           lang=user_data['new_module']['language'])
                db_work.db.session.add(module)
                db_work.db.session.commit()
                module_id = db_work.ModulesDB.query.filter_by(
                    name=user_data['new_module']['name']).first().module_id
                for s in user_data['new_module']['sets']:
                    words = s['first'].split('\n') + s['second']
                    new_set = db_work.WordsSets(module_id=module_id,
                                                word1=words[0].strip(),
                                                word2=words[1].strip(),
                                                word3='' if len(words) < 3 else words[2].strip(),
                                                word4='' if len(words) < 4 else words[3].strip(),
                                                image='')
                    db_work.db.session.add(new_set)
                db_work.db.session.commit()
                bot.send_message(update.effective_user.id, 'Модуль сохранен!')
            else:
                bot.send_message(update.effective_user.id, 'Так как модуль был пустым, он не был сохранен')
            return back_to_menu(bot, update, user_data)
        except Exception:
            traceback.print_exc()
            return back_to_menu(bot, update, user_data)
    elif update.callback_query.data == 'continue':
        bot.send_message(update.effective_user.id, 'Хорошо, продолжайте ровно там же, где и закончили')
        return user_data['new_module']['step']


def get_term(bot, update, user_data):
    pass


if __name__ == '__main__':
    main()
