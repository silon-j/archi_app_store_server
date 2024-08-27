from django.http import HttpRequest
from django.views import View

from libs.boost.http import HttpStatus, JsonResponse
from libs.boost.parser import Argument, JsonParser
from loguru import logger

from utils.decorators import admin_required
from const.error import ErrorType

def age_filter(value):
    if value < 18:
        return False

def score_handler(value):
    if value < 60:
        return 60
    else:
        return value

def base_req(request):
    form, error = JsonParser(
        Argument('name',data_type=str, required=True, help='路径不能为空'),
        Argument('age',data_type=int, required=True, help="步骤不能为空", filter_func=age_filter),
        Argument('score', required=False, default=60, handler_func=score_handler),
    ).parse(request.GET)
    if error is not None:
        # 系统请求日志
        logger.debug('请求错误')
        # handler 会将参数处理后放入form
        return JsonResponse({'name': form.name, "score": form.score})
    return JsonResponse(error)


class ClassRequestView(View):
    """常用类视图：get、post、patch、put、delete
    """
    # 权限校验
    @admin_required
    def get(self, request: HttpRequest):
        form, error = JsonParser(
            Argument('name',data_type=str, required=True, help='路径不能为空'),
            Argument('age',data_type=int, required=True, help="步骤不能为空", filter_func=age_filter),
            Argument('score', required=False, default=60, handler_func=score_handler),
        ).parse(request.GET)
        if error is not None:
            # 返回指定的错误信息
            return JsonResponse(error_type=ErrorType.ACCOUNT_NOT_EXIST)
            # 返回自定义的错误信息
            return JsonResponse(error_message="自定义错误信息")
        return JsonResponse(error_message=error)


    def post(self, request: HttpRequest):
        form, error = JsonParser(
            Argument('name',data_type=str, required=True, help='路径不能为空'),
            Argument('age',data_type=int, required=True, help="步骤不能为空", filter_func=age_filter),
            Argument('score', required=False, default=60, handler_func=score_handler),
        ).parse(request.POST)
        if error is not None:
            return JsonResponse(
                # 该数据会被中间件转换为小驼峰输出。包括数据中的list 及dict
                data = {
                    'm_a': "1",
                    "m_b_C": 1,
                    "m_v_c": True,
                    "m_d": {
                        "m_d_a": 1,
                        "m_d_b": 2,
                        "m_d_c": [1, 2, 3, {"m_d_c_a": 1}]
                    },
                    "m_e": [
                        1,
                        {
                            "n_a": 1,
                            "n_B": 2,
                        }                
                    ]
                },
                status_code=HttpStatus.HTTP_200_OK
        )
        return JsonResponse(error_message=error)