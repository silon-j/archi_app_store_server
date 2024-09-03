from django.urls import path

from .views import *

urlpatterns = [
    path('/cos-credential', CosTempCredentialView.as_view()),
    path('/category', PluginCategoryView.as_view(), name='plugin-category'),
    path('', PluginView.as_view(), name='plugin'),
    path('/version', PluginVersionView.as_view(), name='plugin-version'),
    path('/version/detail', PluginVersionDetailView.as_view(), name='plugin-detail'),
    path('/version/log', OperationLogView.as_view(), name='plugin-log')
]