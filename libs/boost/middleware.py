import json
import threading
import time
import traceback
import uuid
from django.utils.deprecation import MiddlewareMixin
from loguru import logger
from .utils import underscoreize, camelize


class HandleExceptionMiddleware(MiddlewareMixin):
    """
    处理视图中函数异常
    """

    def process_exception(self, request, exception):
        traceback.print_exc()


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
