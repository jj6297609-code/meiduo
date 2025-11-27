from random import randint
import logging

from django_redis import get_redis_connection
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from redis.exceptions import RedisError

from . import constants
from celery_tasks.sms.tasks import send_sms_code

logger = logging.getLogger('django')

class SMSCodeView(APIView):
    def get(self, request, mobile):
        redis_conn = get_redis_connection('verify_code')

        # 先快速检查标志，避免不必要生成验证码
        try:
            send_flag = redis_conn.get(f'send_flag_{mobile}')
        except RedisError as e:
            logger.exception('读取 send_flag 失败: %s', e)
            return Response({'message': '服务器内部错误'}, status=status.HTTP_503_SERVICE_UNAVAILABLE)

        if send_flag:
            return Response({'message': '手机号频繁发送短信'}, status=status.HTTP_400_BAD_REQUEST)

        # 生成验证码
        sms_code = '%06d' % randint(0, 999999)
        print(sms_code)

        # 使用 pipeline 原子写入：set sms_key 并 set send_flag（使用 SET ... NX EX）
        try:
            pl = redis_conn.pipeline()
            # 存验证码（ex 为有效期，单位秒）
            pl.set(f'sms_{mobile}', sms_code, ex=constants.SMS_CODE_REDIS_EXPIRES)
            # 设置发送标记：只有当不存在时才设置，并带过期时间（避免使用 expire(..., NX)）
            pl.set(f'send_flag_{mobile}', 1, ex=constants.SEND_SMS_CODE_INTERVAL, nx=True)
            results = pl.execute()
        except RedisError as e:
            logger.exception('Redis 保存短信相关 key 失败: %s', e)
            return Response({'message': '服务器内部错误'}, status=status.HTTP_503_SERVICE_UNAVAILABLE)
        except Exception as e:
            logger.exception('保存短信键时发生意外错误: %s', e)
            return Response({'message': '服务器内部错误'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        # results 是一个列表，results[0] 对应第一个 set 返回（通常 True），results[1] 对应第二个 set 的返回
        # 第二个 set 在 key 已存在时会返回 False/None（表示未设置），表明此请求在并发竞争里未获胜
        send_flag_set = results[1]

        if not send_flag_set:
            # 并发情况下另一个请求已经设置了 send_flag，返回频繁提示
            return Response({'message': '手机号频繁发送短信'}, status=status.HTTP_400_BAD_REQUEST)

        # 若 send_flag_set 为真，则此次请求成功写入标志，可以发送短信（交给 celery）
        try:
            send_sms_code.delay(mobile, sms_code)
        except Exception as e:
            # 如果任务投递失败，记录日志；但验证码已写入 redis（可考虑补偿策略）
            logger.exception('发送短信任务投递失败: mobile=%s, error=%s', mobile, e)
            # 仍返回 OK 或根据你策略返回 500/503；这里返回 200 以免用户重复触发
            return Response({'message': 'OK'})

        return Response({'message': 'OK'})
