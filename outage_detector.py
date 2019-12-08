import os
import sys
from datetime import datetime, timedelta
import socket
import json
import pushnotification as push
import send_mail as mail

timestamp_format = "%d-%m-%Y %H-%M-%S"


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


internet_connected = check_internet_connection()

try:
    if sys.argv[1] == "boot":   # if script is executed at start up, assume there was a power outage
        just_booted = True      # this assumption holds up if system will be up 24/7
    elif sys.argv[1] == "scheduled":
        just_booted = False
    if sys.argv[2] == "notification":
        send_notification = True
    elif sys.argv[2] == "mail":
        send_notification = False
except IndexError:
    print("You need to give two arguments when calling the script!")
    exit(1)

if not send_notification:
    try:
        with open("config.json") as json_file:
            mail_json = json.load(json_file)
            sender = mail_json["sender"]
            receivers = mail_json["receivers"]
            smtp_server = mail_json["smtp_server"]
            password = mail_json["password"]
    except FileNotFoundError:
        print("Mail will not be sent, there is no config file in the folder.")

current_timestamp = datetime.now()
current_timestring = datetime.strftime(current_timestamp, timestamp_format)

try:
    with open("last_timestamp.txt") as file:
        read_string = file.read()
except FileNotFoundError:
    read_string = ""
    print("File doesn't exist, creating it now!")

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

periodicity = extract_run_periodicity(sys.argv[1],
                                      last_argument,
                                      current_timestamp,
                                      last_power_timestamp,
                                      last_periodicity)

with open("last_timestamp.txt", 'w+') as file:
    if internet_connected:
        file.write("{},{},{},{}".format(current_timestring, current_timestring, sys.argv[1], periodicity))
    else:
        file.write("{},{},{},{}".format(current_timestring, last_internet_timestring, sys.argv[1], periodicity))


if internet_connected:
    if just_booted:
        power_outage_time = int((current_timestamp - last_power_timestamp).total_seconds() / 60)
        if periodicity > 0:
            min_outage_time = max(range(0, power_outage_time + 1, periodicity))
        else:
            min_outage_time = 0
        print("Power was out for {} to {} minutes at {}".format(min_outage_time, power_outage_time, current_timestring))
        if send_notification:
            push.push_to_iOS("Power outage",
                             "Power was out for {} to {} minutes.".format(min_outage_time, power_outage_time),
                             "pb_key.txt")
        else:
            mail.send_mail(sender, receivers, "Power outage", "Power was out for {} to {} minutes."
                           .format(min_outage_time, power_outage_time), smtp_server, password)

    if not last_power_timestring == last_internet_timestring:
        last_internet_timestamp = datetime.strptime(last_internet_timestring, timestamp_format)
        internet_downtime = int((current_timestamp - last_internet_timestamp).total_seconds() / 60)
        if periodicity > 0:
            min_outage_time = max(range(0, internet_downtime + 1, periodicity))
        else:
            min_outage_time = 0
        print("Internet was down for {} to {} minutes at {}".format(min_outage_time, internet_downtime,
                                                                    current_timestring))
        if send_notification:
            push.push_to_iOS("Internet down",
                             "Internet has been down for {} to {} minutes.".format(min_outage_time, internet_downtime),
                             "pb_key.txt")
        else:
            mail.send_mail(sender, receivers, "Internet down", "Internet has been down for {} to {} minutes."
                           .format(min_outage_time, internet_downtime), smtp_server, password)

print("Script has run at {}. Internet connected: {}. Just booted: {}.".format(current_timestring, internet_connected,
                                                                              just_booted))
