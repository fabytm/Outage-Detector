import os
import sys
from datetime import datetime, timedelta
import socket
import pushnotification as push

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
        return int((last_power_time - current_time).total_seconds() / 60)
    else:
        return last_period


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
        push.push_to_iOS("Power outage",
                         "Power was out for {} to {} minutes.".format(min_outage_time, power_outage_time),
                         "pb_key.txt")

    if not last_power_timestring == last_internet_timestring:
        last_internet_timestamp = datetime.strptime(last_internet_timestring, timestamp_format)
        internet_downtime = int((current_timestamp - last_internet_timestamp).total_seconds() / 60)
        if periodicity > 0:
            min_outage_time = max(range(0, internet_downtime + 1, periodicity))
        else:
            min_outage_time = 0
        print("Internet was down for {} to {} minutes at {}".format(min_outage_time, internet_downtime,
                                                                    current_timestring))
        push.push_to_iOS("Internet down",
                         "Internet has been down for {} to {} minutes.".format(min_outage_time, internet_downtime),
                         "pb_key.txt")
