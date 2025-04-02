from django.urls import path
from .views import *

urlpatterns = [
    path('/latest', DesktopClientVersionView.as_view()),
]