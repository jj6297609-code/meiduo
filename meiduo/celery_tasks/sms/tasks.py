from ..sms.yuntongxun.sms import CCP
from ..sms import constants
from ..main import celery_app

@celery_app.task(name='send_sms_code')
def send_sms_code(mobile, sms_code):
    CCP.send_template_sms(mobile, [sms_code, constants.SMS_CODE_REDIS_EXPIRES // 60], 1)
