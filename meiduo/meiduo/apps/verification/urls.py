
from django.urls import re_path
from verification import views

from meiduo.apps.verification.models import SMSCodeView

urlpatterns = [
    re_path(r'^sms_code/(?P<mobile>1[3-9]\d{9})/$', views.SMSCodeView.as_view()),
]