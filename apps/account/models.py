from django.db import models
from django.utils import timezone
from libs.boost.mixin import ModelMixin
import uuid
from typing import Any

# Create your models here.
class ModelAccount(ModelMixin):
    # 用户表主键
    id: uuid.UUID = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    # 工号，如35529
    username: str = models.CharField(max_length=20)  # 账号-工号
    # 员工真实姓名
    name : str = models.CharField(max_length=100)
    # 员工所属部门
    department = models.CharField(max_length=100)
    # @ecadi.com结尾的公司邮箱
    email = models.EmailField()
    # 密码哈希值
    password_hash = models.CharField(max_length=100)
    # Token值
    access_token = models.CharField(max_length=50,default='')
    # Token有效期
    token_expired = models.DateTimeField(default=timezone.now)
    # 是否是管理员
    is_super = models.BooleanField(default=False)

    def __str__(self) -> str:
        return f"{self.username}: {self.name}, {self.department}"

    class Meta:
        db_table='app_account'

