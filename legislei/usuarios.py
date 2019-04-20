from flask_login import login_user, logout_user
from mongoengine.errors import NotUniqueError, ValidationError
from passlib.hash import pbkdf2_sha256

from legislei.exceptions import UsernameOrEmailAlreadyExistis, RequirementsNotMet, InvalidEmail
from legislei.models.user import User

class Usuario():

    def obter_por_id(self, id):
        return User.objects(pk=id).first()
    
    def registrar(self, nome, senha, senha_confirmada, email):
        user_name = nome.lower()
        if not(len(user_name) > 3 and len(senha) and senha == senha_confirmada):
            raise RequirementsNotMet()
        user = User(
            username=user_name,
            password=pbkdf2_sha256.using(rounds=16, salt_size=16).hash(senha),
            email=email
        )
        try:
            user.save()
            # Idealmente essa camada não deveria precisar conhecer exceptions do mongoengine?
        except NotUniqueError:
            raise UsernameOrEmailAlreadyExistis()
        except ValidationError:
            raise InvalidEmail()
        except Exception as e:
            raise e

    def login(self, user_name, user_psw, remember_me):
        user_name = user_name.lower()
        user = User.objects(username=user_name).first()
        if user and pbkdf2_sha256.verify(user_psw, user.password):
            login_user(user, remember=remember_me)
            return True
        return False

    def logout(self):
        logout_user()
