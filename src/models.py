import enum


from botmanlib.menus.helpers import translator
from botmanlib.models import Database, BaseUser, UserPermissionsMixin, BasePermission, BaseUserSession, UserSessionsMixin, ModelPermissionsBase
from sqlalchemy import Column, Float, Integer, Enum, String, ForeignKey, ARRAY, UniqueConstraint, Date, Table
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


class TaxationService(Base):
    __tablename__ = 'taxation_services'

    id = Column(Integer, primary_key=True)
    type = Column(Enum(ServiceType), default=ServiceType.regional)
    name = Column(String, nullable=False)
    city = Column(String, nullable=False)
    year = Column(Integer, nullable=False)
    phone = Column(String, nullable=False)
    address = Column(String, nullable=False)

    # employees = relationship("Player", back_populates='team', cascade='all ,delete')


class UserSession(BaseUserSession, Base):
    __tablename__ = 'user_sessions'


DBSession = database.create_session("DBSession")
BlockSession = database.create_session("BlockSession")
