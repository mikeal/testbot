from testbot.decorators import notification

@notification
def mobile_build_notification(notification, request, db):
    jobs = []
    return job