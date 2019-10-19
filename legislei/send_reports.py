import json
import logging
import os
import smtplib
from copy import deepcopy
from datetime import datetime
from email.header import Header
from email.mime.text import MIMEText

import certifi
import urllib3
from flask import render_template

from legislei import settings
from legislei.app import app

smtp_server = os.environ.get("EMAIL_ENDPOINT", "smtp.gmail.com")
smtp_server_port = os.environ.get("EMAIL_PORT", "587")
from_email = os.environ.get("EMAIL_USR", None)
password = os.environ.get("EMAIL_PSW", None)
uses_ssl = os.environ.get("EMAIL_SSL", "False") in ['True', 'true']
uses_tls = os.environ.get("EMAIL_TLS", "True") in ['True', 'true']
fcm_access_token = os.environ.get("FIREBASE_API_TOKEN")


def send_email(email, reports, dates):
    """
    Sends email to given email with reports overview

    :param email: Email to send reports overview to
    :type email: String
    :param reports: Lists of reports to be sent
    :type reports: List[Relatorio.to_dict()]
    :param dates: Initial and final dates of reports
    :type dates: Tuple(datetime, datetime)
    """
    data_inicial, data_final = dates
    with app.app_context():
            html_report = render_template(
                'relatorio_deputado_email.out.html',
                relatorios=reports,
                data_inicial=data_inicial.strftime('%d/%m/%Y'),
                data_final=data_final.strftime('%d/%m/%Y'),
                host=os.environ.get('HOST_ENDPOINT')
            )
    if uses_ssl:
        s = smtplib.SMTP_SSL(smtp_server, int(smtp_server_port))
    else:
        s = smtplib.SMTP(smtp_server, int(smtp_server_port))
    if uses_tls:
        s.starttls()
    s.login(from_email, password)
    msg = MIMEText(html_report, 'html', 'utf-8')
    msg['Subject'] = Header(u'🇧🇷 Relatório de parlamentares', 'utf-8')
    msg['From'] =  'Legislei <{}>'.format(from_email)
    msg['To'] = email
    s.sendmail(from_email, email, msg.as_string())
    s.quit()
    logging.info('Email enviado para {}'.format(email))

def send_push_notification(user_token, reports):
    """
    Sends push notification to given token with short reports

    :param user_token: FCM token
    :type user_token: String
    :param reports: Lists of reports to be sent
    :type reports: List[Relatorio.to_dict()]
    """
    http = urllib3.PoolManager(
        cert_reqs='CERT_REQUIRED',
        ca_certs=certifi.where()
    )
    reduced_reports = []
    for report in reports:
        reduced_report = deepcopy(report)
        reduced_report["orgaos"] = len(report["orgaos"]) if report["orgaos"] else 0
        reduced_report["proposicoes"] = len(report["proposicoes"]) if report["proposicoes"] else 0
        reduced_report["eventosPresentes"] = len(report["eventosPresentes"]) if report["eventosPresentes"] else 0
        reduced_report["eventosPrevistos"] = len(report["eventosPrevistos"]) if report["eventosPrevistos"] else 0
        reduced_report["eventosAusentes"] = len(report["eventosAusentes"]) if report["eventosAusentes"] else 0
        reduced_reports.append(reduced_report)
    notification = {
        "notification": {
            "title": "Relatórios de parlamentares",
            "subtitle": "Chegaram seus relatórios periódicos de seus parlamentares",
            "body": "Chegaram seus relatórios periódicos de seus parlamentares"
        },
        "data": {
            "reports": reduced_reports
        },
        "priority": "NORMAL",
        "to": user_token
    }
    response = http.request(
        "POST",
        "https://fcm.googleapis.com/fcm/send",
        headers={
            'Authorization': 'key={}'.format(fcm_access_token),
            'Content-Type': 'application/json'
        },
        body=json.dumps(notification, default=str).encode('utf-8')
    )
    try:
        formatted_response = json.loads(response.data.decode('utf-8'))
    except json.JSONDecodeError:
        logging.error("Erro de decodificacao JSON do retorno do FCM")
        logging.error(response.data.decode('utf-8'))
        return False
    logging.debug(len(json.dumps(notification["data"], default=str).encode('utf-8')))
    logging.debug(formatted_response)
    if (response.status == 200 and 'error' not in formatted_response['results'][0]):
        logging.info('Notificacao padrao enviada para {}'.format(user_token))
        return True
    elif (formatted_response['results'][0] == {'error': 'MessageTooBig'}):
        logging.warning('Notificacao padrao muito longa para {}'.format(user_token))
        notification['data'] = {'reportsIds': [r['_id'] for r in reports]}
        logging.debug(notification)
        response = http.request(
            "POST",
            "https://fcm.googleapis.com/fcm/send",
            headers={
                'Authorization': 'key={}'.format(fcm_access_token),
                'Content-Type': 'application/json'
            },
            body=json.dumps(notification, default=str).encode('utf-8')
        )
        formatted_response = json.loads(response.data.decode('utf-8'))
        if (response.status == 200 and 'error' not in formatted_response['results'][0]):
            logging.info('Notificacao alternativa enviada para {}'.format(user_token))
            return True
    logging.error('Nao foi possivel enviar notificacao para {}'.format(user_token))
    logging.error(formatted_response)
    return False
