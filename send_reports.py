import json
import os
import settings
import smtplib
from datetime import datetime
from email.mime.text import MIMEText
from email.header import Header
from db import MongoDBClient

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
    mongo_db = MongoDBClient()
    subscription_col = mongo_db.get_collection('inscricoes')
    for inscricao in subscription_col.find():
        yield inscricao
