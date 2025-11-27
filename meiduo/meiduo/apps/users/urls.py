from django.urls import re_path
from rest_framework_jwt.views import obtain_jwt_token

from . import views

urlpatterns = [
    re_path(r'^users/$', views.UserView.as_view(), name='注册'),
    re_path(
        r'^usernames/(?P<username>\w{5,20})/count/$', views.UsernameCountView.as_view(), ),
    re_path(
        r'^mobiles/(?P<mobile>1[3-9]\d{9})/count/$', views.MobileCountView.as_view(), ),
    re_path(r'^authorizations/$',obtain_jwt_token),
]
