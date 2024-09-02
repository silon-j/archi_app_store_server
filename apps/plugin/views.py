from django.shortcuts import get_object_or_404, render
from django.views import View
from django.db import transaction
import loguru

from apps.plugin.models import Developer, OperationLog, Plugin, PluginCategory, PluginVersion, Tag
from const.error import ErrorType
from libs.boost.parser import Argument, JsonParser
from libs.boost.http import HttpStatus, JsonResponse
import os
from libs.boost.Sts import Sts, CIScope, Scope

__FILED_REQUIRED__ : str = "不可以为空"
__FILED_EXISTS__ : str = "已存在"
__FILED_NOT_EXISTS__ : str = "不可用"
# Create your views here.
class CosTempCredentialView(View):
    def get(self, request):
        config = {
            'url': 'https://sts.tencentcloudapi.com/',
            # 临时密钥有效时长，单位是秒
            'duration_seconds': 1800,
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
                "name/cos:GetObject"
            ],
            # 临时密钥生效条件，关于condition的详细设置规则和COS支持的condition类型可以参考 https://cloud.tencent.com/document/product/436/71306
        }

        try:
            sts = Sts(config)
            response = sts.get_credential()
        except Exception as e:
            print(e)
        return JsonResponse(response)
    
#插件信息
class PluginView(View):
    '''
        创建插件信息,新建插件必然带一个版本信息
    '''
    def post(self, request):
        plugin, error = JsonParser(
            Argument('name', data_type=str, required=True),
            Argument('icon_url', data_type=str, required=True),
            Argument('category_ids', data_type=list, required=True),
            Argument('version_no', data_type=str, required=True),
            Argument('description', data_type=str, required=True),
            Argument('type', data_type=int, required=True, filter_func=lambda type: [Plugin.TYPE_PLUGIN, Plugin.TYPE_LINK, Plugin.TYPE_APPLICATION].__contains__(type)),
            Argument('attachment_url', data_type=str, required=False),
            Argument('attachment_size', data_type=int, required=False, nullable=True),
            Argument('execution_file_path', data_type=str, required=False),
            Argument('authors', data_type=list, required=False),
            Argument('tags', data_type=list, required=False),
        ).parse(request.body)
        if error:
            return JsonResponse(error_message=error)
        if plugin.attachment_url is None :
            return JsonResponse(error_message=f"文件链接{__FILED_REQUIRED__}")
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
    
#插件版本信息
class PluginVersionView(View):
    #获取插件列表
    def get(self, request):
        name = request.GET.get('name', None)  
        category_id = request.GET.get('category_id', 0)  
        if category_id == 0:
            return JsonResponse(error_message=f'分类ID{__FILED_REQUIRED__}')
        # 从所有插件开始
        plugin_ids = Plugin.objects.all().values('id')
        if name:
            plugin_ids = plugin_ids.filter(name__icontains=name)
        if category_id is not None :
            if not PluginCategory.objects.filter(id=category_id).exists():
                return JsonResponse(error_message=f"分类id{__FILED_NOT_EXISTS__}")
            category_ids_query = PluginCategory.objects.filter(parent__id=category_id).values('id')
            category_ids = [item['id'] for item in category_ids_query]
            plugin_ids = plugin_ids.filter(categories__id__in=category_ids)
        plugins = Plugin.objects.all().filter(id__in=plugin_ids)
        #怎么获取最新的插件版本 item.versions.first() 这里要特殊处理下
        result = []
        for item in plugins:
            newest_version = item.versions.order_by('-id').first()
            tags = [tag.text for tag in newest_version.tags.all()]
            for category in item.categories.all():
                result.append({'id':item.id, 'version_id':newest_version.id, 'name':item.name, 'icon_url':item.icon_url, 'attachment_url':newest_version.attachment_url, 'execution_file_path':newest_version.execution_file_path,'type':item.type,'category':category.name, 'tags': tags })
        return JsonResponse(result)

#插件分类信息接口
class PluginCategoryView(View):
    def get(self, request):
        try:
            categories = list(PluginCategory.objects.filter(parent=None))
            categorized_data = self._build_category_tree(categories)
            return JsonResponse(categorized_data)
        except Exception as e:
            loguru.logger.error(f"生成插件类别失败: {e}")
            return JsonResponse(error_message='获取插件分类失败')

    def post(self, request):
        form, error = JsonParser(
            Argument('name', data_type=str, required=True),
            Argument('parent_id', data_type=int, required=False),
        ).parse(request.body)
        if error:
            return JsonResponse(error_message=error)
        if PluginCategory.objects.filter(name=form.name).exists():
            return JsonResponse(error_message=f'分类名称:({form.name}){__FILED_EXISTS__}')
        if not request.account.is_super:
            return JsonResponse(error_message='仅限管理员添加')
        parent_category = None
        if form.parent_id != None and form.parent_id > 0:
            if PluginCategory.objects.filter(id=form.parent_id).exists():
                parent_category = PluginCategory.objects.get(id=form.parent_id)
            else:
                return JsonResponse(error_message=f'分类id({form.parent_id}){__FILED_NOT_EXISTS__}')
        category = PluginCategory.objects.create(
            name=form.name,
            parent=parent_category
        )
        return JsonResponse(category.id)
 
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

#插件详情接口
class PluginVersionDetailView(View):
    def get(self, request, version_id):
        if not PluginVersion.objects.filter(id=version_id).exists():
            return JsonResponse(error_type=ErrorType.OBJECT_NOT_FOUND)
        pluginVersionObj = PluginVersion.objects.filter(id=version_id).first()
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
    def post(self, request, version_id):
        form, error = JsonParser(
            Argument('type', data_type=str, required=True, filter_func=lambda type: [OperationLog.TYPE_OPEN, OperationLog.TYPE_OPEN , OperationLog.TYPE_INSTALL].__contains__(type)),
        ).parse(request.body)
        if error:
            return JsonResponse(error_message=error)
        version = get_object_or_404(PluginVersion, id=version_id)
        log = OperationLog.objects.create(
            version=version,
            type=form.type,
            created_user=request.account
        )
        return JsonResponse(log.id)
    def get(self, request, version_id):
        logs = OperationLog.objects.filter(version__id=version_id)
        return JsonResponse([{'id':log.id,'plugin_name':log.version.plugin.name, 'version_no':log.version.version_no, 'type': log.type, 'created_at':log.created_at } for log in logs])