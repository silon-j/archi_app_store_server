from django.views.generic import View
from django.http import HttpRequest
from django.db import models
from django.db.models.functions import Coalesce
from apps.account.models import Account
from apps.plugin.models import Developer, OperationLog
from libs.boost.parser import Argument, JsonParser
from libs.boost.http import JsonResponse
from utils.decorators import admin_required
from const.error import ErrorType
from typing import List
from collections import defaultdict
from apps.plugin.models import PluginVersion

class AdminGetAllAccounts(View):
    
    @admin_required
    def get(self, request:HttpRequest):
        # 获取所有的版本信息
        plugin_versions: List[PluginVersion] = PluginVersion.objects.all().select_related('created_user')
        # 获取所有的
        accounts = Account.objects.all()
        
        # 批量获取所有操作日志的数量，并构建 {account_id: use_count} 映射
        operation_logs = OperationLog.objects.values('created_user').annotate(use_count=models.Count('id'))
        account_operation_counts = {log['created_user']: log['use_count'] for log in operation_logs}
        # 使用 defaultdict 初始化插件版本计数
        account_plugin_version_dict = defaultdict(int)

        for pv in plugin_versions:
            account_plugin_version_dict[pv.created_user.id]+=1

        result = [
            {
            'id':account.id, 
            'username':account.username, 
            'fullname':account.fullname, 
            'email': account.email, 
            'can_admin':account.can_admin,
            'is_super':account.is_super,
            'is_active':account.is_active,
            'app_use_count': account_operation_counts.get(account.id, 0),
            'app_publish_count': account_plugin_version_dict.get(account.id, 0),
            'last_login':account.last_login,
            } 
            for account in accounts]
        return JsonResponse(result)