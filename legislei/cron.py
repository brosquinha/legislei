import os
from datetime import datetime

from apscheduler.schedulers.background import BackgroundScheduler
from flask import render_template
from pytz import timezone

from legislei.app import app
from legislei.house_selector import obter_relatorio
from legislei.send_reports import check_reports_to_send, send_email


def check_and_send_reports():
    return send_reports(check_reports_to_send())


def send_reports(data):
    for item in data:
        reports = []
        for par in item["parlamentares"]:
            reports.append(obter_relatorio(
                parlamentar=par['id'],
                data_final=datetime.now().strftime('%Y-%m-%d'),
                model=par['cargo'],
                periodo=item["intervalo"]
            ))
        with app.app_context():
            html_report = render_template(
                'relatorio_deputado_email.out.html',
                relatorios=reports,
                data_final=datetime.now().strftime('%Y-%m-%d'),
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