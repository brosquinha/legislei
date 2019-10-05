import logging
import os
from datetime import datetime, timedelta

from apscheduler.schedulers.background import BackgroundScheduler
from flask import render_template
from pytz import timezone

from legislei.app import app
from legislei.exceptions import ModelError
from legislei.send_reports import check_reports_to_send, send_email
from legislei.services.relatorios import Relatorios


def check_and_send_reports():
    return send_reports(check_reports_to_send())


def send_reports(data, data_final = None):
    if data_final == None:
        data_final = datetime.now()
    numero_semana = int(data_final.strftime("%V"))
    for user in data:
        reports = []
        inscricao = user.inscricoes
        if (numero_semana % (inscricao["intervalo"]/7) != 0):
            logging.info("Pulando {} (intervalo de inscricao: {})".format(
                user.username, inscricao["intervalo"]))
            continue
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
                    'parlamentar': par,
                    'eventosPresentes': None,
                    'eventosPrevistos': None,
                    'proposicoes': None
                })
        with app.app_context():
            html_report = render_template(
                'relatorio_deputado_email.out.html',
                relatorios=reports,
                data_inicial=data_inicial.strftime('%d/%m/%Y'),
                data_final=data_final.strftime('%d/%m/%Y'),
                data_final_link=data_final.strftime('%Y-%m-%d'),
                intervalo=inscricao["intervalo"],
                host=os.environ.get('HOST_ENDPOINT')
            )
        send_email(user["email"], html_report)


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
