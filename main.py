from telegram.ext import Updater, MessageHandler, Filters, CommandHandler
from telegram import ReplyKeyboardMarkup, ReplyKeyboardRemove
import json


def main():
    token = '812410140:AAECjhbi19Q43rDt654K1El3wxaQXYuMmTo'
    updater = Updater(token)
    dp = updater.dispatcher

    dp.add_handler(CommandHandler('start', start))
    dp.add_handler(CommandHandler('info', info))
    dp.add_handler(CommandHandler('menu', back_to_menu))

    updater.start_polling()

    updater.idle()


def info(bot, update):
    text = open('texts/info.txt', mode='r', encoding='utf8').read()
    reply_keyboard = [['/menu Вернуться на главную']
                      ]
    markup = ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=True)
    update.message.reply_text(text,
                              reply_markup=markup)


def back_to_menu(bot, update):
    text = '''/train - тренироваться
/add_module - Добавить новый учебный модуль
/info - информация и инструкция к пользованию'''
    reply_keyboard = [['/train'],
                      ['/add_module'],
                      ['/info']]
    markup = ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=True)
    update.message.reply_text(text,
                              reply_markup=markup)


def start(bot, update):
    text = open('texts/start.txt', mode='r', encoding='utf8').read()
    reply_keyboard = [['/train'],
                      ['/add_module'],
                      ['/info']]
    markup = ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=True)
    update.message.reply_text(text,
                              reply_markup=markup)


if __name__ == '__main__':
    main()
