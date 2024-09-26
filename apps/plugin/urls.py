from django.urls import path

from .views import *

urlpatterns = [
    path('/cos-credential', CosTempCredentialView.as_view()),
    path('/category', PluginCategoryView.as_view(), name='plugin-category'),
    path('', PluginView.as_view(), name='plugin'),
    path('/list', PluginListView.as_view(), name='plugin-list'),
    path('/version', PluginVersionView.as_view(), name='plugin-version'),
    path('/version/list', PluginVersionListView.as_view(), name='plugin-version-list'),
    path('/version/detail', PluginVersionDetailView.as_view(), name='plugin-detail'),
    path('/version/log', OperationLogView.as_view(), name='plugin-log'),
    path('/category/list', PluginCategoryListView.as_view(), name='category-list'),
]