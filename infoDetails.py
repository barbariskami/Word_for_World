from telegram import InlineKeyboardMarkup, InlineKeyboardButton

text = open('texts/small_info.txt').read().split('\n~\n')


def w_t_info(bot, update, user_data):
    keyboard = InlineKeyboardMarkup([[InlineKeyboardButton(text='Назад', callback_data='main_info')],
                                     [InlineKeyboardButton(text='Главное меню', callback_data='back_to_main')]
                                     ])
    bot.edit_message_text(text[0], update.effective_user.id, user_data['last_message'].message_id,
                          reply_markup=keyboard)


def w_def_info(bot, update, user_data):
    keyboard = InlineKeyboardMarkup([[InlineKeyboardButton(text='Назад', callback_data='main_info')],
                                     [InlineKeyboardButton(text='Главное меню', callback_data='back_to_main')]
                                     ])
    bot.edit_message_text(text[1], update.effective_user.id, user_data['last_message'].message_id,
                          reply_markup=keyboard)


def w34_info(bot, update, user_data):
    keyboard = InlineKeyboardMarkup([[InlineKeyboardButton(text='Назад', callback_data='main_info')],
                                     [InlineKeyboardButton(text='Главное меню', callback_data='back_to_main')]
                                     ])
    bot.edit_message_text(text[2], update.effective_user.id, user_data['last_message'].message_id,
                          reply_markup=keyboard)


def w_t_e_info(bot, update, user_data):
    keyboard = InlineKeyboardMarkup([[InlineKeyboardButton(text='Назад', callback_data='main_info')],
                                     [InlineKeyboardButton(text='Главное меню', callback_data='back_to_main')]
                                     ])
    bot.edit_message_text(text[3], update.effective_user.id, user_data['last_message'].message_id,
                          reply_markup=keyboard)


def add_info(bot, update, user_data):
    keyboard = InlineKeyboardMarkup([[InlineKeyboardButton(text='Назад', callback_data='main_info')],
                                     [InlineKeyboardButton(text='Главное меню', callback_data='back_to_main')]
                                     ])
    bot.edit_message_text(text[4], update.effective_user.id, user_data['last_message'].message_id,
                          reply_markup=keyboard)


def train_info(bot, update, user_data):
    keyboard = InlineKeyboardMarkup([[InlineKeyboardButton(text='Назад', callback_data='main_info')],
                                     [InlineKeyboardButton(text='Главное меню', callback_data='back_to_main')]
                                     ])
    bot.edit_message_text(text[5], update.effective_user.id, user_data['last_message'].message_id,
                          reply_markup=keyboard)


def edit_info(bot, update, user_data):
    keyboard = InlineKeyboardMarkup([[InlineKeyboardButton(text='Назад', callback_data='main_info')],
                                     [InlineKeyboardButton(text='Главное меню', callback_data='back_to_main')]
                                     ])
    bot.edit_message_text(text[6], update.effective_user.id, user_data['last_message'].message_id,
                          reply_markup=keyboard)
