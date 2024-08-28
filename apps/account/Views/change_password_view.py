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

class ChangePasswordView(View):
    
    # ERROR MSG
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

        if error:
            # 客户端没有发送所需的参数
            return JsonResponse(error_type=ErrorType.REQUEST_ILLEGAL, status_code=HttpStatus.HTTP_400_BAD_REQUEST)
        
        # 检查用户是否存在
        account = Account.objects.filter(username=form.username).first()
        if account is None:
            # 用户不存在
            return JsonResponse(error_type=ErrorType.ACCOUNT_NOT_EXIST, status_code=HttpStatus.HTTP_404_NOT_FOUND)

        vertify_code = AccountEmailAuthCode.objects.filter(
            email=account.email,
            for_what = EmailAuthCodeForWhat.PASSWORD.value,
            expired__gt = timezone.now(),
            is_valid = True
            ).order_by('-id').first()
        
        if vertify_code and vertify_code.code == form.verify_code:
            # 修改密码哈希，清空token
            account.password_hash = Account.make_password(form.password)
            account.access_token = None
            account.save()
            vertify_code.is_valid = False
            vertify_code.save()
            return JsonResponse(data=self.__CHANGE_SUCCESS__, status_code=HttpStatus.HTTP_201_CREATED)
        else:
            return JsonResponse(error_type=ErrorType.VERIFY_CODE_ERROR, status_code=HttpStatus.HTTP_404_NOT_FOUND)

            