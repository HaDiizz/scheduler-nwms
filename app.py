from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from time import sleep
from modules.host import host_down_handler
from modules.service import service_down_handler
from modules.access_point import accessPoint_down_handler
import models


models.init_mongoengine()


def main():
    scheduler = BackgroundScheduler()
    scheduler = BackgroundScheduler()
    scheduler.start()

    trigger = CronTrigger(
        year="*", month="*", day="*", hour="*", minute="*", second="0"
    )
    scheduler.add_job(
        host_down_handler,
        trigger=trigger,
        name="host_down_handler",
    )
    scheduler.add_job(
        service_down_handler,
        trigger=trigger,
        name="service_down_handler",
    )
    scheduler.add_job(
        accessPoint_down_handler,
        trigger=trigger,
        name="accessPoint_down_handler",
    )

    try:
        while True:
            sleep(5)
    except (KeyboardInterrupt, SystemExit):
        print("Shutting down...")
        scheduler.shutdown()


if __name__ == '__main__':
    main()
