from django.urls import path
from apps.demo.views import *

# 在server 的urls.py中使用include添加该路由路径
urlpatterns = [
    path('base', base_req.as_view()),
    path('class', ClassRequestView.as_view()),
]