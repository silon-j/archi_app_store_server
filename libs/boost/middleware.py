import json
import threading
import time
import traceback
import uuid
from django.utils.deprecation import MiddlewareMixin
from loguru import logger
from .utils import underscoreize, camelize

REQUEST_POST_PROCESS_TYPES = ('application/x-www-form-urlencoded', 'multipart/form-data')
ALLOWED_POST_TYPE_METHODS = ('POST', 'PATCH', 'PUT')
ALLOWED_GET_TYPE_METHODS = ('GET', 'DELETE')

class HandleExceptionMiddleware(MiddlewareMixin):
    """
    处理视图中函数异常
    """

    def process_exception(self, request, exception):
        traceback.print_exc()
        trace_back = traceback.format_exc()
        logger.error(trace_back)


class AutoRequestPostMiddleware(MiddlewareMixin):
    """
    自动处理请求参数，将表单及json请求均转移至request.POST
    请将该中间件放置在进入视图之前，参数前期处理之后
    """

    def process_request(self, request):
        if request.method in ALLOWED_POST_TYPE_METHODS and request.content_type not in REQUEST_POST_PROCESS_TYPES:
            request.POST = request.body
        return request


class CamelToSnakeMiddleware(MiddlewareMixin):
    """请求及返回参数序列化，进行驼峰和蛇形互转
    """

    def process_request(self, request):
        if request.method in ('POST', 'PATCH', 'PUT'):
            try:
                data = json.loads(request.body.decode('utf-8'))
                snake_case_data = underscoreize(data)
                request._body = snake_case_data
            except json.JSONDecodeError:
                # 如果解析失败，可能是非JSON格式的数据，不做处理
                pass
        elif request.method in ('GET', 'DELETE'):
            new_data = underscoreize(request.GET)
            request.GET = new_data
        else:
            raise NotImplementedError(f"Unsupported request method: {request.method}")

    def process_response(self, request, response):
        if 'application/json' in response['Content-Type']:
            content = response.content.decode('utf-8')
            modified_content = camelize(json.loads(content))
            modified_content_en = json.dumps(modified_content).encode('utf-8')
            response.content = modified_content_en
        return response


class LogRequestMiddleware(MiddlewareMixin):
    """请求过程日志
    """

    def __init__(self, get_response):
        super().__init__(get_response)
        self.get_response = get_response

    def process_request(self, request):
        request_id = str(uuid.uuid4())
        threading.current_thread().name = request_id
        meta_info = f'"{request.method} {request.get_full_path()} {request.META.get("SERVER_PROTOCOL")}" {request.META.get("CONTENT_LENGTH") or 0}'
        logger.info(meta_info)
        request.request_id = request_id
        request.start_time = time.time()

    def process_response(self, request, response):
        end_time = time.time()
        duration = end_time - request.start_time
        logger.info(f"Request processed in {duration:.2f} seconds. Response status code: {response.status_code}")
        return response
