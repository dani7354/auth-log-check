#!/usr/bin/env python3
from bs4 import BeautifulSoup
from email.header import Header
from email.mime.text import MIMEText
from records import Record
import smtplib
import ssl


NOTIFICATION_EMAIL_TEMPLATE = "./email_templates/notification.html"
EMAIL_TEMPLATE_ROOT_ID = "root"


class EmailConfiguration:
    def __init__(self, smtp_host, smtp_port, smtp_user, smtp_password, mail_sender, mail_recipient):
        self.smtp_host = smtp_host
        self.smtp_port = smtp_port
        self.smtp_user = smtp_user
        self.smtp_password = smtp_password
        self.mail_sender = mail_sender
        self.mail_recipient = mail_recipient


class EmailNotificationService:
    def __init__(self, configuration):
        self.configuration = configuration

    def _create_message_str(self, new_records) -> MIMEText:
        email_body = EmailNotificationService._read_html_template(NOTIFICATION_EMAIL_TEMPLATE)
        soup = BeautifulSoup(email_body, "html.parser")
        root_tag = soup.select_one(f"#{EMAIL_TEMPLATE_ROOT_ID}")

        for type_name, records in new_records.items():
            if len(records) == 0:
                continue
            record = records[0][1]

            type_name_tag = soup.new_tag("h3")
            type_name_tag.string = record.get_type_name()
            root_tag.append(type_name_tag)

            list_tag = soup.new_tag("ul")
            root_tag.append(list_tag)

            for new_record in records:
                li_tag = soup.new_tag("li")
                li_tag.string = new_record[1].__str__()
                list_tag.append(li_tag)

        mime_text_message = MIMEText(soup.__str__(), 'html', 'utf-8')
        subject = f"auth-log-check: new auth log entries"
        mime_text_message['Subject'] = Header(subject, 'utf-8')
        mime_text_message['From'] = self.configuration.mail_sender
        mime_text_message['To'] = self.configuration.mail_recipient

        return mime_text_message

    def _send_email(self, email_str) -> None:
        context = ssl.create_default_context()
        with smtplib.SMTP(host=self.configuration.smtp_host, port=self.configuration.smtp_port) as mail_server:
            mail_server.starttls(context=context)
            mail_server.login(self.configuration.smtp_user, self.configuration.smtp_password)
            mail_server.send_message(email_str)

    def send_email_notification(self, new_records):
        email_str = self._create_message_str(new_records)
        self._send_email(email_str)

    @staticmethod
    def _read_html_template(path) -> str:
        with open(path, "r", encoding="utf-8") as template_file:
            template = template_file.read()

            return template
