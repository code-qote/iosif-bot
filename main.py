from requests import post
from telegram.ext import Updater, MessageHandler, Filters, CallbackContext
from telegram.ext import CallbackContext, CommandHandler, CallbackQueryHandler, ConversationHandler
from telegram.ext.dispatcher import run_async
from telegram import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardRemove, Document
from io import BytesIO
from consts import *
import logging
import os

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.INFO)
logger = logging.getLogger(__name__)

def get_callback(type, obj):
    return "{'type':" + f"'{type}'" + ", 'id':" + f"{obj['id']}" + "}"

def error(update, context):
    logger.warning('Update "%s" caused error "%s"', update, context.error)

def send(message):
    json = {'token': MESSAGE_API_TOKEN, 'message': message}
    if post('https://iosif.herokuapp.com/send_message', json=json).status_code == 200:
        return True
    return False

def message_start(update, context):
    if update.message.from_user['username'] in enabled_users:   
        update.message.reply_text('Отправьте мне текст сообщения')
    return 1

def message_receive(update, context):
    if send(update.message.text):
        update.message.reply_text('Отправлено')
    else:
        update.message.reply_text('Произошла ошибка')
    return ConversationHandler.END

def start(update, context):
    if update.message.from_user['username'] in enabled_users:
        update.message.reply_text('Я отправлю ваше сообщение всем')
    else:
        update.message.reply_text('Ты не можешь пользоваться этим ботом!')

def cancel(update, context):
    update.message.reply_text('Ок, передумали получается')
    return ConversationHandler.END

def main():
    PORT = int(os.environ.get('PORT', 88))
    updater = Updater(TOKEN, use_context=True)
    updater.start_webhook(listen="0.0.0.0",
                          port=PORT,
                          url_path=TOKEN)
    updater.bot.set_webhook('https://iosif-telegram.herokuapp.com/' + TOKEN)
    dp = updater.dispatcher
    conv = ConversationHandler(
        entry_points=[CommandHandler('message', message_start)],
        states = {1: [MessageHandler(Filters.text & ~Filters.command, message_receive)]},
        fallbacks=[CommandHandler('cancel', cancel)]
    )

    dp.add_handler(CommandHandler('start', start))
    dp.add_handler(conv)
    updater.start_polling()

    updater.idle()


if __name__ == '__main__':
    main()
