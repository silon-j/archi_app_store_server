from django.db import models
from apps.account.models import Account
from django.utils import timezone

from libs.boost.mixin import ModelMixin
from utils.mixin import ModelAudit

# 标签信息
class Tag(ModelMixin):
    text = models.CharField(max_length=200, unique=True)
    def __str__(self):
        return self.text
    class Meta:
        db_table = 'plugin_tag'
        ordering = ('-id',)
    
# 开发者信息
class Developer(ModelMixin):
    name = models.CharField(max_length=200)
    phone = models.CharField(max_length=50)
    email = models.EmailField(max_length=50)
    def __str__(self):
        return self.name
    class Meta:
        db_table = 'plugin_developer'
        ordering = ('-id',)

# 插件分类信息
class PluginCategory(ModelAudit):
    name = models.CharField(max_length=200)
    parent = models.ForeignKey(
        'self',  # 外键指向自身
        on_delete=models.SET_NULL,  # 如果父类型被删除，将该字段设置为NULL
        null=True,  # 允许该字段为空
        blank=True,  # 允许表单不填写该字段
        related_name='children',  # 给反向关系命名，方便访问子类型
        verbose_name="父级分类"
    )
    def __str__(self):
        return self.name
    class Meta:
        db_table = 'plugin_category'
        ordering = ('-id',)

# 插件信息
class Plugin(ModelAudit):
    TYPE_PLUGIN=1
    TYPE_APPLICATION=2
    TYPE_LINK=3
    TYPES_CHOICES = (
        (TYPE_PLUGIN, '插件'),
        (TYPE_APPLICATION, '应用'),
        (TYPE_LINK, '链接'),
    )
    name = models.CharField(max_length=200)
    type = models.IntegerField(choices=TYPES_CHOICES, default=TYPE_LINK, verbose_name='版本类别')
    icon_url = models.URLField('插件图标')
    categories = models.ManyToManyField(PluginCategory, related_name='plugin_category', db_table='r_plugin_category')
    def __str__(self):
        return self.name
    class Meta:
        db_table = 'plugin'
        ordering = ('-id',)
    
# 插件版本信息
class PluginVersion(ModelAudit):
    STATUS_NEW=1
    STATUS_PENDING=2
    STATUS_APROVE=3
    STATUS_PULISH=4
    STATUS_FAIL=5

    STATUSES_CHOICES = [
        (STATUS_NEW, '新建'),
        (STATUS_PENDING, '待审核'),
        (STATUS_APROVE, '已审核'),
        (STATUS_PULISH, '发布'),
        (STATUS_FAIL, '审核不通过'),
    ]
    plugin = models.ForeignKey(Plugin, on_delete=models.CASCADE, related_name='versions')
    version_no = models.CharField(max_length=50,verbose_name='版本号')
    description = models.TextField(verbose_name='版本说明')
    attachment_url = models.URLField(verbose_name='文件链接') #文件链接
    attachment_size = models.BigIntegerField(verbose_name='文件大小', null=True)
    execution_file_path = models.CharField(max_length=200,verbose_name='应用入口',null=True,blank=True)
    authors = models.ManyToManyField(Developer, db_table='r_plugin_version_developer')
    tags = models.ManyToManyField(Tag, related_name='tags',db_table='r_plugin_version_tag')
    status = models.IntegerField(choices=STATUSES_CHOICES, default=STATUS_NEW, verbose_name='状态')
    publish_date = models.DateTimeField("发布时间", default=timezone.now)
    def __str__(self):
        return self.plugin.name
    class Meta:
        db_table = 'plugin_version'
        ordering = ('-id',)

# 插件版本操作信息
class OperationLog(ModelMixin):
    TYPE_OPEN=1
    TYPE_INSTALL=2
    TYPE_RUN=3
    TYPES_CHOICES = [
        (TYPE_OPEN, '打开'),
        (TYPE_INSTALL, '安装'),
        (TYPE_RUN, '运行'),
    ]
    version = models.ForeignKey(PluginVersion, on_delete=models.CASCADE, related_name='logs')
    created_user = models.ForeignKey(Account, on_delete=models.CASCADE, verbose_name='操作者')
    type = models.IntegerField(choices=TYPES_CHOICES, default=TYPE_OPEN, verbose_name='操作类型')
    
    def __str__(self):
        return self.created_user.username + '-' + self.version.plugin.name + '-' + self.version.version_no
    class Meta:
        db_table = 'plugin_operation_log'
        ordering = ('-id',)