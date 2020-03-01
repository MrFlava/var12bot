import datetime

from botmanlib.validators import PhoneNumber
from botmanlib.menus import OneListMenu, ArrowAddEditMenu
from botmanlib.menus.helpers import add_to_db

from formencode import validators
from telegram import InlineKeyboardButton
from telegram.ext import CallbackQueryHandler, ConversationHandler


from src.models import DBSession, Payment, Company, PaymentType, CompanyType


class ServicePaymentsMenu(OneListMenu):
    menu_name = 'service_payments_menu'
    model = Payment

    def entry(self, update, context):
        return super(ServicePaymentsMenu, self).entry(update, context)

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

    def center_buttons(self, context, o=None):
        buttons = []
        buttons.append(InlineKeyboardButton("Добавить новый платёж", callback_data="add_payment"))
        if o:
            buttons.append(InlineKeyboardButton("Редактировать инофрмацию о платеже", callback_data="edit_payment"))
        return buttons

    def additional_states(self):
        add_payment = AddPaymentMenu(self)
        edit_payment = EditPaymentMenu(self)
        return {self.States.ACTION: [add_payment.handler,
                                     edit_payment.handler]}


class AddPaymentMenu(ArrowAddEditMenu):
    menu_name = 'add_payment_menu'
    model = Payment

    def entry(self, update, context):
        return super(AddPaymentMenu, self).entry(update, context)

    def query_object(self, context):
        return None

    def fields(self, context):
        year = datetime.datetime.now().year
        fields = [
                   self.Field('name', "*Название компании", validators.String(), required=True),
                   self.Field('year', "*Год основания", validators.Number(min=1, max=year), required=True),
                   self.Field('phone', "*Телефон", PhoneNumber, required=True),
                   self.Field('employees_quantity', "*Кол-во работников", validators.Number(), required=True),
                   self.Field('date', "*Дата", validators.DateConverter(), required=True),
                   self.Field('amount', "*Сумма", validators.Number(), required=True)]
        return fields

    def entry_points(self):
        return [CallbackQueryHandler(self.entry, pattern="^add_payment$")]

    def save_object(self, obj, context, session=None):
        user_data = context.user_data
        payment = Payment()
        company = Company()
        company.name = user_data[self.menu_name]['name']
        company.year = user_data[self.menu_name]['year']
        company.phone = user_data[self.menu_name]['phone']
        company.employees_quantity = user_data[self.menu_name]['employees_quantity']
        payment.companies.append(company)
        payment.date = user_data[self.menu_name]['date']
        payment.amount = user_data[self.menu_name]['amount']
        payment.taxation_service = self.parent.parent.selected_object(context)
        if not add_to_db([payment, company], session):
            return self.conv_fallback(context)


class EditPaymentMenu(ArrowAddEditMenu):
    menu_name = 'edit_payment_menu'
    model = Payment

    def entry(self, update, context):
        return super(EditPaymentMenu, self).entry(update, context)

    def query_object(self, context):

        payment = self.parent.selected_object(context)
        if payment:
            return DBSession.query(Payment).filter(Payment.id == payment.id).first()
        else:
            self.parent.update_objects(context)
            self.parent.send_message(context)
            return ConversationHandler.END

    def fields(self, context):
        year = datetime.datetime.now().year
        fields = [
                   self.Field('name', "*Название компании", validators.String(), required=True),
                   self.Field('year', "*Год основания", validators.Number(min=1, max=year), required=True),
                   self.Field('phone', "*Телефон", PhoneNumber, required=True),
                   self.Field('employees_quantity', "*Кол-во работников", validators.Number(), required=True),
                   self.Field('date', "*Дата", validators.DateConverter(), required=True),
                   self.Field('amount', "*Сумма", validators.Number(), required=True)]
        return fields

    def entry_points(self):
        return [CallbackQueryHandler(self.entry, pattern="^edit_payment$")]

    def save_object(self, obj, context, session=None):
        user_data = context.user_data
        company = Company()
        company.name = user_data[self.menu_name]['name']
        company.year = user_data[self.menu_name]['year']
        company.phone = user_data[self.menu_name]['phone']
        company.employees_quantity = user_data[self.menu_name]['employees_quantity']
        obj.companies.append(company)
        obj.date = user_data[self.menu_name]['date']
        obj.amount = user_data[self.menu_name]['amount']

        if not add_to_db([obj, company], session):
            return self.conv_fallback(context)
