from telegram.ext import Updater, MessageHandler, Filters, CallbackContext
from telegram.ext import CallbackContext, CommandHandler, CallbackQueryHandler
from telegram.ext.dispatcher import run_async
from telegram import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardRemove, Document
from io import BytesIO
from mega import Mega
from consts import *
import logging
import random
import os

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.INFO)
logger = logging.getLogger(__name__)

def get_callback(type, obj):
    return "{'type':" + f"'{type}'" + ", 'id':" + f"{obj['id']}" + "}"

def error(update, context):
    logger.warning('Update "%s" caused error "%s"', update, context.error)

@run_async
def add_photo(update, context):
    if update.message.from_user['username'] in enabled_users:
        photos = update.message.photo
        photo_file = photos[-1].get_file()
        filename = f'meme_' + photo_file.file_path.split('/')[-1]
        photo_file.download(filename)
        mega = Mega()
        m = mega.login(mega_email, mega_password)
        folder = m.find('memes')
        m.upload(filename, folder[0])
        os.remove(filename)
        update.message.reply_text('Мем загружен.')
    else:
        update.message.reply_text('Ты не можешь пользоваться этим ботом!')

@run_async
def start(update, context):
    if update.message.from_user['username'] in enabled_users:
        update.message.reply_text('Пришли мне мем!')
    else:
        update.message.reply_text('Ты не можешь пользоваться этим ботом!')

def main():
    updater = Updater(TOKEN, use_context=True)
    updater.start_webhook(listen='0.0.0.0', port=PORT, url_path=TOKEN)
    updater.bot.set_webhook('https://iosif-telegram.herokuapp.com/' + TOKEN)
    dp = updater.dispatcher
    dp.add_handler(MessageHandler(Filters.photo, add_photo))
    dp.add_handler(CommandHandler('start', start))
    updater.start_polling()

    updater.idle()


if __name__ == '__main__':
    main()