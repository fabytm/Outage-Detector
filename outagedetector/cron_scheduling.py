import os
import sys

from crontab import CronTab


def schedule_job(script_path, script_arguments, output, minute_periodicity=0, hour_periodicity=0, at_boot=False):
    interpreter_path = sys.executable
    command = "{} {} {} >> {}/log.txt 2>{}/errors.txt".format(interpreter_path, script_path, script_arguments, output,
                                                              output)
    if at_boot:     # wait for internet connection
        command = "sleep 60 && " + command
    crontab = CronTab(user=True)
    cronjob = crontab.new(command=command)
    if at_boot:
        cronjob.every_reboot()
    elif hour_periodicity != 0 and hour_periodicity <= 23:
        cronjob.hour.every(hour_periodicity)
    elif minute_periodicity != 0 and minute_periodicity <= 59:
        cronjob.minute.every(minute_periodicity)
    crontab.write()

