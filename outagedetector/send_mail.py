import email, ssl
from smtplib import SMTP_SSL, SMTPAuthenticationError
from email import encoders
from email.mime.base import MIMEBase
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import re


def check_mails(mails):
    regex = '^\w+([\.-]?\w+)*@\w+([\.-]?\w+)*(\.\w{2,3})+$'
    mail_list = mails.split(',')
    mail_addresses = []
    for mail in mail_list:
        check_result = re.search(regex, mail)
        if not check_result:
            return None
        mail_addresses.append(mail)

    mail_addresses_string = ",".join(mail_addresses)

    return mail_addresses_string


def send_mail(sender, receivers, subject, body, smtp_server, password, port=465):
    # Create a multipart message and set headers
    message = MIMEMultipart()
    message["From"] = sender
    message["To"] = receivers
    message["Subject"] = subject
    message["Bcc"] = receivers  # Recommended for mass emails

    # Add body to email
    message.attach(MIMEText(body, "plain"))

    text = message.as_string()

    # Log in to server using secure context and send email
    context = ssl.create_default_context()
    with SMTP_SSL(smtp_server, port, context=context) as server:
        server.login(sender, password)
        server.sendmail(sender, receivers.split(','), text)




