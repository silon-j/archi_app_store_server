from django.http import HttpRequest
from django.shortcuts import get_object_or_404, render
from django.views import View
from django.db import transaction, models
from django.db.models import Count

import loguru

from apps.account.models import Account
from apps.plugin.models import Developer, OperationLog, Plugin, PluginCategory, PluginVersion, Tag
from const.error import ErrorType
from libs.boost.parser import Argument, JsonParser
from libs.boost.http import HttpStatus, JsonResponse
import os
from sts.sts import Sts
from utils.decorators import admin_required

__FILED_REQUIRED__ : str = "不可以为空"
__FILED_EXISTS__ : str = "已存在"
__FILED_NOT_EXISTS__ : str = "不可用"
__COS_CREDENTIAL_ERR__ : str = "获取腾讯云对象存储令牌出现错误"
# Create your views here.
class CosTempCredentialView(View):
    def get(self, request:HttpRequest):
        config = {
            'url': 'https://sts.tencentcloudapi.com/',
            # 临时密钥有效时长，单位是秒
            'duration_seconds': 36000,
            'secret_id': os.environ['COS_SECRET_ID'],
            # 固定密钥
            'secret_key': os.environ['COS_SECRET_KEY'],
            # 换成你的 bucket
            'bucket': 'archi-1317440414',
            # 换成 bucket 所在地区
            'region': 'ap-shanghai',
            # 这里改成允许的路径前缀，可以根据自己网站的用户登录态判断允许上传的具体路径
            # 例子： a.jpg 或者 a/* 或者 * (使用通配符*存在重大安全风险, 请谨慎评估使用)
            'allow_prefix': ['app_store/attachments/*','app_store/icons/*'],
            'resource': [
                "qcs::cos:ap-shanghai:archi-1317440414/app_store/*"
            ],
            # 密钥的权限列表。简单上传和分片需要以下的权限，其他权限列表请看 https://cloud.tencent.com/document/product/436/31923
            'allow_actions': [
                # 简单上传
                'name/cos:PutObject',
                'name/cos:PostObject',
                "name/cos:InitiateMultipartUpload", 
                "name/cos:ListMultipartUploads", 
                "name/cos:ListParts",
                "name/cos:UploadPart",
                "name/cos:CompleteMultipartUpload",
                "name/cos:HeadObject",
                "name/cos:GetObject"
            ],

            # 临时密钥生效条件，关于condition的详细设置规则和COS支持的condition类型可以参考 https://cloud.tencent.com/document/product/436/71306
        }

        try:
            sts = Sts(config)
            response = sts.get_credential()
            return JsonResponse(response)
        except Exception as e:
            loguru.logger.error(e)
            return JsonResponse(error_message=__COS_CREDENTIAL_ERR__)
    
#插件信息
class PluginView(View):
    '''
        创建插件信息,新建插件必然带一个版本信息
    '''
    def post(self, request:HttpRequest):
        plugin, error = JsonParser(
            Argument('name', data_type=str, required=True),
            Argument('icon_url', data_type=str, required=True),
            Argument('category_ids', data_type=list, required=True),
            Argument('version_no', data_type=str, required=True),
            Argument('description', data_type=str, required=True),
            Argument('type', data_type=int, required=True, filter_func=lambda type: [Plugin.TYPE_PLUGIN, Plugin.TYPE_LINK, Plugin.TYPE_APPLICATION].__contains__(type)),
            Argument('attachment_url', data_type=str, required=True, help=f"文件链接{__FILED_REQUIRED__}"),
            Argument('attachment_size', data_type=int, required=False, nullable=True),
            Argument('execution_file_path', data_type=str, required=False),
            Argument('authors', data_type=list, required=False),
            Argument('tags', data_type=list, required=False),
        ).parse(request.body)
        if error:
            return JsonResponse(error_message=error)
        if plugin.type == Plugin.TYPE_APPLICATION and plugin.execution_file_path is None :
            return JsonResponse(error_message=f"应用入口{__FILED_REQUIRED__}")
        if Plugin.objects.filter(name=plugin.name).exists() :
            return JsonResponse(error_message=f"插件名称{__FILED_EXISTS__}")
        pluginObj = None
        with transaction.atomic():
            savepoint_id = transaction.savepoint()
            try:
                categories = PluginCategory.objects.filter(id__in=plugin.category_ids)
                pluginObj = Plugin.objects.create(
                    name=plugin.name,
                    icon_url=plugin.icon_url,
                    type=plugin.type,
                    created_user=request.account
                )
                pluginObj.categories.set(categories)
                tags = []
                for tag_text in plugin.tags:
                    tag, created = Tag.objects.get_or_create(text=tag_text)  # 假设Tag模型有一个name字段
                    tags.append(tag)
                developers = []
                for developer in plugin.authors:
                    if developer.get('name','') == '':
                        return JsonResponse(error_message=f"开发者名字{__FILED_REQUIRED__}")
                    developer, created = Developer.objects.get_or_create(name=developer.get('name'),phone=developer.get('phone', ''),email=developer.get('email','')) 
                    developers.append(developer)
                pluginVersionObj = PluginVersion.objects.create(
                    plugin=pluginObj,
                    version_no=plugin.version_no,
                    description=plugin.description,
                    attachment_url=plugin.attachment_url,
                    attachment_size=plugin.attachment_size,
                    execution_file_path=plugin.execution_file_path,
                    created_user=request.account
                )
                pluginVersionObj.tags.set(tags)
                pluginVersionObj.authors.set(developers)
            except Exception as e:
                transaction.savepoint_rollback(savepoint_id)
                # 事务继续，但是撤销到了savepoint_id指定的状态
                loguru.logger.error(f"创建失败: {e}")
                return JsonResponse(error_message=e)
        return JsonResponse(pluginObj.id)
    @admin_required
    def patch(self, request:HttpRequest):
        plugin, error = JsonParser(
            Argument('id', data_type=int, required=True, filter_func=lambda id: Plugin.objects.filter(id=id).exists()),
            Argument('name', data_type=str, required=True),
            Argument('icon_url', data_type=str, required=True),
        ).parse(request.body)
        if error:
            return JsonResponse(error_message=error)
        if Plugin.objects.filter(name=plugin.name).exclude(id=plugin.id).exists() :
            return JsonResponse(error_message=f"插件名称{__FILED_EXISTS__}")
        return JsonResponse(Plugin.objects.filter(id=plugin.id).update(name=plugin.name,icon_url=plugin.icon_url))

#插件信息
class PluginListView(View):
    @admin_required
    def get(self, request:HttpRequest):
        # param, error = JsonParser(
        #     Argument('view', data_type=str, required=True, help=f'视图模型{__FILED_REQUIRED__}', filter_func=lambda name: [self.VIEW_MAIN, self.VIEW_SECOND].__contains__(name)),
        # ).parse(request.GET)
        # if error:
        #     return JsonResponse(error_message=error)
        plugins = Plugin.objects.all()
        result = [
            {
            'id':plugin.id, 
            'icon_url':plugin.icon_url, 
            'name': plugin.name, 
            'type':plugin.type,
            'version_count':plugin.versions.count(),
            'use_count': plugin.versions.annotate(log_count=Count('logs')).aggregate(use_count=models.Sum('log_count'))['use_count']  
            } 
            for plugin in plugins]
        return JsonResponse(result)

#插件版本信息
class PluginVersionView(View):
    #获取插件列表
    def get(self, request:HttpRequest):
        param, error = JsonParser(
            Argument('name', data_type=str, required=False),
            Argument('category_id', data_type=int, required=True, help=f'分类ID{__FILED_REQUIRED__}'),
        ).parse(request.GET)
        if error:
            return JsonResponse(error_message=error)
        # 从所有插件开始
        plugin_ids = Plugin.objects.all().values('id')
        if param.name:
            plugin_ids = plugin_ids.filter(name__icontains=param.name)
        if not PluginCategory.objects.filter(id=param.category_id).exists():
            return JsonResponse(error_message=f"分类id{__FILED_NOT_EXISTS__}")
        category_ids_query = PluginCategory.objects.filter(parent__id=param.category_id).values('id')
        category_ids = [item['id'] for item in category_ids_query]
        plugin_ids = plugin_ids.filter(categories__id__in=category_ids)
        plugins = Plugin.objects.all().filter(id__in=plugin_ids)
        #怎么获取最新的插件版本 item.versions.first() 这里要特殊处理下
        result = []
        for item in plugins:
            newest_version = item.versions.order_by('-id').first()
            tags = [tag.text for tag in newest_version.tags.all()]
            for category in item.categories.filter(id__in=category_ids):
                result.append({'id':item.id, 'version_id':newest_version.id, 'version_no':newest_version.version_no, 'name':item.name, 'icon_url':item.icon_url, 'attachment_url':newest_version.attachment_url, 'attachment_size':newest_version.attachment_size, 'execution_file_path':newest_version.execution_file_path,'type':item.type,'category':category.name, 'tags': tags })
        return JsonResponse(result)
    
    @admin_required
    def patch(self, request:HttpRequest):
        version, error = JsonParser(
            Argument('id', data_type=int, required=True, filter_func=lambda id: PluginVersion.objects.filter(id=id).exists()),
            Argument('version_no', data_type=str, required=True),
            Argument('description', data_type=str, required=True),
        ).parse(request.body)
        if error:
            return JsonResponse(error_message=error)
        # if Plugin.objects.filter(name=plugin.name).exclude(id=plugin.id).exists() :
        #     return JsonResponse(error_message=f"插件名称{__FILED_EXISTS__}")
        return JsonResponse(PluginVersion.objects.filter(id=version.id).update(description=version.description,version_no=version.version_no))

#插件版本信息
class PluginVersionListView(View):
    @admin_required
    def get(self, request:HttpRequest):
        # param, error = JsonParser(
        #     Argument('name', data_type=str, required=False),
        #     Argument('category_id', data_type=int, required=True, help=f'分类ID{__FILED_REQUIRED__}'),
        # ).parse(request.GET)
        # if error:
        #     return JsonResponse(error_message=error)
        # 从所有插件开始
        pluginVersions = PluginVersion.objects.all()
        result = [
            {
            'id':pluginVersion.id, 
            'plugin_id':pluginVersion.plugin.id, 
            'version_no': pluginVersion.version_no, 
            'description':pluginVersion.description,
            'publish_date':pluginVersion.publish_date,
            'use_count': pluginVersion.logs.count()
            } 
            for pluginVersion in pluginVersions]
        return JsonResponse(result)

#插件分类信息接口
class PluginCategoryView(View):
    def get(self, request:HttpRequest):
        try:
            categories = list(PluginCategory.objects.filter(parent=None))
            categorized_data = self._build_category_tree(categories)
            return JsonResponse(categorized_data)
        except Exception as e:
            loguru.logger.error(f"生成插件类别失败: {e}")
            return JsonResponse(error_message='获取插件分类失败')
    @admin_required
    def post(self, request:HttpRequest):
        form, error = JsonParser(
            Argument('name', data_type=str, required=True),
            Argument('parent_id', data_type=int, required=False),
        ).parse(request.body)
        if error:
            return JsonResponse(error_message=error)
        if PluginCategory.objects.filter(name=form.name).exists():
            return JsonResponse(error_message=f'分类名称:({form.name}){__FILED_EXISTS__}')
        parent_category = None
        if form.parent_id != None and form.parent_id > 0:
            if PluginCategory.objects.filter(id=form.parent_id).exists():
                parent_category = PluginCategory.objects.get(id=form.parent_id)
            else:
                return JsonResponse(error_message=f'分类id({form.parent_id}){__FILED_NOT_EXISTS__}')
        category = PluginCategory.objects.create(
            name=form.name,
            parent=parent_category,
            created_user=request.account
        )
        return JsonResponse(category.id)
 
    @admin_required
    def patch(self, request:HttpRequest):
        form, error = JsonParser(
            Argument('id', data_type=int, required=True, filter_func=lambda id: PluginCategory.objects.filter(id=id).exists()),
            Argument('name', data_type=str, required=True),
        ).parse(request.body)
        if error:
            return JsonResponse(error_message=error)
        if PluginCategory.objects.filter(name=form.name).exclude(id=form.id).exists():
            return JsonResponse(error_message=f'分类名称:({form.name}){__FILED_EXISTS__}')
        return JsonResponse(PluginCategory.objects.filter(id=form.id).update(name=form.name))
 
    #构建插件分类的树状结构
    def _build_category_tree(self, categories):
        tree = []
        for category in categories:
            tree.append({
                'id': category.id,
                'name': category.name,
                'children': self._build_category_tree(category.children.all())
            })
        return tree

#插件分类列表
class PluginCategoryListView(View):
    VIEW_MAIN='main'
    VIEW_SECOND='second'
    @admin_required
    def get(self, request:HttpRequest):
        param, error = JsonParser(
            Argument('view', data_type=str, required=True, help=f'视图模型{__FILED_REQUIRED__}', filter_func=lambda name: [self.VIEW_MAIN, self.VIEW_SECOND].__contains__(name)),
        ).parse(request.GET)
        if error:
            return JsonResponse(error_message=error)
        try:
            if param.view == self.VIEW_MAIN:
                categories = list(PluginCategory.objects.filter(parent=None))
                result = [{'id':category.id, 'name':category.name, 'children_count': category.children.count(), 'app_count': category.children.aggregate(appcount=models.Count('plugin_category'))['appcount'] } for category in categories]
                return JsonResponse(result)
            else:
                categories = list(PluginCategory.objects.filter(parent__isnull=False))
                result = [{'id':category.id, 'name':category.name, 'parent_name':category.parent.name, 'app_count': category.plugin_category.count() } for category in categories]
                return JsonResponse(result)
        except Exception as e:
            loguru.logger.error(f"获取插件分类失败: {e}")
            return JsonResponse(error_message='获取插件分类失败')
  
#插件详情接口
class PluginVersionDetailView(View):
    def get(self, request:HttpRequest):
        param, error = JsonParser(
            Argument('version_id', data_type=int, required=True, help=f'插件版本ID{__FILED_REQUIRED__}', filter_func=lambda id: PluginVersion.objects.filter(id=id).exists()),
        ).parse(request.GET)
        if error:
            return JsonResponse(error_message=error)
        pluginVersionObj = PluginVersion.objects.filter(id=param.version_id).first()
        # 将模型实例序列化为字典或其他格式
        plugin_dto = {
            'id': pluginVersionObj.id,
            'plugin_id': pluginVersionObj.plugin.id,
            'icon_url': pluginVersionObj.plugin.icon_url,
            'plugin_type': pluginVersionObj.plugin.type,
            'version_no': pluginVersionObj.version_no,
            'versions':[{ 'id': item.id, 'version_no': item.version_no } for item in pluginVersionObj.plugin.versions.all()],
            'name': pluginVersionObj.plugin.name, 
            'description':pluginVersionObj.description,
            'attachment_url':pluginVersionObj.attachment_url,
            'attachment_size':pluginVersionObj.attachment_size,
            'execution_file_path':pluginVersionObj.execution_file_path,
            'publish_date':pluginVersionObj.publish_date,
            'tags':[item.text for item in pluginVersionObj.tags.all()],
            'authors':[{'name':item.name, 'phone':item.phone,'email':item.email} for item in pluginVersionObj.authors.all()],
        }
        # 返回JSON响应
        return JsonResponse(plugin_dto)
#操作记录
class OperationLogView(View):
    def post(self, request:HttpRequest):
        form, error = JsonParser(
            Argument('version_id', data_type=int, required=True, help=f'插件版本ID{__FILED_REQUIRED__}'),
            Argument('type', data_type=str, required=True, filter_func=lambda type: [OperationLog.TYPE_OPEN, OperationLog.TYPE_OPEN , OperationLog.TYPE_INSTALL].__contains__(type)),
        ).parse(request.body)
        if error:
            return JsonResponse(error_message=error)
        version = get_object_or_404(PluginVersion, id=form.version_id)
        log = OperationLog.objects.create(
            version=version,
            type=form.type,
            created_user=request.account
        )
        return JsonResponse(log.id)
    def get(self, request:HttpRequest):
        form, error = JsonParser(
            Argument('version_id', data_type=int, required=True, help=f'插件版本ID{__FILED_REQUIRED__}'),
        ).parse(request.GET)
        logs = OperationLog.objects.filter(version__id=form.version_id)
        return JsonResponse([{'id':log.id,'plugin_name':log.version.plugin.name, 'version_no':log.version.version_no, 'type': log.type, 'created_at':log.created_at } for log in logs])
    

#用户信息表
class AccountListView(View):
    @admin_required
    def get(self, request:HttpRequest):
        # param, error = JsonParser(
        #     Argument('view', data_type=str, required=True, help=f'视图模型{__FILED_REQUIRED__}', filter_func=lambda name: [self.VIEW_MAIN, self.VIEW_SECOND].__contains__(name)),
        # ).parse(request.GET)
        # if error:
        #     return JsonResponse(error_message=error)
        accounts = Account.objects.all()
        result = [
            {
            'id':account.id, 
            'username':account.username, 
            'fullname':account.fullname, 
            'email': account.email, 
            'can_admin':account.can_admin,
            'is_super':account.is_super,
            'is_active':account.is_active,
            'is_active':account.is_active,
            'app_use_count':account.operationlog_set.count(),
            'app_publish_count':0, #TODO 这个逻辑比较恶心，建议暂时别写
            'last_login':account.last_login,
            } 
            for account in accounts]
        return JsonResponse(result)
 