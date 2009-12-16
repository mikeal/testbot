from testbot.decorators import notification

@notification
def firefox_build_notification(notification, request, db):
    jobs = []
    return job