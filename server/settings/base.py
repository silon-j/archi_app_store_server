import os
import re
from pathlib import Path
import environ

# 获取当前文件的路径，即 base.py 的路径
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# 回退两级目录到 server 的父目录
PROJECT_ROOT = os.path.dirname(os.path.dirname(BASE_DIR))

# 定义 .env 文件的路径
env_file = os.path.join(PROJECT_ROOT, '.env')

# 初始化 environ
env = environ.Env(
    # 设置类型和默认值
    KEYS_TO_CAMEL_CASE=(bool, True),
    DATABASE_POSTGRES_NAME=(str, ''),
    DATABASE_POSTGRES_PASSWORD=(str, ''),
    DATABASE_POSTGRES_USER=(str, ''),
    DATABASE_POSTGRES_HOST=(str, ''),
    DATABASE_POSTGRES_PORT=(str, '')
)

# 读取 .env 文件
env.read_env(env_file)

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent


# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/3.2/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = "django-insecure-^%j97cwg1g0m=%jf14ntfid25+rjt2pi@jyx9)16ehamlo&#28"

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

ALLOWED_HOSTS = ['localhost', '127.0.0.1']


# # 从环境变量中获取额外的主机
# extra_hosts = os.getenv('EXTRA_ALLOWED_HOSTS', '')

# # 如果 EXTRA_ALLOWED_HOSTS 有值，则将其分割后追加到 ALLOWED_HOSTS
# if extra_hosts:
#     ALLOWED_HOSTS += extra_hosts.split(',')

# print(f"Allowed Hosts: {ALLOWED_HOSTS}")


# Application definition
INSTALLED_APPS = [
    'apps.account.apps.AccountConfig',
    # 'apps.plugin',
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
]



MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    # "django.middleware.csrf.CsrfViewMiddleware",
    'libs.middleware.AuthenticationMiddleware',
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = 'server.urls'

WSGI_APPLICATION = "server.wsgi.application"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]


# Database
# https://docs.djangoproject.com/en/3.2/ref/settings/#databases
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': os.getenv('DATABASE_POSTGRES_NAME'),
        'USER': os.getenv('DATABASE_POSTGRES_USER'),
        'PASSWORD': os.getenv('DATABASE_POSTGRES_PASSWORD'),
        'HOST':  os.getenv('DATABASE_POSTGRES_HOST'),
        'PORT': os.getenv('DATABASE_POSTGRES_PORT'),
    }
}

# Set The Cache DataBase as Django Default cache database
# If need persistent data can upgrade to redis or leveldb.
CACHED = {
    'default': {
        'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
        'LOCATION': 'unique-snowflake',
    }
}


# Internationalization
# https://docs.djangoproject.com/en/3.2/topics/i18n/

LANGUAGE_CODE = 'zh-hans'

TIME_ZONE = 'Asia/Shanghai'

USE_I18N = True

USE_L10N = True

USE_TZ = True


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/3.2/howto/static-files/

STATIC_URL = '/static/'

# Default primary key field type
# https://docs.djangoproject.com/en/3.2/ref/settings/#default-auto-field

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

CACHES = {
    "default": {
        "BACKEND": "django.core.cache.backends.locmem.LocMemCache",
    }
}

AUTHENTICATION_EXCLUDES = (
    re.compile('/api/v1/account/.*'),
)

TOKEN_TTL = 7 * 24 * 3600

# cors settings
CORS_ALLOW_CREDENTIALS = True
CORS_ALLOW_HEADERS  =  [ 
    "accept" , 
    "accept-encoding" , 
    "authorization" , 
    "content-type" , 
    "dnt" , 
    "origin" , 
    "user-agent" , 
    "x-csrftoken" , 
    "x-requested-with" , 
    'timestamp',
    'nonce',
    'sign',
    'appid'
]
CORS_ALLOW_ALL_ORIGINS = True
# CORS_ORIGIN_WHITELIST = (
#     '*',
# )

"""
email server
"""
DEFAULT_EMAIL_ACCOUNT = os.environ.get('DEFAULT_EMAIL_ACCOUNT')
DEFAULT_EMAIL_PASSWORD = os.environ.get('DEFAULT_EMAIL_PASSWORD')

# json_response key_type 默认小驼峰
# 获取环境变量REDIS_HOST
# KEYS_TO_CAMEL_CASE = env.bool('KEYS_TO_CAMEL_CASE') # 这种也可以，使用这种方式获取，上面就不需要定义类型了
KEYS_TO_CAMEL_CASE = env('KEYS_TO_CAMEL_CASE')