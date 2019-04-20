import os
from datetime import datetime, timedelta

from apscheduler.schedulers.background import BackgroundScheduler
from flask import render_template
from pytz import timezone

from legislei.app import app
from legislei.exceptions import ModelError
from legislei.send_reports import check_reports_to_send, send_email
from legislei.relatorios import Relatorios


def check_and_send_reports():
    return send_reports(check_reports_to_send())


def send_reports(data):
    for item in data:
        reports = []
        data_final = datetime.now().strftime('%d/%m/%Y')
        data_inicial = (datetime.now() - timedelta(days=int(item["intervalo"]))).strftime('%d/%m/%Y')
        for par in item["parlamentares"]:
            try:
                reports.append(Relatorios().obter_relatorio(
                    parlamentar=par['id'],
                    data_final=datetime.now().strftime('%Y-%m-%d'),
                    cargo=par['cargo'],
                    periodo=item["intervalo"]
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
                data_inicial=data_inicial,
                data_final=data_final,
                data_final_link=datetime.now().strftime('%Y-%m-%d'),
                intervalo=item["intervalo"],
                host=os.environ.get('HOST_ENDPOINT')
            )
        send_email(item["email"], html_report)


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