import smtplib
import unittest
from send_reports import send_email
from unittest.mock import patch

class TestSendReports(unittest.TestCase):

    @patch("smtplib.SMTP")
    def test_send_email(
            self,
            mock_SMTP,
    ):
        #Não consegui nem encontrei como mockar Header e MIMEText...
        class FakeSMTP():
            def __init__(self, *args, **kwargs):
                pass
            def starttls(self):
                self.starttls_called = True
            def login(self, *args):
                self.login_args = args
            def sendmail(self, *args):
                self.sendmail_args = args
            def quit(self):
                self.quit_called = True

        mock_SMTP.side_effect = FakeSMTP

        send_email("test@test.com", "<html>Report</html>")

        mock_SMTP.assert_called_once_with('smtp.gmail.com', 587)