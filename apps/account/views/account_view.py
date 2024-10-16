from apps.account.models import Account, EmailAuthCodeChoice, AccountEmailAuthCode, LoginLog
from libs.boost.parser import Argument, JsonParser
from libs.boost.http import JsonResponse, HttpStatus
from const.error import ErrorType
from django.views.generic import View
from django.conf import settings
from django.utils import timezone
from django.db.models import Q
from datetime import timedelta
from django.db import transaction
from utils.utils import get_client_ip
import uuid
import loguru

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
            return JsonResponse(error_type=ErrorType.REQUEST_ILLEGAL)
        
        # 检查用户是否存在
        account = Account.objects.filter(username=form.username).first()
        if account is None:
            # 用户不存在
            return JsonResponse(error_type=ErrorType.ACCOUNT_NOT_EXIST)

        vertify_code = AccountEmailAuthCode.objects.filter(
            email=account.email,
            code_choice = EmailAuthCodeChoice.PASSWORD,
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
            return JsonResponse(error_type=ErrorType.VERIFY_CODE_ERROR)

class RegisterView(View):
    
    __REGISTE_SUCCESS__ : str = "注册成功"

    def post(self, request) -> JsonResponse:
        '''
        注册一个用户
        '''
        form, error = JsonParser(
            Argument('username', data_type=str, required=True),
            Argument('fullname', data_type=str, required=False),
            Argument('department', data_type=str, required=True),
            Argument('email', data_type=str, required=True, filter_func=lambda email: email.endswith('@ecadi.com')),
            Argument('password', data_type=str, required=True),
            Argument('verify_code', data_type=str, required=True),
        ).parse(request.body)

        if error:
            # 客户端没有发送所需的参数
            return JsonResponse(error_type=ErrorType.REQUEST_ILLEGAL)
        
        # 检查用户或者邮箱是否存在
        exist_account: Account = Account.all_objects.filter((Q(email=form.email) | Q(username=form.username))).first()
        if exist_account:
            if exist_account.deleted_at is None:
                # 用户已存在
                return JsonResponse(error_type=ErrorType.ACCOUNT_EXIST)
        
        vertify_code = AccountEmailAuthCode.objects.filter(
            email=form.email,
            code_choice = EmailAuthCodeChoice.REGISTER,
            is_valid = True,
            is_success = False,
            expired__gt = timezone.now()
            ).order_by("-id").first()
        
        if  vertify_code and vertify_code.code == form.verify_code:
            if exist_account is None:
                # 从来没有过记录，新建一个用户
                new_account : Account = Account(
                    username=form.username,
                    fullname = form.fullname,
                    department = form.department,
                    email = form.email,
                    password_hash=Account.make_password(form.password)
                    )
                new_account.save()
            else:
                # 如果找到软删除用户，则恢复该用户
                exist_account.deleted_at = None
                exist_account.fullname = form.fullname
                exist_account.department = form.department
                exist_account.is_active = True
                exist_account.password_hash = Account.make_password(form.password)
                exist_account.save()

            vertify_code.is_valid = False
            vertify_code.is_success = True
            vertify_code.save()
            return JsonResponse(data=self.__REGISTE_SUCCESS__, status_code=HttpStatus.HTTP_201_CREATED)
        else:
            if vertify_code:
                vertify_code.is_valid = False
                vertify_code.save()
            return JsonResponse(error_type=ErrorType.VERIFY_CODE_ERROR)

class LoginView(View):

    __LOGIN_SUCCESS__ : str = "登录成功"

    def post(self, request) -> JsonResponse:
        
        form, error = JsonParser(
            Argument('username', data_type=str, required=True),
            Argument('password', data_type=str, required=True),
        ).parse(request.body)
        
        if error:
            return JsonResponse(error_type=ErrorType.REQUEST_ILLEGAL)
        
#       记录一次用户登录
        login_log = LoginLog(
            username=form.username,
            # 更新ip，使用utils里面的ip函数
            ip=get_client_ip(request),
            agent=request.META.get('HTTP_USER_AGENT', ''),
        )

        #匹配数据库是否一致,不一致则返回登录失败
        account: Account = Account.objects.filter(username=form.username).first()
        if account is None:
            # 用户名不存在
            login_log.message = ErrorType.ACCOUNT_NOT_EXIST.message
            login_log.is_success = False
            login_log.save()
            return JsonResponse(error_type=ErrorType.ACCOUNT_NOT_EXIST)
        
        if account.verify_password(form.password) == False:
            # 密码错误
            login_log.message = ErrorType.LOGIN_FAILED.message
            login_log.is_success = False
            login_log.save()
            return JsonResponse(error_type=ErrorType.LOGIN_FAILED)
        
        if not account.is_active:
             # 用户被ban了
            login_log.message = ErrorType.ACCOUNT_DISABLED.message
            login_log.is_success = False
            login_log.save()
            return JsonResponse(error_type=ErrorType.ACCOUNT_DISABLED)

        #如果数据一致则生成生成密钥给用户
        account.access_token = uuid.uuid4().hex
        account.token_expired = timezone.now() + timedelta(seconds=settings.AUTHENTICATION_EXPIRE_TIME)
        # 修改账户最后一次登录和IP
        account.last_ip = login_log.ip
        account.last_login = timezone.now()
        account.save()
        
        # 记录一次用户登录
        login_log.message = self.__LOGIN_SUCCESS__
        login_log.is_success = True
        login_log.save()

        return JsonResponse(data={"token": account.access_token, "username": account.username, "is_admin": account.can_admin & account.is_super }, status_code=HttpStatus.HTTP_201_CREATED)
    
class UserInfoView(View):
    def get(self, request) -> JsonResponse:
        current_user = request.account
        if current_user is None:
            return JsonResponse(error_type=ErrorType.ACCOUNT_NOT_EXIST)
        return JsonResponse(data={"username": current_user.username, "nickname": current_user.fullname, "avatarUrl": '', "is_admin": current_user.can_admin & current_user.is_super,  "email": current_user.email, 'department': current_user.department }, status_code=HttpStatus.HTTP_201_CREATED)
    