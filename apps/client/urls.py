from django.urls import path
from .views import *

urlpatterns = [
    path('/version_check', DesktopClientVersionView.as_view()),
]