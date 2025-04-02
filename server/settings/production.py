from .base import *
from loguru import logger

logger.info("You are using settings.production")

DEBUG = False

ALLOWED_HOSTS = ['*']