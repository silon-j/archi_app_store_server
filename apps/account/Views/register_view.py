import secrets
import string
import random
from apps.account.models import Account, EmailAuthCodeForWhat, AccountEmailAuthCode
from libs.boost.http import HttpStatus
from libs.boost.parser import Argument, JsonParser
from libs.boost.http import JsonResponse
from const.error import ErrorType
from django.views.generic import View
from django.conf import settings
from django.utils import timezone
from datetime import timedelta
from django.db import transaction

class RegisterView(View):
    
    __REGISTE_SUCCESS__ : str = "注册成功"

    def post(self, request) -> JsonResponse:
        '''
        注册一个用户
        '''
        form, error = JsonParser(
            Argument('username', data_type=str, required=True),
            Argument('fullname', data_type=str),
            Argument('department', data_type=str, required=True),
            Argument('email', data_type=str, required=True, filter_func=lambda email: email.endswith('@ecadi.com')),
            Argument('password', data_type=str, required=True),
            Argument('verify_code', data_type=str, required=True),
        ).parse(request.body)

        if error:
            # 客户端没有发送所需的参数
            return JsonResponse(error_type=ErrorType.REQUEST_ILLEGAL, status_code=HttpStatus.HTTP_400_BAD_REQUEST)
        
        # 检查用户是否存在
        is_account_exist = Account.objects.filter(email=form.email).exists()
        if is_account_exist:
            # 用户已存在
            return JsonResponse(error_type=ErrorType.ACCOUNT_EXIST, status_code=HttpStatus.HTTP_400_BAD_REQUEST)
        
        vertify_code = AccountEmailAuthCode.objects.filter(
            email=form.email,
            for_what = EmailAuthCodeForWhat.REGISTER.value,
            is_valid = True,
            expired__gt = timezone.now()
            ).order_by("-id").first()
        
        if  vertify_code and vertify_code.code == form.verify_code:
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
        else:
            return JsonResponse(error_type=ErrorType.VERIFY_CODE_ERROR, status_code=HttpStatus.HTTP_400_BAD_REQUEST)
            
            