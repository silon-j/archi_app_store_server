from django.conf import settings
from django.utils.deprecation import MiddlewareMixin
from django.utils import timezone
from loguru import logger
from apps.account.models import Account
from const.error import ErrorType
from libs.boost.http import HttpStatus, JsonResponse

class AuthenticationMiddleware(MiddlewareMixin):
    """用户认证
    """
    def get_current_account(self, request):
        """获取当前请求的用户"""
        
        account = None
        access_token = request.headers.get('X-Token') or request.GET.get('X-Token')
        if access_token is None:
            logger.error(f"权限校验未通过，缺少X-Token: {access_token}")
        if access_token and len(access_token) == 32:
            account = Account.objects.filter(access_token=access_token).first()
        return account

    def process_request(self, request):
        # 请求地址满足 AUTHENTICATION_EXCLUDES，或符合正则表达，则不使用该中间件验证请求
        if request.path in settings.AUTHENTICATION_EXCLUDES:
            return None
        elif any(x.match(request.path) for x in settings.AUTHENTICATION_EXCLUDES if hasattr(x, 'match')):
            return None

        account = self.get_current_account(request)
        if account is not None:
            if account.is_active and account.token_expired >= timezone.now():
                request.account = account
                # 可自行定制token更新规则
                account.token_expired = timezone.now() + timezone.timedelta(seconds=settings.AUTHENTICATION_EXPIRE_TIME)
                account.save()
                return None
        return JsonResponse(errType=ErrorType.TOKEN_EXPIRED, status=HttpStatus.HTTP_401_UNAUTHORIZED)
