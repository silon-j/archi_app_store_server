import secrets
import string
import random
from apps.account.models import Account, LoginLog, EmailAuthCodeChoice, AccountEmailAuthCode
from libs.boost.parser import Argument, JsonParser
from libs.boost.http import JsonResponse
from libs.boost.http import HttpStatus
from libs.email.netease import MailServer
from const.error import ErrorType
from django.views.generic import View
from django.conf import settings
from django.utils import timezone
from datetime import timedelta
from django.db import transaction
from utils.utils import generate_random_str
from django.conf import settings
from smtplib import SMTPRecipientsRefused
import loguru

__EMAIL_SUBJECT__ = "数字化工具库-验证码"

def __generate_mail_content(email: str, verify_code: str) -> str:
    '''
    生成邮件内容
    '''
    content =  """
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <title>Email Verification Code</title>
        </head>
        <body>
            <h2>验证码通知</h2>
            <p>您已选择 <u>{email}</u> 作为您的邮箱账户，为验证此电子邮箱属于您，请在您的邮箱验证界面输入下方6位验证码：</p>
            <p id="verification-code">{code}</p>
            <p>此验证码将于{time}分钟后失效，请您尽快完成验证。</p>
        </body>
        </html>
    """.format(email=email, code=verify_code, time=settings.VERIFY_CODE_EXPIRED)
    return content

def send_verify_code(verify_code: str, email: str):
    '''
    向指定邮箱发送验证码
    '''
    mail_server = MailServer()
    mail_server.login()
    mail_server.send([email], __EMAIL_SUBJECT__, __generate_mail_content(email, verify_code), [])
    mail_server.quit()


class RegisterVerifyCode(View):

    def get(self, request)->JsonResponse:
        form, err = JsonParser(
            Argument('email', data_type =str, required=True, filter_func=lambda email: email.endswith('@ecadi.com')),
            ).parse(request.GET)
        '''
        注册新用户的发送验证码逻辑
        '''
        if err:
            return JsonResponse(error_type=ErrorType.REQUEST_ILLEGAL)
        is_account_exist: bool = Account.objects.filter(email=form.email).exists()

        if is_account_exist:
            return JsonResponse(error_type=ErrorType.ACCOUNT_EXIST)
        
        code = generate_random_str(6, True)
        email_auth_code = AccountEmailAuthCode(
            email=form.email,
            code=code, 
            is_valid=True,
            is_success=False,
            expired = timezone.now() + timedelta(minutes=settings.VERIFY_CODE_EXPIRED),
            code_choice=EmailAuthCodeChoice.REGISTER
            )
        
        try:
            # 发送验证码
            send_verify_code(email_auth_code.code, email_auth_code.email)
            email_auth_code.save()
            return JsonResponse(data='验证码已发送', status_code=HttpStatus.HTTP_200_OK)
        except SMTPRecipientsRefused:
            return JsonResponse(error_type=ErrorType.ACCOUNT_MAIL_DONT_EXIST)
        except Exception as e:
            loguru.logger.warning(str(e))
            return JsonResponse(error_message=e)
        
class ChangePasswordVerifyCode(View):

    def get(self, request)-> JsonResponse:
        form, err = JsonParser(
            Argument('username', data_type =str, required=True),
            Argument('email', data_type=str, required=True)
            ).parse(request.GET)
        
        if err:
            return JsonResponse(error_type=ErrorType.REQUEST_ILLEGAL)
        
        account: Account = Account.objects.filter(email=form.email, username=form.username).first()
        if account is None:
            return JsonResponse(error_type=ErrorType.ACCOUNT_NOT_EXIST)

        # 生成随机码        
        code = generate_random_str(6, True)
        email_auth_code = AccountEmailAuthCode(
            email=form.email,
            code=code, 
            is_valid=True,
            is_success=False,
            expired = timezone.now() + timedelta(minutes=settings.VERIFY_CODE_EXPIRED),
            code_choice=EmailAuthCodeChoice.PASSWORD
            )

        # 发送验证码
        send_verify_code(email_auth_code.code, email_auth_code.email)

        email_auth_code.save()
        return JsonResponse(data='验证码已发送', status_code=HttpStatus.HTTP_200_OK)
    
