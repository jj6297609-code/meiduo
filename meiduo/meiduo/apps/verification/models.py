
from django.db import models
from rest_framework.views import APIView

class SMSCodeView(APIView):
    def get(self, request, mobile):
        pass
