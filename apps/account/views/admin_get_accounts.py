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

class AdminGetAllAccounts(View):
    
    @admin_required
    def get(self, request:HttpRequest):
        
        accounts = Account.objects.all()
        
        # 批量获取所有操作日志的数量，并构建 {account_id: use_count} 映射
        operation_logs = OperationLog.objects.values('created_user').annotate(use_count=models.Count('id'))
        account_operation_counts = {log['created_user']: log['use_count'] for log in operation_logs}
        
        # 构建一个 {username: Developer} 映射
        developers = Developer.objects.filter(
            username__in=[account.username for account in accounts],
            email__in=[account.email for account in accounts]
        )

        # 构建一个 {developer_id: plugin_count} 映射
        developer_plugin_counts = defaultdict(int)
        for dev in developers:
            # 构件一个{plugin_name: version_count} 映射
            dev_plugin_relation = defaultdict(int)
            plugin_versions = dev.pluginversion_set
            for plugin_version in plugin_versions:
                dev_plugin_relation[plugin_version.plugin.name] += 1
            developer_plugin_counts[(dev.username, dev.email)] = len(dev_plugin_relation.keys())


        result : List[Account] = [
            {
            'id':account.id, 
            'username':account.username, 
            'fullname':account.fullname, 
            'email': account.email, 
            'can_admin':account.can_admin,
            'is_super':account.is_super,
            'is_active':account.is_active,
            'app_use_count': account_operation_counts.get(account.id, 0),
            'app_publish_count': developer_plugin_counts.get((account.username, account.email), 0),
            'last_login':account.last_login,
            } 
            for account in accounts]
        return JsonResponse(result)