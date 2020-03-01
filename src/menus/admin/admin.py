import enum

from botmanlib.menus.basemenu import BaseMenu
from botmanlib.menus.helpers import group_buttons, prepare_user, inline_placeholder
from botmanlib.menus.ready_to_use.permissions import PermissionsMenu
from botmanlib.messages import send_or_edit, delete_interface, delete_user_message
from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ConversationHandler, Filters, MessageHandler, CallbackQueryHandler, PrefixHandler


from src.models import User, Permission
from src.menus.admin.taxation_services import ServicesMenu


class AdminMenu(BaseMenu):
    menu_name = 'admin_menu'

    class States(enum.Enum):
        ACTION = 1

    def entry(self, update, context):
        user = prepare_user(User, update, context)
        _ = context.user_data['user'].translator

        if self.menu_name not in context.user_data:
            context.user_data[self.menu_name] = {}

        delete_interface(context)
        self.send_message(context)

        if update.callback_query:
            self.bot.answer_callback_query(update.callback_query.id)

        return self.States.ACTION

    def send_message(self, context):
        user = context.user_data['user']

        buttons = []

        buttons.append(InlineKeyboardButton("Работа с налоговыми службами", callback_data='taxation_services'))
        buttons.append(InlineKeyboardButton("Вернуться к главному меню", callback_data='start'))

        send_or_edit(context, chat_id=user.chat_id, text="Админ меню:", reply_markup=InlineKeyboardMarkup(group_buttons(buttons, 1)))

    def goto_next_menu(self, update, context):
        context.update_queue.put(update)
        return ConversationHandler.END

    def get_handler(self):
        permissions_menu = PermissionsMenu(User, Permission, parent=self)
        taxation_services_menu = ServicesMenu(self)

        handler = ConversationHandler(entry_points=[PrefixHandler('/', "admin", self.entry)],
                                      states={
                                          self.States.ACTION: [PrefixHandler('/', 'start', self.goto_next_menu),
                                                               CallbackQueryHandler(self.entry, pattern='^back$'),
                                                               CallbackQueryHandler(inline_placeholder(self.States.ACTION, "Menu is under development"), pattern="moderation"),
                                                               permissions_menu.handler,
                                                               taxation_services_menu.handler
                                                               ],

                                      },
                                      fallbacks=[MessageHandler(Filters.all, lambda update, context: delete_user_message(update))],
                                      allow_reentry=True)

        return handler
