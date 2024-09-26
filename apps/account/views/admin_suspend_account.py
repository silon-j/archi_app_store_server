from django.views.generic import View
from django.http import HttpRequest
from apps.account.models import Account
from libs.boost.parser import Argument, JsonParser
from libs.boost.http import JsonResponse, HttpStatus
from utils.decorators import admin_required
from const.error import ErrorType
from django.utils import timezone


class AdminSuspendAccount(View):
    
    @admin_required
    def patch(self, request: HttpRequest) -> JsonResponse:
        """
        禁用用户，修改is_active字段
        不可以自我禁用
        管理员权限才可以行使删除
        Args:
            request (HttpRequest): 请求
            id: 用户的ID
            username: 账号[工号]
        Returns:
            JsonResponse: _description_
        """
        form, error = JsonParser(
            Argument('id_ban', data_type=int, required=True),
            Argument('username_ban', data_type=str, required=True)
        ).parse(request.body)

        if error:
            return JsonResponse(error_type=ErrorType.REQUEST_ILLEGAL)
        
        account_ban:Account = Account.objects.filter(id=form.id_ban, username = form.username_ban).first()
        
        if account_ban is None:
            # 用户不存在
            return JsonResponse(error_type=ErrorType.ACCOUNT_NOT_EXIST)
        if account_ban.id == request.account.id:
            # 自我禁用，不被允许
            return JsonResponse(error_type=ErrorType.REQUEST_ILLEGAL)
        if account_ban.is_active is False:
            # 已经被禁用
            return JsonResponse(status_code=HttpStatus.HTTP_204_NO_CONTENT)

        account_ban.is_active = False
        account_ban.save()
        return JsonResponse(status_code=HttpStatus.HTTP_200_OK)


class AdminDeleteAccount(View):

    @admin_required
    def delete(self, request: HttpRequest) -> JsonResponse:
        """
        删除用户，修改DeleteAt值，标记为删除
        不可以自我删除
        管理员权限才可以行使删除
        Args:
            request (HttpRequest): 请求
            id: 用户的ID
            username: 账号[工号]
        Returns:
            JsonResponse: 返回值
        """
        form, error = JsonParser(
            Argument('id_del', data_type=int, required=True),
            Argument('username_del', data_type=str, required=True)
        ).parse(request.GET)

        if error:
            return JsonResponse(error_type=ErrorType.REQUEST_ILLEGAL)
        
        account_del:Account = Account.objects.filter(id=form.id_del, username = form.username_del).first()
        
        if account_del is None:
            # 用户不存在
            return JsonResponse(error_type=ErrorType.ACCOUNT_NOT_EXIST)
        if account_del.id == request.account.id:
            # 自我删除，不被允许
            return JsonResponse(error_type=ErrorType.REQUEST_ILLEGAL)
        if account_del.deleted_at is not None:
            # 已经删除了。
            return JsonResponse(status_code=HttpStatus.HTTP_204_NO_CONTENT)
            
        account_del.deleted_at = timezone.now()
        account_del.save()
        return JsonResponse(status_code=HttpStatus.HTTP_200_OK)
    

class AdminActivateAccount(View):
    
    @admin_required
    def patch(self, request: HttpRequest) -> JsonResponse:
        """
        解禁用户，修改is_active字段
        不可以自我解除禁用
        管理员权限才可以行使删除
        Args:
            request (HttpRequest): 请求
            id: 用户的ID
            username: 账号[工号]
        Returns:
            JsonResponse: _description_
        """
        form, error = JsonParser(
            Argument('id_activation', data_type=int, required=True),
            Argument('username_activation', data_type=str, required=True)
        ).parse(request.body)

        if error:
            return JsonResponse(error_type=ErrorType.REQUEST_ILLEGAL)
        
        account_ban:Account = Account.objects.filter(id=form.id_activation, username = form.username_activation).first()
        
        if account_ban is None or account_ban.deleted_at is not None:
            # 用户不存在
            return JsonResponse(error_type=ErrorType.ACCOUNT_NOT_EXIST)
        if account_ban.is_active is True:
            # 已经解禁了
            return JsonResponse(status_code=HttpStatus.HTTP_204_NO_CONTENT)

        account_ban.is_active = True
        account_ban.save()
        return JsonResponse(status_code=HttpStatus.HTTP_200_OK)