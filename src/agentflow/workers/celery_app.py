from celery import Celery

from agentflow.core.config import Setting

setting = Setting()

celery_app = Celery(
    "agentflow", #the name of the celery aplication
    broker = setting.CELERY_BROKER_URL, # where the task messages are sent
    backend= setting.CELERY_RESULT_BACKEND, # like caching (result backend storage)
    include=[
        "agentflow.workers.tasks",
    ]

)

celery_app.conf.update(
    task_serializer="json", #task arguments json format
    result_serializer="json", # results as json
    accept_content=["json"], # accept only json
    task_track_started=True, 
    timezone="UTC",
    enable_utc=True,
    broker_connection_retry_on_startup=True, # Redis has a delay, worker tries again.
)