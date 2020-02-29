import enum


from botmanlib.menus.helpers import translator
from botmanlib.models import Database, BaseUser, UserPermissionsMixin, BasePermission, BaseUserSession, UserSessionsMixin, ModelPermissionsBase
from sqlalchemy import Column, Float, Integer, Enum, String, ForeignKey, ARRAY, UniqueConstraint, Date, Table, DateTime
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


class EmployeeEducation(enum.Enum):
    higher_education = 'higher education'
    secondary_technical_education = 'secondary technical education'
    secondary_education = 'secondary education'
    specialized_secondary_education = 'specialized secondary education'


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


class UserSession(BaseUserSession, Base):
    __tablename__ = 'user_sessions'


DBSession = database.create_session("DBSession")
BlockSession = database.create_session("BlockSession")
