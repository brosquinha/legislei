import logging
import smtplib
import unittest
from unittest.mock import patch

from legislei.send_reports import send_email, uses_ssl


class TestSendReports(unittest.TestCase):

    def setUp(self):
        logging.disable(logging.CRITICAL)

    def tearDown(self):
        logging.disable(logging.NOTSET)
    
    @patch("smtplib.SMTP_SSL" if uses_ssl else "smtplib.SMTP")
    def test_send_email(
            self,
            mock_SMTP
    ):
        #Não consegui nem encontrei como mockar Header e MIMEText...
        class FakeSMTP():
            def __init__(self, *args, **kwargs):
                pass
            def starttls(self):
                self.starttls_called = True
            def ehlo(self):
                pass
            def login(self, *args):
                self.login_args = args
            def sendmail(self, *args):
                self.sendmail_args = args
            def quit(self):
                self.quit_called = True

        mock_SMTP.side_effect = FakeSMTP

        send_email("test@test.com", "<html>Report</html>")

        self.assertEqual(1, mock_SMTP.call_count)
