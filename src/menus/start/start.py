import enum

from botmanlib.menus.basemenu import BaseMenu
from botmanlib.menus.helpers import add_to_db, prepare_user, require_permission
from botmanlib.messages import send_or_edit, delete_interface, delete_user_message
from telegram import TelegramError, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ConversationHandler, CallbackQueryHandler, Filters, MessageHandler, PrefixHandler

from src.models import User


class StartMenu(BaseMenu):
    menu_name = 'start_menu'

    class States(enum.Enum):
        ACTION = 1
        LANGUAGE = 2

    def entry(self, update, context):
        user = prepare_user(User, update, context)

        _ = user.translator

        if self.menu_name not in context.user_data:
            context.user_data[self.menu_name] = {}

        if update.effective_message and update.effective_message.text and update.effective_message.text.startswith("/"):
            delete_interface(context)

        if update.callback_query and update.callback_query.data == 'start':
            update.callback_query.answer()
            try:
                update.effective_message.edit_reply_markup()
            except (TelegramError, AttributeError):
                pass

        self.send_message(context)
        return self.States.ACTION

    def send_message(self, context):
        user = context.user_data['user']
        _ = user.translator
        message_text = _("Select action")

        buttons = [[InlineKeyboardButton(_("Create order"), callback_data='make_order'),
                        InlineKeyboardButton(_("My orders"), callback_data='my_orders')],
                       [InlineKeyboardButton(_("Profile"), callback_data='profile'),
                        InlineKeyboardButton(_("Change language"), callback_data='language')]]

        send_or_edit(context, chat_id=user.chat_id, text=message_text, reply_markup=InlineKeyboardMarkup(buttons))
        return self.States.ACTION

    def ask_language(self, update, context):
        user = context.user_data['user']
        _ = user.translator

        buttons = [[InlineKeyboardButton("Українська", callback_data='language_uk')],
                   [InlineKeyboardButton("Русский", callback_data='language_ru')]]
        send_or_edit(context, chat_id=user.chat_id, text=_("Select a language:"),
                     reply_markup=InlineKeyboardMarkup(buttons))
        return self.States.LANGUAGE

    def set_language(self, update, context):
        user = context.user_data['user']
        _ = user.translator

        value = update.callback_query.data.replace("language_", "")

        if value == 'ru':
            user.language_code = 'ru'
        elif value == 'uk':
            user.language_code = 'uk'
        else:
            user.language_code = 'ru'

        add_to_db(user)
        context.user_data['_'] = _ = user.translator

        self.send_message(context)

        return self.States.ACTION

    def goto_next_menu(self, update, context):
        context.update_queue.put(update)
        return ConversationHandler.END

    def get_handler(self):

        handler = ConversationHandler(entry_points=[PrefixHandler('/', 'start', self.entry),
                                                    CallbackQueryHandler(self.entry, pattern='^start$')],
                                      states={
                                          self.States.ACTION: [PrefixHandler('/', 'admin', self.goto_next_menu),
                                                               CallbackQueryHandler(self.ask_language,
                                                                                    pattern="^language$"),
                                                               ],

                                          self.States.LANGUAGE: [
                                              CallbackQueryHandler(self.set_language, pattern="^language_\w\w$")],

                                      },
                                      fallbacks=[MessageHandler(Filters.all,
                                                                lambda update, context: delete_user_message(update))],
                                      allow_reentry=True)

        return handler
