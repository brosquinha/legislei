import json
import logging
import os
import smtplib
from datetime import datetime
from email.header import Header
from email.mime.text import MIMEText

from legislei import settings
from legislei.services.inscricoes import Inscricao

smtp_server = os.environ.get("EMAIL_ENDPOINT", "smtp.gmail.com")
smtp_server_port = os.environ.get("EMAIL_PORT", "587")
from_email = os.environ.get("EMAIL_USR", None)
password = os.environ.get("EMAIL_PSW", None)
uses_ssl = os.environ.get("EMAIL_SSL", "False") in ['True', 'true']
uses_tls = os.environ.get("EMAIL_TLS", "True") in ['True', 'true']


def send_email(email, report):
    if uses_ssl:
        s = smtplib.SMTP_SSL(smtp_server, int(smtp_server_port))
    else:
        s = smtplib.SMTP(smtp_server, int(smtp_server_port))
    if uses_tls:
        s.starttls()
    s.login(from_email, password)
    msg = MIMEText(report, 'html', 'utf-8')
    msg['Subject'] = Header(u'🇧🇷 Relatório de deputado', 'utf-8')
    msg['From'] =  'Legislei <{}>'.format(from_email)
    msg['To'] = email
    s.sendmail(from_email, email, msg.as_string())
    s.quit()
    logging.info('Email enviado para {}'.format(email))


def check_reports_to_send():
    for inscricao in Inscricao().obter_todas_inscricoes():
        yield inscricao
