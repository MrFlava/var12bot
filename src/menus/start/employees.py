import enum

from botmanlib.menus import OneListMenu, ArrowAddEditMenu
from botmanlib.menus.helpers import add_to_db, group_buttons
from botmanlib.messages import send_or_edit
from formencode import validators
from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import CallbackQueryHandler, ConversationHandler


from src.models import DBSession, Employee, EmployeeEducation, EmployeePayment, Payment


class EmployeesMenu(OneListMenu):
    menu_name = 'employees_menu'
    model = Employee

    class States(enum.Enum):
        ACTION = 1
        ASK_PAYMENT = 2

    def entry(self, update, context):
        return super(EmployeesMenu, self).entry(update, context)

    def query_objects(self, context):
        service = self.parent.selected_object(context)
        return DBSession.query(Employee).filter(Employee.taxation_service_id == service.id).all()

    def entry_points(self):
        return [CallbackQueryHandler(self.entry, pattern='^service_employees$', pass_user_data=True)]

    def message_text(self, context, obj):

            if obj:
                message_text = "Сотрудники инспекции" + '\n'
                message_text += f"ФИО: {obj.FIO}" + '\n'
                message_text += f"Дата рождения: {obj.date_of_birth.strftime('%d.%m.%Y ')}" + '\n'
                message_text += f"Положение в налоговой: {obj.position}" + '\n'
                message_text += f"Образование: {obj.educational_degree.to_str()}" + '\n'
                message_text += f"Зарплата: {obj.salary} UAH" + '\n'

            else:
                message_text = "Нет никаких данных о сотрудниках!" + '\n'

            return message_text

    def ask_payment(self, update, context):
        user = context.user_data['user']
        service = self.parent.selected_object(context)
        payment = DBSession.query(Payment).filter(Payment.taxation_service_id == service.id).first()
        employee = self.selected_object(context)
        buttons = []
        employee_payment_aosc = DBSession.query(EmployeePayment).get((employee.id, payment.id))
        if employee_payment_aosc:
            message_text = "Оформленные платежи" + '\n'
            message_text += f"Дата: {payment.date.strftime('%d.%m.%Y ')}" + '\n'
            message_text += f"Сумма: {payment.amount}" + '\n'
            message_text += f"Тип: {payment.type.to_str()}" + '\n'
        else:
            message_text = "Данные о оформленных платежах отсутствуют!"
        buttons.append([InlineKeyboardButton("🔙 Back", callback_data=f'back_to_employee')])
        send_or_edit(context, chat_id=user.chat_id, text=message_text, reply_markup=InlineKeyboardMarkup(buttons, resize_keyboard=True))
        return self.States.ASK_PAYMENT

    def back_button(self, context):
        return InlineKeyboardButton("🔙 Назад", callback_data=f"back_{self.menu_name}")

    def object_buttons(self, context, obj):
        buttons = []
        if obj:
            buttons.append(InlineKeyboardButton("Оформление оплаты", callback_data='employee_payment'))
        return group_buttons(buttons, 1)

    def back_to_employee(self, update, context):
        self.send_message(context)
        return self.States.ACTION

    def additional_states(self):

        return {self.States.ACTION: [CallbackQueryHandler(self.ask_payment, pattern='^employee_payment$')],
                self.States.ASK_PAYMENT: [CallbackQueryHandler(self.back_to_employee, pattern='^back_to_employee$')]}
