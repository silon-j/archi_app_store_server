from django.http import HttpRequest
from django.shortcuts import get_object_or_404, render
from django.views import View
from django.db import transaction, models
from django.db.models import Count
from django.utils import timezone
import loguru
from django.db.models import Q

from apps.account.models import Account
from apps.plugin.models import Developer, OperationLog, Plugin, PluginCategory, PluginVersion, Tag
from const.error import ErrorType
from libs.boost.parser import Argument, JsonParser
from libs.boost.http import HttpStatus, JsonResponse, paginate_data
import os
from sts.sts import Sts
from utils.decorators import admin_required

__FILED_REQUIRED__ : str = "不可以为空"
__FILED_EXISTS__ : str = "已存在"
__FILED_NOT_EXISTS__ : str = "不可用"
__COS_CREDENTIAL_ERR__ : str = "获取腾讯云对象存储令牌出现错误"
__VERSION_DELETE_REQUIRE_ERR__ : str = "无法删除插件最后一个版本"
# Create your views here.
class CosTempCredentialView(View):
    def get(self, request:HttpRequest):
        config = {
            'url': 'https://sts.tencentcloudapi.com/',
            # 临时密钥有效时长，单位是秒
            'duration_seconds': 1800,
            'secret_id': os.environ['COS_SECRET_ID'],
            # 固定密钥
            'secret_key': os.environ['COS_SECRET_KEY'],
            # 换成你的 bucket
            'bucket': 'app-store-1332569462',
            # 换成 bucket 所在地区
            'region': 'ap-shanghai',
            # 这里改成允许的路径前缀，可以根据自己网站的用户登录态判断允许上传的具体路径
            # 例子： a.jpg 或者 a/* 或者 * (使用通配符*存在重大安全风险, 请谨慎评估使用)
            'allow_prefix': ['app_store/attachments/*','app_store/icons/*'],
            'resource': [
                "qcs::cos:ap-shanghai:app-store-1332569462/app_store/*"
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
            Argument('link', data_type=str, required=False),
            Argument('type', data_type=int, required=True, filter_func=lambda type: [Plugin.TYPE_PLUGIN, Plugin.TYPE_LINK, Plugin.TYPE_APPLICATION].__contains__(type)),
            Argument('attachment_url', data_type=str, required=True, help=f"请确认文件上传完成或填写文件链接"),
            Argument('attachment_size', data_type=int, required=False, nullable=True),
            Argument('is_external', data_type=bool, required=False),
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
                    link=plugin.link,
                    type=plugin.type,
                    description=plugin.description,
                    is_external=plugin.is_external if plugin.is_external is not None else False,
                    created_user=request.account
                )
                pluginObj.categories.set(categories)
                tags = []
                for tag_text in plugin.tags:
                    tag, created = Tag.objects.get_or_create(text=tag_text)  # 假设Tag模型有一个name字段
                    tags.append(tag)
                pluginObj.tags.set(tags)
                developers = []
                for developer in plugin.authors:
                    if developer.get('name','') == '':
                        return JsonResponse(error_message=f"开发者名字{__FILED_REQUIRED__}")
                    developer, created = Developer.objects.get_or_create(name=developer.get('name'),phone=developer.get('phone', ''),email=developer.get('email','')) 
                    developers.append(developer)
                pluginVersionObj = PluginVersion.objects.create(
                    plugin=pluginObj,
                    version_no=plugin.version_no,
                    description='',
                    attachment_url=plugin.attachment_url,
                    attachment_size=plugin.attachment_size,
                    execution_file_path=plugin.execution_file_path,
                    created_user=request.account
                )
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
            Argument('description', data_type=str, required=False),
            Argument('icon_url', data_type=str, required=True),
            Argument('category_ids', data_type=list, required=False),
        ).parse(request.body)
        if error:
            return JsonResponse(error_message=error)
        if Plugin.objects.filter(name=plugin.name).exclude(id=plugin.id).exists() :
            return JsonResponse(error_message=f"插件名称{__FILED_EXISTS__}")
        if plugin.category_ids is None:
           return JsonResponse(Plugin.objects.filter(id=plugin.id).update(name=plugin.name,icon_url=plugin.icon_url))
        else:
            categories = PluginCategory.objects.filter(id__in=plugin.category_ids)
            if categories.count() < len(plugin.category_ids):
                return JsonResponse(error_message=f"存在非法的插件分类Id")
            plugin_obj = Plugin.objects.filter(id=plugin.id).first()
            plugin_obj.name = plugin.name
            plugin_obj.description = plugin.description
            plugin_obj.icon_url = plugin.icon_url
            plugin_obj.categories.set(categories)
            plugin_obj.save()
            return JsonResponse()
    
    @admin_required
    def delete(self, request:HttpRequest):
        plugin, error = JsonParser(
            Argument('id', data_type=int, required=True, filter_func=lambda id: Plugin.objects.filter(id=id).exists()),
        ).parse(request.GET)
        if error:
            return JsonResponse(error_message=error)
        with transaction.atomic():
            savepoint_id = transaction.savepoint()
            try:
                # 先将子类标志为删除
                children:PluginVersion = PluginVersion.objects.filter(plugin_id=plugin.id)
                for child in children:
                    child.deleted_at = timezone.now()
                    child.deleted_user = request.account
                    child.save()
                obj:Plugin = Plugin.objects.filter(id=plugin.id).first()
                if obj.deleted_at is not None:
                    return JsonResponse(status_code=HttpStatus.HTTP_204_NO_CONTENT)
                obj.deleted_at = timezone.now()
                obj.deleted_user = request.account
                obj.save()
                return JsonResponse(status_code=HttpStatus.HTTP_200_OK)
       
            except Exception as e:
                transaction.savepoint_rollback(savepoint_id)
                # 事务继续，但是撤销到了savepoint_id指定的状态
                loguru.logger.error(f"删除失败: {e}")
                return JsonResponse(error_message=e)
    #获取插件详情
    def get(self, request:HttpRequest):
        param, error = JsonParser(
            Argument('id', data_type=int, required=True, help=f'插件ID{__FILED_REQUIRED__}', filter_func=lambda id: Plugin.objects.filter(id=id).exists()),
        ).parse(request.GET)
        if error:
            return JsonResponse(error_message=error)
        pluginObj = Plugin.objects.filter(id=param.id).first()
        # 将模型实例序列化为字典或其他格式
        plugin_dto = pluginObj.to_dto()
        # 返回JSON响应
        return JsonResponse(plugin_dto)
#插件信息
class PluginListView(View):
    @admin_required
    def get(self, request:HttpRequest):
        param, error = JsonParser(
            Argument('current', data_type=int, required=False),
            Argument('page_size', data_type=int, required=False),
        ).parse(request.GET)
        if error:
            return JsonResponse(error_message=error)

        plugins = Plugin.objects.all()
        page_data = paginate_data(plugins, 
                                  current=param.current if param.current != None else 1, 
                                  page_size=param.page_size if param.page_size != None else 10, 
                                  item_handler=lambda plugin:
                                    {
                                    'id':plugin.id, 
                                    'icon_url':plugin.icon_url, 
                                    'name': plugin.name, 
                                    'description': plugin.description, 
                                    'categories': [{'id':category.id, 'name':category.name, 'parent_name':category.parent.name if category.parent != None else None } for category in plugin.categories.all()],
                                    'type':plugin.type,
                                    'link':plugin.link,
                                    'version_count':plugin.versions.count(),
                                    'use_count': plugin.versions.annotate(log_count=Count('logs')).aggregate(use_count=models.Sum('log_count'))['use_count']  
                                    })
        return JsonResponse(page_data)

#获取我的已发布插件信息
class PluginPublishListView(View):
    @admin_required
    def get(self, request:HttpRequest):
        plugins = Plugin.objects.filter(created_user__id=request.account.id)
        result = []
        for item in plugins:
            newest_version = item.versions.order_by('-id').first()
            tags = [tag.text for tag in item.tags.all()]
            result.append({'id':item.id, 'version_id':newest_version.id, 'version_no':newest_version.version_no, 'name':item.name, 'icon_url':item.icon_url, 'attachment_url':newest_version.attachment_url, 'attachment_size':newest_version.attachment_size, 'execution_file_path':newest_version.execution_file_path,'type':item.type,'link':item.link, 'tags': tags })
        return JsonResponse(result)


#插件版本信息
class PluginVersionView(View):
    ORDER_USE='use_count'
    ORDER_CREATE='recent_create'
    ORDER_UPDATE='recent_update'
    ORDER_CHOICES = (
        (ORDER_USE, '下载量'),
        (ORDER_CREATE, '最近创建'),
        (ORDER_UPDATE, '最近更新'),
    )
    #获取插件列表
    def get(self, request:HttpRequest):
        param, error = JsonParser(
            Argument('filter', data_type=str, required=False),
            Argument('category_id', data_type=int, required=False),
            Argument('order', data_type=str, required=False, filter_func=lambda order_type: [PluginVersionView.ORDER_USE, PluginVersionView.ORDER_CREATE, PluginVersionView.ORDER_UPDATE].__contains__(order_type))
        ).parse(request.GET)
        if error:
            return JsonResponse(error_message=error)
        param.ids = request.GET.getlist('ids')
        if (param.category_id is None and param.filter is None) and (param.ids is None or len(param.ids) == 0):
            return JsonResponse(error_message=f"分类ID{__FILED_REQUIRED__}")
        # 从所有插件开始
        plugin_ids = Plugin.objects.all().values('id')
        #如果直接查询插件版本列表，使用特殊逻辑返回数据
        if param.ids and len(param.ids) > 0:
            try:
                [int(id) for id in param.ids]
            except:
                return JsonResponse(error_message=f"存在非法或已被删除的插件版本Id")
            plugin_versions = PluginVersion.objects.filter(id__in=param.ids)
            # if len(plugin_versions) != len(param.ids):
            #     return JsonResponse(error_message=f"存在非法或已被删除的插件版本Id")
            result = []
            for item in plugin_versions:
                tags = [tag.text for tag in item.plugin.tags.all()]
                result.append({'id':item.plugin.id, 'version_id':item.id, 'version_no':item.version_no, 'name':item.plugin.name, 'icon_url':item.plugin.icon_url, 'attachment_url':item.attachment_url, 'attachment_size':item.attachment_size, 'execution_file_path':item.execution_file_path,'type':item.plugin.type,'link':item.plugin.link,'tags': tags })
            return JsonResponse(result)
        category_ids = None
        if param.category_id:
            if not PluginCategory.objects.filter(id=param.category_id).exists():
                return JsonResponse(error_message=f"分类id{__FILED_NOT_EXISTS__}")
            category_ids_query = PluginCategory.objects.filter(parent__id=param.category_id).values('id')
            category_ids = [item['id'] for item in category_ids_query]
            plugin_ids = plugin_ids.filter(categories__id__in=category_ids)
        if param.filter and len(param.filter) > 0:
            # 插件名称, 插件描述 ,更新描述, 标签 包含搜索内容
            plugin_ids = plugin_ids.filter(Q(name__contains=param.filter)|Q(description__contains=param.filter)|Q(tags__text__contains=param.filter)|Q(versions__description__contains=param.filter)).values('id')
        plugins = Plugin.objects.all().filter(id__in=plugin_ids)
        if param.order:
            match param.order:
                case PluginVersionView.ORDER_USE:
                    plugins = plugins.annotate(log_count=Count('versions__logs')).order_by('log_count')  
                case PluginVersionView.ORDER_CREATE:
                    plugins = plugins.order_by('-created_at')
                case PluginVersionView.ORDER_UPDATE:
                    plugins = plugins.order_by('-versions__created_at')                
        #怎么获取最新的插件版本 item.versions.first() 这里要特殊处理下
        result = []
        for item in plugins:
            newest_version = item.versions.order_by('-id').first()
            tags = [tag.text for tag in item.tags.all()]
            if param.category_id:
                for category in item.categories.filter(id__in=category_ids) if category_ids != None else item.categories.all():
                    result.append({'id':item.id, 'version_id':newest_version.id, 'version_no':newest_version.version_no, 'name':item.name, 'icon_url':item.icon_url, 'attachment_url':newest_version.attachment_url, 'attachment_size':newest_version.attachment_size, 'execution_file_path':newest_version.execution_file_path,'type':item.type, 'link':item.link,'category':category.name, 'tags': tags })
            else:
                result.append({'id':item.id, 'version_id':newest_version.id, 'version_no':newest_version.version_no, 'name':item.name, 'icon_url':item.icon_url, 'attachment_url':newest_version.attachment_url, 'attachment_size':newest_version.attachment_size, 'execution_file_path':newest_version.execution_file_path,'type':item.type, 'link':item.link, 'tags': tags })

        return JsonResponse(result)
    
    '''
    发布新版本信息
    '''
    @admin_required
    def post(self, request:HttpRequest):
        version, error = JsonParser(
            Argument('app_id',  data_type=int, required=True, filter_func=lambda id: Plugin.objects.filter(id=id).exists()),
            Argument('version_no', data_type=str, required=True),
            Argument('description', data_type=str, required=True),
            Argument('attachment_url', data_type=str, required=True, help=f"请确认文件上传完成或填写文件链接"),
            Argument('attachment_size', data_type=int, required=False, nullable=True),
            Argument('is_external', data_type=bool, required=False),
            Argument('execution_file_path', data_type=str, required=False),
            Argument('authors', data_type=list, required=False),
        ).parse(request.body)
        if error:
            return JsonResponse(error_message=error)
        plugin = Plugin.objects.filter(id=version.app_id).first()
        if plugin.type == Plugin.TYPE_APPLICATION and version.execution_file_path is None :
            return JsonResponse(error_message=f"应用入口{__FILED_REQUIRED__}")
        if PluginVersion.objects.filter(Q(plugin__id=version.app_id)&Q(version_no=version.version_no)).exists() :
            return JsonResponse(error_message=f"插件版本号{__FILED_EXISTS__}")
        pluginVersionObj = None
        with transaction.atomic():
            savepoint_id = transaction.savepoint()
            try:
                developers = []
                for developer in version.authors:
                    if developer.get('name','') == '':
                        return JsonResponse(error_message=f"开发者名字{__FILED_REQUIRED__}")
                    developer, created = Developer.objects.get_or_create(name=developer.get('name'),phone=developer.get('phone', ''),email=developer.get('email','')) 
                    developers.append(developer)
                pluginVersionObj = PluginVersion.objects.create(
                    plugin=plugin,
                    version_no=version.version_no,
                    description=version.description,
                    attachment_url=version.attachment_url,
                    attachment_size=version.attachment_size,
                    execution_file_path=version.execution_file_path,
                    created_user=request.account
                )
                pluginVersionObj.authors.set(developers)
            except Exception as e:
                transaction.savepoint_rollback(savepoint_id)
                # 事务继续，但是撤销到了savepoint_id指定的状态
                loguru.logger.error(f"创建失败: {e}")
                return JsonResponse(error_message=e)
        return JsonResponse(pluginVersionObj.id)
    
    @admin_required
    def patch(self, request:HttpRequest):
        version, error = JsonParser(
            Argument('id', data_type=int, required=True, filter_func=lambda id: PluginVersion.objects.filter(id=id).exists()),
            Argument('version_no', data_type=str, required=True),
            Argument('description', data_type=str, required=True),
            Argument('developers', data_type=list, required=False),
        ).parse(request.body)
        if error:
            return JsonResponse(error_message=error)
        # if Plugin.objects.filter(name=plugin.name).exclude(id=plugin.id).exists() :
        #     return JsonResponse(error_message=f"插件名称{__FILED_EXISTS__}")
        with transaction.atomic():
            savepoint_id = transaction.savepoint()
            try:
                pluginVersionObj = PluginVersion.objects.filter(id=version.id).first()
                pluginVersionObj.description = version.description
                pluginVersionObj.version_no = version.version_no

                if version.developers is not None:
                    developers = []
                    for developer in version.developers:
                        if developer.get('name','') == '':
                            transaction.savepoint_rollback(savepoint_id)
                            return JsonResponse(error_message=f"开发者名字{__FILED_REQUIRED__}")
                        developer_id = int(developer.get('id',0))
                        if developer_id > 0:
                            if Developer.objects.filter(id=developer_id).exists():
                                developer_obj = Developer.objects.filter(id=developer_id).first()
                                developer_obj.name = developer.get('name')
                                developer_obj.phone = developer.get('phone', '')
                                developer_obj.email = developer.get('email','')
                                developer_obj.save()
                            else:
                                transaction.savepoint_rollback(savepoint_id)
                                return JsonResponse(error_message=f"不存在的开发者id-{developer_id}")
                        else:
                            developer_obj, created = Developer.objects.get_or_create(name=developer.get('name'),phone=developer.get('phone', ''),email=developer.get('email','')) 
                        developers.append(developer_obj)
                    pluginVersionObj.authors.set(developers)
                    
                pluginVersionObj.save()
                return JsonResponse(status_code=HttpStatus.HTTP_200_OK)
    
            except Exception as e:
                transaction.savepoint_rollback(savepoint_id)
                # 事务继续，但是撤销到了savepoint_id指定的状态
                loguru.logger.error(f"更新失败: {e}")
                return JsonResponse(error_message=e)


    @admin_required
    def delete(self, request:HttpRequest):
        plugin_version, error = JsonParser(
            Argument('id', data_type=int, required=True, filter_func=lambda id: PluginVersion.objects.filter(id=id).exists()),
        ).parse(request.GET)
        if error:
            return JsonResponse(error_message=error)
        obj:PluginVersion = PluginVersion.objects.filter(id=plugin_version.id).first()

        if obj.deleted_at is not None:
            return JsonResponse(status_code=HttpStatus.HTTP_204_NO_CONTENT)
        if PluginVersion.objects.filter(plugin__id=obj.plugin_id).count() == 1:
            return JsonResponse(error_message=__VERSION_DELETE_REQUIRE_ERR__)
        obj.deleted_at = timezone.now()
        obj.deleted_user = request.account
        obj.save()
        return JsonResponse(status_code=HttpStatus.HTTP_200_OK)
        
#插件版本信息
class PluginVersionListView(View):
    @admin_required
    def get(self, request:HttpRequest):
        param, error = JsonParser(
            Argument('current', data_type=int, required=False),
            Argument('page_size', data_type=int, required=False),
        ).parse(request.GET)
        if error:
            return JsonResponse(error_message=error)
        # 从所有插件开始
        pluginVersions = PluginVersion.objects.all()
        page_data = paginate_data(pluginVersions, 
                                  current=param.current if param.current != None else 1, 
                                  page_size=param.page_size if param.page_size != None else 10, 
                                  item_handler=lambda pluginVersion:
                                    {
                                    'id':pluginVersion.id, 
                                    'plugin_id':pluginVersion.plugin.id, 
                                    'plugin_name':pluginVersion.plugin.name, 
                                    'version_no': pluginVersion.version_no, 
                                    'description':pluginVersion.description,
                                    'publish_date':pluginVersion.publish_date,
                                    'developers': [{'id': author.id, 'name': author.name, 'email': author.email, 'phone': author.phone} for author in pluginVersion.authors.all()],
                                    'use_count': pluginVersion.logs.count()
                                    })
        return JsonResponse(page_data)

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
        if (form.parent_id != None and PluginCategory.objects.filter(name=form.name, parent__id=form.parent_id).exists()) or (form.parent_id == None and PluginCategory.objects.filter(name=form.name).exists()):
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
        plugin = PluginCategory.objects.filter(id=form.id).first()
        if (plugin.parent_id != None and PluginCategory.objects.filter(name=form.name, parent__id=plugin.parent_id).exclude(id=form.id).exists()) or (plugin.parent_id == None and PluginCategory.objects.filter(name=form.name).exclude(id=form.id).exists()):
            return JsonResponse(error_message=f'分类名称:({form.name}){__FILED_EXISTS__}')
        return JsonResponse(PluginCategory.objects.filter(id=form.id).update(name=form.name))
    
    @admin_required
    def delete(self, request:HttpRequest):
        request_obj, error = JsonParser(
            Argument('id', data_type=int, required=True, filter_func=lambda id: PluginCategory.objects.filter(id=id).exists()),
        ).parse(request.GET)
        if error:
            return JsonResponse(error_message=error)
       
        with transaction.atomic():
            savepoint_id = transaction.savepoint()
            try:
                children:PluginCategory = PluginCategory.objects.filter(parent__id=request_obj.id)
                for child in children:
                    child.deleted_at = timezone.now()
                    child.deleted_user = request.account
                    child.save()
                obj:PluginCategory = PluginCategory.objects.filter(id=request_obj.id).first()

                if obj.deleted_at is not None:
                    return JsonResponse(status_code=HttpStatus.HTTP_204_NO_CONTENT)

                obj.deleted_at = timezone.now()
                obj.deleted_user = request.account
                obj.save()
                return JsonResponse(status_code=HttpStatus.HTTP_200_OK)
            except Exception as e:
                transaction.savepoint_rollback(savepoint_id)
                # 事务继续，但是撤销到了savepoint_id指定的状态
                loguru.logger.error(f"删除失败: {e}")
                return JsonResponse(error_message=e)
 
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
            Argument('current', data_type=int, required=False),
            Argument('page_size', data_type=int, required=False),
        ).parse(request.GET)
        if error:
            return JsonResponse(error_message=error)
        try:
            if param.view == self.VIEW_MAIN:
                categories = list(PluginCategory.objects.filter(parent=None))
                page_data = paginate_data(categories, 
                                          current=param.current if param.current != None else 1, 
                                          page_size=param.page_size if param.page_size != None else 10, 
                                          item_handler=lambda category:
                                          {'id':category.id, 'name':category.name, 'children_count': category.children.count(), 'app_count': category.children.aggregate(appcount=models.Count('plugin_category'))['appcount'] } )
                return JsonResponse(page_data)
            else:
                categories = list(PluginCategory.objects.filter(parent__isnull=False))
                page_data = paginate_data(categories, 
                                          current=param.current if param.current != None else 1, 
                                          page_size=param.page_size if param.page_size != None else 10, 
                                          item_handler=lambda category:
                                          {'id':category.id, 'name':category.name, 'parent_name':category.parent.name, 'app_count': category.plugin_category.count() })
                return JsonResponse(page_data)
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
            'is_external': pluginVersionObj.plugin.is_external, 
            'description':pluginVersionObj.plugin.description,
            'update_description':pluginVersionObj.description,
            'link':pluginVersionObj.plugin.link,
            'update_description':pluginVersionObj.description,
            'attachment_url':pluginVersionObj.attachment_url,
            'attachment_size':pluginVersionObj.attachment_size,
            'execution_file_path':pluginVersionObj.execution_file_path,
            'publish_date':pluginVersionObj.publish_date,
            'tags':[item.text for item in pluginVersionObj.plugin.tags.all()],
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
    
 