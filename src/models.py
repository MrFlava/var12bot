import enum

from botmanlib.models import Database, BaseUser, UserPermissionsMixin, BasePermission, BaseUserSession, UserSessionsMixin
from sqlalchemy import Column, Float, Integer, Enum, String, ForeignKey, DateTime
from sqlalchemy.orm import object_session, relationship

database = Database()
Base = database.Base


class User(Base, BaseUser, UserPermissionsMixin, UserSessionsMixin):
    __tablename__ = 'users'

    def init_permissions(self):
        session = object_session(self)
        if session is None:
            session = database.DBSession
        for permission in ['start_menu_access',
                           ]:
            perm = session.query(Permission).get(permission)
            if perm not in self.permissions:
                self.permissions.append(perm)


class Permission(BasePermission, Base):
    __tablename__ = 'permissions'


class ServiceType(enum.Enum):
    urban = 'urban'
    district = 'district'
    regional = 'regional'

    def to_str(self):
        if self is ServiceType.urban:
            return "Городская"
        elif self is ServiceType.district:
            return "Районная"
        elif self is ServiceType.regional:
            return "Региональная"
        else:
            return "Неизвестно"


class PaymentType(enum.Enum):
    value_added_tax = 'value added tax'
    income_tax = 'income tax'
    penalty_for_tax_evasion = 'penalty for tax evasion'

    def to_str(self):
        if self is PaymentType.value_added_tax:
            return "Налог на добавленную стоимость"
        elif self is PaymentType.income_tax:
            return "Подоходный налог"
        elif self is PaymentType.penalty_for_tax_evasion:
            return "Штраф за уклонение от уплаты налогов"
        else:
            return "Неизвестно"


class EmployeeEducation(enum.Enum):
    higher_education = 'higher education'
    secondary_technical_education = 'secondary technical education'
    secondary_education = 'secondary education'
    specialized_secondary_education = 'specialized secondary education'

    def to_str(self):
        if self is EmployeeEducation.higher_education:
            return "Высшее образование"
        elif self is EmployeeEducation.secondary_technical_education:
            return "Среднее техническое образование"
        elif self is EmployeeEducation.secondary_education:
            return "Среднее образование"
        elif self is EmployeeEducation.specialized_secondary_education:
            return "Среднее специальное образование"
        else:
            return "Неизвестно"


class EmployeePayment(Base):
    __tablename__ = 'employee_payment_association_table'

    employee_id = Column(Integer, ForeignKey('employees.id'), primary_key=True)
    employee = relationship("Employee")
    payment_id = Column(Integer, ForeignKey('payments.id'), primary_key=True)
    payment = relationship("Payment")


class TaxationService(Base):
    __tablename__ = 'taxation_services'

    id = Column(Integer, primary_key=True)
    type = Column(Enum(ServiceType), default=ServiceType.regional)
    name = Column(String, nullable=False)
    city = Column(String, nullable=False)
    year = Column(Integer, nullable=False)
    phone = Column(String, nullable=False)
    address = Column(String, nullable=False)

    employees = relationship("Employee", back_populates='taxation_service', cascade='all ,delete')
    payments = relationship("Payment", back_populates='taxation_service', cascade='all, delete')


class Employee(Base):
    __tablename__ = 'employees'

    id = Column(Integer, primary_key=True)
    FIO = Column(String, nullable=False)
    date_of_birth = Column(DateTime, nullable=False)
    position = Column(String, nullable=False)
    salary = Column(Integer, nullable=False, default=0)
    educational_degree = Column(Enum(EmployeeEducation), default=EmployeeEducation.specialized_secondary_education)

    taxation_service_id = Column(Integer, ForeignKey('taxation_services.id'), nullable=False)
    taxation_service = relationship("TaxationService", back_populates="employees")
    payment = relationship("Payment", secondary=EmployeePayment.__table__, back_populates="employee", lazy='joined')


class Payment(Base):
    __tablename__ = 'payments'

    id = Column(Integer, primary_key=True)
    date = Column(DateTime, nullable=False)
    amount = Column(Float, nullable=False)
    type = Column(Enum(PaymentType), default=PaymentType.income_tax)

    taxation_service_id = Column(Integer, ForeignKey('taxation_services.id'), nullable=False)
    taxation_service = relationship("TaxationService", back_populates="payments")
    companies = relationship("Company", back_populates='payment', cascade='all ,delete')
    employee = relationship("Employee", secondary=EmployeePayment.__table__, lazy='joined')


class Company(Base):
    __tablename__ = 'companies'
    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)
    year = Column(Integer, nullable=False)
    phone = Column(String, nullable=False)
    employees_quantity = Column(Integer, nullable=False)

    payment_id = Column(Integer, ForeignKey('payments.id'), nullable=False)
    payment = relationship("Payment", back_populates="companies")


class UserSession(BaseUserSession, Base):
    __tablename__ = 'user_sessions'


DBSession = database.create_session("DBSession")
BlockSession = database.create_session("BlockSession")
