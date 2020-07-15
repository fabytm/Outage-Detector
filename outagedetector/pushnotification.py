from pushbullet import PushBullet, errors
import requests


def push_to_iOS(title, body, pb_key):
    pb = PushBullet(pb_key)

    pb.push_note(title, body)


def push_to_ifttt(ifttt_name, api_key, notification):
    requests.post(url = 'https://maker.ifttt.com/trigger/{}/with/key/{}'.format(ifttt_name, api_key), data = {'value1':notification})

