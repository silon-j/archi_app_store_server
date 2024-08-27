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

class ChangePasswordView(View):
    
    # ERROR MSG
    __PARAM_ERROR__ : str = "请求参数错误"
    __USER_NOT_EXIST__ : str = "用户不存在"
    __NO_VERIFY_CODE__ : str =  "验证码不存在"
    __VERIFY_CODE_EXPIRE_ERROR__ : str = "验证码过期或错误"
    __CHANGE_SUCCESS__ : str = "密码修改成功"


    def post(self, request) -> JsonResponse:
        '''
        修改密码
        '''
        form, error = JsonParser(
            Argument('username', data_type=str, required=True),
            Argument('password', data_type=str, required=True),
            Argument('verify_code', data_type=str, required=True),
        ).parse(request.body)

        if form is None:
            # 客户端没有发送所需的参数
            return JsonResponse(error_message=self.__PARAM_ERROR__ + "\n" + error, status_code=HttpStatus.HTTP_400_BAD_REQUEST)
        
        # 检查用户是否存在
        account = Account.objects.filter(username=form.username).first()
        if account is None:
            # 用户不存在
            return JsonResponse(error_message=self.__USER_NOT_EXIST__, status_code=HttpStatus.HTTP_404_NOT_FOUND)
        
        vertify_code = AccountEmailAuthCode.objects.filter(email=account.email, for_what = EmailAuthCodeForWhat.PASSWORD.value, is_valid = True).first()
        if vertify_code is None:
            # 数据库当中没有验证码
            return JsonResponse(error_message=self.__NO_VERIFY_CODE__, status_code=HttpStatus.HTTP_404_NOT_FOUND)
        elif vertify_code.code != form.verify_code or vertify_code.expired<timezone.now():
            # 验证码错误或者过期
            return JsonResponse(error_message=self.__VERIFY_CODE_EXPIRE_ERROR__, status_code=HttpStatus.HTTP_400_BAD_REQUEST)
        # 修改密码哈希，清空token
        account.password_hash = Account.make_password(form.password)
        account.access_token = None
        account.save()
        vertify_code.is_valid = False
        vertify_code.save()
        return JsonResponse(data=self.__CHANGE_SUCCESS__, status_code=HttpStatus.HTTP_201_CREATED)

            