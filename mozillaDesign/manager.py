from testbot.decorators import notification, get_job, heartbeat, report

@notification
def manager_notification(notification, request, db):
    # db.create( document for manager )
    return []

@get_job
def get_job_for_manager(manager, request, db):
    
    return #[job to connect to device]

# @report
# def report_for_manager(device, request, db):
#     pass

@heartbeat
def manager_heartbeat(device, request, db):
    return device