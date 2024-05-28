import os
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from dotenv import load_dotenv
from twilio.rest import Client


class NotificationManager:
    """This class is responsible for sending notifications."""

    def __init__(self) -> None:
        load_dotenv()
        self.account_sid = os.getenv("TWILIO_ACCOUNT_SID")
        self.auth_token = os.getenv("TWILIO_AUTH_TOKEN")
        self.client = Client(self.account_sid, self.auth_token)
        self.email_user = os.getenv("MY_EMAIL")
        self.email_pass = os.getenv("MAIL_APP_PASS")

    def send_sms(self, message: str, to_phone: str):
        """Send an SMS with the given message.

        Args:
            message (str): The message to send.
            to_phone (str): The recipient's phone number.
        """
        message = self.client.messages.create(
            body=message,
            from_=os.getenv("TWILIO_PHONE_NUMBER"),
            to=to_phone,
        )
        print(message.sid)

    def send_email(
        self, subject: str, body: str, recipient_email: str, html: bool = False
    ):
        """Send an email with the given subject and body.

        Args:
            subject (str): The subject of the email.
            body (str): The body of the email.
            recipient_email (str): The recipient's email address.
            html (bool): If True, send the email as HTML. Default is False.
        """
        msg = MIMEMultipart()
        msg['From'] = self.email_user
        msg['To'] = recipient_email
        msg['Subject'] = subject
        if html:
            msg.attach(MIMEText(body, 'html'))
        else:
            msg.attach(MIMEText(body, 'plain'))

        with smtplib.SMTP("smtp.gmail.com", port=587) as connection:
            connection.starttls()
            connection.login(user=self.email_user, password=self.email_pass)
            connection.send_message(msg)
