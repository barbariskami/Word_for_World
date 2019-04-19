from telegram.ext import Updater, MessageHandler, Filters, CommandHandler, CallbackQueryHandler, ConversationHandler
from telegram import ReplyKeyboardMarkup, ReplyKeyboardRemove, InlineKeyboardMarkup, InlineKeyboardButton
import infoDetails
import json


# import db_work


def main():
    token = '812410140:AAECjhbi19Q43rDt654K1El3wxaQXYuMmTo'
    updater = Updater(token)
    dp = updater.dispatcher

    dp.add_handler(CommandHandler('start', start))
    dp.add_handler(CommandHandler('info', info, pass_user_data=True))
    dp.add_handler(CommandHandler('menu', back_to_menu))
    dp.add_handler(CommandHandler('add_module', start_adding, pass_user_data=True))
    dp.add_handler(CallbackQueryHandler(inline_q_handler, pass_user_data=True))

    updater.start_polling()

    updater.idle()


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
            bot.edit_message_text(text, update.effective_user.id, user_data['info_message'].message_id, reply_markup=keyboard)
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
    try:
        bot.send_message(update.effective_user.id, text, reply_markup=keyboard)
        user_data['info_message'] = False
    except Exception as e:
        print(e, type(e))


def start(bot, update):
    text = open('texts/start.txt', mode='r', encoding='utf8').read()

    button1 = InlineKeyboardButton(text='Информация', callback_data='main_info')
    button2 = InlineKeyboardButton(text='Добавить модуль', callback_data='add_mod|1|2|3')
    button3 = InlineKeyboardButton(text='Тренироваться', callback_data='train')
    keyboard = InlineKeyboardMarkup([[button1],
                                     [button2],
                                     [button3]])
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
        for i in args:
            print(i)

    def train(*args):
        pass

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

    method, *payload = update.callback_query.data.split('|')
    try:
        text = locals().get(method, lambda d: None)(*payload)
        bot.answer_callback_query(update.callback_query.id, text=text)
    except Exception as ex:
        print(666, ex, type(ex))
        bot.sendMessage(125562178, text='hey')


def start_adding(bot, update, user_data):
    text = 'Введите название будующего модуля'
    bot.send_message(update.effective_user.id, text)


if __name__ == '__main__':
    main()
