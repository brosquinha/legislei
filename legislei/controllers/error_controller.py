from legislei.app import rest_api_v1
from legislei.exceptions import AppError

@rest_api_v1.errorhandler(AppError)
def app_error_handler(error):
    return {'message': str(error)}, 500