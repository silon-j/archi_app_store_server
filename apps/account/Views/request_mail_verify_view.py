import secrets
import string
import random
from apps.account.models import Account, LoginLog, EmailAuthCodeForWhat, AccountEmailAuthCode, AccountEmailAuthLog
from libs.boost.parser import Argument, JsonParser
from libs.boost.http import JsonResponse
from libs.boost.http import HttpStatus
from libs.email.netease import MailServer
from django.views.generic import View
from django.conf import settings
from django.utils import timezone
from datetime import timedelta
from django.db import transaction


class RequestMailVerifyView(View):

    VERIFY_CODE_LENGTH = 5
    VERIFY_CODE_EXPIRED = 5
    __EMAIL_SUBJECT__ = "数字化工具库-验证码"

    def get(self, request) -> JsonResponse:
        form, err = JsonParser(
            Argument('email', data_type =str),
            Argument('for_what', data_type=EmailAuthCodeForWhat)
            # Argument('for_what', data_type=[1,2,3],())
            ).parse(request.body)
        
        if (form.for_what == EmailAuthCodeForWhat.REGISTER):
            return self._regist_new_account(form.email)
        elif (form.for_what == EmailAuthCodeForWhat.PASSWORD):
            return self._change_password(form.email)
        else:
            return JsonResponse(error_message='未知的请求', status_code=HttpStatus.HTTP_400_BAD_REQUEST)


    def _change_password(self, email: str) -> JsonResponse:
        '''
        重置密码的发送验证码逻辑
        '''
        account: Account = Account.objects.filter(email=email).first()
        if account is None:
            return JsonResponse(error_message='用户不存在')
        code = self.__generate_verification_code()

        email_auth_code = AccountEmailAuthCode.objects.filter(email=email, for_what=EmailAuthCodeForWhat.PASSWORD.value).first()
        if email_auth_code is None:
            # 不存在则创建
            email_auth_code = AccountEmailAuthCode(
                email=email,
                code=code, 
                is_valid=True,
                expired = timezone.now() + timedelta(minutes=self.VERIFY_CODE_EXPIRED),
                for_what=EmailAuthCodeForWhat.PASSWORD.value
                )
        else:
            email_auth_code.code = code
            email_auth_code.is_valid = True
            email_auth_code.expired = timezone.now() + timedelta(minutes=self.VERIFY_CODE_EXPIRED)
        
        # 发送验证码
        self.__send_verify_code(email_auth_code.code, email_auth_code.email)
        # 创建发送日志
        email_auth_log = AccountEmailAuthLog(
            email=email,
            code=code,
            is_success=False,
            for_what=EmailAuthCodeForWhat.PASSWORD.value
            )
        email_auth_code.save()
        email_auth_log.save()
        return JsonResponse(data='验证码已发送', status_code=HttpStatus.HTTP_200_OK)


    def _regist_new_account(self, email: str) -> JsonResponse:
        '''
        注册新用户的发送验证码逻辑
        '''
        account: Account = Account.objects.filter(email=email).first()
        if account is not None:
            return JsonResponse(error_message='用户已存在')
        
        code = self.__generate_verification_code()
        
        email_auth_code = AccountEmailAuthCode.objects.filter(email=email, for_what=EmailAuthCodeForWhat.REGISTER.value).first()
        if email_auth_code is None:
        # 不存在则创建
            email_auth_code = AccountEmailAuthCode(
                email=email,
                code=code, 
                is_valid=True,
                expired = timezone.now() + timedelta(minutes=self.VERIFY_CODE_EXPIRED),
                for_what=EmailAuthCodeForWhat.REGISTER.value
                )
        else:
            email_auth_code.code = code
            email_auth_code.is_valid = True
            email_auth_code.expired = timezone.now() + timedelta(minutes=self.VERIFY_CODE_EXPIRED)
        # 创建发送日志
        email_auth_log = AccountEmailAuthLog(
            email=email,
            code=code,
            is_success=False,
            for_what=EmailAuthCodeForWhat.REGISTER.value
        )
        email_auth_code.save()
        email_auth_log.save()
        
        # 发送验证码
        self.__send_verify_code(email_auth_code.code, email_auth_code.email)
        return JsonResponse(data='验证码已发送', status_code=HttpStatus.HTTP_200_OK)
    

    def __generate_verification_code(self, length=5) -> str:
        '''
        生成5位验证码, 大写字母和数字
        '''
        characters = string.ascii_uppercase + string.digits
        return ''.join(random.choice(characters) for _ in range(length))
    

    def __send_verify_code(self, verify_code: str, email: str) -> None:
        '''
        向指定邮箱发送验证码
        '''
        mail_server = MailServer()
        mail_server.login()
        mail_server.send([email], self.__EMAIL_SUBJECT__, self.__generate_mail_content(verify_code),[])
        mail_server.quit()


    def __generate_mail_content(self, verify_code: str) -> str:
        '''
        生成邮件内容
        '''
        content = f"您的验证码为：{verify_code}。{self.VERIFY_CODE_EXPIRED}分钟内有效。"
        return content