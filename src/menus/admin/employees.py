import enum

from botmanlib.menus import OneListMenu, ArrowAddEditMenu
from botmanlib.menus.helpers import add_to_db, group_buttons
from botmanlib.messages import send_or_edit
from formencode import validators
from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import CallbackQueryHandler, ConversationHandler


from src.models import DBSession, Employee, EmployeeEducation, EmployeePayment, Payment


def delete_refresh_job(context):
    user_id = context.user_data['user'].id
    for job in context.job_queue.get_jobs_by_name(f"refresh_employees_menu_job_{user_id}"):
        job.schedule_removal()


class ServiceEmployeesMenu(OneListMenu):
    menu_name = 'service_employees_menu'
    model = Employee

    class States(enum.Enum):
        ACTION = 1
        ASK_EDUCATION = 2
        # ASK_GAME = 3

    def entry(self, update, context):
        return super(ServiceEmployeesMenu, self).entry(update, context)

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

    def back_button(self, context):
        return InlineKeyboardButton("🔙 Назад", callback_data=f"back_{self.menu_name}")

    def center_buttons(self, context, o=None):
        buttons = []
        buttons.append(InlineKeyboardButton("Добавить сотрудника", callback_data="add_employee"))
        if o:
            buttons.append(InlineKeyboardButton("Редактировать данные сотрудника", callback_data="edit_employee"))
        return buttons

    def object_buttons(self, context, obj):

        buttons = []

        if obj:
            buttons.append(InlineKeyboardButton("Изменить данные об образовании", callback_data='change_education'))
            buttons.append(InlineKeyboardButton("Оформление оплаты", callback_data='employee_payment'))
            buttons.append(InlineKeyboardButton("Удалить данные сотрудника", callback_data=f"delete_{self.menu_name}"))
        return group_buttons(buttons, 1)

    # def ask_game(self, update, context):
    #     user = context.user_data['user']
    #     team = self.parent.selected_object(context)
    #     game = DBSession.query(Game).filter(Game.team_id == team.id).first()
    #     player = self.selected_object(context)
    #     buttons = []
    #     player_game_aosc = DBSession.query(PlayerGame).get((player.id, game.id))
    #     message_text = "Участие в игре" + '\n'
    #     message_text += f"Денежная премия: {player_game_aosc.cash_bonus} UAH" + '\n'
    #     message_text += f"Нарушение: {player_game_aosc.player_violations_str()}" + '\n'
    #     buttons.append([InlineKeyboardButton("🔙 Back", callback_data=f'back_to_player')])
    #     send_or_edit(context, chat_id=user.chat_id, text=message_text, reply_markup=InlineKeyboardMarkup(buttons, resize_keyboard=True))
    #     return self.States.ASK_GAME

    def ask_change_education(self, update, context):
        delete_refresh_job(context)
        user = context.user_data['user']
        buttons = []
        message_text = "Пожалуйста, выберите новое положение в команде"
        obj = self.selected_object(context)
        if obj:
            buttons.append([InlineKeyboardButton("Высшее образование", callback_data='edu_higher_education')])
            buttons.append([InlineKeyboardButton("Среднее техническое образование", callback_data='edu_secondary_technical_education')])
            buttons.append([InlineKeyboardButton("Среднее образование", callback_data='edu_secondary_education')])
            buttons.append([InlineKeyboardButton("Среднее специальное образование", callback_data='edu_specialized_secondary_education')])
            buttons.append([InlineKeyboardButton("🔙 Назад", callback_data=f'back_to_employee')])
            send_or_edit(context, chat_id=user.chat_id, text=message_text, reply_markup=InlineKeyboardMarkup(buttons, resize_keyboard=True))

        return self.States.ASK_POSITION

    def set_change_position(self, update, context):
        edu_str = update.callback_query.data.replace("edu_", "")
        obj = self.selected_object(context)
        obj.position = EmployeeEducation[edu_str]
        if not add_to_db(obj):
            return self.conv_fallback(context)
        self.send_message(context)
        return self.States.ACTION

    def back_to_employee(self, update, context):
        self.send_message(context)
        return self.States.ACTION

    def additional_states(self):
        add_employee = EmployeeAddMenu(self)
        edit_emplpyee = EmployeeEditMenu(self)
        return {self.States.ACTION: [add_employee.handler,
                                     edit_emplpyee.handler,
                                     CallbackQueryHandler(self.ask_change_education, pattern='^change_education$')],
                self.States.ASK_EDUCATION: [CallbackQueryHandler(self.back_to_employee, pattern='^back_to_employees$'),
                                           CallbackQueryHandler(self.set_change_position, pattern='^edu_(higher_education|secondary_technical_education|secondary_education|specialized_secondary_education)$')]}

    def after_delete_text(self, context):
        return "Данные сотрудника удалены"


class EmployeeAddMenu(ArrowAddEditMenu):
    menu_name = 'employee_add_menu'
    model = Employee

    def entry(self, update, context):
        return super(EmployeeAddMenu, self).entry(update, context)

    def query_object(self, context):
        return None

    def fields(self, context):

        fields = [self.Field('FIO', "*ФИО", validators.String(), required=True),
                  self.Field('date_of_birth', "*Дата рождения", validators.DateConverter()),
                  self.Field('position', "*Положение в налоговой", validators.String(), required=True),
                  self.Field('salary', "*Стоимость контракта", validators.Number(),  units=" " + "UAH")]
        return fields

    def entry_points(self):
        return [CallbackQueryHandler(self.entry, pattern="^add_employee$")]

    def save_object(self, obj, context, session=None):
        user_data = context.user_data
        obj.FIO = user_data[self.menu_name]['FIO']
        obj.date_of_birth = user_data[self.menu_name]['date_of_birth']
        obj.position = user_data[self.menu_name]['position']
        obj.salary = user_data[self.menu_name]['salary']
        obj.taxation_service = self.parent.parent.selected_object(context)

        if not add_to_db(obj, session):
            return self.conv_fallback(context)


class EmployeeEditMenu(ArrowAddEditMenu):
    menu_name = 'employee_edit_menu'
    model = Employee

    def entry(self, update, context):
        return super(EmployeeEditMenu, self).entry(update, context)

    def query_object(self, context):

        employee = self.parent.selected_object(context)
        if employee:
            return DBSession.query(Employee).filter(Employee.id == employee.id).first()
        else:
            self.parent.update_objects(context)
            self.parent.send_message(context)
            return ConversationHandler.END

    def fields(self, context):

        fields = [self.Field('FIO', "*ФИО", validators.String(), required=True),
                  self.Field('date_of_birth', "*Дата рождения", validators.DateConverter()),
                  self.Field('position', "*Положение в налоговой", validators.String(), required=True),
                  self.Field('salary', "*Стоимость контракта", validators.Number(), units=" " + "UAH")]
        return fields

    def entry_points(self):
        return [CallbackQueryHandler(self.entry, pattern="^edit_employee$")]




