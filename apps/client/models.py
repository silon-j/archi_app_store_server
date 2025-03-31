from libs.boost.mixin import ModelMixin
from django.db import models


class ClientVersion(ModelMixin):
    
    major_version = models.IntegerField(null= False, verbose_name='主版本号')
    minor_version = models.IntegerField(null= False, verbose_name='次版本号')
    patch_version = models.IntegerField(null= False, verbose_name='修订号')
    is_active = models.BooleanField(null=False, default=True)
    is_latest = models.BooleanField(null=False, default=False)
    description = models.TextField(verbose_name='更新说明', default='')
    version_str = models.CharField(max_length=32, null=False)
    cos_dir = models.URLField(null=False, verbose_name='下载地址', max_length=512)
    sha512_hash = models.CharField(max_length=128, default='')
    size = models.BigIntegerField(default=0)

    class Meta:
        db_table = 'client'
        ordering = ('-id',)
        indexes = [
            models.Index(fields=['version_str']),
            models.Index(fields=['major_version', 'minor_version', 'patch_version']),
        ]
        unique_together = [
            ('major_version', 'minor_version', 'patch_version'), 
        ]
