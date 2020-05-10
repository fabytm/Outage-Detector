from pushbullet import PushBullet, errors


def push_to_iOS(title, body, pb_key):
    pb = PushBullet(pb_key)

    pb.push_note(title, body)