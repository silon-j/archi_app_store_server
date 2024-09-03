from django.db import models
from apps.account.models import Account
from libs.boost.mixin import ModelMixin


class ModelAudit(ModelMixin):
    """审计模型类，提供操作Account
    """
    created_user = models.ForeignKey(Account, on_delete=models.SET_NULL, verbose_name='创建人', related_name='+', null=True)
    updated_user = models.ForeignKey(Account, on_delete=models.SET_NULL, verbose_name='更新人', related_name='+', null=True)
    deleted_user = models.ForeignKey(Account, on_delete=models.SET_NULL, verbose_name='删除人', related_name='+', null=True)

    class Meta:
        """在 Meta 类中填入 abstract=True。该模型将不会创建任何数据表。
        当其用作其它模型类的基类时，它的字段会自动添加至子类
        """
        abstract = True
