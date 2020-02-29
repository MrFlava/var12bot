from src.models import DBSession, Permission, User

# noinspection SpellCheckingInspection
from src.settings import SUPERUSER_ACCOUNTS


def main():
    """"""
    _ = lambda text: text

    """-----------------User-----------------"""
    Permission.create('start_menu_access', _('Access to "Start" menu'))

    """-----------------Admin-----------------"""
    # menus
    Permission.create('admin_menu_access', _('Access to "Admin" menu'))
    Permission.create('distribution_menu_access', _('Access to "Distribution" admin menu'))

    Permission.create('settings_menu_access', _('Access to "Settings" admin menu'))

    # permissions menu
    Permission.create(Permission.view_permission, _('Access to "Permissions" menu'))
    Permission.create(Permission.add_permission, _('Allow add permission'))
    Permission.create(Permission.delete_permission, _('Allow remove permission'))

    Permission.create('superuser', _('Superuser'))

    DBSession.commit()

    users = DBSession.query(User).filter(User.chat_id.in_(SUPERUSER_ACCOUNTS)).all()
    permission = DBSession.query(Permission).get('superuser')
    for user in users:
        if not user.has_permission(permission.code):
            user.permissions.append(permission)
        DBSession.add(user)
    DBSession.commit()


if __name__ == '__main__':
    main()
