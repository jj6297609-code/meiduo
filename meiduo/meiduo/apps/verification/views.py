from random import randint

from django_redis import get_redis_connection
from django.shortcuts import render
from rest_framework.views import APIView
from meiduo.libs.yuntongxun.sms import CCP
from rest_framework.response import Response
class SMSCodeView(APIView):
    def get(self, request, mobile):
        sms_code = '%06d' % randint(0, 999999)
        redis_conn=get_redis_connection('verify_code')
        redis_conn.setex('sms_%s' % mobile,300,sms_code)
        CCP().send_template_sms(mobile,[sms_code,5],1)
        return Response({'message':'OK'})