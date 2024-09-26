from django.views.generic import View
from django.http import HttpRequest
from apps.account.models import Account
from libs.boost.parser import Argument, JsonParser
from libs.boost.http import JsonResponse, HttpStatus
from utils.decorators import admin_required
from const.error import ErrorType
from django.utils import timezone


class AdminModifyAccount(View):
    
    @admin_required
    def patch(self, request: HttpRequest) -> JsonResponse:
        """
        修改账号、姓名、邮箱、权限

        Args:
            request (HttpRequest): 
            id: 账户主键，必须
            fullname：用户昵称，不必须
            email：邮箱，不必须，必须ecadi邮箱
            is_admin：是否管理员
        Returns:
            JsonResponse: _description_
        """
        form, error = JsonParser(
            Argument('id', data_type=int, required=True),
            # 工号绑定的用户名应该不能修改的，保证唯一性，仅用作验证，而不修改
            Argument('username', data_type=str, required=False),
            Argument('fullname', data_type=str, required=False),
            Argument('email', data_type=str, required=False, filter_func=lambda email: email.endswith('@ecadi.com')),
            Argument('is_admin', data_type=bool, required=False)
        ).parse(request.body)

        if error:
            return JsonResponse(error_type=ErrorType.REQUEST_ILLEGAL)
        
        account:Account = Account.objects.filter(id = form.id, username=form.username).first()
        if account is None:
            # 查无此人
            return JsonResponse(error_type=ErrorType.ACCOUNT_NOT_EXIST)
        
        if form.fullname is not None:
            account.fullname = form.fullname
        if form.email is not None:
            if Account.objects.filter(email=form.email).exists():
                # 邮箱与他人的冲突
                return JsonResponse(error_type=ErrorType.ACCOUNT_MAIL_EXIST)
            account.email = form.email
        if form.is_admin is not None:
            account.is_super = form.is_admin
        
        account.save()
        return JsonResponse(status_code=HttpStatus.HTTP_200_OK)


class AdminChangeAccountPassword(View):

    @admin_required
    def patch(self, request: HttpRequest) -> JsonResponse:
        """
        修改账号的密码
        需要管理员权限
        Args:
            request (HttpRequest): 
            id: 账户主键，必须
            username：用户名称[工号版本]，必须
            password：新密码，必须
        Returns:
            JsonResponse: _description_
        """

        form, error = JsonParser(
            Argument('id', data_type=int, required=True),
            Argument('username', data_type=str, required=True),
            Argument('password', data_type=str, required=True),
        ).parse(request.body)

        if error:
            return JsonResponse(error_type=ErrorType.REQUEST_ILLEGAL)
        
        account:Account = Account.objects.filter(id = form.id, username = form.username).first()
        if account is None:
            # 查无此人
            return JsonResponse(error_type=ErrorType.ACCOUNT_NOT_EXIST)
        
        account.password_hash = Account.make_password(form.password)
        account.access_token = None
        account.save()
        return JsonResponse(status_code=HttpStatus.HTTP_200_OK)