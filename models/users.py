from sqlalchemy import Column, String, Integer
from models.entity import Entity
from sqlalchemy.event import listen

from app import db, session


class User(Entity, db.Model):
    __tablename__ = 'users'
    username = Column(String(255), nullable=False, unique=True)
    password = Column(String(50), nullable=False,)

    def __init__(self, username, password, role=0):
        super().__init__()
        Entity.__init__(self)
        self.username = username
        self.password = password

    def toDict(self):
        repre = Entity.toDict(self)
        repre.update({
            'username': self.username,

        })
        # no need to send the password as it would not be transmitted
        return repre


def create_default_users(target, connection, **kw):
    import hashlib
    default_user_details = [{
        'username': 'admin',
        'password': 'Password123',
    }, {
        'username': 'joshua',
        'password': 'SliceBread',
    }]
    try:
        for user_details in default_user_details:
            hashed_password = hashlib.sha1(user_details['password'].encode('utf-8')).hexdigest()
            user = User(user_details['username'], hashed_password)
            session.add(user)
        session.commit()
        print("Successfully created {0} users".format(len(default_user_details)))
    except Exception as e:
        print(e)
        session.rollback()


listen(User.__table__, 'after_create', create_default_users)