import secrets
from apps.account.models import Account, LoginLog
from libs.boost.parser import Argument, JsonParser
from libs.boost.http import JsonResponse, HttpStatus
from django.views.generic import View
from django.conf import settings
from django.utils import timezone
from datetime import timedelta
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi

class LoginView(View):

    # ERROR MSG
    __USER_NDEFINE__ : str =  "用户不存在"
    __PASSWORD_ERROR__ : str = "密码错误"
    __LOGIN_SUCCESS__ : str = "登录成功"

    @swagger_auto_schema(
        operation_description="处理用户登录的请求",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'username': openapi.Schema(type=openapi.TYPE_STRING, description='用户名'),
                'password': openapi.Schema(type=openapi.TYPE_STRING, description='密码'),
            },
            required=['username', 'password']
        )
        # TODO 添加返回值描述
    )
    def post(self, request) -> JsonResponse:
        
        form, error = JsonParser(
            Argument('username', data_type=str, required=True),
            Argument('password', data_type=str, required=True),
        ).parse(request.body)
        
        if error:
            return JsonResponse(error_message=error, status_code=HttpStatus.HTTP_400_BAD_REQUEST)
        
#       记录一次用户登录
        login_log = LoginLog(
            username=form.username,
            ip=request.META.get('REMOTE_ADDR', ''),
            agent=request.META.get('HTTP_USER_AGENT', ''),
        )

        #匹配数据库是否一致,不一致则返回登录失败
        account = Account.objects.filter(username=form.username).first()
        if account == None:
            # 用户名不存在
            login_log.message = self.__USER_NDEFINE__
            login_log.is_success = False
            login_log.save()
            return JsonResponse(error_message=self.__USER_NDEFINE__, status_code=HttpStatus.HTTP_404_NOT_FOUND)
        
        elif account.verify_password(form.password) == False:
            # 密码错误
            login_log.message = self.__PASSWORD_ERROR__
            login_log.is_success = False
            login_log.save()
            return JsonResponse(error_message=self.__PASSWORD_ERROR__, status_code=HttpStatus.HTTP_400_BAD_REQUEST)
        
        #如果数据一致则生成生成密钥给用户
        account.access_token = secrets.token_urlsafe(24)
        account.token_expired = timezone.now() + timedelta(seconds=settings.AUTHENTICATION_EXPIRE_TIME)
        # 修改账户最后一次登录和IP
        account.last_ip = login_log.ip
        account.last_login = timezone.now()
        account.save()
        
        # 记录一次用户登录
        login_log.message = self.__LOGIN_SUCCESS__
        login_log.is_success = True
        login_log.save()

        return JsonResponse(data=account.access_token, status_code=HttpStatus.HTTP_202_ACCEPTED)
    
    
