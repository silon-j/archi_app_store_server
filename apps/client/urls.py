from django.urls import path
from .views import *

urlpatterns = [
    path('/latest.yml', DesktopClientVersionYmlView.as_view()),
    path('/latest', DesktopClientVersionView.as_view()),
]