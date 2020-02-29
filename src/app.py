import datetime
import logging
import os
import pprint
import traceback

from botmanlib.bot import BotmanBot
from botmanlib.updater import BotmanUpdater
from telegram import Message, Chat, TelegramError
from telegram.ext import MessageHandler, Filters, messagequeue, CallbackQueryHandler
from telegram.utils.request import Request

from src.jobs import start_check_blocked_job, stop_check_blocked_job
from src.menus.admin.admin import AdminMenu
from src.menus.start.start import StartMenu
from src.models import User, DBSession
from src.settings import MEDIA_FOLDER, RESOURCES_FOLDER, SETTINGS_FILE, WEBHOOK_PORT, WEBHOOK_IP, WEBHOOK_URL, WEBHOOK_ENABLE

logger = logging.getLogger(__name__)


def stop(update, context):
    # if user never have a conversation with bot and sending /stop he has empty user_data
    if context.user_data:
        _ = context.user_data['user'].translator
        user = DBSession.query(User).filter(User.chat_id == context.user_data['user'].chat_id).first()
        user.active = False
        user.chat_room_id = None
        DBSession.add(user)
        DBSession.commit()
        context.bot.send_message(chat_id=user.chat_id, text=_("You are deleted from this bot."))


def error(update, context):
    """Log Errors caused by Updates."""
    pp = pprint.PrettyPrinter(indent=4)
    logger.error(f'Update "{pp.pformat(update.to_dict())}" caused error \n{context.error}"')
    traceback.print_exc()


def goto_start(update, context):
    if update.effective_message and update.effective_message.message_id != 0:
        try:
            context.bot.delete_message(chat_id=update.effective_chat.id, message_id=update.effective_message.message_id)
        except TelegramError as e:
            logger.error(str(e))

    update.message = Message(0, update.effective_user, datetime.datetime.utcnow(), Chat(0, Chat.PRIVATE), text='/start', bot=context.bot)
    update._effective_message = None
    update.callback_query = None
    context.update_queue.put(update)


def main():
    bot_token = os.environ['bot.token']
    mqueue = messagequeue.MessageQueue(all_burst_limit=30, all_time_limit_ms=1000)
    request = Request(con_pool_size=8)

    bot = BotmanBot(token=bot_token, request=request, mqueue=mqueue)
    updater = BotmanUpdater(bot=bot, use_context=True, use_sessions=True)

    dispatcher = updater.dispatcher
    job_queue = updater.job_queue

    # Handlers
    start_menu = StartMenu(bot=bot, dispatcher=dispatcher)
    admin_menu = AdminMenu(bot=bot, dispatcher=dispatcher)
    stop_handler = MessageHandler(Filters.regex('^/stop$'), stop)

    # adding menus
    dispatcher.add_handler(stop_handler)
    dispatcher.add_handler(start_menu.handler)
    dispatcher.add_handler(admin_menu.handler)
    dispatcher.add_handler(MessageHandler(Filters.all, goto_start))
    dispatcher.add_handler(CallbackQueryHandler(goto_start))
    dispatcher.add_error_handler(error)

    # Start bot
    if not os.path.exists(MEDIA_FOLDER):
        os.mkdir(MEDIA_FOLDER)
        logger.info("Media folder created")
    if not os.path.exists(RESOURCES_FOLDER):
        os.mkdir(RESOURCES_FOLDER)
        logger.info("Resources folder created")
    if not os.path.exists(SETTINGS_FILE):
        with open(SETTINGS_FILE + ".default", 'r') as settings:
            out = open(SETTINGS_FILE, 'w')
            out.write(settings.read())
            out.close()
        logger.info("Settings file created")

    if WEBHOOK_ENABLE:
        update_queue = updater.start_webhook(listen=WEBHOOK_IP, port=WEBHOOK_PORT, allowed_updates=['message', 'edited_message', 'callback_query'])
        updater.bot.set_webhook(url=WEBHOOK_URL)
    else:
        update_queue = updater.start_polling(allowed_updates=['message', 'edited_message', 'callback_query'])

    start_check_blocked_job(job_queue)

    logger.info("Bot started")
    updater.idle()

    bot.stop()
    stop_check_blocked_job(job_queue)


if __name__ == "__main__":
    main()
