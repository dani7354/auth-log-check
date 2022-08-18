#!/usr/bin/env python3
from bs4 import BeautifulSoup, Tag
from email.header import Header
from email.mime.text import MIMEText
import smtplib
import ssl

NOTIFICATION_EMAIL_TEMPLATE = "./email_templates/notification.html"
HTML_TABLE_ID = "records"
HTML_TR = "tr"


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
        all_records = self._sort_records_by_date(new_records)

        email_body = EmailNotificationService._read_html_template(NOTIFICATION_EMAIL_TEMPLATE)

        soup = self._create_table(email_body, all_records)

        mime_text_message = MIMEText(soup.__str__(), 'html', 'utf-8')
        subject = f"auth-log-check: new auth log entries"
        mime_text_message['Subject'] = Header(subject, 'utf-8')
        mime_text_message['From'] = self.configuration.mail_sender
        mime_text_message['To'] = self.configuration.mail_recipient

        return mime_text_message

    @classmethod
    def _create_table(cls, html_template_str, records) -> BeautifulSoup:
        soup = BeautifulSoup(html_template_str, "html.parser")

        table_tag = soup.select_one(f"#{HTML_TABLE_ID}")

        table_header_row = soup.new_tag("tr")
        table_tag.append(table_header_row)

        for new_record in records:
            table_row = cls._create_table_row(soup, new_record)
            table_tag.append(table_row)

        return soup

    @staticmethod
    def _create_table_row(soup, record) -> Tag:
        tr_tag = soup.new_tag("tr")

        time_td = soup.new_tag("td")
        time_td.string = record.datetime

        type_td = soup.new_tag("td")
        type_td.string = record.get_type_name()

        ip_td = soup.new_tag("td")
        ip_td.string = record.src_ip

        port_td = soup.new_tag("td")
        port_td.string = record.src_port

        id_td = soup.new_tag("td")
        id_td.string = record.id

        tr_tag.append(time_td)
        tr_tag.append(type_td)
        tr_tag.append(ip_td)
        tr_tag.append(port_td)
        tr_tag.append(id_td)

        return tr_tag

    @staticmethod
    def _sort_records_by_date(new_records) -> list:
        all_records = []
        for type_id, records_and_type in new_records.items():
            records_only = [r[1] for r in records_and_type]
            all_records.extend(records_only)

        all_records.sort(key=lambda r: r.datetime)

        return all_records

    def _send_email(self, email_str) -> None:
        context = ssl.create_default_context()
        with smtplib.SMTP(host=self.configuration.smtp_host, port=self.configuration.smtp_port) as mail_server:
            mail_server.starttls(context=context)
            mail_server.login(self.configuration.smtp_user, self.configuration.smtp_password)
            mail_server.send_message(email_str)

    def send_email_notification(self, new_records) -> None:
        email_str = self._create_message_str(new_records)
        self._send_email(email_str)

    @staticmethod
    def _read_html_template(path) -> str:
        with open(path, "r", encoding="utf-8") as template_file:
            template = template_file.read()

            return template
