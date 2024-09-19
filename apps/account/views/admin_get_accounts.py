from django.views.generic import View
from django.http import HttpRequest
from django.db.models import OuterRef, Subquery, DateTimeField
from django.db.models.functions import Coalesce
from apps.account.models import Account, LoginLog
from libs.boost.parser import Argument, JsonParser
from libs.boost.http import JsonResponse
from utils.decorators import admin_required
from const.error import ErrorType
from django.utils import timezone
from typing import List

class AdminGetAllAccounts(View):
    
    @admin_required
    def get(self, request:HttpRequest):
        
        accounts = Account.objects.all()
        result : List[Account] = [
            {
            'id':account.id, 
            'username':account.username, 
            'fullname':account.fullname, 
            'email': account.email, 
            'can_admin':account.can_admin,
            'is_super':account.is_super,
            'is_active':account.is_active,
            'app_use_count':account.operationlog_set.count(),
            'app_publish_count':0, #TODO 这个逻辑比较恶心，建议暂时别写
            'last_login':account.last_login,
            } 
            for account in accounts]
        return JsonResponse(result)