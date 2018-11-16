import json
import settings
import smtplib
import os
from datetime import datetime
from email.mime.text import MIMEText
from email.header import Header
from flask import render_template
from models.deputados import DeputadosApp

from_email = os.environ.get("GMAIL_USR", None)
password = os.environ.get("GMAIL_PSW", None)

def send_email(email, report):
    s = smtplib.SMTP('smtp.gmail.com', 587)
    s.starttls()
    s.login(from_email, password)
    msg = MIMEText(report, 'html', 'utf-8')
    msg['Subject'] = Header(u'🇧🇷 Relatório de deputado', 'utf-8')
    msg['From'] =  'Legislei <{}>'.format(from_email)
    msg['To'] = email
    s.sendmail(from_email, email, msg.as_string())
    s.quit()

def check_reports_to_send():
    arq = open("reports/subscription-list.json")
    subscription = json.loads(arq.read())
    return subscription
