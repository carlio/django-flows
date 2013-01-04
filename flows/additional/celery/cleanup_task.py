
from celery.task import periodic_task

@periodic_task(run_every=crontab(minute='0', hour='3'))
def cleanup_expired_tasks():
    count = StateModel.objects.remove_expired_state()
    logger = cleanup_expired_tasks.get_logger()
    logger.info("Deleted %s expired tasks' state" % count)