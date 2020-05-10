from datetime import datetime
import json
import os
from pathlib import Path
import socket

import keyring

from outagedetector import pushnotification as push
from outagedetector import send_mail as mail


def check_internet_connection():
    try:
        socket.create_connection(("www.google.com", 80))    # if connection to google fails, we assume internet is down
        return True
    except OSError:
        pass
    return False


# if power is on, script will run even if internet is down, therefore we only take into account the power timestamp
# from the last run in determining the periodicity of the script runs
def extract_run_periodicity(scheduled_now, last_scheduled, current_time, last_power_time, last_period):
    if scheduled_now == "scheduled" and last_scheduled == "scheduled":
        return int((current_time - last_power_time).total_seconds() / 60)
    else:
        return last_period


def check_power_and_internet(run, notification):
    if run == "boot":
        just_booted = True
    elif run == "scheduled":
        just_booted = False
    if notification == "notification":
        send_notification = True
    elif notification == "mail":
        send_notification = False

    config_path = os.path.join(os.path.expanduser("~"), ".config/outagedetector")
    address_available = False
    address = ""
    timestamp_format = "%d-%m-%Y %H-%M-%S"
    hour_minute_format = "%H:%M"

    internet_connected = check_internet_connection()

    if not send_notification:
        try:
            with open(os.path.join(config_path, "config.json")) as json_file:
                mail_json = json.load(json_file)
                sender = mail_json["sender"]
                receivers = mail_json["receivers"]
                smtp_server = mail_json["smtp_server"]
                password = keyring.get_password("Mail-OutageDetector", sender)
                if password is None:
                    print("Mail password not found, try running initial configuration again!")
                    exit(1)
                address = mail_json["house_address"]
        except FileNotFoundError:
            print("Mail will not be sent, there is no config file in the folder.")
        except KeyError:
            print("Config.json file doesn't have all fields (sender, receivers, smtp_server, house address")
    else:
        with open(os.path.join(config_path, "pb_key.txt"), 'r') as push_file:
            push_key = push_file.read()
        try:
            with open(os.path.join(config_path, "config.json")) as json_file:
                notification_json = json.load(json_file)
                address = notification_json["house_address"]
        except FileNotFoundError:
            print("Configuration file does not exist, try running the initial configuration again!")
        except KeyError:
            print("Config.json file doesn't have all fields, try running the initial configuration again!")

    if address:
        address_available = True

    current_timestamp = datetime.now()
    current_timestring = datetime.strftime(current_timestamp, timestamp_format)
    current_hour_min = datetime.strftime(current_timestamp, hour_minute_format)

    try:
        with open(os.path.join(config_path, "last_timestamp.txt")) as file:
            read_string = file.read()
    except FileNotFoundError:
        read_string = ""

    file_data = read_string.split(",")

    try:
        last_power_timestring = file_data[0]
        last_internet_timestring = file_data[1]
        last_argument = file_data[2]
        last_periodicity = int(file_data[3])
    except IndexError:
        last_power_timestring = current_timestring
        last_internet_timestring = current_timestring
        last_argument = "N/A"
        last_periodicity = 0

    last_power_timestamp = datetime.strptime(last_power_timestring, timestamp_format)

    periodicity = extract_run_periodicity(run,
                                          last_argument,
                                          current_timestamp,
                                          last_power_timestamp,
                                          last_periodicity)

    with open(os.path.join(config_path, "last_timestamp.txt"), 'w+') as file:
        if internet_connected:
            file.write("{},{},{},{}".format(current_timestring, current_timestring, run, periodicity))
        else:
            file.write("{},{},{},{}".format(current_timestring, last_internet_timestring, run, periodicity))

    if internet_connected:
        if just_booted:
            power_outage_time = int((current_timestamp - last_power_timestamp).total_seconds() / 60)
            if periodicity > 0:
                min_outage_time = max(range(0, power_outage_time + 1, periodicity))
            else:
                min_outage_time = 0
            notification = "Power was out for {} to {} minutes at {}.".format(min_outage_time, power_outage_time,
                                                                              current_hour_min)
            if address_available:
                notification += " Address: {}.".format(address)
            print("Power was out for {} to {} minutes at {}".format(min_outage_time, power_outage_time,
                                                                    current_timestring))
            if send_notification:
                push.push_to_iOS("Power outage", notification, push_key)
            else:
                mail.send_mail(sender, receivers, "Power outage", notification, smtp_server, password)

        if not last_power_timestring == last_internet_timestring:
            last_internet_timestamp = datetime.strptime(last_internet_timestring, timestamp_format)
            internet_downtime = int((current_timestamp - last_internet_timestamp).total_seconds() / 60)
            if periodicity > 0:
                min_outage_time = max(range(0, internet_downtime + 1, periodicity))
            else:
                min_outage_time = 0
            print("Internet was down for {} to {} minutes at {}".format(min_outage_time, internet_downtime,
                                                                        current_timestring))
            notification = "Internet has been down for {} to {} minutes at {}.".format(min_outage_time,
                                                                                       internet_downtime,
                                                                                       current_hour_min)
            if address_available:
                notification += " Address: {}.".format(address)
            if send_notification:
                push.push_to_iOS("Internet down", notification, push_key)
            else:
                mail.send_mail(sender, receivers, "Internet down", notification, smtp_server, password)

    print("Script has run at {}. Internet connected: {}. Just booted: {}.".format(current_timestring,
                                                                                  internet_connected,
                                                                                  just_booted))

