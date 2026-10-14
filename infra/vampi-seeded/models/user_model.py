import datetime
import jwt
from sqlalchemy.orm import relationship
from config import db, vuln_app
from app import vuln, alive
from models.books_model import Book
from random import randrange
from sqlalchemy.sql import text


class User(db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True, unique=True, autoincrement=True)
    username = db.Column(db.String(128), unique=True, nullable=False)
    password = db.Column(db.String(128), nullable=False)
    email = db.Column(db.String(128), nullable=False)
    admin = db.Column(db.Boolean, nullable=False, default=False)

    books = relationship("Book", order_by=Book.id, back_populates="user")

    def __init__(self, username, password, email, admin=False):
        self.username = username
        self.email = email
        self.password = password
        self.admin = admin

    def __repr__(self):
        return f'{{"username": "{self.username}", "email": "{self.email}"}}'

    def encode_auth_token(self, user_id):
        try:
            payload = {
                'exp': datetime.datetime.utcnow() + datetime.timedelta(days=0, seconds=alive),
                'iat': datetime.datetime.utcnow(),
                'sub': user_id,
                # THESIS SEED: the role is snapshotted into the token at login time. This is what
                # makes the A1 bug possible -- the claim goes stale the moment the role changes.
                'admin': self.admin
            }
            return jwt.encode(
                payload,
                vuln_app.app.config.get('SECRET_KEY'),
                algorithm='HS256'
            )
        except Exception as e:
            return e

    @staticmethod
    def decode_auth_token(auth_token):
        try:
            payload = jwt.decode(auth_token, vuln_app.app.config.get('SECRET_KEY'), algorithms=["HS256"])
            return payload
        except jwt.ExpiredSignatureError:
            return {'error': 'Signature expired. Please log in again.'}
        except jwt.InvalidTokenError:
            return {'error': 'Invalid token. Please log in again.'}

    def json(self):
        return {'username': self.username, 'email': self.email}

    def json_debug(self):
        return {'username': self.username, 'password': self.password, 'email': self.email, 'admin': self.admin}

    @staticmethod
    def get_all_users():
        return [User.json(user) for user in User.query.all()]

    @staticmethod
    def get_all_users_debug():
        return [User.json_debug(user) for user in User.query.all()]

    @staticmethod
    def get_user(username):
        if vuln:  # SQLi Injection
            user_query = f"SELECT * FROM users WHERE username = '{username}'"
            query = db.session.execute(text(user_query))
            ret = query.fetchone()
            if ret:
                fin_query = '{"username": "%s", "email": "%s"}' % (ret[1], ret[3])
            else:
                fin_query = None
        else:
            fin_query = User.query.filter_by(username=username).first()
        return fin_query

    @staticmethod
    def register_user(username, password, email, admin=False, book_suffix=None):
        new_user = User(username=username, password=password, email=email, admin=admin)
        # THESIS SEED: stock VAmPI picks the starter book title with randrange(100) against a
        # UNIQUE column, so seeding collides at random and /createdb 500s. Seeded users pass an
        # explicit suffix to make the reset deterministic across the trial batch; ad-hoc
        # registrations keep the original random behaviour.
        randomint = str(randrange(100)) if book_suffix is None else str(book_suffix)
        new_user.books = [Book(book_title="bookTitle" + randomint, secret_content="secret for bookTitle" + randomint)]
        db.session.add(new_user)
        db.session.commit()

    @staticmethod
    def delete_user(username):
        done = User.query.filter_by(username=username).delete()
        db.session.commit()
        return done

    @staticmethod
    def set_role(username, role):
        """THESIS SEED: the permission-reducing transition. 'admin' -> privileged, anything
        else -> unprivileged. Returns None when the user does not exist."""
        user = User.query.filter_by(username=username).first()
        if not user:
            return None
        user.admin = (str(role).lower() == 'admin')
        db.session.commit()
        return user

    @staticmethod
    def init_db_users():
        User.register_user("name1", "pass1", "mail1@mail.com", False, book_suffix=1)
        User.register_user("name2", "pass2", "mail2@mail.com", False, book_suffix=2)
        User.register_user("admin", "pass1", "admin@mail.com", True, book_suffix=3)
        # THESIS SEED: a second, stable admin used only as the transition *operator*, so that a
        # constructed triple which demotes `admin` cannot strand the fuzzer without a privileged
        # actor (the state-isolation caveat, tier2 plan §7).
        User.register_user("superadmin", "pass1", "superadmin@mail.com", True, book_suffix=4)
