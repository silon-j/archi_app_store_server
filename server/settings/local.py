from .base import *
from loguru import logger

logger.info("You are using settings.local")

DEBUG = True

ALLOWED_HOSTS = ['*']

INSTALLED_APPS.append('rest_framework')
INSTALLED_APPS.append('drf_yasg')