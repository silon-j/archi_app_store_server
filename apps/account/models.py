from django.db import models
from django.contrib.auth.hashers import make_password, check_password
from libs.boost.mixin import ModelMixin
from enum import Enum
from django.db.models import UniqueConstraint
import uuid

# Create your models here.
class Account(ModelMixin):
    # 文档中描述的账号->首字母加工号
    username = models.CharField(max_length = 20)
    # 真实姓名
    fullname = models.CharField(max_length = 20)
    # 所属部门
    department = models.CharField(max_length = 20)
    password_hash = models.CharField(max_length = 100)
    email = models.CharField(max_length=100, null=True)
    # 是否管理员
    can_admin = models.BooleanField(default=False)
    is_super= models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    access_token = models.UUIDField(default=uuid.uuid4, null=True, blank=True)
    token_expired = models.DateTimeField(null=True, default=None)
    last_login = models.DateTimeField(null=True, default=None)
    last_ip = models.CharField(max_length=20)

    @staticmethod
    def make_password(plain_password: str) -> str:
        return make_password(plain_password, hasher='pbkdf2_sha256')

    def verify_password(self, plain_password: str) -> bool:
        return check_password(plain_password, self.password_hash)

    def __repr__(self):
        return '<Account %r>' % self.username

    class Meta:
        db_table = 'account'
        ordering = ('-id',)
        constraints = [
            UniqueConstraint(fields=['username'], name='unique_username')
        ]


class LoginLog(ModelMixin):
    username = models.CharField(max_length=20)
    ip = models.CharField(max_length=50)
    agent = models.CharField(max_length=255, null=True)
    message = models.CharField(max_length=255, null=True)
    is_success = models.BooleanField(default=True)

    class Meta:
        db_table = 'login_log'
        ordering = ('-id',)

            
class EmailAuthCodeChoice(models.IntegerChoices):
    # 注册
    REGISTER = (1, "用户注册")
    # 重置密码
    PASSWORD = (2, "修改密码")


class AccountEmailAuthCode(ModelMixin):
    """
    邮箱验证码
    """    

    email = models.EmailField(max_length=255)
    code = models.CharField(max_length=10)
    is_valid = models.BooleanField(default=True)
    is_success = models.BooleanField(default=False)
    expired = models.DateTimeField(null=True, default=None)    
    for_what = models.SmallIntegerField(choices=EmailAuthCodeChoice.choices, null=False)

    class Meta:
        db_table = 'account_email_auth_code'
        ordering = ('-id',)
