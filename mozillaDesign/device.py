from testbot.decorators import notification, get_job, heartbeat, report

@notification
def device_notification(notification, request, db):
    return #[job to connect to device]

@get_job
def get_job_for_device(device, request, db):
    # do db lookup
    return job

@report
def report_for_device(device, request, db):
    pass

@heartbeat
def device_heartbeat(device, request, db):
    return device

