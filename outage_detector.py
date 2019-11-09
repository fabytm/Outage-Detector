import os
import sys
from datetime import datetime, timedelta
import socket
import pushnotification

timestamp_format = "%d-%m-%Y %H-%M-%S"


def check_internet_connection():
    try:
        socket.create_connection(("www.google.com", 80))    # if connection to google fails, we assume internet is down
        return True
    except OSError:
        pass
    return False


internet_connected = check_internet_connection()

try:
    if sys.argv[1] == "boot":   # if script is executed at start up, assume there was a power outage
        just_booted = True      # this assumption holds up if system will be up 24/7
    elif sys.argv[1] == "scheduled":
        just_booted = False
except IndexError:
    print("You need to give one argument!")
    exit(1)


current_timestamp = datetime.now()
current_timestring = datetime.strftime(current_timestamp, timestamp_format)

try:
    with open("last_timestamp.txt") as file:
        read_string = file.read()
except FileNotFoundError:
    read_string = ""
    print("File doesn't exist, creating it now!")

file_data = read_string.split(",")
last_power_timestring = file_data[0]
last_internet_timestring = file_data[1]

with open("last_timestamp.txt", 'w+') as file:
    if internet_connected:
        file.write("{},{}".format(current_timestring, current_timestring))
    else:
        file.write("{},{}".format(current_timestring, last_internet_timestring))


if internet_connected:
    if just_booted:
        last_power_timestamp = datetime.strptime(last_power_timestring, timestamp_format)
        power_outage_time = int((current_timestamp - last_power_timestamp).total_seconds() / 60)
        print("Power outage shorter than {} minutes detected at {}".format(power_outage_time, current_timestring))
        pushnotification.push_to_iOS("Power outage",
                                     "Power has been out for less than {} minutes".format(power_outage_time),
                                     "pb_key.txt")

    if not last_power_timestring == last_internet_timestring:
        last_internet_timestamp = datetime.strptime(last_internet_timestring, timestamp_format)
        internet_downtime = int((current_timestamp - last_internet_timestamp).total_seconds() / 60)
        print("Power outage shorter than {} minutes detected at {}".format(internet_downtime, current_timestring))
        pushnotification.push_to_iOS("Internet down",
                                     "Internet has been down for less than {} minutes".format(internet_downtime),
                                     "pb_key.txt")
