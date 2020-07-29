# Author: Patrick Shapard
# Created: 04/22/2020
# Python script to send emails with and without attachments

# If you don't have an email account to use, issue the command below to run on your local host.
# python -m smtpd -c DebuggingServer -n localhost:1025


import os
import smtplib
import imghdr
from email.message import EmailMessage

RECEIVER = 'pshapard@outlook.com'
EMAIL_ADDRESS = 'shapardpatrick@gmail.com'
EMAIL_PASSWORD = 'Tr0jans7'

msg = EmailMessage()
msg['Subject'] = 'Webex meeting set for 2:30'
msg['From'] = EMAIL_ADDRESS
msg['To'] = RECEIVER
msg.set_content('Resume attached')

files = ['C:\\Users\\shapard\\Pictures\\Coins\\AGE_1OZ.jpg','C:\\Users\\shapard\\Pictures\\Coins\\AGE_1OZ_Reverse.jpg']

for file in files:
    with open(file, 'rb') as f:
        data_file = f.read()
        file_type = imghdr.what(f.name)
        file_name = f.name

    msg.add_attachment(data_file, maintype='image', subtype=file_type, filename=file_name)

with smtplib.SMTP_SSL('smtp.gmail.com', 465) as smtp:
    smtp.login(EMAIL_ADDRESS, EMAIL_PASSWORD)

    smtp.send_message(msg)
