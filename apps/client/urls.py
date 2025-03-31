from django.urls import path
from .views import *

urlpatterns = [
    path('/latest.yml', DesktopClientVersionView.as_view()),
]