import json
import os
import requests
import socket
import sys

import getpass
import keyring
import keyring.backend
from keyrings.alt.file import PlaintextKeyring

from outagedetector import cron_scheduling
from outagedetector import pushnotification as push
from outagedetector import send_mail as mail


def curate_input(shown_message, expected_values):
    result = input(shown_message)
    if result in expected_values:
        return result.lower()
    else:
        return curate_input("You need to input one of the following: {}. Try again! ".format(expected_values),
                            expected_values)

def initialize():
    config_path = os.path.join(os.path.expanduser("~"), ".config/outagedetector")
    if not os.path.exists(config_path):
        os.makedirs(config_path)
    if os.path.exists(os.path.join(config_path, "config.json")):
        result = curate_input("Configuration file already exists. Would you like to reconfigure the script? (y/n) ",
                              ("y", "n"))
        if result != "y":
            print("Alright, script should be ready to run. If you run into issues, run the initialization process "
                  "again")
            exit(1)

    json_data = {}
    print("We are going to walk you through setting up this script!")
    notification_type = curate_input("Would you like to be alerted of an outage through a notification"
                                     " on your phone, through mail, or through ifttt? ",
                                     ("notification", "mail", "ifttt"))
    json_data["notification_type"] = notification_type
    if notification_type == "mail":
        mail_working = False
        failed_attempts = 0
        while not mail_working:
            sender_mail_address = None
            while sender_mail_address is None:
                sender_mail_address = mail.check_mails(input("Please input the mail address you want to send the "
                                                             "notification mail from: "))
            json_data["sender"] = sender_mail_address
            keyring.set_keyring(PlaintextKeyring())
            keyring.set_password("Mail-OutageDetector", json_data["sender"],
                                 getpass.getpass("Type in your password: "))

            receiver_mail_addresses = None
            while receiver_mail_addresses is None:
                receiver_mail_addresses = mail.check_mails(input("Please input the mail addresses "
                                                                 "(separated by a comma) to which you want to send "
                                                                 "the notification: "))
            json_data["receivers"] = receiver_mail_addresses

            if "gmail" in json_data["sender"]:
                json_data["smtp_server"] = "smtp.gmail.com"
                json_data["port"] = 465
            elif "yahoo" in json_data["sender"]:
                json_data["smtp_server"] = "smtp.mail.yahoo.com"
                json_data["port"] = 465
            else:
                json_data["smtp_server"] = input("Please enter the SMTP server of your mail provider "
                                                 "(you can look it up online): ")
                port_number = ""
                while not port_number.isdigit():
                    port_number = input("Type in the port number of the SMTP server: ")
                json_data["port"] = port_number
            password = keyring.get_password("Mail-OutageDetector", json_data["sender"])
            try:
                mail.send_mail(json_data["sender"], json_data["receivers"], "Testing mail notification",
                               "Mail sent successfully!", json_data["smtp_server"], password, json_data["port"])
                mail_working = True
                print("Mail has been successfully sent, check your mailbox!")
            except mail.SMTPAuthenticationError as e:
                failed_attempts += 1
                if failed_attempts >= 3:
                    print("Too many failed attempts, exiting script, try again later!")
                    exit(1)
                if "BadCredentials" in str(e):
                    print(e)
                    print("Wrong user/password or less secure apps are turned off")
                elif "InvalidSecondFactor" in str(e):
                    print(e)
                    print("Two factor authentification is not supported! Turn it off and try again!")
            except socket.gaierror:
                print("No internet connection, try again later!")
                exit(1)

    elif notification_type == "notification":
        pushbullet_working = False
        failed_attempts = 0
        while not pushbullet_working:
            try:
                keyring.set_keyring(PlaintextKeyring())
                keyring.set_password("PushBullet-OutageDetector", "pushbullet",
                                     getpass.getpass("Input your PushBullet API key: "))
                pushbullet_key = keyring.get_password("PushBullet-OutageDetector", "pushbullet")
                print("Trying to send a notification through PushBullet!")
                push.push_to_iOS("Testing PushBullet Key", "Test is successful!", pushbullet_key)
                pushbullet_working = True
                print("Notification has been successfully sent, check your phone!")
            except push.errors.InvalidKeyError:
                failed_attempts += 1
                if failed_attempts >= 3:
                    print("Too many failed attempts, exiting script, try again later!")
                    exit(1)
                print("Key is not valid, try again!")

            except requests.exceptions.ConnectionError:
                print("No internet, try reconnecting and running the script again!")
                exit(1)

    elif notification_type == "ifttt":
        ifttt_working = False
        failed_attempts = 0
        while not ifttt_working:
            try:
                ifttt_name = input("Input your IFTTT event name: ")
                keyring.set_keyring(PlaintextKeyring())
                keyring.set_password("IFTTT-OutageDetector", ifttt_name, getpass.getpass("Input your IFTTT API key: "))
                api_key = keyring.get_password("IFTTT-OutageDetector", ifttt_name)
                print("Trying to send a notification through IFTTT!")
                push.push_to_ifttt(ifttt_name, api_key, "Testing IFTTT")
                ifttt_work = curate_input("Did you get the notification? (y/n) ", ("y", "n"))
                if ifttt_work == "y":
                    ifttt_working = True
                else:
                    failed_attempts += 1
                    if failed_attempts >= 3:
                        print("Too many failed attempts, exiting script, try again later!")
                        exit(1)
                    print("Check to make sure you followed the steps correctly and try again.")

            except requests.exceptions.ConnectionError:
                print("No internet, try reconnecting and running the script again!")
                exit(1)
        json_data["ifttt_event"] = ifttt_name
    
    json_data["house_address"] = input("Enter a description of the run location (used to tell you in the "
                                       "{} where the outage happened): ".format(notification_type))
    with open(os.path.join(config_path, 'config.json'), 'w+') as json_file:
        json.dump(json_data, json_file)

    crontab_edit = curate_input("Would you like to setup the script to run automatically "
                                "(it will run at boot time and at 5 minute intervals)? (y/n)", ("y", "n"))
    if crontab_edit == "y":
        exec_path = os.path.join(os.path.dirname(sys.executable), "outage_detector")
        cron_scheduling.schedule_job(exec_path, "--run scheduled --notify {}".format(notification_type), config_path, 5)
        cron_scheduling.schedule_job(exec_path, "--run boot --notify {}".format(notification_type), config_path,
                                     at_boot=True)


if __name__ == '__main__':
    initialize()
