import secrets
import string
import random
from apps.account.models import Account, LoginLog, EmailAuthCodeForWhat, AccountEmailAuthCode, AccountEmailAuthLog
from libs.boost.parser import Argument, JsonParser
from libs.boost.http import JsonResponse
from django.views.generic import View
from django.conf import settings
from django.utils import timezone
from datetime import timedelta
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
from django.db import transaction


class RequestMailVerifyView(View):

    VERIFY_CODE_LENGTH = 5
    VERIFY_CODE_EXPIRED = 5

    @swagger_auto_schema(
        operation_description="处理邮箱验证码请求",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'email': openapi.Schema(type=openapi.TYPE_STRING, description='邮箱地址'),
                'for_what': openapi.Schema(
                    type=openapi.TYPE_STRING, 
                    enum=['REGISTER', 'PASSWORD'], 
                    description='验证码用途'
                ),
            },
            required=['email', 'for_what']
        )
        # TODO 添加返回值描述
    )
    def get(self, request) -> JsonResponse:
        parser = JsonParser(
            Argument('email', str),
            Argument('for_what', data_type=EmailAuthCodeForWhat)
            )
        email: str = parser.parse(request.body).email
        for_what: EmailAuthCodeForWhat = parser.parse(request.body).for_what

        if (for_what == EmailAuthCodeForWhat.REGISTER):
            return self._request_register_verify(email)
        elif (for_what == EmailAuthCodeForWhat.PASSWORD):
            return self._change_password(email)
        else:
            return JsonResponse(error_message='未知的请求')

    def _change_password(self, email: str) -> JsonResponse:
        '''
        重置密码的发送验证码逻辑
        '''
        account: Account = Account.objects.filter(email=email).first()
        if account is None:
            return JsonResponse(error_message='用户不存在')
        code = self.__generate_verification_code()
        with transaction.atomic():
            email_auth_code = AccountEmailAuthCode.objects.filter(email=email, for_what=EmailAuthCodeForWhat.PASSWORD).first()
            if email_auth_code is None:
                # 不存在则创建
                email_auth_code = AccountEmailAuthCode(
                    email=email,
                    code=code, 
                    is_valid=True,
                    expired = timezone.now() + timedelta(minutes=self.VERIFY_CODE_EXPIRED),
                    for_what=EmailAuthCodeForWhat.PASSWORD
                    )
            else:
                email_auth_code.code = code
            # 发送验证码
            # TODO: 发送验证码

            # 创建发送日志
            email_auth_log = AccountEmailAuthLog(
                email=email,
                code=code,
                is_success=False,
                for_what=EmailAuthCodeForWhat.PASSWORD
                )
            email_auth_code.save()
            email_auth_log.save()
            return JsonResponse(message='验证码已发送')
        
    
    def _regist_new_account(self, email: str) -> JsonResponse:
        '''
        注册新用户的发送验证码逻辑
        '''
        account: Account = Account.objects.filter(email=email).first()
        if account is None:
            return JsonResponse(error_message='用户已存在')
        code = self.__generate_verification_code()
        with transaction.atomic():
            email_auth_code = AccountEmailAuthCode.objects.filter(email=email, for_what=EmailAuthCodeForWhat.REGISTER).first()
            if email_auth_code is None:
            # 不存在则创建
                email_auth_code = AccountEmailAuthCode(
                    email=email,
                    code=code, 
                    is_valid=True,
                    expired = timezone.now() + timedelta(minutes=self.VERIFY_CODE_EXPIRED),
                    for_what=EmailAuthCodeForWhat.REGISTER
                    )
            else:
                email_auth_code.code = code
            # 发送验证码
            # TODO: 发送验证码

            # 创建发送日志
            email_auth_log = AccountEmailAuthLog(
                email=email,
                code=code,
                is_success=False,
                for_what=EmailAuthCodeForWhat.REGISTER
            )
            email_auth_code.save()
            email_auth_log.save()
            return JsonResponse(message='验证码已发送')
    
    def __generate_verification_code(self, length=5) -> str:
        '''
        生成5位验证码, 大写字母和数字
        '''
        characters = string.ascii_uppercase + string.digits
        return ''.join(random.choice(characters) for _ in range(length))