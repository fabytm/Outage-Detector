from outagedetector import initial_config as config
from outagedetector import outage_detector as outage

import argparse


def main(sysargv=None):
    parser = argparse.ArgumentParser(description="Find out internet or power outage downtime!")
    parser.add_argument('--init', dest='init', help='Meant for first run only', action='store_true')
    parser.add_argument('--run', dest='run', help='Must be used in conjunction with --notify',
                        choices={"boot", "scheduled"})
    parser.add_argument('--notify', dest='notify', help='Must be used in conjunction with --run',
                        choices={"mail", "notification"})

    args = parser.parse_args()

    if args.init:
        config.initialize()
    elif args.run and args.notify:
        outage.check_power_and_internet(args.run, args.notify)


if __name__ == "__main__":
    main()
