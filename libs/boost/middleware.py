import traceback
from django.utils.deprecation import MiddlewareMixin


class HandleExceptionMiddleware(MiddlewareMixin):
    """
    处理视图中函数异常
    """

    def process_exception(self, request, exception):
        traceback.print_exc()
