
from botmanlib.menus import OneListMenu

from telegram.ext import CallbackQueryHandler

from src.models import DBSession, Payment


class PaymentsMenu(OneListMenu):
    menu_name = 'payments_menu'
    model = Payment

    def entry(self, update, context):
        return super(PaymentsMenu, self).entry(update, context)

    def query_objects(self, context):
        service = self.parent.selected_object(context)
        return DBSession.query(Payment).filter(Payment.taxation_service_id == service.id).all()

    def entry_points(self):
        return [CallbackQueryHandler(self.entry, pattern='^taxation_payments$', pass_user_data=True)]

    def message_text(self, context, obj):

        if obj:
            message_text = "Платежи налоговой службы" + '\n'
            for company in obj.companies:
                message_text += f"Название компании: {company.name}" + '\n'
                message_text += f"Тип: {company.type.to_str()}" + '\n'
                message_text += f"Год основания: {company.year}" + '\n'
                message_text += f"Телефон: {company.phone}" + '\n'
                message_text += f"Кол-во работников: {company.employees_quantity}" + '\n'

            message_text += '\n'
            message_text += f"Дата: {obj.date.strftime('%d.%m.%Y ')}" + '\n'
            message_text += f"Сумма: {obj.amount}" + '\n'
            message_text += f"Тип: {obj.type.to_str()}" + '\n'
        else:
            message_text = "Нет никаих данных о платежах!"

        return message_text

    def additional_states(self):
        return {self.States.ACTION: []}

