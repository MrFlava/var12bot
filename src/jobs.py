import logging

from telegram.error import Unauthorized, BadRequest

from src.models import BlockSession
from src.models import User

logger = logging.getLogger(__name__)


def start_check_blocked_job(job_queue):
    stop_check_blocked_job(job_queue)
    job_queue.run_repeating(check_blocked_job, 60 * 120, first=0, name="check_blocked_job")
    logging.info("Check blocked users job started...")


def stop_check_blocked_job(job_queue):
    for job in job_queue.get_jobs_by_name("check_blocked_job"):
        job.schedule_removal()
        logging.info("Check blocked users job stopped...")


def check_blocked_job(context):
    users = BlockSession.query(User).all()
    for user in users:
        try:
            context.bot.send_chat_action(user.chat_id, 'typing')
        except (Unauthorized, BadRequest):
            user.deactivate()
            BlockSession.add(user)

    BlockSession.commit()
