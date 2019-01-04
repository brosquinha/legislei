import smtplib
import unittest
from send_reports import send_email, uses_ssl
from unittest.mock import patch

class TestSendReports(unittest.TestCase):

    @patch("builtins.print")
    @patch("smtplib.SMTP_SSL" if uses_ssl else "smtplib.SMTP")
    def test_send_email(
            self,
            mock_SMTP,
            mock_print
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