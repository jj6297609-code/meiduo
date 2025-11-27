from rest_framework.views import exception_handler as drf_exception_handler
import logging
import traceback
import uuid
from django.db import DatabaseError
from redis.exceptions import RedisError
from rest_framework.response import Response
from rest_framework import status

logger = logging.getLogger('django')

def exception_handler(exc, context):
    """
    改进点：
    - 使用 logger.exception 记录完整 traceback 和上下文（view/request）
    - 生成 request_id，返回给客户端，方便关联日志
    - 区分 '存储/内存' 类错误返回 507，其它外部依赖问题返回 503
    - 不把异常细节暴露给客户端，只返回通用友好信息 + request_id
    """
    # 先尝试 DRF 默认的处理（比如 ValidationError 会生成 response）
    response = drf_exception_handler(exc, context)
    if response is None:
        view = context.get('view')
        request = context.get('request')
        request_id = str(uuid.uuid4())

        # 记录日志：包含 view、path、method、user（如果有）、异常及traceback
        log_extra = {
            'view': repr(view),
            'path': getattr(request, 'path', None),
            'method': getattr(request, 'method', None),
            'user': getattr(getattr(request, 'user', None), 'username', None),
            'request_id': request_id
        }
        # 记录完整 traceback
        tb = traceback.format_exc()
        logger.error('Unhandled exception in view=%s path=%s user=%s request_id=%s\nException: %s\nTraceback:\n%s',
                     log_extra['view'], log_extra['path'], log_extra['user'],
                     request_id, repr(exc), tb)

        # 如果是数据库或 redis 相关异常，归类返回
        if isinstance(exc, (DatabaseError, RedisError)):
            # 进一步区分是否为“存储/内存”相关错误（如 Redis OOM / 磁盘满）
            exc_msg = str(exc).lower()
            if 'oom' in exc_msg or 'no space left' in exc_msg or 'disk' in exc_msg:
                status_code = status.HTTP_507_INSUFFICIENT_STORAGE
            else:
                # 外部依赖出错（如 redis 连接失败或第三方接口异常）用 503 更合适
                status_code = status.HTTP_503_SERVICE_UNAVAILABLE

            response = Response({
                'message': '服务器内部错误',
                'request_id': request_id
            }, status=status_code)
        else:
            # 其它未处理异常，返回 500 并带 request_id
            response = Response({
                'message': '服务器内部错误',
                'request_id': request_id
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    return response
