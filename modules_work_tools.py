import db_work
from telegram import InlineKeyboardButton, InlineKeyboardMarkup


def share_mod(bot, update, user_data):
    pass


def start_edit_mod(bot, update, user_data):
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
    keyboard = []
    for i in sets:
        words = i.word1 + ' = ' + i.word2
        words += (' = ' + i.word3) if i.word3 else ''
        words += (' = ' + i.word4) if i.word4 else ''
        keyboard.append([InlineKeyboardButton(text=words, callback_data='edit_set|' + str(i.set_id))])
    keyboard.append([InlineKeyboardButton(text='Назад', callback_data='edit_mod')])
    keyboard = InlineKeyboardMarkup(keyboard)
    text = 'Выберите пару, которую хотите редактировать:'
    user_data['last_message'] = bot.edit_message_text(text, update.effective_user.id,
                                                      user_data['last_message'].message_id,
                                                      reply_markup=keyboard)


def edit_set(bot, update, user_data, set_id):
    set = db_work.WordsSets.query.filter_by(set_id=set_id).first()
    db_work.db.session.delete(set)
    print('success')


def edit_mod_page_forward(bot, update, user_data, type, page, module_id=None):
    print(page)
    if type == 'modules':
        data = sorted(db_work.ModulesDB.query.filter_by(user_id=update.effective_user.id).all(),
                      key=lambda x: x.module_id,
                      reverse=True)
        t = 'modules|'
        id = ''
    else:
        data = db_work.WordsSets.query.filter_by(module_id=module_id).all()
        t = 'modules|'
        id = '|' + str(module_id)
    keyboard = []
    if len(data) - int(str(page)) <= 10:
        for i in data[int(str(page)):]:
            button = [InlineKeyboardButton(text=i.name, callback_data='choose_edit_set|' + str(i.module_id))]
            keyboard.append(button)
        button = [InlineKeyboardButton(text='<-', callback_data='edit_mod_page_back|' + t + str(page) + id)]
        keyboard.append(button)
    else:
        for i in data[int(str(page)):int(str(page)) + 10]:
            button = [InlineKeyboardButton(text=i.name, callback_data='choose_edit_set|' + str(i.module_id))]
            keyboard.append(button)
        button = [InlineKeyboardButton(text='<-', callback_data='edit_mod_page_back|' + t + str(page) + id),
                  InlineKeyboardButton(text='->',
                                       callback_data='edit_mod_page_forward|' + t + str(int(str(page)) + 10) + id)]
        keyboard.append(button)
    keyboard.append([InlineKeyboardButton(text='Назад', callback_data='modules_work')])
    keyboard = InlineKeyboardMarkup(keyboard)
    user_data['last_message'] = bot.edit_message_reply_markup(chat_id=update.effective_user.id,
                                                              message_id=user_data['last_message'].message_id,
                                                              reply_markup=keyboard)


def edit_mod_page_back(bot, update, user_data, type, page, module_id=None):
    print(page)
    if type == 'modules':
        data = sorted(db_work.ModulesDB.query.filter_by(user_id=update.effective_user.id).all(),
                      key=lambda x: x.module_id,
                      reverse=True)
        t = 'modules|'
        id = ''
    else:
        data = db_work.WordsSets.query.filter_by(module_id=module_id).all()
        t = 'modules|'
        id = '|' + str(module_id)
    keyboard = []
    for i in data[int(page) - 10:int(page)]:
        button = [InlineKeyboardButton(text=i.name, callback_data='choose_edit_set|' + str(i.module_id))]
        keyboard.append(button)
    button = []
    if int(page) != 10:
        button = [InlineKeyboardButton(text='<-',
                                       callback_data='edit_mod_page_back|' + t + str(int(str(page)) - 10) + id)]
    button.append(
        InlineKeyboardButton(text='->', callback_data='edit_mod_page_forward|' + t + str(page) + id))
    keyboard.append(button)
    keyboard.append([InlineKeyboardButton(text='Назад', callback_data='modules_work')])
    keyboard = InlineKeyboardMarkup(keyboard)
    user_data['last_message'] = bot.edit_message_reply_markup(chat_id=update.effective_user.id,
                                                              message_id=user_data['last_message'].message_id,
                                                              reply_markup=keyboard)
