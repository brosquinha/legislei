from mongoengine.errors import ValidationError

from legislei.exceptions import (DeviceDoesNotExistError,
                                 InvalidParametersError, UserDoesNotExist)
from legislei.models.user import User, UserDevice


class Dispositivo():

    def _obter_usuario(self, user_id):
        try:
            user = User.objects(pk=user_id).first()
            return user if user.pk else None
        except (ValidationError, AttributeError):
            raise UserDoesNotExist()
    
    def obter_dispositivos_de_usuario(self, user_id):
        user = self._obter_usuario(user_id)
        return user.devices if user.devices else []

    def adicionar_dispostivo(self, user_id, uuid, token, name, active=True, os=""):
        user = self._obter_usuario(user_id)
        try:
            device = UserDevice(
                id=uuid,
                token=token,
                active=active,
                name=name,
                os=os
            )
            if [x for x in user.devices if x.id == uuid] != []:
                raise InvalidParametersError("Dispositivo já existe")
            if user.devices:
                user.devices.append(device)
            else:
                user.devices = [device]
            user.save()
        except ValidationError as e:
            raise InvalidParametersError(e.message)

    def atualizar_dispositivo(self, user_id, device_id, **kwargs):
        user = self._obter_usuario(user_id)
        try:
            device = next(x for x in user.devices if x.id == device_id)
        except StopIteration:
            raise DeviceDoesNotExistError()
        for key, item in kwargs.items():
            setattr(device, key, item)
        return user.save()

    def apagar_dispositivo(self, user_id, device_id):
        self._obter_usuario(user_id).update(
            pull__devices__id=device_id
        )
