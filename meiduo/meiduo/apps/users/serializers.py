import re

import redis
from django_redis import get_redis_connection
from rest_framework import serializers

from .models import User
from rest_framework_jwt.settings import api_settings


class CreateUserSerializer(serializers.ModelSerializer):
    """
    用户注册序列化器：
    - password2, sms_code, allow 为额外写入字段（不映射到模型）
    - validate 做密码一致性、手机号格式、短信验证码、是否同意协议的校验
    - create 正确设置密码并返回带 token 的 user 对象
    """
    password2 = serializers.CharField(label='确认密码', write_only=True)
    sms_code = serializers.CharField(label='验证码', write_only=True)
    allow = serializers.CharField(label='同意协议', write_only=True)

    class Meta:
        model = User
        # 注意：password2 不属于模型字段，但我们在类中显式定义了它，这样可以放在 fields 里使用
        fields = ('id', 'username', 'password', 'password2', 'mobile', 'sms_code', 'allow',)
        read_only_fields = ('id',)
        extra_kwargs = {
            'username': {
                'min_length': 5,
                'max_length': 20,
                'error_messages': {
                    'min_length': '仅允许5-20字符的用户名',
                    'max_length': '仅允许5-20字符的用户名'
                }
            },
            'password': {
                'write_only': True,
                'min_length': 8,
                'max_length': 20,
                'error_messages': {
                    'min_length': '仅允许8-20字符的密码',
                    'max_length': '仅允许8-20字符的密码'
                }
            }
        }

    def validate_mobile(self, value):
        """校验手机号格式"""
        if not re.match(r'^1[3-9]\d{9}$', value):
            raise serializers.ValidationError('手机号格式有误')
        return value

    def validate_allow(self, value):
        """
        兼容前端传 'true' 字符串或布尔 True 等情况
        要求同意协议，否则报错
        """
        if str(value).lower() not in ('true', '1', 'yes', 'on'):
            raise serializers.ValidationError('请同意用户协议')
        return value

    def validate(self, attrs):
        """整体字段校验：密码一致性与短信验证码"""
        password = attrs.get('password')
        password2 = attrs.get('password2')
        if password != password2:
            raise serializers.ValidationError({'password2': '两次密码不一致'})

        mobile = attrs.get('mobile')
        sms_code = attrs.get('sms_code')

        # 从 redis 中取出真实验证码并比较
        try:
            redis_conn = get_redis_connection('verify_code')  # 若你的 redis 配置名不同，请修改
            real_sms_code = redis_conn.get(f'sms_{mobile}')
        except Exception:
            # 读取 redis 失败，建议返回通用错误或记录日志；这里返回验证码错误
            raise serializers.ValidationError({'sms_code': '验证码校验失败'})

        if real_sms_code is None:
            raise serializers.ValidationError({'sms_code': '验证码错误'})

        # real_sms_code 可能是 bytes 或 str
        if isinstance(real_sms_code, bytes):
            real_sms_code = real_sms_code.decode()

        if real_sms_code != sms_code:
            raise serializers.ValidationError({'sms_code': '验证码错误'})

        return attrs

    def create(self, validated_data):
        """
        创建用户：
        - 去掉不属于模型的字段（password2, sms_code, allow）
        - 通过 set_password 保存哈希密码
        - 生成 JWT token 并附加到返回的 user 对象（user.token）
        """
        # 删除非模型字段
        validated_data.pop('password2', None)
        validated_data.pop('sms_code', None)
        validated_data.pop('allow', None)

        password = validated_data.pop('password')

        # 使用 User model 创建用户并设置密码（兼容自定义 User）
        user = User(**validated_data)
        user.set_password(password)
        user.save()

        # 生成 JWT token（如果你使用 rest_framework_jwt）
        jwt_payload_handler = api_settings.JWT_PAYLOAD_HANDLER
        jwt_encode_handler = api_settings.JWT_ENCODE_HANDLER
        payload = jwt_payload_handler(user)
        token = jwt_encode_handler(payload)

        # 将 token 附加到 user 对象（序列化/返回时可取）
        user.token = token

        return user