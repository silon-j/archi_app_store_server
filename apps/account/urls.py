from django.urls import path
from apps.account.Views.login_view import UserView
from apps.account.Views.request_mail_verify_view import RequestMailVerifyView

urlpatterns = [
    path('mailverify/', UserView.as_view(), name='user-list'),
    path('login/', RequestMailVerifyView.as_view(), name='product-list'),
]