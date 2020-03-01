import enum

from botmanlib.menus.basemenu import BaseMenu
from botmanlib.menus.helpers import prepare_user
from botmanlib.messages import send_or_edit, delete_interface, delete_user_message
from telegram import TelegramError, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ConversationHandler, CallbackQueryHandler, Filters, MessageHandler, PrefixHandler

from src.models import User
from src.menus.start.taxation_services import TaxationServiceMenu


class StartMenu(BaseMenu):
    menu_name = 'start_menu'

    class States(enum.Enum):
        ACTION = 1

    def entry(self, update, context):
        user = prepare_user(User, update, context)

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

        message_text = "Приветствую, я бот для мониторинга налоговых служб"

        buttons = [[InlineKeyboardButton("Налоговые службы", callback_data='taxation_services')]]

        send_or_edit(context, chat_id=user.chat_id, text=message_text, reply_markup=InlineKeyboardMarkup(buttons))
        return self.States.ACTION

    def goto_next_menu(self, update, context):
        context.update_queue.put(update)
        return ConversationHandler.END

    def get_handler(self):
        taxation_service_menu = TaxationServiceMenu(self)

        handler = ConversationHandler(entry_points=[PrefixHandler('/', 'start', self.entry),
                                                    CallbackQueryHandler(self.entry, pattern='^start$')],
                                      states={
                                          self.States.ACTION: [PrefixHandler('/', 'admin', self.goto_next_menu),
                                                               taxation_service_menu.handler
                                                               ]
                                      },
                                      fallbacks=[MessageHandler(Filters.all,
                                                                lambda update, context: delete_user_message(update))],
                                      allow_reentry=True)

        return handler
