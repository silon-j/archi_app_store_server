import secrets
import string
import random
from apps.account.models import Account, EmailAuthCodeForWhat, AccountEmailAuthCode
from libs.boost.http import HttpStatus
from libs.boost.parser import Argument, JsonParser
from libs.boost.http import JsonResponse
from django.views.generic import View
from django.conf import settings
from django.utils import timezone
from datetime import timedelta
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
from django.db import transaction

class RegisterView(View):
    
    # ERROR MSG
    __PARAM_ERROR__ : str = "请求参数错误"
    __USER_ALREADY_EXIST__ : str = "用户已存在"
    __NO_VERIFY_CODE__ : str =  "验证码不存在"
    __VERIFY_CODE_EXPIRE_ERROR__ : str = "验证码过期或错误"
    __REGISTE_SUCCESS__ : str = "注册成功"


    def post(self, request) -> JsonResponse:
        '''
        注册一个用户
        '''
        form, error = JsonParser(
            Argument('username', type=str, required=True),
            Argument('fullname', type=str, required=True),
            Argument('department', type=str, required=True),
            Argument('email', type=str, required=True, filter_func=lambda email: email.endswith('@ecadi.com')),
            Argument('password', type=str, required=True),
            Argument('verify_code', type=str, required=True),
        ).parse(request.body)

        if form is None:
            # 客户端没有发送所需的参数
            return JsonResponse(error_message=self.__PARAM_ERROR__ + "\n" + error)
        
        with transaction.atomic():
            # 检查用户是否存在
            account = Account.objects.filter(email=form.username).first()
            if account is not None:
                # 邮箱已存在
                return JsonResponse(error_message=self.__USER_ALREADY_EXIST__)
            
            vertify_code = AccountEmailAuthCode.objects.filter(email=form.email, for_what = EmailAuthCodeForWhat.REGISTER, is_valid = True).first()
            if vertify_code is None:
                # 数据库当中没有验证码
                return JsonResponse(error_message=self.__NO_VERIFY_CODE__)
            elif vertify_code.code != form.verify_code or vertify_code.expired<timezone.now:
                # 验证码错误或者过期
                return JsonResponse(error_message=self.__VERIFY_CODE_EXPIRE_ERROR__)

            new_account : Account = Account(
                username=form.username,
                fullname = form.fullname,
                department = form.department,
                email = form.email,
                password_hash=Account.make_password(form.password)
            )

            new_account.save()
            vertify_code.is_valid = False
            vertify_code.save()

            return JsonResponse(data=self.__REGISTE_SUCCESS__, status_code=HttpStatus.HTTP_201_CREATED)

            