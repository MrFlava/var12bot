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


class UserSession(BaseUserSession, Base):
    __tablename__ = 'user_sessions'


DBSession = database.create_session("DBSession")
BlockSession = database.create_session("BlockSession")
