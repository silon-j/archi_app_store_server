from functools import wraps
from typing import Callable
from libs.boost.http import JsonResponse, HttpStatus
from const.error import ErrorType


def admin_required(f):
    """
    管理员权限装饰器。

    确保只有具有管理员权限或超级用户权限的用户才能访问装饰的视图函数。

    参数:
    - f: 需要管理员权限的视图函数。

    返回:
    - 如果用户没有管理员权限或超级用户权限，将返回 `ErrorType.ADMIN_REQUIRED` 错误。
    - 如果用户具有足够的权限，将执行原始的视图函数。
    """
    @wraps(f)
    def wrapper(cls, request, *args, **kwargs):
        # 提取请求中的用户信息
        account = request.account
        if not account:
            return JsonResponse(error_type=ErrorType.AUTH_FAILED, status_code=HttpStatus.HTTP_401_UNAUTHORIZED)

        # 检查用户是否具有管理员或超级用户权限
        if not account.can_admin: # and not account.is_super:
            # 如果用户没有必要的权限，返回错误响应
            return JsonResponse(error_type=ErrorType.PERMIT_FAILED, status_code=HttpStatus.HTTP_403_FORBIDDEN)
        # 用户具有足够的权限，调用原始的视图函数
        return f(cls, request, *args, **kwargs)
    # 返回包装后的函数
    return wrapper


def permission_required(check_func: Callable):
    """
    自定义装饰器，用于检查用户权限

    该装饰器接受一个检查函数作为参数，用于判断用户是否满足某种权限。
    如果用户不满足权限要求，则返回一个指定的错误响应。

    参数:
    - check_func: 一个函数，用于检查用户是否满足权限要求; 返回值必须是布尔值！

    返回:
    一个装饰器函数，用于包裹需要权限检查的视图函数。
    """

    def decorator(f):

        @wraps(f)
        def wrapper(cls, request, *args, **kwargs):
            """
            包装函数，执行权限检查并调用视图函数。

            参数:
            - cls: 类视图的类对象。
            - request: HTTP请求对象，包含用户信息。
            - *args, **kwargs: 传递给视图函数的额外参数和关键字参数。

            返回:
            视图函数的返回值，或权限不足时返回的错误响应。
            """
            # 使用传入的check_func来检查用户是否有权限
            if not check_func(request):
                # 如果用户权限不足，返回权限不足的错误响应, 默认返回错误类型为ADMIN_REQUIRED, 可以根据需要修改
                return JsonResponse(error_type=ErrorType.PERMIT_FAILED, status_code=HttpStatus.HTTP_403_FORBIDDEN)
            # 如果用户权限足够，调用原视图函数并返回其结果
            return f(cls, request, *args, **kwargs)

        # 返回包装后的函数作为装饰器结果
        return wrapper

    # 返回装饰器工厂函数作为custom_decorator的结果
    return decorator
