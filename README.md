# Outage Detector
Simple script meant to notify user if a power outage has occured or if the internet has been down.

## What it does

At every run it writes to a text file timestamps for power and internet, whether the last run was scheduled or at boot and the last calculated periodicity.

If the script was run after a boot up, it will assume there was a power outage (the system is meant to run 24/7, for example a Raspberry Pi Zero) and send a notification, approximating the power outage duration through the last known timestamp and calculated periodicity of the runs.

Internet downtime is detected if the 2 timestamps written to the file differ and the downtime is approximated again through the calculated periodicity. It is possible that an internet downtime is missed if the script is run too rarely.

## How to run it

The script is meant to be run periodically (ideally scheduled through a task scheduler, such as cron, on machines with Unix OSes).

Using the requirements.txt file you can install the required packages through pip.

You need to provide your own Pushbullet API key, which can be optained at: https://docs.pushbullet.com/#api-quick-start

Cron job template (script running every 5 minutes):

```
*/5 * * * * path/to/python/interpreter/python3 /path/to/project/outage_detector.py >> path/to/project/log.txt 2>path/to/project/errors.txt
```
