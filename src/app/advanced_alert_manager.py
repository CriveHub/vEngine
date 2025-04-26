import smtplib
import requests
from email.mime.text import MIMEText
from logging_config import logger

class AdvancedAlertManager:
    def __init__(self, slack_webhook, smtp_server, smtp_port, smtp_user, smtp_password, email_from, email_to):
        self.slack_webhook = slack_webhook
        self.smtp_server = smtp_server
        self.smtp_port = smtp_port
        self.smtp_user = smtp_user
        self.smtp_password = smtp_password
        self.email_from = email_from
        self.email_to = email_to
    
    def send_slack_alert(self, message):
        payload = {"text": message}
        try:
            response = requests.post(self.slack_webhook, json=payload, timeout=5)
            if response.status_code != 200:
                logger.error("Errore Slack: %s", response.text)
        except Exception as e:
            logger.error("Eccezione in Slack alert: %s", e)
    
    def send_email_alert(self, subject, message):
        msg = MIMEText(message)
        msg['Subject'] = subject
        msg['From'] = self.email_from
        msg['To'] = self.email_to
        try:
            with smtplib.SMTP(self.smtp_server, self.smtp_port, timeout=10) as server:
                server.starttls()
                server.login(self.smtp_user, self.smtp_password)
                server.sendmail(self.email_from, [self.email_to], msg.as_string())
        except Exception as e:
            logger.error("Errore in invio email alert: %s", e)
    
    def send_sms_alert(self, message):
        logger.info("SMS Alert inviato (stub): %s", message)
    
    def send_alert(self, subject, message):
        self.send_slack_alert(message)
        self.send_email_alert(subject, message)
        self.send_sms_alert(message)
        logger.info("Alert inviato: %s - %s", subject, message)

default_alert_manager = AdvancedAlertManager(
    slack_webhook="https://hooks.slack.com/services/XXX/YYY/ZZZ",
    smtp_server="smtp.example.com",
    smtp_port=587,
    smtp_user="alert@example.com",
    smtp_password="password",
    email_from="alert@example.com",
    email_to="admin@example.com"
)