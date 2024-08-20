from django.db import models

class SoftDeleteQuerySet(models.QuerySet):
    """拓展QuerySet，默认只查询未删除的数据，提供新方法all_with_deleted，获取所有数据（包括已删除）"""
    def all(self):
        return self.filter(deleted_at__isnull=True)
    
    def all_with_deleted(self):
        return self.all()


class SoftDeleteManager(models.Manager):
    """拓展Manager，支持软删除"""
    def get_queryset(self):
        return SoftDeleteQuerySet(self.model, using=self._db)

class ModelMixin(models.Model):
    """模型混入类，提供必备默认字段及常用对象操作方法
    """
    created_at = models.DateTimeField(auto_now_add=True)
    deleted_at = models.DateTimeField(null=True, default=None)  # 标记伪删除状态
    last_update = models.DateTimeField(auto_now=True)

    # 限制class绑定新属性
    __slots__ = ()

    class Meta:
        """在 Meta 类中填入 abstract=True。该模型将不会创建任何数据表。
        当其用作其它模型类的基类时，它的字段会自动添加至子类
        """
        abstract = True

    def to_dict(self, excludes: tuple = None, selects: tuple = None) -> dict:
        """将对象所有属性输出为dict

        Args:
            excludes (tuple, optional): 不包含的属性. Defaults to None.
            selects (tuple, optional): 仅指定属性输出. Defaults to None.

        Raises:
            TypeError: 对象不是 django Model 对象
        Returns:
            dict: Model 实例的所有属性
        """
        if not hasattr(self, '_meta'):
            raise TypeError('<%r> is not a django.db.models.Model object.' % self)
        elif selects:
            return {f: getattr(self, f) for f in selects}
        elif excludes:
            return {f.attname: getattr(self, f.attname) for f in self._meta.fields if f.attname not in excludes}
        else:
            return {f.attname: getattr(self, f.attname) for f in self._meta.fields}


    def update_by_dict(self, data: dict):
        """通过字典按需更新实例
        Args:
            data (dict): 待更新的数据
        """
        for k, v in data.items():
            if hasattr(self, k):
                setattr(self, k, v)
        self.save(update_fields=data.keys())