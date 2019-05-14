import db_work
from telegram import InlineKeyboardButton, InlineKeyboardMarkup
import main
import pyqrcode
import os


def start_share_mod(bot, update, user_data):
    user_data['edit'] = {}
    user_data['edit']['adding_pair'] = False
    user_data['edit']['edit_mod'] = {}
    user_data['edit']['edit_mod']['set_id'] = None
    user_data['edit']['edit_mod']['mod'] = None

    modules = sorted(db_work.ModulesDB.query.filter_by(user_id=update.effective_user.id).all(),
                     key=lambda x: x.module_id,
                     reverse=True)
    keyboard = []
    if not modules:
        bot.edit_message_text('Вы еще не добавили ни одного модуля',
                              update.effective_user.id,
                              user_data['last_message'].message_id)
        user_data['last_message'] = False
        return
    if len(modules) <= 10:
        for i in modules:
            keyboard.append([InlineKeyboardButton(text=i.name, callback_data='share_module|' + str(i.module_id))])
    else:
        for i in modules[:10]:
            keyboard.append([InlineKeyboardButton(text=i.name, callback_data='share_module|' + str(i.module_id))])
        keyboard.append([InlineKeyboardButton(text='->', callback_data='edit_mod_page_forward|module_share|10')])
    keyboard.append([InlineKeyboardButton(text='Назад', callback_data='modules_work')])
    keyboard = InlineKeyboardMarkup(keyboard)
    text = 'Выберите модуль, которым хотите поделиться:'
    if 'last_message' in user_data.keys() and user_data['last_message']:
        user_data['last_message'] = bot.edit_message_text(text, update.effective_user.id,
                                                          user_data['last_message'].message_id,
                                                          reply_markup=keyboard)
    else:
        user_data['last_message'] = bot.send_message(update.effective_user.id,
                                                     text,
                                                     reply_markup=keyboard)


def share_module(bot, update, user_data, module_id):
    url = pyqrcode.create('t.me/word_for_world_bot?start=' + str(module_id))
    url.png('code.png', scale=7)
    if user_data['last_message']:
        bot.delete_message(update.effective_user.id, user_data['last_message'].message_id)
    text = 'Вот код, который вы можете отправить или показать кому-то, чтобы тот отсканировал его'
    bot.send_photo(chat_id=update.effective_user.id,
                   photo=open('code.png', mode='rb'),
                   caption=text)
    user_data['last_message'] = None
    os.remove('code.png')
    main.back_to_menu(bot, update, user_data)


def start_edit_mod(bot, update, user_data):
    user_data['edit'] = {}
    user_data['edit']['adding_pair'] = False
    user_data['edit']['edit_mod'] = {}
    user_data['edit']['edit_mod']['set_id'] = None
    user_data['edit']['edit_mod']['mod'] = None

    modules = sorted(db_work.ModulesDB.query.filter_by(user_id=update.effective_user.id).all(),
                     key=lambda x: x.module_id,
                     reverse=True)
    keyboard = []
    if not modules:
        bot.send_message(update.effective_user.id,
                         'Вы еще не добавили ни одного модуля, нечего редактировать')
        user_data['last_message'] = False
        return
    if len(modules) <= 10:
        for i in modules:
            keyboard.append([InlineKeyboardButton(text=i.name, callback_data='choose_edit_set|' + str(i.module_id))])
    else:
        for i in modules[:10]:
            keyboard.append([InlineKeyboardButton(text=i.name, callback_data='choose_edit_set|' + str(i.module_id))])
        keyboard.append([InlineKeyboardButton(text='->', callback_data='edit_mod_page_forward|modules|10')])
    keyboard.append([InlineKeyboardButton(text='Назад', callback_data='modules_work')])
    keyboard = InlineKeyboardMarkup(keyboard)
    text = 'Выберите модуль, который хотите редактировать:'
    if 'last_message' in user_data.keys() and user_data['last_message']:
        user_data['last_message'] = bot.edit_message_text(text, update.effective_user.id,
                                                          user_data['last_message'].message_id,
                                                          reply_markup=keyboard)
    else:
        user_data['last_message'] = bot.send_message(update.effective_user.id,
                                                     text,
                                                     reply_markup=keyboard)


def choose_edit_set(bot, update, user_data, module_id):
    sets = db_work.WordsSets.query.filter_by(module_id=module_id).all()
    keyboard = list()
    keyboard.append([InlineKeyboardButton(text='➕Добавить новую пару', callback_data='add_pair|' + str(module_id))])
    for i in sets if len(sets) <= 10 else sets[:10]:
        words = i.word1 + ' = ' + i.word2
        words += (' = ' + i.word3) if i.word3 else ''
        words += (' = ' + i.word4) if i.word4 else ''
        keyboard.append([InlineKeyboardButton(text=words, callback_data='choose_edit_action|' + str(i.set_id))])
    if len(sets) > 10:
        keyboard.append(
            [InlineKeyboardButton(text='->', callback_data='edit_mod_page_forward|sets|10|' + str(module_id))])
    keyboard.append([InlineKeyboardButton(text='Назад', callback_data='edit_mod')])
    keyboard = InlineKeyboardMarkup(keyboard)
    text = 'Выберите пару, которую хотите редактироватьили добавьте новую:'
    if user_data['last_message']:
        user_data['last_message'] = bot.edit_message_text(text, update.effective_user.id,
                                                          user_data['last_message'].message_id,
                                                          reply_markup=keyboard)
    else:
        user_data['last_message'] = bot.send_message(update.effective_user.id, text, reply_markup=keyboard)


def choose_edit_action(bot, update, user_data, set_id):
    set = db_work.WordsSets.query.filter_by(set_id=set_id).first()
    keyboard = [[InlineKeyboardButton(text='Изменить слова', callback_data='edit_action|words|' + str(set_id))]]
    if set.image:
        keyboard.append(
            [InlineKeyboardButton(text='Изменить картинку', callback_data='edit_action|image|' + str(set_id))])
    else:
        keyboard.append(
            [InlineKeyboardButton(text='Добавить картинку', callback_data='edit_action|image|' + str(set_id))])
    keyboard.append([InlineKeyboardButton(text='Удалить пару', callback_data='edit_action|ask_del|' + str(set_id))])
    keyboard.append([InlineKeyboardButton(text='Отмена', callback_data='cancel_editing_module')])
    keyboard = InlineKeyboardMarkup(keyboard)
    text = 'Выберите действие'
    if user_data['last_message']:
        user_data['last_message'] = bot.edit_message_text(text, update.effective_user.id,
                                                          user_data['last_message'].message_id,
                                                          reply_markup=keyboard)
    else:
        user_data['last_message'] = bot.send_message(update.effective_user.id, text, reply_markup=keyboard)


def add_pair(bot, update, user_data, module_id):
    user_data['edit']['adding_pair'] = module_id
    keyboard = InlineKeyboardMarkup([[InlineKeyboardButton(text='Отменить', callback_data='cancel_editing_module')]])
    user_data['last_message'] = bot.edit_message_text('Введите новую пару в нужном формате или отмените действие',
                                                      update.effective_user.id,
                                                      user_data['last_message'].message_id,
                                                      reply_markup=keyboard)


def edit_words(bot, update, user_data, set_id):
    user_data['edit']['edit_mod']['mod'] = 'words'
    user_data['edit']['edit_mod']['set_id'] = set_id
    keyboard = InlineKeyboardMarkup(
        [[InlineKeyboardButton(text='Отмена', callback_data='cancel_editing_module')]])
    if user_data['last_message']:
        user_data['last_message'] = None
        bot.edit_message_text('Введите новые слова для пары в верном формате',
                              update.effective_user.id,
                              user_data['last_message'].message_id,
                              reply_markup=keyboard)
    else:
        user_data['last_message'] = None
        bot.send_message(update.effective_user.id,
                         'Введите новые слова для пары в верном формате',
                         reply_markup=keyboard)


def edit_image(bot, update, user_data, set_id):
    user_data['edit']['edit_mod']['mod'] = 'image'
    user_data['edit']['edit_mod']['set_id'] = set_id
    keyboard = InlineKeyboardMarkup(
        [[InlineKeyboardButton(text='Отмена', callback_data='cancel_editing_module')]])
    if user_data['last_message']:
        bot.edit_message_text('Отправьте картинку без подписи',
                              update.effective_user.id,
                              user_data['last_message'].message_id,
                              reply_markup=keyboard)
        user_data['last_message'] = None
    else:
        bot.send_message(update.effective_user.id,
                         'Отправьте картинку без подписи',
                         reply_markup=keyboard)


def delete_set(bot, update, user_data, set_id, delete):
    if delete:
        set = db_work.WordsSets.query.filter_by(set_id=set_id).first()
        db_work.db.session.delete(set)
        bot.edit_message_text('Удалено',
                              update.effective_user.id,
                              user_data['last_message'].message_id)
        user_data['last_message'] = None
        choose_edit_set(bot, update, user_data, set.module_id)
    else:
        keyboard = [[InlineKeyboardButton(text='Да', callback_data='edit_action|del|' + str(set_id))],
                    [InlineKeyboardButton(text='Отмена', callback_data='cancel_editing_module')]]
        keyboard = InlineKeyboardMarkup(keyboard)
        if user_data['last_message']:
            user_data['last_message'] = bot.edit_message_text('Вы действительно хотите удалить эту пару?',
                                                              update.effective_user.id,
                                                              user_data['last_message'].message_id,
                                                              reply_markup=keyboard)
        else:
            user_data['last_message'] = bot.send_message(update.effective_user.id,
                                                         'Вы действительно хотите удалить эту пару?',
                                                         reply_markup=keyboard)


def edit_mod_page_forward(bot, update, user_data, type, page, module_id=None):
    keyboard = list()
    if type == 'modules':
        data = sorted(db_work.ModulesDB.query.filter_by(user_id=update.effective_user.id).all(),
                      key=lambda x: x.module_id,
                      reverse=True)
        func = 'choose_edit_set|'
        id_ = ''
    elif type == 'module_del':
        data = sorted(db_work.ModulesDB.query.filter_by(user_id=update.effective_user.id).all(),
                      key=lambda x: x.module_id,
                      reverse=True)
        func = 'delete_module|'
        id_ = ''
    elif type == 'module_share':
        data = sorted(db_work.ModulesDB.query.filter_by(user_id=update.effective_user.id).all(),
                      key=lambda x: x.module_id,
                      reverse=True)
        func = 'share_module|'
        id_ = ''
    else:
        data = db_work.WordsSets.query.filter_by(module_id=module_id).all()
        func = 'choose_edit_action|'
        id_ = '|' + str(module_id)
        keyboard.append([InlineKeyboardButton(text='➕Добавить новую пару', callback_data='add_pair|' + str(module_id))])
    t = type + '|'
    if len(data) - int(str(page)) <= 10:
        for i in data[int(str(page)):]:
            button = [InlineKeyboardButton(text=get_name(i), callback_data=func + str(get_id(i)))]
            keyboard.append(button)
        button = [InlineKeyboardButton(text='<-', callback_data='edit_mod_page_back|' + t + str(page) + id_)]
        keyboard.append(button)
    else:
        for i in data[int(str(page)):int(str(page)) + 10]:
            button = [InlineKeyboardButton(text=get_name(i), callback_data=func + str(get_id(i)))]
            keyboard.append(button)
        button = [InlineKeyboardButton(text='<-', callback_data='edit_mod_page_back|' + t + str(page) + id_),
                  InlineKeyboardButton(text='->',
                                       callback_data='edit_mod_page_forward|' + t + str(int(str(page)) + 10) + id_)]
        keyboard.append(button)
    keyboard.append(
        [InlineKeyboardButton(text='Назад', callback_data='modules_work' if type == 'modules' else 'edit_mod')])
    keyboard = InlineKeyboardMarkup(keyboard)
    user_data['last_message'] = bot.edit_message_reply_markup(chat_id=update.effective_user.id,
                                                              message_id=user_data['last_message'].message_id,
                                                              reply_markup=keyboard)


def edit_mod_page_back(bot, update, user_data, type, page, module_id=None):
    keyboard = list()
    if type == 'modules':
        data = sorted(db_work.ModulesDB.query.filter_by(user_id=update.effective_user.id).all(),
                      key=lambda x: x.module_id,
                      reverse=True)
        func = 'choose_edit_set|'
        id_ = ''
    elif type == 'module_del':
        data = sorted(db_work.ModulesDB.query.filter_by(user_id=update.effective_user.id).all(),
                      key=lambda x: x.module_id,
                      reverse=True)
        func = 'delete_module|'
        id_ = ''
    elif type == 'module_share':
        data = sorted(db_work.ModulesDB.query.filter_by(user_id=update.effective_user.id).all(),
                      key=lambda x: x.module_id,
                      reverse=True)
        func = 'share_module|'
        id_ = ''
    else:
        data = db_work.WordsSets.query.filter_by(module_id=module_id).all()
        func = 'choose_edit_action|'
        id_ = '|' + str(module_id)
        keyboard.append([InlineKeyboardButton(text='➕Добавить новую пару', callback_data='add_pair|' + str(module_id))])
    t = type + '|'
    for i in data[int(page) - 10:int(page)]:
        button = [InlineKeyboardButton(text=get_name(i), callback_data=func + str(get_id(i)))]
        keyboard.append(button)
    button = []
    if int(page) != 10:
        button = [InlineKeyboardButton(text='<-',
                                       callback_data='edit_mod_page_back|' + t + str(int(str(page)) - 10) + id_)]
    button.append(
        InlineKeyboardButton(text='->', callback_data='edit_mod_page_forward|' + t + str(page) + id_))
    keyboard.append(button)
    keyboard.append(
        [InlineKeyboardButton(text='Назад', callback_data='modules_work' if type == 'modules' else 'edit_mod')])
    keyboard = InlineKeyboardMarkup(keyboard)
    user_data['last_message'] = bot.edit_message_reply_markup(chat_id=update.effective_user.id,
                                                              message_id=user_data['last_message'].message_id,
                                                              reply_markup=keyboard)


def get_name(obj):
    try:
        name = obj.name
        return name
    except Exception:
        words = obj.word1 + ' = ' + obj.word2
        words += (' = ' + obj.word3) if obj.word3 else ''
        words += (' = ' + obj.word4) if obj.word4 else ''
        return words


def get_id(obj):
    try:
        i = obj.set_id
        return i
    except Exception:
        i = obj.module_id
        return i


def start_del_mod(bot, update, user_data):
    user_data['edit'] = {}
    user_data['edit']['adding_pair'] = False
    user_data['edit']['edit_mod'] = {}
    user_data['edit']['edit_mod']['set_id'] = None
    user_data['edit']['edit_mod']['mod'] = None

    modules = sorted(db_work.ModulesDB.query.filter_by(user_id=update.effective_user.id).all(),
                     key=lambda x: x.module_id,
                     reverse=True)
    keyboard = []
    if not modules:
        bot.edit_message_text('Вы еще не добавили ни одного модуля, нечего удалять',
                              update.effective_user.id,
                              user_data['last_message'].message_id)
        user_data['last_message'] = False
        return
    if len(modules) <= 10:
        for i in modules:
            keyboard.append([InlineKeyboardButton(text=i.name, callback_data='delete_module|' + str(i.module_id))])
    else:
        for i in modules[:10]:
            keyboard.append([InlineKeyboardButton(text=i.name, callback_data='delete_module|' + str(i.module_id))])
        keyboard.append([InlineKeyboardButton(text='->', callback_data='edit_mod_page_forward|modules_del|10')])
    keyboard.append([InlineKeyboardButton(text='Назад', callback_data='modules_work')])
    keyboard = InlineKeyboardMarkup(keyboard)
    text = 'Выберите модуль, который хотите удалить:'
    if 'last_message' in user_data.keys() and user_data['last_message']:
        user_data['last_message'] = bot.edit_message_text(text, update.effective_user.id,
                                                          user_data['last_message'].message_id,
                                                          reply_markup=keyboard)
    else:
        user_data['last_message'] = bot.send_message(update.effective_user.id,
                                                     text,
                                                     reply_markup=keyboard)


def delete_module(bot, update, user_data, module_id, mod):
    if mod:
        module = db_work.ModulesDB.query.filter_by(module_id=module_id).first()
        db_work.db.session.delete(module)
        db_work.db.session.commit()
        sets = db_work.WordsSets.query.filter_by(module_id=module_id).all()
        for s in sets:
            is_image_used = db_work.WordsSets.query.filter_by(image=s.image).all()
            if len(is_image_used) == 1:
                os.remove('user_data/images/' + s.image)
            db_work.db.session.delete(set)
        bot.edit_message_text('Модуль удален, моете продолжать работу',
                              update.effective_user.id, user_data['last_message'].message_id)
        user_data['last_message'] = None
        main.modules_work_menu(bot, update, user_data)
    else:
        keyboard = [[InlineKeyboardButton(text='Да', callback_data='delete_module|{}|del'.format(str(module_id)))],
                    [InlineKeyboardButton(text='Отмена', callback_data='cancel_editing_module')]]
        keyboard = InlineKeyboardMarkup(keyboard)
        if user_data['last_message']:
            user_data['last_message'] = bot.edit_message_text('Вы действительно хотите удалить этот модуль?',
                                                              update.effective_user.id,
                                                              user_data['last_message'].message_id,
                                                              reply_markup=keyboard)
        else:
            user_data['last_message'] = bot.send_message(update.effective_user.id,
                                                         'Вы действительно хотите удалить этот модуль?',
                                                         reply_markup=keyboard)


def copy_module(bot, update, module):
    new_module = db_work.ModulesDB(user_id=update.effective_user.id,
                                   name=module.name,
                                   type=module.type)
    db_work.db.session.add(new_module)
    db_work.db.session.commit()
    module_id = db_work.ModulesDB.query.filter_by(user_id=update.effective_user.id,
                                                  name=module.name).first().module_id
    sets = db_work.WordsSets.query.filter_by(module_id=module_id).all()
    for s in sets:
        new_set = db_work.WordsSets(module_id=module_id,
                                    word1=s.word1,
                                    word2=s.word2,
                                    word3=s.word3,
                                    word4=s.word4,
                                    image=s.image)
        db_work.db.session.add(new_set)
    db_work.db.session.commit()
