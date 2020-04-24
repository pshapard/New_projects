# Author: Patrick Shapard
# Created: 04/22/2020
# Python script to send emails with and without attachments

# If you don't have an email account to use, issue the command below to run on your local host.
# python -m smtpd -c DebuggingServer -n localhost:1025

"""Email_variables is a file which contains username and password
   of the email account that will be used to send the emails.  For security reasons, 
   store login credentials in a separate file and import them in this script.  Or, you can store
   login creds in emvironment variables and use the os.environ module to read the username and password."""

import os
import smtplib
import imghdr
from Email_variables import EMAIL_ADDRESS, EMAIL_PASSWORD, EMAIL_SERVER, TO_RECEIVER, CC_RECEIVER, email_body, email_subject

files = ['image file to attach. example:  C:\\Folder\\image.jpg']

def EmailConstructor():
    """Function to construct email message with attachment and send it. """
    msg = EmailMessage()
    msg['Subject'] = email_subject
    msg['From'] = EMAIL_ADDRESS
    msg['To'] = TO_RECEIVER
    msg['Cc'] = CC_RECEIVER
    msg.set_content(email_body)
    
    for file in files:
        with open(file, 'rb') as f:
            data_file = f.read()
    
         msg.add_attachment(data_file, maintype='image', subtype=file_type, filename=image.jpg'])
    
    with smtplib.SMTP_SSL(EMAIL_SERVER, 465) as smtp:
        smtp.login(EMAIL_ADDRESS, EMAIL_PASSWORD)
        smtp.send_message(msg)


def main():
    EmailConstructor()

if __name__ == '__main__':
    main()