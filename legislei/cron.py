import logging
import os
from datetime import datetime, timedelta

from apscheduler.schedulers.background import BackgroundScheduler
from pytz import timezone

from legislei.exceptions import ModelError
from legislei.send_reports import send_email, send_push_notification
from legislei.services.inscricoes import Inscricao
from legislei.services.relatorios import Relatorios


def get_users_by_subscriptions():
    for user in Inscricao().obter_todas_inscricoes_para_processar():
        yield user

def check_and_send_reports():
    return generate_reports(get_users_by_subscriptions())


def generate_reports(users, data_final = None):
    if data_final == None:
        data_final = datetime.now()
    for user in users:
        reports = []
        inscricao = user.inscricoes
        data_inicial = (data_final - timedelta(days=int(inscricao["intervalo"])))
        logging.info("Obtendo relatorios para {}".format(user.username))
        for par in inscricao["parlamentares"]:
            try:
                reports.append(Relatorios().obter_relatorio(
                    parlamentar=par['id'],
                    data_final=data_final.strftime('%Y-%m-%d'),
                    cargo=par['cargo'],
                    periodo=inscricao["intervalo"]
                ))
            except ModelError:
                reports.append({
                    'parlamentar': par.to_dict(),
                    'orgaos': None,
                    'eventosPresentes': None,
                    'eventosPrevistos': None,
                    'eventosAusentes': None,
                    'proposicoes': None,
                    '_id': None
                })
        
        send_email(user["email"], reports, dates=(data_inicial, data_final))
        if user.devices:
            for device in user.devices:
                if device.active:
                    send_push_notification(device.token, reports)


scheduler = BackgroundScheduler()
scheduler.configure(timezone=timezone('America/Sao_Paulo'))
scheduler.add_job(
    func=check_and_send_reports,
    trigger='cron',
    day_of_week='sat',
    hour='12',
    minute='0',
    second=0,
    day='*',
    month='*'
)
