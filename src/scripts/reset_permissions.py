from src.models import DBSession, User

def main():
    users = DBSession.query(User).filter(User.is_active == True).all()

    for user in users:
        user.init_permissions()
        DBSession.add(user)
    DBSession.commit()

if __name__ == '__main__':
    main()
