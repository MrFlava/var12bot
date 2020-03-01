
from botmanlib.menus import OneListMenu
from botmanlib.menus.helpers import group_buttons

from telegram import InlineKeyboardButton
from telegram.ext import CallbackQueryHandler

from src.models import TaxationService, DBSession
# from src.menus.start. import PlayersMenu
# from src.menus.start. import UserTeamGamesMenu


class TaxationServiceMenu(OneListMenu):
    menu_name = 'taxation_service_menu'
    model = TaxationService
    auto_hide_arrows = True

    def entry(self, update, context):
        return super(TaxationServiceMenu, self).entry(update, context)

    def query_objects(self, context):
        return DBSession.query(TaxationService).all()

    def entry_points(self):
        return [CallbackQueryHandler(self.entry, pattern='^taxation_services$')]

    def message_text(self, context, obj):

        if obj:
            message_text = "Отделения налоговых служб" + '\n'
            message_text += f"Номер отделения: {obj.id}" + '\n'
            message_text += f"Тип: {obj.type.to_str()}" + '\n'
            message_text += f"Название: {obj.name}" + '\n'
            message_text += f"Город: {obj.city}" + '\n'
            message_text += f"Работает с: {obj.year}" + '\n'
            message_text += f"Телефон: {obj.phone}" + '\n'
            message_text += f"Адрес: {obj.address}" + '\n'

        else:
            message_text = "Нет никаких данных о налоговых службах!" + '\n'

        return message_text

    def back_button(self, context):
        return InlineKeyboardButton("🔙 Назад", callback_data=f"back_{self.menu_name}")

    def object_buttons(self, context, obj):
        buttons = []

        if obj:
            buttons.append(InlineKeyboardButton("Оплата налогов", callback_data='taxation_payments'))
            buttons.append(InlineKeyboardButton("Работники службы", callback_data='service_employees'))
        return group_buttons(buttons, 1)

    def additional_states(self):

        return {
            self.States.ACTION: []
        }
