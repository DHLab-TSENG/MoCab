from datetime import datetime
import requests
from dateutil.relativedelta import relativedelta

from base.object_store import training_sets_table
from config import configObject as conf


def scheduled_jobs():
    """
    Description:
        This function is used to define the scheduled jobs.
    """
    return_list = []
    schedules = training_sets_table.get_training_set_schedule()
    for schedule in schedules:
        interval_time_obj = schedule["interval"]
        return_list.append({
            "id": schedule["model_name"],
            "func": "base.scheduler.jobs:call_api",
            "args": [schedule["model_name"]],
            "trigger": "interval",
            # "next_run_time": datetime.now() + relativedelta(seconds=10),
            "days": interval_time_obj.get_days_from_now(),
            "hours": interval_time_obj.get_hours(),
            "minutes": interval_time_obj.get_minutes(),
            "seconds": interval_time_obj.get_seconds()
        })
    return return_list


class Config(object):
    JOBS = scheduled_jobs()
    SCHEDULER_API_ENABLED = True


def call_api(model_name):
    """
    Description:
        This function is used to trigger the continuous training pipeline.
        It would be called by the scheduler.
    """
    api_url = f"http://localhost:{conf.get('flask_config').get('PORT')}{conf.get('base_urls').get('continuous_training_prefix')}/{model_name}"
    requests.get(api_url)
