"""
Django settings for server project.

Generated by 'django-admin startproject' using Django 4.2.

For more information on this file, see
https://docs.djangoproject.com/en/4.2/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/4.2/ref/settings/
"""

import os
import re
import environ
from pathlib import Path
from loguru import logger

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent.parent

# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/4.2/howto/deployment/checklist/

logger.info("server starting...")

"""
环境变量配置
"""
# 初始化
env_file = os.path.join(BASE_DIR, '.env')
env = environ.Env(
    # 设置参数和默认值
    DATABASE_POSTGRES_NAME=(str, ''),
    DATABASE_POSTGRES_USER=(str, ''),
    DATABASE_POSTGRES_PASSWORD=(str, ''),
    DATABASE_POSTGRES_HOST=(str, ''),
    DATABASE_POSTGRES_PORT=(str, ''),
    # MYSQL_ALLOWED_TIME_ZONE=(str, ''),
)
env.read_env(env_file=env_file)


"""
服务端基础配置
"""
# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = 'django-insecure-x4o+k48k)@x78zc&1m35yphbnj-yp2&0xr$e_9g%1=qi4vea93'

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = False

ALLOWED_HOSTS = ['localhost', '127.0.0.1']
# 从环境变量中获取额外的主机
extra_hosts = os.getenv('EXTRA_ALLOWED_HOSTS', '')
if extra_hosts:
    ALLOWED_HOSTS += extra_hosts.split(',')

ROOT_URLCONF = 'server.urls'

WSGI_APPLICATION = 'server.wsgi.application'

STATIC_URL = '/static/'

"""
django 系统检查配置
"""
# settings.py
SILENCED_SYSTEM_CHECKS = ['urls.W002']


"""
时区及语言
https://docs.djangoproject.com/en/4.2/topics/i18n/
"""
LANGUAGE_CODE = 'zh-hans'

TIME_ZONE = 'Asia/Shanghai'

USE_I18N = True

USE_L10N = True

USE_TZ = True

"""
注册应用及中间件

本项目不使用django自带后台及账户系统，如需可自行加入
app
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',

middleware
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
"""
INSTALLED_APPS = [
    'corsheaders',
    'apps.account',
    'apps.plugin',
]

MIDDLEWARE = [
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.security.SecurityMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'libs.boost.middleware.HandleExceptionMiddleware',
    'libs.boost.middleware.LogRequestMiddleware',
    'libs.boost.middleware.CamelToSnakeMiddleware',
    'libs.boost.middleware.AutoRequestPostMiddleware',
    'utils.middleware.AuthenticationMiddleware',
]


"""
database配置
https://docs.djangoproject.com/en/4.2/ref/settings/#databases
"""
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'
DATABASES = {

    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': env('DATABASE_POSTGRES_NAME').strip(),
        'USER': env('DATABASE_POSTGRES_USER').strip(),
        'PASSWORD': env('DATABASE_POSTGRES_PASSWORD').strip(),
        'HOST': env('DATABASE_POSTGRES_HOST').strip(),
        'PORT': env('DATABASE_POSTGRES_PORT').strip(),
        # 'TIME_ZONE': env('MYSQL_ALLOWED_TIME_ZONE').strip(),
    }
}

# Set Cache
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
        'LOCATION': 'unique-snowflake',
    }
}


"""
用户认证配置
"""
# token校验白名单
AUTHENTICATION_EXCLUDES = (
    re.compile(r'^/api/v\d+/account/(?!admin).*'),
)

# token过期时间
AUTHENTICATION_EXPIRE_TIME = 3600 * 24 * 7

# 邮箱验证码过期时间
VERIFY_CODE_EXPIRED = 5

"""
cors settings
"""
CORS_ORIGIN_ALLOW_ALL = False
CORS_ALLOW_CREDENTIALS = True
CORS_ALLOW_HEADERS = [
    "accept",
    "accept-encoding",
    "authorization",
    "content-type",
    "dnt",
    "origin",
    "user-agent",
    "x-csrftoken",
    "x-requested-with",
    'X-Token',
    'timestamp',
    'nonce',
    'sign',
    'appid'
]
CORS_ORIGIN_WHITELIST = (
    'http://localhost:3000',
)

"""
邮箱配置
"""
DEFAULT_EMAIL_ACCOUNT = os.environ.get('DEFAULT_EMAIL_ACCOUNT')
DEFAULT_EMAIL_PASSWORD = os.environ.get('DEFAULT_EMAIL_PASSWORD')

# 文件上传配置
# MEDIA_ROOT = os.path.join(BASE_DIR, 'media')
# MEDIA_URL = '/media/'
