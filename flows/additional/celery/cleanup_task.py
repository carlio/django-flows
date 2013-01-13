
from celery.task import periodic_task
from celery.schedules import crontab
from flows.statestore.django_store import StateModel


@periodic_task(run_every=crontab(minute='*/5', hour='*'))
def cleanup_expired_tasks():
    count = StateModel.objects.remove_expired_state()
    logger = cleanup_expired_tasks.get_logger()
    logger.info("Deleted %s expired tasks' state" % count)