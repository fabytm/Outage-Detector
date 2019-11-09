from pushbullet import PushBullet



def push_to_iOS(title, body, pb_key_filename):
    with open(pb_key_filename) as pb_key_file:
        pb_key = pb_key_file.read()

    pb = PushBullet(pb_key)

    pb.push_note(title,body)