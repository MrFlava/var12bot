import enum
import datetime

from botmanlib.validators import PhoneNumber
from botmanlib.menus import OneListMenu, ArrowAddEditMenu
from botmanlib.menus.helpers import add_to_db, group_buttons
from botmanlib.messages import send_or_edit

from formencode import validators

from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import CallbackQueryHandler, ConversationHandler

from src.models import TaxationService, DBSession, ServiceType
# from src.menus.admin. import
# from src.menus.admin. import


def delete_refresh_job(context):
    user_id = context.user_data['user'].id
    for job in context.job_queue.get_jobs_by_name(f"refresh_services_menu_job_{user_id}"):
        job.schedule_removal()


class ServicesMenu(OneListMenu):
    menu_name = "services_menu"

    class States(enum.Enum):
        ACTION = 1
        ASK_TYPE = 2

    def entry(self, update, context):
        return super(ServicesMenu, self).entry(update, context)

    def query_objects(self, context):
        return DBSession.query(TaxationService).all()

    def entry_points(self):
        return [CallbackQueryHandler(self.entry, pattern='^taxation_services$', pass_user_data=True)]

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

    def delete_ask(self, update, context):
        return super(ServicesMenu, self).delete_ask(update, context)

    def center_buttons(self, context, o=None):
        buttons = []
        buttons.append(InlineKeyboardButton("Добавить налоговую службу", callback_data="add_service"))
        if o:
            buttons.append(InlineKeyboardButton("Редактировать данные налоговой службы", callback_data="edit_service"))
        return buttons

    def back_button(self, context):
        return InlineKeyboardButton("🔙 Назад", callback_data=f"back_{self.menu_name}")

    def object_buttons(self, context, obj):

        buttons = []

        if obj:
                buttons.append(InlineKeyboardButton("Изменить тип службы", callback_data='change_type'))
                buttons.append(InlineKeyboardButton("Оплата налогов", callback_data='taxation_payments'))
                buttons.append(InlineKeyboardButton("Работники службы", callback_data='service_employees'))
                buttons.append(InlineKeyboardButton("Удалить службу", callback_data=f"delete_{self.menu_name}"))
        return group_buttons(buttons, 1)

    def ask_change_type(self, update, context):
        delete_refresh_job(context)
        user = context.user_data['user']
        buttons = []
        message_text = "Пожалуйста, выберите новый тип"
        obj = self.selected_object(context)
        if obj:
            buttons.append([InlineKeyboardButton("Городская служба", callback_data='type_urban')])
            buttons.append([InlineKeyboardButton("Районная служба", callback_data='type_district')])
            buttons.append([InlineKeyboardButton("Региональная служба", callback_data='type_regional')])
            buttons.append([InlineKeyboardButton("🔙 Назад", callback_data=f'back_to_service')])
            send_or_edit(context, chat_id=user.chat_id, text=message_text, reply_markup=InlineKeyboardMarkup(buttons, resize_keyboard=True))

        return self.States.ASK_TYPE

    def set_change_type(self, update, context):
        type_str = update.callback_query.data.replace("type_", "")
        obj = self.selected_object(context)
        obj.type = ServiceType[type_str]
        if not add_to_db(obj):
            return self.conv_fallback(context)
        self.send_message(context)
        return self.States.ACTION

    def back_to_service(self, update, context):
        self.send_message(context)
        return self.States.ACTION

    def additional_states(self):

        add_service = ServiceAddMenu(self)
        edit_service = ServiceEditMenu(self)
        return {self.States.ACTION: [add_service.handler,
                                     edit_service.handler,
                                     CallbackQueryHandler(self.ask_change_type, pattern='^change_type$')
                                     ],
                self.States.ASK_TYPE: [CallbackQueryHandler(self.back_to_service, pattern='^back_to_service$'),
                                       CallbackQueryHandler(self.set_change_type, pattern='^type_(urban|district|regional)$')]}

    def after_delete_text(self, context):
        return "Служба удалена"


class ServiceAddMenu(ArrowAddEditMenu):
    menu_name = 'service_add_menu'
    model = TaxationService

    def entry(self, update, context):
        return super(ServiceAddMenu, self).entry(update, context)

    def query_object(self, context):
        return None

    def fields(self, context):
        year = datetime.datetime.now().year
        fields = [self.Field('name', "*Назвнаие", validators.String(), required=True),
                  self.Field('city', "*Город", validators.String(), required=True),
                  self.Field('year', "*Работает с", validators.Number(min=1, max=year), required=True, default=0),
                  self.Field('phone', "*Телефон", PhoneNumber, required=True),
                  self.Field('address', "*Адрес", validators.String(), required=True)]
        return fields

    def entry_points(self):
        return [CallbackQueryHandler(self.entry, pattern="^add_service$")]

    def save_object(self, obj, context, session=None):
        user_data = context.user_data
        obj.name = user_data[self.menu_name]['name']
        obj.city = user_data[self.menu_name]['city']
        obj.year = user_data[self.menu_name]['year']
        obj.phone = user_data[self.menu_name]['phone']
        obj.address = user_data[self.menu_name]['address']

        if not add_to_db(obj, session):
            return self.conv_fallback(context)


class ServiceEditMenu(ArrowAddEditMenu):
    menu_name = 'service_edit_menu'
    model = TaxationService

    def entry(self, update, context):
        return super(ServiceEditMenu, self).entry(update, context)

    def query_object(self, context):

        service = self.parent.selected_object(context)
        if service:
            return DBSession.query(TaxationService).filter(TaxationService.id == service.id).first()
        else:
            self.parent.update_objects(context)
            self.parent.send_message(context)
            return ConversationHandler.END

    def fields(self, context):
        year = datetime.datetime.now().year
        fields = [self.Field('name', "*Назвнаие", validators.String(), required=True),
                  self.Field('city', "*Город", validators.String(), required=True),
                  self.Field('year', "*Работает с", validators.Number(min=1, max=year), required=True, default=0),
                  self.Field('phone', "*Телефон", PhoneNumber, required=True),
                  self.Field('address', "*Адрес", validators.String(), required=True)]
        return fields

    def entry_points(self):
        return [CallbackQueryHandler(self.entry, pattern='^edit_service$')]




