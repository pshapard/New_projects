# Author: Patrick Shapard
# Created: 04/22/2020
# Python script to send emails with and without attachments

#If you don't have an email account to use, issue the command below to run on your local host.
#python -m smtpd -c DebuggingServer -n localhost:1025


import os
import smtplib
from email.message import EmailMessage

RECEIVER = 'pshapard@outlook.com'
EMAIL_ADDRESS = 'shapardpatrick@gmail.com'
EMAIL_PASSWORD = 'Tr0jans7'

"""
with smtplib.SMTP('smtp.gmail.com', 587) as smtp:
    smtp.ehlo()
    smtp.starttls()
    smtp.ehlo()

    smtp.login(EMAIL_ADDRESS, EMAIL_PASSWORD)

    subject = 'This is my first try at send email using python'
    body = 'Wow, this is so cool using python to send an email'

    msg = f'Subject: {subject}\n\n{body}'

    smtp.sendmail(SENDER, EMAIL_ADDRESS, msg)
"""

msg = EmailMessage()
msg['Subject'] = 'Webex meeting set for 2:30'
msg['From'] = EMAIL_ADDRESS
msg['To'] = RECEIVER
msg.set_content("""This is to confirm our meeting at 2:30. Is this ok with you? 
                 Regards, \n 
                 Patrick.""")


with smtplib.SMTP_SSL('smtp.gmail.com', 465) as smtp:
    smtp.login(EMAIL_ADDRESS, EMAIL_PASSWORD)

    smtp.send_message(msg)